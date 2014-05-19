from itertools import izip

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

    def __init__(self, data_path):
        self.data_path = data_path
        self.accounts = load_accounts(data_path)

    def get_feature(self, user):
        if user.id not in self.accounts:
            return [0.0] * len(self.keys)
        item = self.accounts[user.id]
        feature = [float(item.get(k) or 0) for k in self.keys]
        return feature


class RepositoryFeature(object):
    node_cls = Repository
    keys = ['fork', 'open_issues_count', 'has_wiki', 'has_downloads', 'forks_count',
        'has_issues', 'stargazers_count', 'size']

    def __init__(self, data_path):
        self.data_path = data_path
        self.repositories = load_repositories(data_path)
        self.languages = load_repository_languages(data_path)
        self.languages = LanguageVector(self.languages)
        self.language_feature_count = len(self.languages.vectorizer.get_feature_names())
        self.feature_count = len(self.keys) + self.language_feature_count

    def get_feature(self, repo):
        if repo.id in self.repositories:
            item = self.repositories[repo.id]
            feature = [float(item.get(k) or 0) for k in self.keys]
        else:
            feature = [0.0] * len(self.keys)
        index = self.languages.sample_indices.get(repo.id, None)
        if index is not None:
            feature.extend(self.languages.features[index, :].toarray()[0])
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
            weight=self.weight_key, format='coo')
        self.row = self.adjacency.row.astype(np.int)
        self.col = self.adjacency.col.astype(np.int)

    def _create_feature_matrix(self):
        size = self.adjacency.data.size
        self.features = np.zeros((size, self.feature_count))
        for i, (r, c) in enumerate(izip(self.row, self.col)):
            u, v = self.nodes[r], self.nodes[c]
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
