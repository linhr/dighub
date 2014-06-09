import random

from ghanalyzer.algorithms.graphs import get_nodes
from ghanalyzer.algorithms.recommenders.base import Recommender
from ghanalyzer.models import Repository

class RandomRecommender(Recommender):
    """random recommender"""
    
    def train(self, graph):
        self.graph = graph
        self.repos = set(get_nodes(graph, Repository))

    def recommend(self, user, n=None):
        candidates = list(self.repos - set(self.graph.neighbors_iter(user)))
        if n is not None and n < len(candidates):
            return random.sample(candidates, n)
        else:
            random.shuffle(candidates)
            return candidates
