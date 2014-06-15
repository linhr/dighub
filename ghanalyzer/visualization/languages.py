from matplotlib import pyplot
import numpy as np
import networkx as nx
import math

def draw_co_occurrence_graph(graph, node_size_zoom=50, alpha=0.5, k=1.25):
    nodes = graph.nodes()
    node_size = [math.log(graph.node[n]['size'] or 2, 2)*node_size_zoom for n in nodes]
    
    pos = nx.spring_layout(graph, k=k/math.sqrt(len(nodes)))
    
    nx.draw_networkx(graph, pos, with_labels=True, alpha=alpha, node_color='r',
        nodelist=nodes,
        node_size=node_size)
    nx.draw_networkx_edge_labels(graph, pos,
        edge_labels={(u, v): d['weight'] for u, v, d in graph.edges(data=True)})


def draw_co_occurrence_matrix(graph, language_count=None, order_key='size', reorder=False):
    assert order_key in ('size', 'occurrence')
    nodes = graph.nodes_iter(data=True)
    nodes = sorted(nodes, key=lambda x: x[1][order_key], reverse=True)
    nodes = list(x[0] for x in nodes)
    if language_count:
        nodes = nodes[:language_count]
    if not nodes:
        return
    
    if reorder:
        first = nodes[0]
        others = nodes[1:]
        others = sorted(others, key=lambda x: graph[first][x]['weight'], reverse=True)
        nodes = [first] + others
    
    matrix = nx.to_numpy_matrix(graph, nodelist=nodes, weight='weight')
    
    image = pyplot.matshow(matrix, cmap=pyplot.get_cmap('GnBu'))
    bar = pyplot.gcf().colorbar(image)
    bar.set_label('Repository count')
    pyplot.xticks(np.arange(0, len(nodes)), [])
    pyplot.yticks(np.arange(0, len(nodes)), [])
    pyplot.gca().set_xticklabels(nodes)
    pyplot.gca().set_yticklabels(nodes)
    pyplot.setp(pyplot.gca().xaxis.get_majorticklabels(), rotation=30, ha='left') 
    
    return nodes, matrix, image, bar
    