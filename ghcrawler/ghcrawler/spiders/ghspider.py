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

    def __init__(self, start_repos=None, start_users=None, start_orgs=None,
            *args, **kwargs):
        super(GitHubSpider, self).__init__(*args, **kwargs)
        self.start_repos = start_repos or [{'owner': 'jquery', 'repo': 'jquery'}]
        self.start_users = start_users or []
        self.start_orgs = start_orgs or []

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
        for repo in self.start_repos:
            yield Request(
                url=expand(self.endpoints['repository_url'], repo),
                callback=self.parse_repository
            )
        for user in self.start_users:
            yield Request(
                url=expand(self.endpoints['user_url'], user),
                callback=self.parse_user
            )
        for org in self.start_orgs:
            yield Request(
                url=expand(self.endpoints['organization_url'], org),
                callback=self.parse_organization
            )

    def parse_repository(self, response):
        repo = parse_json_body(response)
        item = items.Repository.from_dict(repo)
        yield item
        yield self._account_request(repo['owner'])
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
        yield Request(
            url=expand(repo['languages_url'], {}),
            callback=self.parse_repository_languages,
            meta={'repo': item.copy()}
        )
        yield Request(
            url=expand(repo['stargazers_url'], {}),
            callback=self.parse_stargazers,
            meta={'repo': item.copy()}
        )
        yield Request(
            url=expand(repo['subscribers_url'], {}),
            callback=self.parse_subscribers,
            meta={'repo': item.copy()}
        )


    def parse_user(self, response):
        user = parse_json_body(response)
        item = items.Account.from_dict(user)
        yield item
        yield Request(
            url=expand(user['followers_url'], {}),
            callback=self.parse_followers,
            meta={'followee': item.copy()}
        )
        yield Request(
            url=expand(user['following_url'], {}),
            callback=self.parse_accounts
        )
        yield Request(
            url=expand(user['repos_url'], {}),
            callback=self.parse_repositories
        )
        yield Request(
            url=expand(user['starred_url'], {}),
            callback=self.parse_repositories
        )
        yield Request(
            url=expand(user['subscriptions_url'], {}),
            callback=self.parse_repositories
        )
        yield Request(
            url=expand(user['organizations_url'], {}),
            callback=self.parse_accounts
        )

    def parse_organization(self, response):
        org = parse_json_body(response)
        item = items.Account.from_dict(org)
        yield item
        yield Request(
            url=expand(org['members_url'], {}),
            callback=self.parse_members,
            meta={'org': item.copy()}
        )
        yield Request(
            url=expand(org['repos_url'], {}),
            callback=self.parse_repositories
        )

    @paginated
    def parse_collaborators(self, response):
        users = parse_json_body(response)
        repo = response.meta['repo']
        for u in users:
            yield items.Collaborator(repo=repo, user=u)
            yield self._account_request(u)

    @paginated
    def parse_contributors(self, response):
        users = parse_json_body(response)
        repo = response.meta['repo']
        for u in users:
            yield items.Contributor(repo=repo, user=u)
            yield self._account_request(u)

    def parse_repository_languages(self, response):
        languages = parse_json_body(response)
        repo = response.meta['repo']
        yield items.Languages(repo=repo, languages=languages)

    @paginated
    def parse_stargazers(self, response):
        users = parse_json_body(response)
        repo = response.meta['repo']
        for u in users:
            yield items.Stargazer(repo=repo, user=u)
            yield self._account_request(u)

    @paginated
    def parse_subscribers(self, response):
        users = parse_json_body(response)
        repo = response.meta['repo']
        for u in users:
            yield items.Subscriber(repo=repo, user=u)
            yield self._account_request(u)

    @paginated
    def parse_repositories(self, response):
        repos = parse_json_body(response)
        for r in repos:
            yield self._repository_request(r)

    @paginated
    def parse_followers(self, response):
        users = parse_json_body(response)
        followee = response.meta['followee']
        for u in users:
            yield items.Follow(follower=u, followee=followee)
            yield self._account_request(u)

    @paginated
    def parse_accounts(self, response):
        accounts = parse_json_body(response)
        for a in accounts:
            yield self._account_request(a)

    @paginated
    def parse_members(self, response):
        users = parse_json_body(response)
        org = response.meta['org']
        for u in users:
            yield items.Membership(org=org, user=u)
            yield self._account_request(u)

    def next_page(self, response):
        links = parse_link_header(response)
        if 'next' in links:
            r = response.request.replace(url=links['next'])
            r.meta['dont_increase_depth'] = True
            return r

    def _account_request(self, account):
        if account.get('type') == 'Organization':
            endpoint = self.endpoints['organization_url']
            return Request(
                url=expand(endpoint, {'org': account['login']}),
                callback=self.parse_organization
            )
        else:
            endpoint = self.endpoints['user_url']
            return Request(
                url=expand(endpoint, {'user': account['login']}),
                callback=self.parse_user
            )

    def _repository_request(self, repo):
        return Request(
            url=expand(repo['url'], {}),
            callback=self.parse_repository
        )
