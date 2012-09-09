#!/j/Python27/python
# -*- coding: utf-8 -*-

"""
This script is derived from clo-cutechess-cli.py coming with cutechess-cli 0.5.1
It is adapted to run on my local computer and find the chess engines in well known
directories.

Usage: cutechess-match.py engine1 engine2 [fix [var]]

  engine1, engine2 are executables (with or without .exe) which must be on some
    of the paths - see below
  fix is total time in seconds for 40 moves - default 60
  var is time in seconds per move (added to total for 40 moves) - default 0

When the game is completed the script writes the game outcome to its
standard output:
  W = win
  L = loss
  D = draw
"""

from subprocess import Popen, PIPE
import sys
import exceptions
import os
import re
import time

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
proto   = '-each proto=uci tc=40/{fix}+{var}'
term    =  ' -draw 80 1 -resign 5 500'
engines = ' -engine {fcp} -engine {scp}'
pgnout  = ' -pgnout {pout}'

options = proto + term + engines + pgnout

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

    fcp = engine_param.format(name=eng1, cmd=fexc, dir=fpath)
    scp = engine_param.format(name=eng2, cmd=sexc, dir=spath)

    pout = "%s_%s_%s.pgn" % (eng1, eng2, time.strftime('%Y%m%d%H%M%S', time.localtime()))

    cutechess_args = options.format(fix=fix, var=var, fcp=fcp, scp=scp, pout=pout)
    command = '%s %s' % (cutechess_cli_path, cutechess_args)

    print "Start %s against %s with 40/%s+%s" % (eng1, eng2, fix, var)

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
    
    if result == 0:
        print eng1, 'wins'
    elif result == 1:
        print eng1, 'looses'
    elif result == 2:
        print 'Draw'

if __name__ == "__main__":
    sys.exit(main())

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
