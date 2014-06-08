from collections import defaultdict
from itertools import izip

import numpy as np
import networkx as nx

import pyximport
pyximport.install()

import ghanalyzer.utils.randomwalk as randomwalk
from ghanalyzer.models import Repository
from ghanalyzer.utils.recommendation import recommend_by_rank


class PersonalRankRecommender(object):
    """recommender based on Topic-Sensitive PageRank (WWW 2002)"""
    def __init__(self, alpha, max_steps, epsilon):
        self.alpha = float(alpha)  # restart probability
        self.max_steps = max_steps
        self.epsilon = epsilon
        self.other_graphs = []

    def add_other_graphs(self, *graphs):
        for graph in graphs:
            self.other_graphs.append(graph)

    def train(self, graph):
        self.graph = graph.to_directed()
        for g in self.other_graphs:
            g = g.to_directed()
            self.graph.add_edges_from(g.edges_iter(data=True))
        self.nodes = self.graph.nodes()
        self.size = len(self.nodes)
        self.node_indices = {n: i for i, n in enumerate(self.nodes)}
        self.adjacency = nx.to_scipy_sparse_matrix(self.graph, nodelist=self.nodes,
            weight=None, format='coo')
        self.degrees = np.array([self.graph.out_degree(n, weight=None) for n in self.nodes], dtype=np.int)
        self.row = self.adjacency.row.astype(np.int)
        self.col = self.adjacency.col.astype(np.int)
        self.edge_weights = self.adjacency.data.astype(np.float)

    def _get_rank(self, user):
        u = self.node_indices[user]
        rank = np.zeros((self.size,), dtype=np.float)
        rank[u] = 1.0
        for _ in xrange(self.max_steps):
            rank1 = randomwalk.update_rank_numpy(rank, u,
                self.degrees, self.row, self.col, self.edge_weights, self.alpha)
            converged, _ = randomwalk.check_converged(rank, rank1, self.epsilon)
            if converged:
                break
            rank = rank1
        return rank

    def recommend(self, user, n):
        rank = self._get_rank(user)
        rank = {k: v for k, v in izip(self.nodes, rank) \
            if isinstance(k, Repository) and k not in self.graph[user]}
        return recommend_by_rank(rank, n)
