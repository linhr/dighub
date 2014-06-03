import numpy as np
from scipy.stats import nanmean


def get_frequencies(report, cutoff=None):
    repo_map = {r.id: i for i, r in enumerate(report['repos'])}
    repo_count = len(repo_map)
    case_count = len(report['recommendation'])
    try:
        cutoff = tuple(cutoff)
    except TypeError:  # cutoff is a single value (None or int)
        cutoff = (cutoff,)

    def _get_indices(repos):
        return [repo_map[r.id] for r in repos]

    frequencies = np.empty((case_count, len(cutoff), 4))
    for i, x in enumerate(report['recommendation']):
        candidates = np.ones(repo_count, dtype=bool)
        candidates[_get_indices(x['training'])] = False
        groundtruth = np.zeros(repo_count, dtype=bool)
        groundtruth[_get_indices(x['groundtruth'])] = True
        recommended = np.zeros(repo_count, dtype=int)
        recommended[_get_indices(x['recommended'])] = np.arange(len(x['recommended'])) + 1
        for j, k in enumerate(cutoff):
            positive = recommended > 0
            if k is not None:
                positive &= recommended <= k
            negative = candidates & (~positive)
            tp = np.count_nonzero(positive & groundtruth)
            fp = np.count_nonzero(positive) - tp
            fn = np.count_nonzero(negative & groundtruth)
            tn = np.count_nonzero(negative) - fn
            frequencies[i, j, :] = tp, tn, fp, fn
    if len(cutoff) == 1:
        frequencies = np.reshape(frequencies, (case_count, 4))
    return frequencies

def get_precision(frequencies):
    tp = frequencies[:, ..., 0].sum(axis=0)
    fp = frequencies[:, ..., 2].sum(axis=0)
    return tp / (tp + fp)

def get_recall(frequencies):
    tp = frequencies[:, ..., 0].sum(axis=0)
    fn = frequencies[:, ..., 3].sum(axis=0)
    return tp / (tp + fn)

get_sensitivity = get_recall

def get_fallout(frequencies):
    tn = frequencies[:, ..., 1].sum(axis=0)
    fp = frequencies[:, ..., 2].sum(axis=0)
    return fp / (fp + tn)

def precision_recall_curve(frequencies):
    precision = get_precision(frequencies)
    recall = get_recall(frequencies)
    return precision, recall

def roc_curve(frequencies):
    sensitivity = get_sensitivity(frequencies)
    fallout = get_fallout(frequencies)
    return sensitivity, fallout

def get_average_precision(report):
    case_count = len(report['recommendation'])
    average_precision = np.empty((case_count,))
    average_precision.fill(np.nan)
    for i, x in enumerate(report['recommendation']):
        groundtruth = x['groundtruth']
        recommended = x['recommended']
        if not groundtruth:
            continue
        counter, true_positive = 0.0, 0
        for k, r in enumerate(recommended):
            if r in groundtruth:
                true_positive += 1
                counter += float(true_positive) / (k + 1)
        average_precision[i] = float(counter) / len(groundtruth)
    return average_precision

def get_mean_average_precision(report):
    average_precision = get_average_precision(report)
    return nanmean(average_precision)

def get_roc_auc(frequencies):
    sensitivity, fallout = roc_curve(frequencies)
    y = np.atleast_1d(sensitivity)
    x = np.atleast_1d(fallout)
    if 0.0 not in x:
        x = np.append(x, 0.0)
        y = np.append(y, 0.0)
    if 1.0 not in x:
        x = np.append(x, 1.0)
        y = np.append(y, 1.0)
    order = np.lexsort((y, x))
    x, y = x[order], y[order]
    auc = np.trapz(y, x)
    return auc
