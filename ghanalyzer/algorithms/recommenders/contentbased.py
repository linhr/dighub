from collections import defaultdict
from itertools import izip

import numpy as np

from ghanalyzer.algorithms.graphs import Bigraph, BigraphSimilarity
from ghanalyzer.algorithms.features import (
    load_language_features,
    load_description_features,
    load_follow_features,
)
from ghanalyzer.algorithms.recommenders.base import Recommender
from ghanalyzer.models import User, Repository
from ghanalyzer.utils.recommendation import recommend_by_rank


class ContentBasedRecommender(Recommender):
    def __init__(self, data_path):
        self.data_path = data_path

    def train(self, graph):
        self.bigraph = Bigraph(graph, source_cls=User, target_cls=Repository)
        self._calculate_similarities()

    def _calculate_similarities(self):
        raise NotImplementedError()

    def get_rank(self, user):
        u = self.bigraph.source_indices[user]
        rank = self.similarity.st[u, :]
        rank = {k: v for k, v in izip(self.bigraph.targets, rank)}
        return rank

    def recommend(self, user, n=None):
        rank = self.get_rank(user)
        for repo in self.bigraph.graph[user]:
            rank.pop(repo, None)
        return recommend_by_rank(rank, n)


class LanguageBasedRecommender(ContentBasedRecommender):
    def _calculate_similarities(self):
        features = load_language_features(self.data_path, self.bigraph.targets)
        self.similarity = BigraphSimilarity(self.bigraph, features, 'target')


class DescriptionBasedRecommender(ContentBasedRecommender):
    def _calculate_similarities(self):
        features = load_description_features(self.data_path, self.bigraph.targets)
        self.similarity = BigraphSimilarity(self.bigraph, features, 'target')


class QuasiUserCFRecommender(ContentBasedRecommender):
    def _calculate_similarities(self):
        features = self.bigraph.matrix.copy()
        self.similarity = BigraphSimilarity(self.bigraph, features, 'source')


class QuasiItemCFRecommender(ContentBasedRecommender):
    def _calculate_similarities(self):
        features = self.bigraph.matrix.T.tocsr().copy()
        self.similarity = BigraphSimilarity(self.bigraph, features, 'target')


class FollowerBasedRecommender(ContentBasedRecommender):
    def _calculate_similarities(self):
        followers, _ = load_follow_features(self.data_path, self.bigraph.sources)
        self.similarity = BigraphSimilarity(self.bigraph, followers, 'source')


class FolloweeBasedRecommender(ContentBasedRecommender):
    def _calculate_similarities(self):
        _, followees = load_follow_features(self.data_path, self.bigraph.sources)
        self.similarity = BigraphSimilarity(self.bigraph, followees, 'source')
