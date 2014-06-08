from sklearn.decomposition import NMF

from ghanalyzer.algorithms.graphs import Bigraph
from ghanalyzer.models import User, Repository
from ghanalyzer.utils.recommendation import recommend_by_rank


class FactorizationRecommender(object):
    def __init__(self, n_components):
        self.n_components = n_components

    def train(self, graph):
        self.bigraph = Bigraph(graph, source_cls=User, target_cls=Repository)
        self.user_count = len(self.bigraph.sources)
        self.repo_count = len(self.bigraph.targets)
        self._train_model()

    def _train_model(self):
        raise NotImplementedError()

    def _predict(self, u, r):
        return self.user_features[u, :].dot(self.repo_features[r, :].T)

    def recommend(self, user, n=None):
        u = self.bigraph.source_indices[user]
        rank = {}
        candidates = set(self.bigraph.targets) - set(self.bigraph.graph.neighbors_iter(user))
        for repo in candidates:
            r = self.bigraph.target_indices[repo]
            rank[repo] = self._predict(u, r)
        return recommend_by_rank(rank, n)


class NMFRecommender(FactorizationRecommender):
    def _train_model(self):
        factorizer = NMF(n_components=self.n_components)
        self.user_features = factorizer.fit_transform(self.bigraph.matrix)
        self.repo_features = factorizer.components_.T
