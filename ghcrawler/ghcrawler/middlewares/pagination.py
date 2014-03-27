import urllib
import urlparse
import re
import signal
import scrapy.signals
from scrapy import log
from scrapy.http import Request
from scrapy.exceptions import IgnoreRequest

ITEMS_PER_PAGE = 100
PAGINATED_ENDPOINTS = [re.compile(e) for e in [
    r'/orgs/.+?/(repos|members|public_members)',
    r'/users/.+?/(followers|following|starred|subscriptions|orgs|repos)',
    r'/repos/.+?/.+?/(forks|collaborators|contributors|stargazers|subscribers|issues|pulls)',
]]

class PaginationMiddleware(object):
    def process_request(self, request, spider):
        url = request.url
        parts = list(urlparse.urlparse(url))
        path = parts[2]
        query = urlparse.parse_qs(parts[4])
        if 'per_page' in query:
            return
        for r in PAGINATED_ENDPOINTS:
            if r.search(path):
                query.update({'per_page': [ITEMS_PER_PAGE]})
                parts[4] = urllib.urlencode(query, doseq=True)
                url = urlparse.urlunparse(parts)
                return request.replace(url=url)


class PaginationAwareShutdownMiddleware(object):
    '''
    finish spider job gracefully after receiving SIGINT
    try to finish crawling all ongoing paginated endpoints while ignoring others
    '''
    def __init__(self, enabled=False):
        self._shutdown = False
        self._enabled = enabled
        if enabled:
            self._old_interrupt_handler = signal.signal(signal.SIGINT, self._handle_interrupt)

    @classmethod
    def from_crawler(cls, crawler):
        enabled = crawler.settings.getbool('PAGINATION_AWARE_SHUTDOWN_ENABLED', False)
        o = cls(enabled=enabled)
        crawler.signals.connect(o.spider_opened, signal=scrapy.signals.spider_opened)
        return o

    def spider_opened(self, spider):
        shutdown = spider.state.get('pagination_aware_shutdown', False)
        if shutdown:
            log.msg('Continue pagination-aware shutdown for resumed spider',
                level=log.INFO)
            self._shutdown = True

    def _handle_interrupt(self, signum, frame):
        signal.signal(signal.SIGINT, self._old_interrupt_handler)
        if not self._shutdown:
            log.msg('Received SIGINT, start pagination-aware shutdown', level=log.INFO)
            self._shutdown = True
        else:
            log.msg('Received SIGINT (pagination-aware shutdown in progress)', level=log.INFO)
        
    def process_request(self, request, spider):
        if not self._shutdown:
            return
        spider.state['pagination_aware_shutdown'] = True
        if not request.meta.get('has_previous_page'):
            log.msg(format='Ignored <%(method)s %(url)s> (reason: pagination-aware shutdown)',
                level=log.INFO, method=request.method, url=request.url)
            raise IgnoreRequest
        