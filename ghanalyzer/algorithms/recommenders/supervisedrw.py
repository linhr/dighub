import gc
import random
from itertools import izip

import numpy as np
import networkx as nx
from scipy.sparse import csr_matrix
from scipy.optimize import fmin_l_bfgs_b
from sklearn.preprocessing import normalize

from ghanalyzer.algorithms.features import (
    load_language_features,
    load_description_features,
    load_follow_features,
)
from ghanalyzer.algorithms.graphs import Bigraph, AdjacencyMatrix, BigraphSimilarity
from ghanalyzer.algorithms.graphfeatures import *
from ghanalyzer.algorithms.recommenders.base import Recommender
from ghanalyzer.models import User, Repository
from ghanalyzer.utils.randomwalk import check_converged
from ghanalyzer.utils.recommendation import recommend_by_rank
from ghanalyzer.utils import sparsetools


def sigmoid(x):
    return 1 / (1 + np.exp(-x))

class SupervisedRWRecommender(Recommender):
    parameters = ['alpha', 'max_steps', 'lambda_', 'epsilon', 'loss_width',
        'weight_key', 'feature_types']

    """recommender based on Supervised Random Walk (WSDM 2011)"""
    def __init__(self, data_path, max_steps=100, alpha=0.85, lambda_=0.01,
            epsilon=0.01, loss_width=1.0, weight_key=(), feature_types=()):
        self.data_path = data_path
        self.max_steps = max_steps
        self.alpha = float(alpha)
        self.lambda_ = float(lambda_)
        self.epsilon = float(epsilon)
        self.loss_width = float(loss_width)
        self.weight_key = list(weight_key)
        self.feature_types = list(set(feature_types))

    def train(self, graph):
        self.graph = graph.to_directed()
        self.candidates = [n for n in self.graph if isinstance(n, Repository)]
        self.adj = AdjacencyMatrix(self.graph, format='csr')
        self.feature_extractor = self._create_feature_extractor()
        self.nodes = self.feature_extractor.nodes
        self.node_indices = self.feature_extractor.node_indices
        self.indices = self.feature_extractor.indices
        self.indptr = self.feature_extractor.indptr
        self.N = len(self.nodes)
        self.E = self.feature_extractor.edge_count
        self.M = self.feature_extractor.feature_count

    def recommend(self, user, n=None):
        rank = self._get_rank(user)
        rank = {k: v for k, v in izip(self.nodes, rank) \
            if isinstance(k, Repository) and k not in self.graph[user]}
        return recommend_by_rank(rank, n)

    def _create_feature_extractor(self):
        bigraph = Bigraph(self.graph, source_cls=User, target_cls=Repository)
        features = []
        if 'behavior' in self.feature_types:
            features.extend([
                (bigraph.matrix.copy(), 'source'),
                (bigraph.matrix.T.tocsr().copy(), 'target'),
            ])
        if 'content' in self.feature_types:
            languages = load_language_features(self.data_path, bigraph.targets)
            descriptions = load_description_features(self.data_path, bigraph.targets)
            features.extend([
                (languages, 'target'),
                (descriptions, 'target'),
            ])
        if 'relation' in self.feature_types:
            followers, followees = load_follow_features(self.data_path, bigraph.sources)
            features.extend([
                (followers, 'source'),
                (followees, 'source'),
            ])
        gc.collect()  # force garbage collection
        extractors = [
            ConstantFeature(self.adj),
            EdgeAttributeFeature(self.adj, keys=self.weight_key),
        ]
        for feature, type_ in features:
            similarity = BigraphSimilarity(bigraph, feature, type_)
            extractor = SimilarityFeature(self.adj, similarity)
            extractors.append(extractor)
        return CombinedFeature(self.adj, *extractors)

    def _csr_from_data(self, data):
        return csr_matrix((data, self.indices, self.indptr), shape=(self.N, self.N))

    def _get_edge_feature(self, root):
        psi = self.feature_extractor.get_feature_matrix(root)
        return psi

    def _get_edge_strength(self, psi, w):
        S = np.einsum('ij,j->i', psi, w)
        A = sigmoid(S)
        dA = np.empty((self.E, self.M), order='F')
        derivative = A * (1 - A)
        np.multiply(derivative[:, np.newaxis], psi, out=dA)
        return A, dA

    def _get_transition_probability(self, A):
        """calculate unbiased transition probability matrix Q0 such that
        Q = (1 - alpha) * Q0 + alpha * E_root
        where E_root is a matrix containing 1 in the root node's column and 0 elsewhere
        """
        Q0 = self._csr_from_data(A)
        Q0 = normalize(Q0, norm='l1')
        return Q0

    def _get_transition_probability_derivative(self, A, dA):
        F = self._csr_from_data(A)
        norm_F = sparsetools.sum_csr_matrix_column(F)
        denominator = (1.0 - self.alpha) / np.power(norm_F, 2)

        dQ = np.empty((self.M,), dtype=object)
        for m in xrange(self.M):
            dFm = self._csr_from_data(dA[:, m])
            norm_dFm = sparsetools.sum_csr_matrix_column(dFm)
            
            X = sparsetools.csr_matrix_scale_row(dFm, norm_F).data
            Y = sparsetools.csr_matrix_scale_row(F, norm_dFm).data
            dQ[m] = self._csr_from_data(X - Y)
            sparsetools.csr_matrix_scale_row(dQ[m], denominator, inplace=True)

        return dQ

    def _get_stationary_distribution(self, Q0, root):
        P = np.zeros((self.N,))
        P[root] = 1.0
        converged, delta = False, 0.0
        for _ in xrange(self.max_steps):
            P1 = sparsetools.vector_csr_matrix_multiply(P, Q0)
            P1 *= 1 - self.alpha
            P1[root] += self.alpha
            converged, delta = check_converged(P, P1, self.epsilon)
            if converged:
                break
            P = P1
        if not converged:
            print 'Warning: stationary distribution does not converge ' \
                'in %d iteration(s) (delta=%f)' % (self.max_steps, delta)
        return P

    def _get_stationary_distribution_derivative(self, P, Q0, dQ, root):
        shape = (self.N, self.N)
        dP = np.zeros((self.N, self.M), order='F')
        for m in xrange(self.M):
            PdQ = sparsetools.vector_csr_matrix_multiply(P, dQ[m])
            converged, delta = False, 0.0
            for _ in xrange(self.max_steps):
                dPQ = sparsetools.vector_csr_matrix_multiply(dP[:, m], Q0)
                dPQ *= 1 - self.alpha
                dPQ[root] += self.alpha * dP[:, m].sum()
                dPm = dPQ + PdQ
                converged, delta = check_converged(dP[:, m], dPm, self.epsilon)
                if converged:
                    break
                dP[:, m] = dPm
            if not converged:
                print 'Warning: stationary distribution derivative does not converge ' \
                    'in %d iteration(s) (delta=%f, m=%d)' % (self.max_steps, delta, m)
        return dP

    def _loss_function(self, w, psi, root, pairs):
        A, dA = self._get_edge_strength(psi, w)
        Q0 = self._get_transition_probability(A)
        dQ = self._get_transition_probability_derivative(A, dA)
        P = self._get_stationary_distribution(Q0, root)
        dP = self._get_stationary_distribution_derivative(P, Q0, dQ, root)

        diff = np.array([P[u] - P[v] for u, v in pairs])
        loss = sigmoid(diff / self.loss_width)
        objective = np.sum(w ** 2) + self.lambda_ * np.sum(loss)
        ddiff = loss * (1 - loss) / self.loss_width
        dpairs = np.empty((len(pairs), self.M))
        for i, (u, v) in enumerate(pairs):
            dpairs[i, :] = dP[u, :] - dP[v, :]
        gradient = 2 * w + np.einsum('i,im->m', ddiff, dpairs) * self.lambda_
        return objective, gradient

    def _select_samples(self, user):
        positive = self.graph.neighbors(user)
        others = set(self.candidates) - set(positive)
        negative = random.sample(others, min(len(positive), len(others)))
        positive = [self.node_indices[x] for x in positive]
        negative = [self.node_indices[x] for x in negative]
        return positive, negative

    def _get_rank(self, user):
        positive, negative = self._select_samples(user)
        pairs = [(u, v) for u in negative for v in positive]
        u = self.node_indices[user]
        psi = self._get_edge_feature(u)

        w0 = np.random.rand(self.M)
        w, _, _ = fmin_l_bfgs_b(self._loss_function, w0, args=(psi, u, pairs), iprint=0)
        A, _ = self._get_edge_strength(psi, w)
        Q0 = self._get_transition_probability(A)
        P = self._get_stationary_distribution(Q0, u)
        return P
