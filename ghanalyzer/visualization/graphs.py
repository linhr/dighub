from __future__ import with_statement

from matplotlib import pyplot
import networkx as nx
import numpy as np
import math

import ghanalyzer.models
from ghanalyzer.models import Account, User, Organization, Repository


def _node_color(node):
    if isinstance(node, User):
        return 0.3
    elif isinstance(node, Organization):
        return 0.6
    elif isinstance(node, Repository):
        return 1.0

def _get_node_labels(graph):
    labels = {}
    for n in graph:
        if isinstance(n, Repository):
            labels[n] = graph.node[n].get('full_name', '')
        elif isinstance(n, Account):
            labels[n] = graph.node[n].get('login', '')
    return labels

def draw_graph(graph, node_size=300, node_size_zoom=50, edge_label_key=None,
    node_alpha=0.3, edge_alpha=0.5, edge_weight_key=None, k=1.25):
    nodes = graph.nodes()
    node_labels = _get_node_labels(graph)
    if node_size_zoom:
        node_size = [graph.degree(n)*node_size_zoom for n in nodes]
    
    pos = nx.spring_layout(graph, weight=edge_weight_key, k=k/math.sqrt(len(nodes)))
    
    nx.draw_networkx_nodes(graph, pos, with_labels=False, alpha=node_alpha, cmap=pyplot.get_cmap('jet'),
        nodelist=nodes,
        node_color=[_node_color(n) for n in nodes],
        node_size=node_size)
    nx.draw_networkx_edges(graph, pos, alpha=edge_alpha)
    
    nx.draw_networkx_labels(graph, pos, labels=node_labels)
    
    if edge_label_key:
        nx.draw_networkx_edge_labels(graph, pos,
            edge_labels={(u, v): d.get(edge_label_key) for u, v, d in graph.edges_iter(data=True)})


def draw_graph_degrees(graph, node_type=None, weight_key=None):
    if node_type is not None:
        node_class = getattr(ghanalyzer.models, node_type)
        nodes = [n for n in graph if isinstance(n, node_class)]
    else:
        nodes = graph.nodes()
    degrees = graph.degree(nodes, weight=weight_key)
    if not degrees:
        return
    counts = np.bincount(degrees.values())
    indices, = np.nonzero(counts)
    x, y = indices, counts[indices]
    pyplot.loglog(x, y, 'o-', color='black', linewidth=0.5, 
        markersize=2, markeredgecolor='black', markerfacecolor='blue', alpha=1.0)
    pyplot.ylim(ymin=0.5)
    pyplot.xlabel('degree')
    pyplot.ylabel('count')
    return x, y