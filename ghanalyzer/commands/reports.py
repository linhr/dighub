from matplotlib import pyplot

from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.io import read_json_report, read_pickle_report
from ghanalyzer.evaluation.metrics import (
    get_frequencies,
    get_mean_average_precision,
    get_roc_auc,
)
from ghanalyzer.visualization.reports import plot_precision_recall, plot_roc


class Command(AnalyzerCommand):
    def description(self):
        return 'analyze or visualize experiment reports'

    def define_arguments(self, parser):
        parser.add_argument('type', choices=['pr', 'roc', 'metric'])
        parser.add_argument('-p', '--path', nargs='+', required=True)
        parser.add_argument('-f', '--format', choices=['json', 'pickle'], default='json')
        parser.add_argument('-r', '--ranks', nargs='+', type=int, default=())
    
    def run(self, args):
        if args.format == 'json':
            read_report = read_json_report
        elif args.format == 'pickle':
            read_report = read_pickle_report
        
        reports = [read_report(path) for path in args.path]

        if args.type == 'pr':
            plot_precision_recall(reports, args.ranks)
        elif args.type == 'roc':
            plot_roc(reports, args.ranks)
        elif args.type == 'metric':
            self.show_metrics(reports, args.ranks)

        pyplot.show(block=not args.interactive)

    def show_metrics(self, reports, ranks):
        for i, report in enumerate(reports):
            frequencies = get_frequencies(report, cutoff=ranks)
            map_ = get_mean_average_precision(report)
            auc = get_roc_auc(frequencies)
            name = report.get('name', '?')
            print 'Test %d: name=%s, MAP=%f, AUC=%f' % (i+1, name, map_, auc)
