from math import isnan


def _iterate_result(report):
    for x in report.get('recommendation', ()):
        yield x.get('user', None), x.get('recommended', ()), x.get('groundtruth', ())

def iter_precision_recall(report, k=None):
    for _, recommended, groundtruth in _iterate_result(report):
        if k is not None:
            recommended = recommended[:k]
        correct = set(recommended) & set(groundtruth)
        if recommended and groundtruth:
            precision = float(len(correct)) / len(recommended)
            recall = float(len(correct)) / len(groundtruth)
            yield precision, recall
        else:
            yield float('nan'), float('nan')

def iter_precision(report, k=None):
    for precision, _ in iter_precision_recall(report, k):
        yield precision

def iter_recall(report, k=None):
    for _, recall in iter_precision_recall(report, k):
        yield recall

def average_metric(metric_iterable):
    metric = list(filter(lambda x: not isnan(x), metric_iterable))
    if not metric:
        return float('nan')
    return float(sum(metric)) / len(metric)

def precision_recall(report, ranks):
    precision, recall = [], []
    for k in ranks:
        p, r = zip(*list(iter_precision_recall(report, k)))
        precision.append(average_metric(p))
        recall.append(average_metric(r))
    return precision, recall
