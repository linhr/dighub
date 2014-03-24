from scrapy import log

from ghcrawler.utils import parse_rate_limit

class LoggerMiddleware(object):

    def __init__(self):
        self.rate_limit_reset = 0

    def process_response(self, request, response, spider):
        limits = parse_rate_limit(response)
        
        if self.rate_limit_reset != limits.reset:
            self.rate_limit_reset = limits.reset
            log.msg(format='Next rate limit reset: %(reset)d',
                level=log.INFO, spider=spider, reset=limits.reset)
        
        log.msg(format=('Visited (%(status)d) <%(method)s %(url)s> '
            '(rate limit remaining: %(remaining)d/%(limit)d)'),
            level=log.INFO, spider=spider,
            status=response.status, method=request.method, url=request.url,
            remaining=limits.remaining, limit=limits.limit)
        
        return response
