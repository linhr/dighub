import functools
import uritemplate
import urlparse
try:
    from scrapy.spider import Spider # Scrapy version >= 0.22.0
except ImportError:
    from scrapy.spider import BaseSpider as Spider
from scrapy.http import Request
from scrapy import log

import ghcrawler.items as items
from ghcrawler.utils import parse_json_body, parse_link_header


def response_parser(paginated=False):
    def decorator(parser):
        @functools.wraps(parser)
        def wrapper(self, response):
            body = parse_json_body(response)
            if body is not None:
                result = parser(self, body, response.meta)
                for x in result:
                    yield x
            if paginated:
                next = self.next_page(response)
                if next:
                    yield next
        return wrapper
    return decorator


class GitHubSpider(Spider):
    """base class of GitHub spiders"""

    http_user = ''
    http_pass = ''
    name = None
    allowed_domains = ['api.github.com']
    start_urls = []

    site = 'https://api.github.com'
    endpoints = {
        'repository': '/repos/{owner}/{repo}',
        'user': '/users/{user}',
        'organization': '/orgs/{org}',
        'repository_forks': '/repos/{owner}/{repo}/forks',
        'repository_collaborators': '/repos/{owner}/{repo}/collaborators',
        'repository_languages': '/repos/{owner}/{repo}/languages',
        'repository_stargazers': '/repos/{owner}/{repo}/stargazers',
        'repository_contributors': '/repos/{owner}/{repo}/contributors',
        'repository_subscribers': '/repos/{owner}/{repo}/subscribers',
        'repository_commits': '/repos/{owner}/{repo}/commits',
        'user_organizations': '/users/{user}/orgs',
        'user_repositories': '/users/{user}/repos',
        'user_followers': '/users/{user}/followers',
        'user_following': '/users/{user}/following',
        'user_starred': '/users/{user}/starred',
        'user_subscriptions': '/users/{user}/subscriptions',
        'organization_repositories': '/orgs/{org}/repos',
        'organization_members': '/orgs/{org}/members',
    }
    default_policy = {
        'repository': False,
        'user': True,
        'organization': True,
        'repository_forks': False,
        'repository_collaborators': True,
        'repository_languages': True,
        'repository_stargazers': False,
        'repository_contributors': True,
        'repository_subscribers': False,
        'repository_commits': False,
        'user_organizations': True,
        'user_repositories': True,
        'user_followers': False,
        'user_following': False,
        'user_starred': False,
        'user_subscriptions': False,
        'organization_repositories': True,
        'organization_members': True,
    }

    def __init__(self, policy=None, *args, **kwargs):
        super(GitHubSpider, self).__init__(*args, **kwargs)

        def _policy_parser(x):
            parts = x.split(':', 1)
            if len(parts) < 2:
                return None
            return (parts[0], bool(int(parts[1])))

        self.policy = self.default_policy.copy()
        policy = dict(self._parse_spider_option(policy, parser=_policy_parser))
        if policy is not None:
            self.policy.update(policy)

    @classmethod
    def from_crawler(cls, crawler, **spider_kwargs):
        spider = cls(**spider_kwargs)
        token = crawler.settings.get('GITHUB_API_TOKEN', None)
        if token:
            spider.http_user = token
            spider.http_pass = 'x-oauth-basic'
        return spider

    def _parse_spider_option(self, option, parser=None):
        if parser is None:
            parser = lambda x: x
        if isinstance(option, basestring):
            option = (parser(x) for x in option.split(','))
            return filter(None, option)
        else:
            return option or []

    def parse(self, response):
        raise NotImplementedError('response parsing is delegated to dedicated methods')

    def _request_from_endpoint(self, endpoint, params=None, meta=None, callback=None):
        if params is None:
            params = {}
        path = uritemplate.expand(self.endpoints.get(endpoint, ''), params)
        url = urlparse.urljoin(self.site, path)
        if callback is None:
            callback = getattr(self, 'parse_' + endpoint, None)
        request = Request(url=url, callback=callback)
        if endpoint in self.policy:
            visit = self.policy[endpoint]
            request.meta.update({'visit': visit})
        if meta is not None:
            request.meta.update(meta)
        return request

    def _repository_params(self, repo):
        return {'owner': repo['owner']['login'], 'repo': repo['name']}

    def _repository_requests(self, repo, save_summary=True):
        params = self._repository_params(repo)
        yield self._request_from_endpoint('repository', params=params)
        if save_summary:
            yield items.RepositorySummary.from_dict(repo)
        for x in self._repository_resources_requests(repo):
            yield x

    def _repository_resources_requests(self, repo):
        assert 'id' in repo
        params = self._repository_params(repo)
        meta = {'repo': repo}
        yield self._request_from_endpoint('repository_forks', params=params, meta=meta)
        yield self._request_from_endpoint('repository_collaborators', params=params, meta=meta)
        yield self._request_from_endpoint('repository_contributors', params=params, meta=meta)
        yield self._request_from_endpoint('repository_languages', params=params, meta=meta)
        yield self._request_from_endpoint('repository_stargazers', params=params, meta=meta)
        yield self._request_from_endpoint('repository_subscribers', params=params, meta=meta)
        yield self._request_from_endpoint('repository_commits', params=params, meta=meta)

    def _user_params(self, user):
        return {'user': user['login']}

    def _user_requests(self, user, save_summary=True):
        params = self._user_params(user)
        yield self._request_from_endpoint('user', params=params)
        if save_summary:
            yield items.AccountSummary.from_dict(user)
        for x in self._user_resources_requests(user):
            yield x

    def _user_resources_requests(self, user):
        assert 'id' in user
        params = self._user_params(user)
        meta = {'user': user}
        yield self._request_from_endpoint('user_followers', params=params, meta=meta)
        yield self._request_from_endpoint('user_following', params=params, meta=meta)
        yield self._request_from_endpoint('user_repositories', params=params, meta=meta)
        yield self._request_from_endpoint('user_starred', params=params, meta=meta)
        yield self._request_from_endpoint('user_subscriptions', params=params, meta=meta)
        yield self._request_from_endpoint('user_organizations', params=params, meta=meta)

    def _organization_params(self, org):
        return {'org': org['login']}

    def _organization_requests(self, org, save_summary=True):
        params = self._organization_params(org)
        yield self._request_from_endpoint('organization', params=params)
        if save_summary:
            yield items.AccountSummary.from_dict(org)
        for x in self._organization_resources_requests(org):
            yield x

    def _organization_resources_requests(self, org):
        assert 'id' in org
        params = self._organization_params(org)
        meta = {'org': org}
        yield self._request_from_endpoint('organization_members', params=params, meta=meta)
        yield self._request_from_endpoint('organization_repositories', params=params, meta=meta)

    def _account_requests(self, account):
        if account.get('type') == 'Organization':
            requests = self._organization_requests(account)
        else:
            requests = self._user_requests(account)
        for x in requests:
            yield x

    @response_parser()
    def parse_repository(self, repo, meta):
        yield items.Repository.from_dict(repo)
        for x in self._account_requests(repo['owner']):
            yield x
        if 'parent' in repo:
            for x in self._repository_requests(repo['parent']):
                yield x
        if 'source' in repo:
            for x in self._repository_requests(repo['source']):
                yield x
        if meta.get('start'):
            for x in self._repository_resources_requests(repo):
                yield x

    @response_parser()
    def parse_user(self, user, meta):
        yield items.Account.from_dict(user)
        if meta.get('start'):
            for x in self._user_resources_requests(user):
                yield x

    @response_parser()
    def parse_organization(self, org, meta):
        yield items.Account.from_dict(org)
        if meta.get('start'):
            for x in self._organization_resources_requests(org):
                yield x

    @response_parser(paginated=True)
    def parse_repositories(self, repos, meta):
        for repo in repos:
            for x in self._repository_requests(repo):
                yield x

    @response_parser(paginated=True)
    def parse_users(self, users, meta):
        for user in users:
            for x in self._user_requests(user):
                yield x

    @response_parser(paginated=True)
    def parse_organizations(self, orgs, meta):
        for org in orgs:
            for x in self._organization_requests(org):
                yield x

    @response_parser(paginated=True)
    def parse_repository_collaborators(self, users, meta):
        repo = meta['repo']
        for user in users:
            yield items.Collaborator(repo=repo, user=user)
            for x in self._account_requests(user):
                yield x

    @response_parser(paginated=True)
    def parse_repository_contributors(self, users, meta):
        repo = meta['repo']
        for user in users:
            yield items.Contributor(repo=repo, user=user, contributions=user.get('contributions'))
            for x in self._account_requests(user):
                yield x

    @response_parser()
    def parse_repository_languages(self, languages, meta):
        repo = meta['repo']
        yield items.Languages(repo=repo, languages=languages)

    @response_parser(paginated=True)
    def parse_repository_stargazers(self, users, meta):
        repo = meta['repo']
        for user in users:
            yield items.Stargazer(repo=repo, user=user)
            for x in self._account_requests(user):
                yield x

    @response_parser(paginated=True)
    def parse_repository_subscribers(self, users, meta):
        repo = meta['repo']
        for user in users:
            yield items.Subscriber(repo=repo, user=user)
            for x in self._account_requests(user):
                yield x

    parse_repository_forks = parse_repositories

    @response_parser(paginated=True)
    def parse_repository_commits(self, commits, meta):
        repo = meta['repo']
        for commit in commits:
            commit['repo'] = repo
            yield items.Commit.from_dict(commit)
            if commit.get('author') is not None:
                for x in self._account_requests(commit['author']):
                    yield x
            if commit.get('committer') is not None:
                for x in self._account_requests(commit['committer']):
                    yield x

    @response_parser(paginated=True)
    def parse_user_followers(self, users, meta):
        followee = meta['user']
        for user in users:
            yield items.Follow(follower=user, followee=followee)
            for x in self._account_requests(user):
                yield x

    parse_user_following = parse_users
    parse_user_organizations = parse_organizations
    parse_user_repositories = parse_repositories
    parse_user_starred = parse_repositories
    parse_user_subscriptions = parse_repositories

    @response_parser(paginated=True)
    def parse_organization_members(self, users, meta):
        org = meta['org']
        for user in users:
            yield items.Membership(org=org, user=user)
            for x in self._account_requests(user):
                yield x

    parse_organization_repositories = parse_repositories

    def next_page(self, response):
        links = parse_link_header(response)
        if 'next' in links:
            r = response.request.replace(url=links['next'])
            r.meta['dont_increase_depth'] = True
            r.meta['has_previous_page'] = True
            return r
