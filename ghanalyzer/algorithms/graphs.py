from scipy.sparse import dok_matrix

import ghanalyzer.models
from ghanalyzer.models import Account, Repository


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


class AccountRepositoryBigraph(object):
    def __init__(self, graph, weight=None, dtype=float):
        self.graph = graph
        self.weight = weight
        self.dtype = dtype
        self.repos = list(get_nodes(graph, Repository))
        self.accounts = list(get_nodes(graph, Account))
        self.repo_indices = {x: i for i, x in enumerate(self.repos)}
        self.account_indices = {x: i for i, x in enumerate(self.accounts)}

    def _build_matrix(self):
        a = len(self.accounts)
        b = len(self.repos)
        m = dok_matrix((a, b), dtype=self.dtype)
        for account, i in self.account_indices.iteritems():
            for repo, data in self.graph[account].iteritems():
                j = self.repo_indices[repo]
                m[i, j] = data.get(self.weight, 1)
        return m

    @property
    def matrix(self):
        if not hasattr(self, '_matrix'):
            self._matrix = self._build_matrix()
        return self._matrix
