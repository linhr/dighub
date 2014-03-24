import re
import json

LINK_PATTERN = re.compile(r'<(?P<url>.+)>;\s*rel="(?P<rel>next|prev|first|last)"', flags=re.I)


def parse_json_body(response):
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