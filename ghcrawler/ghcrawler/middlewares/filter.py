import urlparse
import shelve
import datetime
import os.path
from scrapy import signals
from scrapy.http import Request
from scrapy.exceptions import IgnoreRequest

from ghcrawler.utils import has_next_page

UTC_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

def _now():
    return datetime.datetime.utcnow().strftime(UTC_TIME_FORMAT)

def _append_value(db, k, v):
    if k in db:
        values = db[k]
        values.append(v)
        db[k] = values
    else:
        db[k] = [v]

def _get_endpoint(url):
    return urlparse.urlparse(url).path

def _get_params(url):
    return urlparse.urlparse(url).query


class FilterMiddleware(object):
    def __init__(self, path):
        self.path = path

    @classmethod
    def from_crawler(cls, crawler):
        path = crawler.settings.get('FILTER_STORAGE_PATH', '')
        if path and not os.path.exists(path):
            os.makedirs(path)
        o = cls(path)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_opened(self):
        return

    def spider_closed(self):
        return

class DuplicateRequestFilter(FilterMiddleware):
    def spider_opened(self):
        filename = os.path.join(self.path, 'visited.db')
        self.visited = shelve.open(filename, 'c')
        filename = os.path.join(self.path, 'pending.db')
        self.pending = shelve.open(filename, 'c')

    def spider_closed(self):
        self.visited.close()
        self.pending.close()

    def process_request(self, request, spider):
        start = request.meta.get('start')
        endpoint = request.meta.get('endpoint')
        if endpoint in self.visited and not start:
            raise IgnoreRequest()

    def process_response(self, request, response, spider):
        if response.status != 200:
            return response
        endpoint = request.meta.get('endpoint', '')
        if endpoint in ['', '/']:
            return response
        if has_next_page(response):
            # mark in progress paginated request
            _append_value(self.pending, endpoint, {
                'time': _now(),
                'params': _get_params(response.url),
            })
        else:
            _append_value(self.visited, endpoint, {'time': _now()})
            self.pending.pop(endpoint, None)
        return response


class RequestRecorder(FilterMiddleware):
    def spider_opened(self):
        filename = os.path.join(self.path, 'requested.db')
        self.requested = shelve.open(filename, 'c')

    def spider_closed(self):
        self.requested.close()

    def _filter_request(self, request):
        # infer endpoint for non-paginated requests or first-page requests
        if 'endpoint' not in request.meta:
            request.meta['endpoint'] = _get_endpoint(request.url)
        # log and select requests to visit
        # start endpoints are always not filtered
        start = request.meta.get('start')
        endpoint = request.meta['endpoint']
        _append_value(self.requested, endpoint, {
            'time': _now(),
            'depth': request.meta.get('depth'),
            'priority': request.priority,
            'params': _get_params(request.url),
        })
        return request.meta.get('visit') or start

    def process_spider_output(self, response, result, spider):
        result = result or ()
        for x in result:
            if not isinstance(x, Request):
                yield x
            elif self._filter_request(x):
                yield x

    def process_start_requests(self, start_requests, spider):
        for x in start_requests:
            if self._filter_request(x):
                yield x
