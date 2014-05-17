from scipy.sparse import dok_matrix

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
