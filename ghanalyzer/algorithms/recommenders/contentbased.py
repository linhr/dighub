from collections import defaultdict
from itertools import izip

import numpy as np

from ghanalyzer.algorithms.features import LanguageVector, DescriptionVector
from ghanalyzer.algorithms.graphs import get_nodes
from ghanalyzer.algorithms.similarities import CosineSimilarity, LinearSimilarity
from ghanalyzer.models import Repository
from ghanalyzer.io import load_repository_languages, load_repository_descriptions
from ghanalyzer.utils.recommendation import recommend_by_rank


class ContentBasedRecommender(object):
    def __init__(self, data_path):
        self.data_path = data_path
    
    def train(self, graph):
        self.graph = graph
        self.repos = list(get_nodes(self.graph, Repository))
        self.repo_indices = {x: i for i, x in enumerate(self.repos)}
        self._calculate_similarities()

    def _calculate_similarities(self):
        raise NotImplementedError()

    def get_rank(self, user):
        indices = [self.repo_indices[r] for r in self.graph[user]]
        rank = np.sum(self.similarity.matrix[indices, :], axis=0)
        rank = {k: v for k, v in izip(self.repos, rank)}
        return rank

    def recommend(self, user, n):
        rank = self.get_rank(user)
        for repo in self.graph[user]:
            rank.pop(repo, None)
        return recommend_by_rank(rank, n)


class LanguageBasedRecommender(ContentBasedRecommender):
    def _calculate_similarities(self):
        languages = load_repository_languages(self.data_path)
        languages[None] = {}  # add dummy data item
        languages = LanguageVector(languages, normalize=False)
        default_index = languages.sample_indices[None]
        indices = [languages.sample_indices.get(r.id, default_index) for r in self.repos]
        self.features = languages.features[indices, :]
        self.similarity = CosineSimilarity(self.features)


class DescriptionBasedRecommender(ContentBasedRecommender):
    def _calculate_similarities(self):
        descriptions = load_repository_descriptions(self.data_path)
        descriptions[None] = ''  # add dummy data item
        descriptions = DescriptionVector(descriptions, tfidf=True)
        default_index = descriptions.sample_indices[None]
        indices = [descriptions.sample_indices.get(r.id, default_index) for r in self.repos]
        self.features = descriptions.features[indices, :]
        self.similarity = LinearSimilarity(self.features)
