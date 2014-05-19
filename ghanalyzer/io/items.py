import os.path
from collections import defaultdict

from ghanalyzer.utils.jsonline import JsonLineData

def _load_datasets(path, *filenames):
    dataset = defaultdict(dict)
    for filename in filenames:
        data_path = os.path.join(path, filename)
        with JsonLineData(data_path) as data:
            for item in data:
                id_ = item.get('id')
                if id_ is None:
                    continue
                dataset[id_].update(item)
    return dataset

def _load_entities(path, type_, summary=None):
    filenames = (type_ + '.jsonl', type_ + 'Summary.jsonl')
    if summary is None:
        return _load_datasets(path, *filenames)
    if summary:
        return _load_datasets(path, filenames[1])
    else:
        return _load_datasets(path, filenames[0])

def load_repositories(path, summary=None):
    return _load_entities(path, 'Repository', summary=summary)

def load_accounts(path, summary=None):
    return _load_entities(path, 'Account', summary=summary)

def load_repository_languages(path):
    path = os.path.join(path, 'Languages.jsonl')
    with JsonLineData(path) as data:
        return {item['repo']['id']: item['languages'] for item in data}

def load_repository_descriptions(path, summary=True, show_fork=False):
    filename = 'RepositorySummary.jsonl' if summary else 'Repository.jsonl'
    path = os.path.join(path, filename)
    if show_fork:
        valid = lambda x: True
    else:
        valid = lambda x: not x.get('fork')
    with JsonLineData(path) as data:
        return {item.get('id'): item.get('description') or '' for item in data if valid(item)}
