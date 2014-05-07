from sklearn.decomposition import NMF

from ghanalyzer.algorithms.graphs import AccountRepositoryBigraph
from ghanalyzer.utils.recommendation import recommend_by_rank


class FactorizationRecommender(object):
    def __init__(self, n_components):
        self.n_components = n_components

    def train(self, graph):
        self.bigraph = AccountRepositoryBigraph(graph)
        self.user_count = len(self.bigraph.accounts)
        self.repo_count = len(self.bigraph.repos)
        self._train_model()

    def _train_model(self):
        raise NotImplementedError()

    def _predict(self, u, r):
        return self.user_features[u, :].dot(self.repo_features[r, :].T)

    def recommend(self, user, n):
        u = self.bigraph.account_indices[user]
        rank = {}
        candidates = set(self.bigraph.repos) - set(self.bigraph.graph.neighbors_iter(user))
        for repo in candidates:
            r = self.bigraph.repo_indices[repo]
            rank[repo] = self._predict(u, r)
        return recommend_by_rank(rank, n)


class NMFRecommender(FactorizationRecommender):
    def _train_model(self):
        factorizer = NMF(n_components=self.n_components)
        self.user_features = factorizer.fit_transform(self.bigraph.matrix)
        self.repo_features = factorizer.components_.T
