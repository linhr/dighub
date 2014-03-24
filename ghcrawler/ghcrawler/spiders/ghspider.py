import functools
from uritemplate import expand
try:
    from scrapy.spider import Spider # Scrapy version >= 0.22.0
except ImportError:
    from scrapy.spider import BaseSpider as Spider
from scrapy.http import Request

import ghcrawler.items as items
from ghcrawler.utils import parse_json_body, parse_link_header


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

    http_user = ''
    http_pass = ''
    name = 'github-spider'
    allowed_domains = ['api.github.com']
    start_urls = ['https://api.github.com/']

    def __init__(self, start_repos=None, start_users=None, *args, **kwargs):
        super(GitHubSpider, self).__init__(*args, **kwargs)
        self.start_repos = start_repos or [{'owner': 'jquery', 'repo': 'jquery'}]
        self.start_users = start_users or []

    @classmethod
    def from_crawler(cls, crawler, **spider_kwargs):
        spider = cls(**spider_kwargs)
        token = crawler.settings.get('GITHUB_API_TOKEN', None)
        if token:
            spider.http_user = token
            spider.http_pass = 'x-oauth-basic'
        return spider

    def parse(self, response):
        self.endpoints = parse_json_body(response)
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
        repo = parse_json_body(response)
        item = items.Repository.from_dict(repo)
        yield item
        yield Request(
            url=expand(repo['owner']['url'], {}),
            callback=self.parse_user,
        )
        yield Request(
            url=expand(repo['collaborators_url'], {}),
            callback=self.parse_collaborators,
            meta={'repo': item.copy()}
        )
        yield Request(
            url=expand(repo['contributors_url'], {}),
            callback=self.parse_contributors,
            meta={'repo': item.copy()}
        )


    def parse_user(self, response):
        user = parse_json_body(response)
        item = items.Account.from_dict(user)
        yield item
        if user['type'] == 'Organization':
            org_url = self.endpoints['organization_url']
            yield Request(
                url=expand(org_url, {'org': user['login']}),
                callback=self.parse_organization
            )

    def parse_organization(self, response):
        org = parse_json_body(response)
        item = items.Account.from_dict(org)
        yield Request(
            url=expand(org['members_url'], {}),
            callback=self.parse_members,
            meta={'org': item}
        )

    @paginated
    def parse_collaborators(self, response):
        users = parse_json_body(response)
        repo = response.meta['repo']
        for u in users:
            yield items.Collaborator(repo=repo, user=u)

    @paginated
    def parse_contributors(self, response):
        users = parse_json_body(response)
        repo = response.meta['repo']
        for u in users:
            yield items.Contributor(repo=repo, user=u)

    @paginated
    def parse_members(self, response):
        users = parse_json_body(response)
        org = response.meta['org']
        for u in users:
            yield items.Membership(org=org, user=u)

    def next_page(self, response):
        links = parse_link_header(response)
        if 'next' in links:
            r = response.request.replace(url=links['next'])
            r.meta['dont_increase_depth'] = True
            return r
