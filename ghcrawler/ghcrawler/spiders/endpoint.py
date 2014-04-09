import os.path
import shelve
import json
import re
from scrapy import log

from ghcrawler.spiders.ghspider import GitHubSpider

class EndpointSpider(GitHubSpider):
    """spider to crawl a specific type of items on GitHub"""

    name = 'endpoint-spider'
    start_urls = []

    requests = []

    def __init__(self, endpoint=None, filter_storage_path='', item_storage_path='',
            policy=None, *args, **kwargs):
        if endpoint in self.default_policy:
            if policy is None:
                policy = {}
            policy.update({endpoint: True})
        super(EndpointSpider, self).__init__(policy=policy, *args, **kwargs)
        self.endpoint = endpoint
        self.filter_storage_path = filter_storage_path
        self.item_storage_path = item_storage_path
        self.requests = self._generate_requests()
    
    def start_requests(self):
        self.log('Start request count: %d' % len(self.requests), level=log.INFO)
        for x in self.requests:
            self.log('Start request: %s' % x, level=log.INFO)
            yield x

    @classmethod
    def from_crawler(cls, crawler, **spider_kwargs):
        kwargs = {
            'filter_storage_path': crawler.settings.get('FILTER_STORAGE_PATH', ''),
            'item_storage_path': crawler.settings.get('ITEM_STORAGE_PATH', ''),
        }
        kwargs.update(spider_kwargs)
        spider_kwargs = kwargs
        spider = super(EndpointSpider, cls).from_crawler(crawler, **spider_kwargs)
        return spider

    def _generate_requests(self):
        if self.endpoint not in self.endpoints:
            return []

        requested = shelve.open(os.path.join(self.filter_storage_path, 'requested.db'), 'r')

        if self.endpoint.startswith('repository'):
            pattern = re.compile(r'^/repos/(?P<owner>[^/]+)/(?P<repo>[^/]+)')
            template = r'\g<owner>/\g<repo>'
            ids = self._load_ids('repository')
            metatype = 'repo'
        elif self.endpoint.startswith('user'):
            pattern = re.compile(r'^/users/(?P<user>[^/]+)')
            template = r'\g<user>'
            ids = self._load_ids('account')
            metatype = 'user'
        elif self.endpoint.startswith('organization'):
            pattern = re.compile(r'^/orgs/(?P<org>[^/]+)')
            template = r'\g<org>'
            ids = self._load_ids('account')
            metatype = 'org'
        
        if self.endpoint in ['repository', 'user', 'organization']:
            meta = lambda k: None
        else:
            meta = lambda k: {metatype: {'id': ids.get(k)}}

        candidates = {}
        for path in requested.iterkeys():
            m = pattern.match(path)
            if not m:
                continue
            key = m.expand(template)
            if key in candidates:
                continue
            candidates[key] = self._request_from_endpoint(self.endpoint,
                params=m.groupdict(), meta=meta(key))

        requested.close()

        return candidates.values()

    def _load_ids(self, item_type):
        filename, key = {
            'account': ('AccountSummary.jsonl', 'login'),
            'repository': ('RepositorySummary.jsonl', 'full_name'),
        }[item_type]
        filename = os.path.join(self.item_storage_path, filename)
        data = open(filename)
        result = {}
        for line in data:
            item = json.loads(line)
            if key in item and 'id' in item:
                result[item[key]] = item['id']
        data.close()
        return result
