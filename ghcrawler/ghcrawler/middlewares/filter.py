import urlparse
import anydbm
import datetime
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
        self.db = anydbm.open(self.path, 'c')

    def spider_closed(self):
        self.db.close()

    def process_request(self, request, spider):
        # infer endpoint for non-paginated requests or first-page requests
        if 'endpoint' not in request.meta:
            request.meta['endpoint'] = self._get_endpoint(request.url)
        
        endpoint = request.meta['endpoint']
        if endpoint in self.db:
            raise IgnoreRequest()

    def process_response(self, request, response, spider):
        if response.status == 200 and not has_next_page(response):
            endpoint = request.meta.get('endpoint', '')
            if endpoint not in ['', '/']:
                time = datetime.datetime.utcnow().strftime(UTC_TIME_FORMAT)
                self.db[endpoint] = time
        return response

    def _get_endpoint(self, url):
        return urlparse.urlparse(url).path
