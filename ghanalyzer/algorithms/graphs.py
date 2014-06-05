import networkx as nx
from scipy.sparse import dok_matrix
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import linear_kernel

import ghanalyzer.models


def filter_edges(graph, edge_filter):
    result = graph.copy()
    for u, v, d in graph.edges_iter(data=True):
        if not edge_filter(u, v, d):
            result.remove_edge(u, v)
    return result

def get_nodes(graph, node_class):
    if isinstance(node_class, basestring):
        if node_class not in ghanalyzer.models.__all__:
            return
        node_class = getattr(ghanalyzer.models, node_class)
    return [n for n in graph if isinstance(n, node_class)]


class Bigraph(object):
    def __init__(self, graph, source_cls, target_cls, weight=None, dtype=float):
        self.graph = graph
        self.weight = weight
        self.dtype = dtype
        self.sources = list(get_nodes(graph, source_cls))
        self.targets = list(get_nodes(graph, target_cls))
        self.source_indices = {x: i for i, x in enumerate(self.sources)}
        self.target_indices = {x: i for i, x in enumerate(self.targets)}

    def _build_matrix(self):
        a = len(self.sources)
        b = len(self.targets)
        m = dok_matrix((a, b), dtype=self.dtype)
        for source, i in self.source_indices.iteritems():
            for target, data in self.graph[source].iteritems():
                j = self.target_indices.get(target, None)
                if j is None:
                    continue
                m[i, j] = data.get(self.weight, 1)
        return m

    @property
    def matrix(self):
        if not hasattr(self, '_matrix'):
            self._matrix = self._build_matrix()
        return self._matrix


class AdjacencyMatrix(object):
    def __init__(self, graph, format='csr', weight=None, dtype=None):
        self.graph = graph
        self.nodes = self.graph.nodes()
        self.node_indices = {n: i for i, n in enumerate(self.nodes)}
        self.matrix = nx.to_scipy_sparse_matrix(self.graph, nodelist=self.nodes,
            dtype=dtype, weight=weight, format=format)


class BigraphSimilarity(object):
    def __init__(self, bigraph, features, feature_type):
        self.bigraph = bigraph
        if feature_type == 'source':
            self._from_source_features(features)
        elif feature_type == 'target':
            self._from_target_features(features)
        else:
            raise ValueError('feature type must be "source" or "target"')
        self._build_similarity_matrix()

    def _from_source_features(self, features):
        assert features.shape[0] == self.bigraph.matrix.shape[0]
        self.source_features = features.copy()
        self.target_features = self.bigraph.matrix.T.dot(features)

    def _from_target_features(self, features):
        assert features.shape[0] == self.bigraph.matrix.shape[1]
        self.target_features = features.copy()
        self.source_features = self.bigraph.matrix.dot(features)

    def _build_similarity_matrix(self):
        """
        partitioned similarity matrix ('s' for source nodes and 't' for target nodes)
        S = [[S_ss, S_st],
             [S_ts, S_tt]]
        """
        normalize(self.source_features, norm='l2', copy=False)
        normalize(self.target_features, norm='l2', copy=False)
        self.ss = linear_kernel(self.source_features)
        self.st = linear_kernel(self.source_features, self.target_features)
        self.ts = self.st.T
        self.tt = linear_kernel(self.target_features)
