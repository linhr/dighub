import os.path
import shelve
import json
import re
from scrapy import log
from scrapy import signals
from scrapy.utils.reqser import request_to_dict, request_from_dict
from scrapy.utils.job import job_dir
from scrapy.utils.misc import load_object

from ghcrawler.spiders.ghspider import GitHubSpider

class EndpointSpider(GitHubSpider):
    """spider to crawl a specific type of items on GitHub"""

    name = 'endpoint-spider'
    start_urls = []

    requestqueue = None

    def __init__(self, endpoint=None, filter_storage_path='', item_storage_path='',
            policy=None, *args, **kwargs):
        super(EndpointSpider, self).__init__(policy=policy, *args, **kwargs)
        self.endpoint = endpoint
        self.filter_storage_path = filter_storage_path
        self.item_storage_path = item_storage_path
    
    def start_requests(self):
        if self.requestqueue is None:
            return
        while True:
            request = self.dequeue_start_request()
            if not request:
                break
            self.log('Start request: %s' % request, level=log.INFO)
            yield request

    @classmethod
    def from_crawler(cls, crawler, **spider_kwargs):
        settings = crawler.settings
        kwargs = {
            'filter_storage_path': settings.get('FILTER_STORAGE_PATH', ''),
            'item_storage_path': settings.get('ITEM_STORAGE_PATH', ''),
        }
        kwargs.update(spider_kwargs)
        spider_kwargs = kwargs
        spider = super(EndpointSpider, cls).from_crawler(crawler, **spider_kwargs)
        spider.stats = crawler.stats
        
        jobdir = job_dir(settings)
        generated = False
        if jobdir:
            queuecls = load_object(settings['SCHEDULER_DISK_QUEUE'])
            queuedir = os.path.join(jobdir, 'startrequests.queue')
            if os.path.exists(queuedir):
                generated = True
            spider.requestqueue = queuecls(os.path.join(queuedir, '0'))
        else:
            queuecls = load_object(settings['SCHEDULER_MEMORY_QUEUE'])
            spider.requestqueue = queuecls()
        if not generated:
            for x in spider.generate_start_requests():
                spider.enqueue_start_request(x)

        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def generate_start_requests(self):
        if self.endpoint not in self.endpoints:
            return

        requested = shelve.open(os.path.join(self.filter_storage_path, 'requested.db'), 'r')

        if self.endpoint.startswith('repository'):
            pattern = re.compile(r'^/repos/(?P<owner>[^/]+)/(?P<repo>[^/]+)')
            template = r'\g<owner>/\g<repo>'
            items = self._load_items('repository')
            metatype = 'repo'
        elif self.endpoint.startswith('user'):
            pattern = re.compile(r'^/users/(?P<user>[^/]+)')
            template = r'\g<user>'
            items = self._load_items('account')
            metatype = 'user'
        elif self.endpoint.startswith('organization'):
            pattern = re.compile(r'^/orgs/(?P<org>[^/]+)')
            template = r'\g<org>'
            items = self._load_items('account')
            metatype = 'org'
        
        if self.endpoint in ['repository', 'user', 'organization']:
            meta = lambda k: {'start': True}
        else:
            meta = lambda k: {metatype: items.get(k), 'start': True}

        candidates = set()
        for path in requested.iterkeys():
            m = pattern.match(path)
            if not m:
                continue
            key = m.expand(template)
            if key in candidates:
                continue
            candidates.add(key)
            yield self._request_from_endpoint(self.endpoint,
                params=m.groupdict(), meta=meta(key))

        requested.close()

    def _load_items(self, item_type):
        filename, key = {
            'account': ('AccountSummary.jsonl', 'login'),
            'repository': ('RepositorySummary.jsonl', 'full_name'),
        }[item_type]
        filename = os.path.join(self.item_storage_path, filename)
        data = open(filename)
        result = {}
        for line in data:
            item = json.loads(line)
            if key in item:
                result[item[key]] = item
        data.close()
        return result

    def enqueue_start_request(self, request):
        if self.requestqueue is None:
            return
        try:
            d = request_to_dict(request, self)
            self.requestqueue.push(d)
            self.stats.inc_value('startrequests/enqueued', spider=self)
        except ValueError as e:
            self.log('Non-serializable start request: %s (reason: %s)' % (request, e),
                level=log.ERROR)

    def dequeue_start_request(self):
        if self.requestqueue is None:
            return
        d = self.requestqueue.pop()
        if d is None:
            return
        self.stats.inc_value('startrequests/dequeued', spider=self)
        return request_from_dict(d, self)

    def spider_closed(self, spider):
        if spider != self:
            return
        if self.requestqueue is not None:
            self.requestqueue.close()
