import os.path

from ghanalyzer.utils.jsonline import JsonLineData

def _load_entities(path, filename):
    path = os.path.join(path, filename)
    with JsonLineData(path) as data:
        return {item.get('id'): item for item in data}

def load_repositories(path, summary=True):
    filename = 'RepositorySummary.jsonl' if summary else 'Repository.jsonl'
    return _load_entities(path, filename)

def load_accounts(path, summary=True):
    filename = 'AccountSummary.jsonl' if summary else 'Account.jsonl'
    return _load_entities(path, filename)

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
