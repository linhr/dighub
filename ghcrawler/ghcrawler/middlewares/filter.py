import urlparse
import shelve
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
        path = crawler.settings.get('FILTER_STORAGE_PATH', '')
        o = cls(path)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_opened(self):
        filename = os.path.join(self.path, 'requested.db')
        self.requested = shelve.open(filename, 'c')
        filename = os.path.join(self.path, 'visited.db')
        self.visited = shelve.open(filename, 'c')
        filename = os.path.join(self.path, 'pending.db')
        self.pending = shelve.open(filename, 'c')

    def spider_closed(self):
        self.requested.close()
        self.visited.close()
        self.pending.close()

    def process_request(self, request, spider):
        # infer endpoint for non-paginated requests or first-page requests
        if 'endpoint' not in request.meta:
            request.meta['endpoint'] = self._get_endpoint(request.url)
        # log and select requests to visit
        # start endpoints are always not filtered
        start = request.meta.get('start')
        endpoint = request.meta['endpoint']
        if endpoint in self.visited and not start:
            raise IgnoreRequest()
        self._append_value(self.requested, endpoint, {
            'time': self._now(),
            'depth': request.meta.get('depth'),
            'priority': request.priority,
            'params': self._get_params(request.url),
        })
        if not request.meta.get('visit') and not start:
            raise IgnoreRequest()

    def process_response(self, request, response, spider):
        if response.status != 200:
            return response
        endpoint = request.meta.get('endpoint', '')
        if endpoint in ['', '/']:
            return response
        if has_next_page(response):
            # mark in progress paginated request
            self._append_value(self.pending, endpoint, {
                'time': self._now(),
                'params': self._get_params(response.url),
            })
        else:
            self._append_value(self.visited, endpoint, {'time': self._now()})
            self.pending.pop(endpoint, None)
        return response

    def _now(self):
        return datetime.datetime.utcnow().strftime(UTC_TIME_FORMAT)

    def _append_value(self, db, k, v):
        if k in db:
            values = db[k]
            values.append(v)
            db[k] = values
        else:
            db[k] = [v]

    def _get_endpoint(self, url):
        return urlparse.urlparse(url).path

    def _get_params(self, url):
        return urlparse.urlparse(url).query
