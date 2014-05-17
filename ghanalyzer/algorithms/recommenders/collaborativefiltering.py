from collections import defaultdict

from ghanalyzer.algorithms.graphs import Bigraph
from ghanalyzer.algorithms.similarities import JaccardSimilarity
from ghanalyzer.models import User, Repository
from ghanalyzer.utils.recommendation import recommend_by_rank


class UserCFRecommender(object):
    """recommender using user-based collaborative filtering"""
    def __init__(self, n_neighbors=None):
        self.n_neighbors = n_neighbors

    def train(self, graph):
        self.bigraph = Bigraph(graph, source_cls=User, target_cls=Repository)
        self.similarity = JaccardSimilarity(self.bigraph.matrix)
        if self.n_neighbors is None:
            self.n_neighbors = len(self.bigraph.sources)

    def recommend(self, user, n):
        rank = defaultdict(float)
        u = self.bigraph.source_indices[user]
        for v, weight in self.similarity.nearest(u, self.n_neighbors):
            friend = self.bigraph.sources[v]
            for repo in self.bigraph.graph[friend]:
                rank[repo] += weight
        for repo in self.bigraph.graph[user]:
            rank.pop(repo, None)
        return recommend_by_rank(rank, n)


class ItemCFRecommender(object):
    """recommender using item-based collaborative filtering"""
    def __init__(self, n_neighbors=None):
        self.n_neighbors = n_neighbors

    def train(self, graph):
        self.bigraph = Bigraph(graph, source_cls=Repository, target_cls=User)
        self.similarity = JaccardSimilarity(self.bigraph.matrix)
        if self.n_neighbors is None:
            self.n_neighbors = len(self.bigraph.sources)

    def recommend(self, user, n):
        rank = defaultdict(float)
        u = self.bigraph.target_indices[user]
        for repo in self.bigraph.graph[user]:
            r = self.bigraph.source_indices[repo]
            for s, weight in self.similarity.nearest(r, self.n_neighbors):
                similar = self.bigraph.sources[s]
                rank[similar] += weight
        for repo in self.bigraph.graph[user]:
            rank.pop(repo, None)
        return recommend_by_rank(rank, n)
