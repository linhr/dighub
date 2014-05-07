from collections import defaultdict

from ghanalyzer.algorithms.graphs import AccountRepositoryBigraph
from ghanalyzer.algorithms.similarities import JaccardSimilarity
from ghanalyzer.utils.recommendation import recommend_by_rank


class UserCFRecommender(object):
    """recommender using user-based collaborative filtering"""
    def __init__(self, n_neighbors=None):
        self.n_neighbors = n_neighbors

    def train(self, graph):
        self.bigraph = AccountRepositoryBigraph(graph)
        self.similarity = JaccardSimilarity(self.bigraph.matrix)
        if self.n_neighbors is None:
            self.n_neighbors = len(self.bigraph.accounts)

    def recommend(self, user, n):
        rank = defaultdict(float)
        u = self.bigraph.account_indices[user]
        for v, weight in self.similarity.nearest(u, self.n_neighbors):
            friend = self.bigraph.accounts[v]
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
        self.bigraph = AccountRepositoryBigraph(graph)
        self.similarity = JaccardSimilarity(self.bigraph.matrix.T)
        if self.n_neighbors is None:
            self.n_neighbors = len(self.bigraph.repos)

    def recommend(self, user, n):
        rank = defaultdict(float)
        u = self.bigraph.account_indices[user]
        for repo in self.bigraph.graph[user]:
            r = self.bigraph.repo_indices[repo]
            for s, weight in self.similarity.nearest(r, self.n_neighbors):
                similar = self.bigraph.repos[s]
                rank[similar] += weight
        for repo in self.bigraph.graph[user]:
            rank.pop(repo, None)
        return recommend_by_rank(rank, n)
