import urllib
import urlparse
import re

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
