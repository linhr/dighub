import re
import json
from collections import namedtuple
import scrapy.log
import scrapy.logformatter

LINK_PATTERN = re.compile(r'<(?P<url>.+)>;\s*rel="(?P<rel>next|prev|first|last)"', flags=re.I)
NEXT_LINK_PATTERN = re.compile(r'<(?P<url>.+)>;\s*rel="next"', flags=re.I)


RateLimit = namedtuple('RateLimit', ['limit', 'remaining', 'reset'])

def parse_json_body(response):
    if not hasattr(response, 'body_as_unicode'):
        return None
    return json.loads(response.body_as_unicode())

def parse_link_header(response):
    links = {}
    link_headers = response.headers.get('link', '').split(',')
    for link in link_headers:
        match = LINK_PATTERN.search(link)
        if not match:
            continue
        rel = match.group('rel').lower()
        url = match.group('url')
        links[rel] = url
    return links

def has_next_page(response):
    link_header = response.headers.get('link', '')
    return bool(NEXT_LINK_PATTERN.search(link_header))

def parse_rate_limit(response):
    limit = response.headers.get('x-ratelimit-limit', '0')
    remaining = response.headers.get('x-ratelimit-remaining', '0')
    reset = response.headers.get('x-ratelimit-reset', '0')
    return RateLimit(limit=int(limit), remaining=int(remaining), reset=int(reset))


class LogFormatter(scrapy.logformatter.LogFormatter):
    def dropped(self, item, exception, response, spider):
        return {
            'level': scrapy.log.DEBUG,
            'format': scrapy.logformatter.DROPPEDFMT,
            'exception': exception,
            'item': item,
        }
