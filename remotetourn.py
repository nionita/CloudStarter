#!env python

"""
This script will "coordinate" tournaments (Schweizer system or round-robin)
via an AWS SQS queue pair (see below) with states in AWS S3
The matches actually ran by agents that take the match requests from the
request queue, execute them and write the results to the results queue

The script manages any number of tournaments (and is the only one doing so!)
by "listening" on the result queue and acting with the current result on
the appropriate tournament state, which is stored in S3 (and updated after
every match result).

When all the games of one round of one tournament are done, the script can proceed
with the next round. Because of this, running only one tournament in the cloud
could be inefficient, as after each match, the (agent) servers will have idle times
until the last match in the round will end
"""

import sys
from pairings import next_round
import random
import time
import config

# Some constants:
# Our queue names:
cli_inp_queue = 'cliqueue'
cli_out_queue = 'clioutqu'

# Our S3 structure for tournaments
stor       = config.s3_root
tours_root = '/chess/tours/'

# Sleep time between main loops:
time_sleep = 30

# Maximum result messages processed in one loop
max_messages = 10

# For debug:
debug = False

def plan_game(tour, eng1, eng2, fix, var, iqueue)
    pout = '%s_%s_%s.pgn' % (eng1, eng2, time.strftime('%Y%m%d%H%M%S', time.localtime()))

    req = {
            'tour' : tour,
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

    if debug:
        print 'Plan %s against %s with 40/%s+%s' % (eng1, eng2, fix, var)

    status = False
    try:
        mes = boto.sqs.message.Message()
        mes.set_body(json.dumps(req))

        status = iqueue.write(mes)
    except Exception as e:
        print 'Error occured in plan_game:', e
    if status:
        if debug
            print 'Successfully written to queue'
    else:
        print 'We could not write to the queue!'
    return status

def decode_result(mes):
    str = mes.get_body()
    dmes = json.loads(str)
    if 'tour' not in dmes and 'engines' not in dmes and 'result' not in dmes:
        if debug:
            print 'Unusual message in result queue:', dmes
        return None
    else:
        return dmes

# This function gets a tournament, a list of results and the boto resources
# and updates the state of the tournament according to the that results
# after which the result messages are deleted from the result queue
def update_tour(tour, results, botor):
    meslist = []
    key = botor.bucket.get_key(tours_root + tour)
    if key:
        str   = key.get_contents_as_string()
        tourd = json.loads(str)
        for r in results:
            meslist.append(r.message)
            if 
    else:
        for r in results:
            meslist.append(r.message)
    botor.SQSConnection.delete_message_batch(meslist)

# This functions gets a maximum number of messages from the result queue
# and updates accordingly the status of the corresponding tournament
# (including generating a new round, when necessary)
# Returns False if there is no new message and True if there could be some
def manage_results(botor):
    results = {}
    i = 0
    for mes in botor.SQSConnection.receive_messages(botor.resQueue, number_of_messages=max_messages):
        i++
        res = decode_result(mes)
        if res == None:
            continue
        res.message = mes	# we need it later to delete it
        if res.tour in results:
            results[res.tour].append(res)
        else:
            results[res.tour] = [res]
        #tour    = res.tour
        #engines = res.engines
        #res     = res.result
    for tour in results.keys():
        # Make a change per tournament at once
        update_tour(tour, results[tour], botor)
    return i >= max_messages

# Open sqs connection and create queues (if not there)
try:
    botor = botoResources(regionName='EU', reqQueueName=cli_inp_queue, resQueueName=cli_out_queue)
except Exception as e:
    print 'Error occured when creating AWS resources:', e
    raise e

    while True:
        t0 = time.time()
        more = manage_results(botor)
        manage_tours()
        t1 = time.time()
        if not more and (t1 - t0) < time_sleep:
            time.sleep(time_sleep - t1 + t0)


    games = []
    for r0 in range(rounds):
        r = r0 + 1
        print 'Round ', r
        #print "Previous games:"
        #for g in games:
        #    print g
        rk, best = next_round(players, games)
        for i, j in best['round']:
            res = play_game(i, j)
            if res == 'W':
                ri, rj = 1, 0
            elif res == 'L':
                ri, rj = 0, 1
            else:
                ri, rj = 0.5, 0.5
            game = { 'wplayer' : i, 'wpoints' : ri, 'bplayer' : j, 'bpoints' : rj }
            games.append(game)
    points = {}
    played = {}
    for p in players:
        points[p] = 0
        played[p] = 0
    #print "Games:"
    for g in games:
        #print g
        wp, wr = g['wplayer'], g['wpoints']
        bp, br = g['bplayer'], g['bpoints']
        points[wp] = points[wp] + wr
        points[bp] = points[bp] + br
        played[wp] = played[wp] + 1
        played[bp] = played[bp] + 1
    print 'End results:'
    rnk = [(points[p], p) for p in points]
    rnk.sort()
    rnk.reverse()
    for r, p in rnk:
        print 'Player %-20s: %5.1f' % (p, r)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
