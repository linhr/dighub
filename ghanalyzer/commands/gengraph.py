import networkx as nx

from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.io import load_graph, load_node_attributes, write_json_graph
from ghanalyzer.io.graphs import GRAPH_METADATA, load_language_graph

class Command(AnalyzerCommand):
    def description(self):
        return 'generate network graphs'

    def define_arguments(self, parser):
        parser.add_argument('type', choices=GRAPH_METADATA.keys()+['language'])
        parser.add_argument('-d', '--data-path', required=True)
        parser.add_argument('-a', '--load-attributes', action='store_true')
        parser.add_argument('-o', '--output')
        parser.add_argument('-f', '--format', choices=['json'], default='json')
    
    def run(self, args):
        if args.type in GRAPH_METADATA:
            graph = load_graph(args.data_path, args.type)
        elif args.type == 'language':
            graph = load_language_graph(args.data_path)
        if args.load_attributes:
            load_node_attributes(args.data_path, graph)
        
        print nx.info(graph)

        if args.output:
            if args.format == 'json':
                write_json_graph(args.output, graph, indent=4)
        
        return {'graph': graph}
