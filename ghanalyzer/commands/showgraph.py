from matplotlib import pyplot

from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.io import read_json_graph
from ghanalyzer.visualization.graphs import draw_graph

class Command(AnalyzerCommand):
    def description(self):
        return 'visualize network graphs'

    def define_arguments(self, parser):
        parser.add_argument('-p', '--path', required=True)
        parser.add_argument('-f', '--format', choices=['json'], default='json')
        
    def run(self, args):
        if args.format == 'json':
            graph = read_json_graph(args.path)
        draw_graph(graph)
        pyplot.show(block=not args.interactive)

        return {'graph': graph, 'pyplot': pyplot, 'draw_graph': draw_graph}
