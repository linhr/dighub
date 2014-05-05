from matplotlib import pyplot

from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.io import read_json_graph
from ghanalyzer.visualization.graphs import draw_graph, draw_graph_degrees

class Command(AnalyzerCommand):
    def description(self):
        return 'visualize network graphs'

    def define_arguments(self, parser):
        parser.add_argument('type', choices=['structure', 'degree'])
        parser.add_argument('-p', '--path', required=True)
        parser.add_argument('-f', '--format', choices=['json'], default='json')
        parser.add_argument('--node-type', choices=['Repository', 'User', 'Organization'],
            default=None)
        parser.add_argument('--weight-key')

        
    def run(self, args):
        if args.format == 'json':
            graph = read_json_graph(args.path)

        if args.type == 'structure':
            draw_graph(graph)
        elif args.type == 'degree':
            draw_graph_degrees(graph, node_type=args.node_type, weight_key=args.weight_key)

        pyplot.show(block=not args.interactive)

        return {
            'graph': graph,
            'pyplot': pyplot,
            'draw_graph': draw_graph,
            'draw_graph_degrees': draw_graph_degrees,
        }
