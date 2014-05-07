
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
