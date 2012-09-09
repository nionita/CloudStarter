#!/j/Python27/python
# -*- coding: utf-8 -*-

"""
This script writes to a SQS requests for cutechess-cli.
The requests are json objects which describe the engines to play with
and the game parameters for cutechess-cli:

    req = {
            engines = [
                { 'name' = 'Abulafia_0_60' },
                { 'name' = 'AbaAba_0_40' }
                ],
            each = {
                'proto' = 'uci',
                'tc' = '40/60+0.5'
                },
            'draw' = '80 1',
            'resign' = '5 500'
            'pgnout' = '...'
          }

This is just a test of concept, the requests will be written in future by a
tournament manager (running on a server).

Usage: cutechess-plan.py engine1 engine2 [fix [var]]

  engine1, engine2 are executables (with or without .exe) which must be on some
    of the paths - see below
  fix is total time in seconds for 40 moves - default 60
  var is time in seconds per move (added to total for 40 moves) - default 0
"""

import sys
import exceptions
import os
import time
import json
import boto

# Our queue names:
cli_inp_queue = 'cliqueue'
cli_out_queue = 'clioutqu'

# To encode the time controls:
timec = "40/%s+%s"

# Directories where to search for engines
searchpaths = [
        'J:/AbaAba/dist/build/Abulafia',
        'J:/AbaAba/dist/build/AbaAba',
        'J:/Engines/AbaAba'
    ]

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

def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]
    
    if len(argv) == 0 or argv[0] == '--help':
        print __doc__
        return 0

    if len(argv) < 2:
        print 'Too few arguments, I need at least the 2 engines'
        return 2
    else:
        eng1 = argv[0]
        eng2 = argv[1]
        fix = 1
        var = 0
        if len(argv) >= 3:
            fix = argv[2]
            try:
                int(fix)
            except exceptions.ValueError:
                print 'Invalid value for minutes, %s: must be an integer' % fix
                return 2
            if len(argv) >= 4:
                var = argv[3]
                try:
                    float(var)
                except exceptions.ValueError:
                    print 'Invalid value for seconds, %s: must be a float' % var
                    return 2
            else:
                var = 0
    
    try:
        (fpath, fexc) = find_engine(eng1)
        (spath, sexc) = find_engine(eng2)
    except Exception as e:
        print 'Engine not found: ', e
        return 2

    print "Eng1 = ", fexc, ' on ', fpath
    print "Eng2 = ", sexc, ' on ', spath

    pout = "%s_%s_%s.pgn" % (eng1, eng2, time.strftime('%Y%m%d%H%M%S', time.localtime()))

    # Now we checked that the engines are here and the parameter are ok
    # We just form the json request and write it to the queue

    req = {
            'tour' : 'test',
            'engines': [
                { 'name': eng1 },
                { 'name': eng2 }
                ],
            'each': {
                'proto': 'uci',
                'tc': timec % (fix, var),
                },
            'draw': '80 1',
            'resign': '5 500',
            'pgnout': pout
        }

    print "Plan %s against %s with 40/%s+%s" % (eng1, eng2, fix, var)

    status = False
    try:
        conn = boto.connect_sqs()
        iqueue = conn.create_queue(cli_inp_queue, 300)
        oqueue = conn.create_queue(cli_out_queue, 30)

        mes = boto.sqs.message.Message()
        mes.set_body(json.dumps(req))

        status = iqueue.write(mes)
    except Exception as e:
        print "An error orccured:", e
    if status:
        print "Successfully written to queue"
    else:
        print "We could not write to the queue!"

if __name__ == "__main__":
    sys.exit(main())

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
