from matplotlib import pyplot

from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.io import read_json_report, read_pickle_report
from ghanalyzer.visualization.reports import plot_precision_recall


class Command(AnalyzerCommand):
    def description(self):
        return 'visualize experiment reports'

    def define_arguments(self, parser):
        parser.add_argument('-p', '--path', nargs='+', required=True)
        parser.add_argument('-f', '--format', choices=['json', 'pickle'], default='json')
        parser.add_argument('-r', '--ranks', nargs='+', type=int, default=())
    
    def run(self, args):
        if args.format == 'json':
            read_report = read_json_report
        elif args.format == 'pickle':
            read_report = read_pickle_report
        
        reports = [read_report(path) for path in args.path]
        plot_precision_recall(reports, args.ranks)

        pyplot.show(block=not args.interactive)
