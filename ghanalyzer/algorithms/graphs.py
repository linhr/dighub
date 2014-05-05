

def filter_edges(graph, edge_filter):
    result = graph.copy()
    for u, v, d in graph.edges_iter(data=True):
        if not edge_filter(u, v, d):
            result.remove_edge(u, v)
    return result
