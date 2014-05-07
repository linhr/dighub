from matplotlib import pyplot

from ghanalyzer.evaluation.metrics import precision_recall

MARKERS = ['s-', '.--', '^-', 'o-']
COLORS = ['blue', 'magenta', 'red', 'green']

def plot_precision_recall(reports, ranks):
    plots, labels = [], []
    precision_lists, recall_lists = [], []
    for i, report in enumerate(reports):
        precisions, recalls = precision_recall(report, ranks)
        marker = MARKERS[i % len(MARKERS)]
        color = COLORS[i % len(COLORS)]
        line, = pyplot.plot(recalls, precisions, marker, color=color,
            linewidth=3.0, markersize=9.0, markeredgecolor=color)
        label = report.get('name', 'Report %d' % (i+1))
        plots.append(line)
        labels.append(label)
        precision_lists.append(precisions)
        recall_lists.append(recalls)

    pyplot.xlabel('Recall')
    pyplot.ylabel('Precision')
    pyplot.legend(plots, labels, loc=1)
    
    return precision_lists, recall_lists, plots, labels
