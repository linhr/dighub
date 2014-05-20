from collections import defaultdict

import numpy as np
import networkx as nx

from ghanalyzer.algorithms.features import LanguageVector
from ghanalyzer.io import load_accounts, load_repositories, load_repository_languages
from ghanalyzer.models import Entity, User, Repository


class DummyFeature(object):
    feature_count = 0

    def __init__(self, node_cls=Entity):
        self.node_cls = node_cls

    def get_feature(self, node):
        return []


class UserFeature(object):
    node_cls = User
    keys = ['public_repos', 'public_gists', 'followers', 'following', 'hireable']
    feature_count = len(keys)

    def __init__(self, graph, data_path, load_entity_data=False):
        self.graph = graph
        self.data_path = data_path
        if load_entity_data:
            self.accounts = load_accounts(data_path)
        else:
            self.accounts = defaultdict(dict)

    def get_feature(self, user):
        item = self.accounts[user.id]
        if user in self.graph:
            item.update(self.graph.node[user])
        feature = [float(item.get(k) or 0) for k in self.keys]
        return feature


class RepositoryFeature(object):
    node_cls = Repository
    keys = ['fork', 'open_issues_count', 'has_wiki', 'has_downloads', 'forks_count',
        'has_issues', 'stargazers_count', 'size']

    def __init__(self, graph, data_path, load_entity_data=False):
        self.graph = graph
        self.data_path = data_path
        if load_entity_data:
            self.repositories = load_repositories(data_path)
        else:
            self.repositories = defaultdict(dict)
        self.languages = load_repository_languages(data_path)
        self.languages = LanguageVector(self.languages)
        self.language_features = self.languages.features.toarray()
        self.language_feature_count = self.language_features.shape[1]
        self.feature_count = len(self.keys) + self.language_feature_count

    def get_feature(self, repo):
        item = self.repositories[repo.id]
        if repo in self.graph:
            item.update(self.graph.node[repo])
        feature = [float(item.get(k) or 0) for k in self.keys]
        index = self.languages.sample_indices.get(repo.id, None)
        if index is not None:
            feature.extend(self.language_features[index, :])
        else:
            feature.extend([0.0] * self.language_feature_count)
        return feature


class BigraphEdgeFeature(object):
    def __init__(self, graph, source_extractor, target_extractor, weight_key=None):
        self.graph = graph
        self.weight_key = weight_key
        self.source_extractor = source_extractor
        self.target_extractor = target_extractor
        self.source_cls = source_extractor.node_cls
        self.target_cls = target_extractor.node_cls
        if weight_key is not None:
            self.edge_feature_count = 1
            self.get_edge_feature = self._get_edge_feature
        else:
            self.edge_feature_count = 0
            self.get_edge_feature = self._get_empty_edge_feature
        self.feature_count = self.source_extractor.feature_count + \
            self.target_extractor.feature_count + self.edge_feature_count + 1

        self._create_graph_matrix()
        self._create_feature_matrix()


    def _get_edge_feature(self, u, v):
        return [self.graph[u][v].get(self.weight_key, 1)]

    def _get_empty_edge_feature(self, u, v):
        return []

    def _create_graph_matrix(self):
        self.nodes = self.graph.nodes()
        self.node_indices = {n: i for i, n in enumerate(self.nodes)}
        self.adjacency = nx.to_scipy_sparse_matrix(self.graph, nodelist=self.nodes,
            weight=self.weight_key, format='csr')
        self.indices = self.adjacency.indices
        self.indptr = self.adjacency.indptr

    def _iter_edges(self):
        for r in xrange(len(self.nodes)):
            for i in xrange(self.indptr[r], self.indptr[r+1]):
                c = self.indices[i]
                yield self.nodes[r], self.nodes[c]

    def _create_feature_matrix(self):
        size = self.adjacency.data.size
        self.features = np.zeros((size, self.feature_count))
        for i, (u, v) in enumerate(self._iter_edges()):
            if not isinstance(u, self.source_cls):
                u, v = v, u
            if not isinstance(u, self.source_cls) or not isinstance(v, self.target_cls):
                continue
            source_feature = self.source_extractor.get_feature(u)
            target_feature = self.target_extractor.get_feature(v)
            edge_feature = self.get_edge_feature(u, v)
            feature = [1]  # include constant feature
            feature.extend(source_feature)
            feature.extend(target_feature)
            feature.extend(edge_feature)
            self.features[i, :] = feature
