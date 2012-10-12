import sets

def printlev(lev, *k):
    print " "*lev*2, k

def add_played(played, i, j):
    if i in played:
        played[i].add(j)
    else:
        played[i] = sets.Set([j])
    if j in played:
        played[j].add(i)
    else:
        played[j] = sets.Set([i])

def add_white(white, p):
    if p in white:
        white[p] = white[p] + 1
    else:
        white[p] = 1

def balance(white, i, j):
    if i in white:
        wi = white[i]
    else:
        wi = 0
    if j in white:
        wj = white[j]
    else:
        wj = 0
    if wi > wj:
        return (j, i)
    else:
        return (i, j)

def balance_white(white, round):
    bround = [ balance(white, i, j) for i, j in round ]
    return bround

# Given a set of unpaired players and a dictionary of already played
# combinations (for every player: a set of players with which it already played)
# return a list af all pairings which still have to be played
# A pairing is a list of tuples of 2 players
def all_pairs(lev, unpaired, played):
    # unpaired is the set of unpaired players
    # played is the dict of played games per player
    ps = []
    ok = 1
    if len(unpaired) >= 2:
        first = None
        ok = 0
        for i in unpaired:
            if first == None:
                first = i
                #printlev(lev, "player-1 ", str(i))
                continue
            if i == first or (first in played and i in played[first]):
                continue
            #printlev(lev, "player ", str(i))
            unpaired1 = sets.Set([j for j in unpaired if j != first and j != i])
            #printlev(lev, "Unpaired1:", unpaired1)
            played1 = played.copy()
            add_played(played1, first, i)
            sps = all_pairs(lev+1, unpaired1, played1)
            #printlev(lev, "Played1:", played1)
            if sps == None:
                continue
            elif len(sps) > 0:
                for p in sps:
                    p.insert(0, (first, i))
                    ps.append(p)
            else:
                ps.append([(first, i)])
            ok = 1
            #printlev(lev, "SPS:", sps)
    if ok:
        return ps
    else:
        return None

players = [1, 2, 3, 4, 5, 6]
games = [
        { 'wplayer' : 1, 'wpoints' : 1.0, 'bplayer' : 2, 'bpoints' : 0.0 },
        { 'wplayer' : 3, 'wpoints' : 0.0, 'bplayer' : 4, 'bpoints' : 1.0 },
        { 'wplayer' : 5, 'wpoints' : 1.0, 'bplayer' : 6, 'bpoints' : 0.0 },
    ]

def comp_round_good(ranking, round):
    good = 0
    for i, j in round:
        g1 = ranking[i] - ranking[j]
        good = good + g1 * g1
    return good

# Given a list of players and a list of games with results,
# compute the ranking of the players and return it together
# with the next pairing so that those games are as balances as possible
# Games are dictionaries with the keys: wplayer, wpoints, bplayer, bpoints
# The wplayer and bplayer contain the 2 players who were involved in the
# game and wpoints and bpoints contain the scores obtained for that
# particular games
# The ranking is done based on the average of points per game (more is better)
# Two games are more balanced if the average of points per game are near
# From all possible pairings the function will return the one which
# minimizes the square sum of the average differences per proposed game
def next_round(players, games):
    unpaired = sets.Set(players)
    played  = {}
    ranking = {}
    white   = {}
    for p in unpaired:
        rankingp = { 'games' : 0, 'points' : 0 }
        for g in games:
            if g['wplayer'] == p:
                add_played(played, p, g['bplayer'])
                add_white(white, p)
                rankingp['games']  = rankingp['games']  + 1
                rankingp['points'] = rankingp['points'] + g['wpoints']
            elif g['bplayer'] == p:
                add_played(played, g['wplayer'], p)
                rankingp['games']  = rankingp['games']  + 1
                rankingp['points'] = rankingp['points'] + g['bpoints']
        if rankingp['games'] == 0:
            ranking[p] = 0
        else:
            ranking[p] = rankingp['points'] / rankingp['games']
    best = None
    #print "Played: ", played
    #print "White:  ", white
    for round in all_pairs(0, unpaired, played):
        good = comp_round_good(ranking, round)
        if best == None:
            best = { 'round' : round, 'good' : good }
        else:
            if best['good'] > good:
                best['round'] = round
                best['good']  = good
    bround = balance_white(white, best['round'])
    best['round'] = bround
    return (ranking, best)

if __name__ == "__main__":
    rk, round = next_round(players, games)
    print "Ranking: ", rk
    print "Next round: ", round