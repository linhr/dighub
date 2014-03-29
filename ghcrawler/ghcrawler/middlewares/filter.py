import urlparse
import anydbm
import datetime
import os.path
from scrapy import signals
from scrapy.exceptions import IgnoreRequest

from ghcrawler.utils import has_next_page

UTC_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

class DuplicateRequestFilter(object):
    def __init__(self, path):
        self.path = path

    @classmethod
    def from_crawler(cls, crawler):
        path = crawler.settings.get('FILTER_STORAGE_PATH')
        o = cls(path)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_opened(self):
        filename = os.path.join(self.path, 'visited.db')
        self.visited = anydbm.open(filename, 'c')
        filename = os.path.join(self.path, 'pending.db')
        self.pending = anydbm.open(filename, 'c')

    def spider_closed(self):
        self.visited.close()
        self.pending.close()

    def process_request(self, request, spider):
        # infer endpoint for non-paginated requests or first-page requests
        if 'endpoint' not in request.meta:
            request.meta['endpoint'] = self._get_endpoint(request.url)
        
        # do not filter start endpoints, even if they are visited
        if request.meta.get('start'):
            return
        
        endpoint = request.meta['endpoint']
        time = self.visited.get(endpoint)
        if time:
            # ignore visited endpoint
            raise IgnoreRequest()
        # mark endpoint for possible visit
        self.visited[endpoint] = ''
        if not request.meta.get('visit'):
            raise IgnoreRequest()

    def process_response(self, request, response, spider):
        if response.status != 200:
            return response
        endpoint = request.meta.get('endpoint', '')
        if endpoint in ['', '/']:
            return response
        if has_next_page(response):
            # mark in progress paginated request
            history = self.pending.get(endpoint)
            self.pending[endpoint] = '; '.join(filter(None, (history, response.url)))
        else:
            time = datetime.datetime.utcnow().strftime(UTC_TIME_FORMAT)
            history = self.visited.get(endpoint)
            self.visited[endpoint] = '|'.join(filter(None, (history, time)))
            self.pending.pop(endpoint, None)
        return response

    def _get_endpoint(self, url):
        return urlparse.urlparse(url).path
