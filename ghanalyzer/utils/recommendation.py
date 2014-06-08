from itertools import islice
from operator import itemgetter

def recommend_by_rank(rank, n=None):
    rank = sorted(rank.iteritems(), key=itemgetter(1), reverse=True)
    return list(islice((x for x, _ in rank), n))
