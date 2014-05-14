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
    def __init__(self, alpha, max_steps):
        self.alpha = float(alpha)
        self.max_steps = max_steps
        self.other_graphs = []

    def add_other_graphs(self, *graphs):
        for graph in graphs:
            self.other_graphs.append(graph)

    def train(self, graph):
        self.graph = graph.copy()
        for g in self.other_graphs:
            self.graph.add_edges_from(g.edges_iter(data=True))
        self.nodes = self.graph.nodes()
        self.size = len(self.nodes)
        self.node_indices = {n: i for i, n in enumerate(self.nodes)}
        self.adjacency = nx.to_scipy_sparse_matrix(self.graph, nodelist=self.nodes,
            weight=None, format='coo')
        self.degrees = np.array([self.graph.degree(n) for n in self.nodes], dtype=np.int)
        self.row = self.adjacency.row.astype(np.int)
        self.col = self.adjacency.col.astype(np.int)

    def _update_rank(self, rank, user):
        updated = defaultdict(float)
        for node in self.graph:
            for neighbor in self.graph[node]:
                updated[node] += self.alpha * rank[neighbor] / len(self.graph[neighbor])
        updated[user] += 1 - self.alpha
        return updated

    def _update_rank_cython(self, rank, user):
        return randomwalk.update_rank(rank, self.graph, user, self.alpha)

    def _update_rank_numpy(self, rank, user):
        u = self.node_indices[user]
        updated = np.zeros((self.size,))
        for a, b in izip(self.adjacency.row, self.adjacency.col):
            updated[a] += self.alpha * rank[b] / self.degrees[b]
        updated[u] += 1 - self.alpha
        return updated

    def _update_rank_numpy_cython(self, rank, user):
        u = self.node_indices[user]
        updated = np.zeros(rank.shape, dtype=np.float)
        randomwalk.update_rank_numpy(rank, updated, u,
            self.degrees, self.row, self.col, self.alpha)
        return updated

    def _recommend(self, user, n, use_cython=True):
        rank = defaultdict(float)
        rank[user] = 1.0
        for _ in xrange(self.max_steps):
            if use_cython:
                rank = self._update_rank_cython(rank, user)
            else:
                rank = self._update_rank(rank, user)
        return rank

    def _recommend_numpy(self, user, n, use_cython=True):
        u = self.node_indices[user]
        rank = np.zeros((self.size,), dtype=np.float)
        rank[u] = 1.0
        for _ in xrange(self.max_steps):
            if use_cython:
                rank = self._update_rank_numpy_cython(rank, user)
            else:
                rank = self._update_rank_numpy(rank, user)
        rank = {self.nodes[i]: r for i, r in enumerate(rank)}
        return rank

    def recommend(self, user, n, use_numpy=True, use_cython=True):
        if use_numpy:
            rank = self._recommend_numpy(user, n, use_cython)
        else:
            rank = self._recommend(user, n, use_cython)
        rank = {k: v for k, v in rank.iteritems() \
            if isinstance(k, Repository) and k not in self.graph[user]}
        return recommend_by_rank(rank, n)
