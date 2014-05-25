import numpy as np
from scipy.integrate import quad
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.stats import nanmean


def get_frequencies(report, cutoff=None):
    repos = set(r.id for r in report['repos'])
    case_count = len(report['recommendation'])
    try:
        cutoff = tuple(cutoff)
    except TypeError:  # cutoff is a single value (None or int)
        cutoff = (cutoff,)
    frequencies = np.empty((case_count, len(cutoff), 4))
    for i, x in enumerate(report['recommendation']):
        candidates = repos - set(r.id for r in x['training'])
        groundtruth = set(r.id for r in x['groundtruth'])
        recommended = [r.id for r in x['recommended']]
        for j, k in enumerate(cutoff):
            # recommendation list is not sliced if k is None
            positive = set(recommended[:k])
            negative = candidates - positive
            tp = len(positive & groundtruth)
            fp = len(positive) - tp
            fn = len(negative & groundtruth)
            tn = len(negative) - fn
            frequencies[i, j, :] = tp, tn, fp, fn
    if len(cutoff) == 1:
        frequencies = np.reshape(frequencies, (case_count, 4))
    return frequencies

def get_precision(frequencies):
    tp = frequencies[:, ..., 0]
    fp = frequencies[:, ..., 2]
    return tp / (tp + fp)

def get_recall(frequencies):
    tp = frequencies[:, ..., 0]
    fn = frequencies[:, ..., 3]
    return tp / (tp + fn)

get_sensitivity = get_recall

def get_fallout(frequencies):
    tn = frequencies[:, ..., 1]
    fp = frequencies[:, ..., 2]
    return fp / (fp + tn)

def precision_recall_curve(frequencies):
    precision = nanmean(get_precision(frequencies), axis=0)
    recall = nanmean(get_recall(frequencies), axis=0)
    return precision, recall

def roc_curve(frequencies):
    sensitivity = nanmean(get_sensitivity(frequencies), axis=0)
    fallout = nanmean(get_fallout(frequencies), axis=0)
    return sensitivity, fallout

def get_average_precision(frequencies, degree=3):
    if frequencies.ndim == 2 or frequencies.shape[1] <= degree:
        raise ValueError('more data points are needed to interpolate precision-recall curve')
    precision = get_precision(frequencies)
    recall = get_recall(frequencies)
    case_count = frequencies.shape[0]
    average_precision = np.empty((case_count,))
    for i in xrange(case_count):
        x = recall[i, :]
        y = precision[i, :]
        if 0.0 not in x:
            x = np.append(x, 0.0)
            y = np.append(y, 0.0)
        try:
            f = InterpolatedUnivariateSpline(x, y, k=degree)
            average_precision[i], _ = quad(f, 0.0, 1.0)
        except:
            average_precision[i] = np.nan
    return average_precision

def get_mean_average_precision(frequencies, degree=3):
    average_precision = get_average_precision(frequencies, degree=degree)
    return nanmean(average_precision)

def get_roc_auc(frequencies, degree=3):
    if frequencies.ndim == 2 or frequencies.shape[1] <= degree:
        raise ValueError('more data points are needed to interpolate ROC curve')
    sensitivity = get_sensitivity(frequencies)
    fallout = get_fallout(frequencies)
    case_count = frequencies.shape[0]
    auc = np.empty((case_count,))
    for i in xrange(case_count):
        x = fallout[i, :]
        y = sensitivity[i, :]
        if 0.0 not in x:
            x = np.append(x, 0.0)
            y = np.append(y, 0.0)
        if 1.0 not in x:
            x = np.append(x, 1.0)
            y = np.append(y, 1.0)
        try:
            f = InterpolatedUnivariateSpline(x, y, k=degree)
            auc[i], _ = quad(f, 0.0, 1.0)
        except:
            auc[i] = np.nan
    return nanmean(auc)
