from scrapy import log

from ghcrawler.utils import parse_rate_limit

class LoggerMiddleware(object):

    def __init__(self):
        self.rate_limit_reset = 0

    def process_response(self, request, response, spider):
        limits = parse_rate_limit(response)
        if self.rate_limit_reset != limits.reset:
            self.rate_limit_reset = limits.reset
            message = 'Next rate limit reset: %d' % limits.reset
            log.msg(message, level=log.INFO, spider=spider)
        message = 'Visited (%d) <%s %s> (rate limit remaining: %d/%d)' % (response.status, 
            request.method, request.url, limits.remaining, limits.limit)
        log.msg(message, level=log.INFO, spider=spider)
        return response
