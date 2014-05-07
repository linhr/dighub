import json
import cPickle as pickle

from ghanalyzer.io.graphs import EntityEncoder, _model_from_json


def read_json_report(path):
    with open(path) as f:
        report = json.load(f)
        for x in report.get('recommendation', ()):
            x['user'] = _model_from_json(x['user'])
            x['recommended'] = list(filter(None, (_model_from_json(y) for y in x['recommended'])))
            x['groundtruth'] = list(filter(None, (_model_from_json(y) for y in x['groundtruth'])))
        return report

def write_json_report(path, report, indent=None):
    with open(path, 'w') as output:
        json.dump(report, output, cls=EntityEncoder, indent=indent)

def read_pickle_report(path):
    with open(path, 'rb') as f:
        return pickle.load(f)

def write_pickle_report(path, report):
    with open(path, 'wb') as output:
        pickle.dump(report, output)
