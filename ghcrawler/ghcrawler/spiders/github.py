import re
import json
import functools
from uritemplate import expand
try:
    from scrapy.spider import Spider # Scrapy version >= 0.22.0
except ImportError:
    from scrapy.spider import BaseSpider as Spider
from scrapy.http import Request

import ghcrawler.items as items


LINK_PATTERN = re.compile(r'<(?P<url>.+)>;\s*rel="(?P<rel>next|prev|first|last)"', flags=re.I)

def paginated(parser):
    @functools.wraps(parser)
    def wrapper(self, response, *args, **kwargs):
        result = parser(self, response, *args, **kwargs)
        for x in result:
            yield x
        next = self.next_page(response)
        if next:
            yield next
    return wrapper


class GitHubSpider(Spider):
    """
    spider to collect data on GitHub
    """

    name = 'github-spider'
    allowed_domains = ['api.github.com']
    start_urls = ['https://api.github.com/']

    def __init__(self, start_repos=None, start_users=None, *args, **kwargs):
        super(GitHubSpider, self).__init__(*args, **kwargs)
        self.start_repos = start_repos or [{ 'owner': 'jquery', 'repo': 'jquery' }]
        self.start_users = start_users or []

    def parse(self, response):
        self.endpoints = self.parse_json_body(response)
        repo_url = self.endpoints['repository_url']
        user_url = self.endpoints['user_url']
        for repo in self.start_repos:
            yield Request(
                url=expand(repo_url, repo),
                callback=self.parse_repository
            )
        for user in self.start_users:
            yield Request(
                url=expand(user_url, user),
                callback=self.parse_user
            )

    def parse_repository(self, response):
        repo = self.parse_json_body(response)
        item = items.Repository.from_dict(repo)
        yield item
        yield Request(
            url=expand(repo['owner']['url'], {}),
            callback=self.parse_user,
        )
        yield Request(
            url=expand(repo['collaborators_url'], {}),
            callback=self.parse_collaborators,
            meta={ 'repo': item.copy() }
        )
        yield Request(
            url=expand(repo['contributors_url'], {}),
            callback=self.parse_contributors,
            meta={ 'repo': item.copy() }
        )


    def parse_user(self, response):
        user = self.parse_json_body(response)
        item = items.Account.from_dict(user)
        yield item
        if user['type'] == 'Organization':
            org_url = self.endpoints['organization_url']
            yield Request(
                url=expand(org_url, { 'org': user['login'] }),
                callback=self.parse_organization
            )

    def parse_organization(self, response):
        org = self.parse_json_body(response)
        item = items.Account.from_dict(org)
        yield Request(
            url=expand(org['members_url'], {}),
            callback=self.parse_members,
            meta={ 'org': item }
        )

    @paginated
    def parse_collaborators(self, response):
        users = self.parse_json_body(response)
        repo = response.meta['repo']
        for u in users:
            yield items.Collaborator(repo=repo, user=u)

    @paginated
    def parse_contributors(self, response):
        users = self.parse_json_body(response)
        repo = response.meta['repo']
        for u in users:
            yield items.Contributor(repo=repo, user=u)

    @paginated
    def parse_members(self, response):
        users = self.parse_json_body(response)
        org = response.meta['org']
        for u in users:
            yield items.Membership(org=org, user=u)

    def parse_json_body(self, response):
        return json.loads(response.body_as_unicode())

    def parse_link_header(self, response):
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

    def next_page(self, response):
        links = self.parse_link_header(response)
        if 'next' in links:
            r = response.request.replace(url=links['next'])
            r.meta['dont_increase_depth'] = True
            return r
