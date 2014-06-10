import numpy as np
from matplotlib import pyplot

from ghanalyzer.evaluation.metrics import (
    get_frequencies,
    precision_recall_curve,
    roc_curve,
)

MARKERS = ['s-', '.--', '^-', 'o-']
COLORS = ['blue', 'magenta', 'red', 'green']

def _plot_report_curves(reports, plotter):
    for i, report in enumerate(reports):
        x, y = plotter(report)
        label = report.get('name', 'Report %d' % (i+1))
        marker = MARKERS[i % len(MARKERS)]
        color = COLORS[i % len(COLORS)]
        pyplot.plot(x, y, marker, label=label, color=color,
            linewidth=3.0, markersize=9.0, markeredgecolor=color)


def plot_precision_recall(reports, ranks):
    def _plot_curve(report):
        frequencies = get_frequencies(report, cutoff=ranks)
        precision, recall = precision_recall_curve(frequencies)
        order = np.argsort(recall)
        return recall[order], precision[order]

    _plot_report_curves(reports, _plot_curve)
    pyplot.xlabel('Recall')
    pyplot.ylabel('Precision')
    pyplot.legend(loc=1)


def plot_roc(reports, ranks):
    def _plot_curve(report):
        frequencies = get_frequencies(report, cutoff=ranks)
        sensitivity, fallout = roc_curve(frequencies)
        x = np.append(fallout, (0.0, 1.0))
        y = np.append(sensitivity, (0.0, 1.0))
        order = np.argsort(x)
        return x[order], y[order]

    _plot_report_curves(reports, _plot_curve)
    pyplot.xlabel('False positive rate')
    pyplot.ylabel('True positive rate')
    pyplot.legend(loc=4)
