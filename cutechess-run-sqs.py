#!/j/Python27/python
# -*- coding: utf-8 -*-

"""
This script will get cutechess-cli run requests from a SQS queue
and will run those requests, writing the results to another queue

Usage: cutechess-run-sqs.py
"""

# TODO:
# - queues must be in EU zone

from subprocess import Popen, PIPE
import sys
import exceptions
import os
import time
import json
import boto

# Our cutechess-cli queues:
cli_inp_queue = 'cliqueue'
cli_out_queue = 'clioutqu'

# Path to the cutechess-cli executable.
# On Windows this should point to cutechess-cli.exe
cutechess_cli_path = 'J:/Chess/cutechess-cli-0.5.1-win32/cutechess-cli.exe'

# Commands parameters per engine will be formatted like this
engine_param = 'name={name} cmd={cmd} dir={dir}'

# Directories where to search for engines
searchpaths = [
        'J:/AbaAba/dist/build/Abulafia',
        'J:/AbaAba/dist/build/AbaAba',
        'J:/Engines/AbaAba'
    ]

# Additional cutechess-cli options, eg. time control and opening book
proto   = '-each proto=uci tc={tc}'
term    =  ' -draw 80 1 -resign 5 500'
engines = ' -engine {fcp} -engine {scp}'
pgnout  = ' -pgnout {pout}'
event   = ' -event {tour}'

options = proto + term + engines + pgnout + event

def find_engine(eng):
    if eng.endswith('.exe'):
        ext1 = eng
        ext0 = eng[:-4]
    else:
        ext0 = eng
        ext1 = eng + ".exe"
    for dir in searchpaths:
        dext0 = dir + '/' + ext0
        dext1 = dir + '/' + ext1
        if os.access(dext0, os.R_OK):
            return (dir, ext0)
        elif os.access(dext1, os.R_OK):
            return (dir, ext1)
    raise Exception(eng)

def read_queue_message(queue, times, tout):
    while (times > 0):
        mes = queue.read()
        if mes == None:
            print "No message, sleep %s seconds" % tout
            time.sleep(tout)
            times = times - 1
            tout  = tout * 2
        else:
            return mes
    return None

def main(argv = None):
    try:
        conn = boto.connect_sqs()
        iqueue = conn.get_queue(cli_inp_queue)
        oqueue = conn.get_queue(cli_out_queue)
    except Exception as e:
        print "Problem getting the cutechess-cli queue: ", e
        return 2

    # Now we have the queue, take messages in a loop and execute them
    while True:
        mes = read_queue_message(iqueue, 3, 15)
        if mes == None:
            print "No further messages, exit."
            return 0
    
        str = mes.get_body()
        dmes = json.loads(str)
    
        # If message has not the requested keys, ignore it:
        if not ('engines' in dmes and 'each' in dmes):
            continue

        engs = dmes['engines']
        eng1 = engs[0]['name']
        eng2 = engs[1]['name']

        proto = dmes['each']['proto']
        tc    = dmes['each']['tc']

        try:
            (fpath, fexc) = find_engine(eng1)
            (spath, sexc) = find_engine(eng2)
        except Exception as e:
            print 'Engine not found: ', e
            return 2
    
        print "Eng1 = ", fexc, ' on ', fpath
        print "Eng2 = ", sexc, ' on ', spath
    
        fcp = engine_param.format(name=eng1, cmd=fexc, dir=fpath)
        scp = engine_param.format(name=eng2, cmd=sexc, dir=spath)

        if 'tour' in dmes:
            tour = dmes['tour']
        else:
            tour = 'test'
    
        pout = "%s_%s_%s.pgn" % (eng1, eng2, time.strftime('%Y%m%d%H%M%S', time.localtime()))
    
        cutechess_args = options.format(tc=tc, fcp=fcp, scp=scp, pout=pout, tour=tour)
        command = '%s %s' % (cutechess_cli_path, cutechess_args)
    
        print "Start %s against %s with %s" % (eng1, eng2, tc)

        # Run cutechess-cli and wait for it to finish
        process = Popen(command, shell = True, stdout = PIPE)
        output = process.communicate()[0]
        if process.returncode != 0:
            print 'Could not execute command: %s' % command
            return 2
        
        # Convert Cutechess-cli's result into W/L/D
        # Note that only one game should be played
        result = -1
        for line in output.splitlines():
            print line
            if line.startswith('Finished game'):
                if line.find(": 1-0") != -1:
                    result = 0
                elif line.find(": 0-1") != -1:
                    result = 1
                elif line.find(": 1/2-1/2") != -1:
                    result = 2
                else:
                    print 'The game did not terminate properly'
                    return 2
                break

        res = {
                'tour'    : tour,
                'engines' : dmes['engines'],
                'result'  : result
            }

        # Write the result in the output queue:
        status = False
        try:
            outmes = boto.sqs.message.Message()
            outmes.set_body(json.dumps(res))

            status = oqueue.write(outmes)
        except Exception as e:
            print "An error occured: ", e
        if not status:
            print "We could not write the result to the output queue!"
            return 2

        # Delete the message:
        iqueue.delete_message(mes)
        
        if result == 0:
            print eng1, 'wins'
        elif result == 1:
            print eng1, 'looses'
        elif result == 2:
            print 'Draw'

if __name__ == "__main__":
    sys.exit(main())

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
