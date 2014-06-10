import os.path

import numpy as np
from matplotlib import pyplot

from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.io import read_json_report, read_pickle_report
from ghanalyzer.evaluation.metrics import (
    get_frequencies,
    get_precision,
    get_recall,
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
        parser.add_argument('--show-precision', action='store_true')
        parser.add_argument('--show-recall', action='store_true')
    
    def run(self, args):
        reports = self._iter_reports(args)

        if args.type == 'pr':
            plot_precision_recall(reports, args.ranks)
        elif args.type == 'roc':
            plot_roc(reports, args.ranks)
        elif args.type == 'metric':
            self.show_metrics(reports, args.ranks,
                show_precision=args.show_precision,
                show_recall=args.show_recall)

        pyplot.show(block=not args.interactive)

    def show_metrics(self, reports, ranks, show_precision=False, show_recall=False):
        for i, report in enumerate(reports):
            frequencies = get_frequencies(report, cutoff=ranks)
            precision = np.atleast_1d(get_precision(frequencies))
            recall = np.atleast_1d(get_recall(frequencies))
            map_ = get_mean_average_precision(report)
            auc = get_roc_auc(frequencies)
            name = report.get('name', '?')
            filename = report.get('filename', '?')
            print 'Test %d: name=%s <%s>' % (i+1, name, filename)
            print '\t',
            if show_precision:
                for i, k in enumerate(ranks):
                    print 'P@%d=%f, ' % (k, precision[i]),
            if show_recall:
                for i, k in enumerate(ranks):
                    print 'R@%d=%f, ' % (k, recall[i]),
            print 'MAP=%f, AUC=%f' % (map_, auc)

    def _iter_reports(self, args):
        if args.format == 'json':
            read_report = read_json_report
        elif args.format == 'pickle':
            read_report = read_pickle_report

        for path in args.path:
            report = read_report(path)
            report['filename'] = os.path.basename(path)
            yield report
