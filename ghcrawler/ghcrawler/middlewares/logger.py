from scrapy import log


class LoggerMiddleware(object):
    def process_response(self, request, response, spider):
        message = 'Visited (%d) <%s %s>' % (response.status, 
            request.method, request.url)
        log.msg(message, level=log.INFO, spider=spider)
        return response