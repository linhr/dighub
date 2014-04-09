from ghcrawler.spiders.ghspider import GitHubSpider

class MultiTaskSpider(GitHubSpider):
    """spider to crawl multiple types of items on GitHub"""

    name = 'multitask-spider'
    start_urls = []

    def __init__(self, start_repos=None, start_users=None, start_orgs=None, policy=None,
            *args, **kwargs):
        super(MultiTaskSpider, self).__init__(policy=policy, *args, **kwargs)

        def _repo_parser(x):
            parts = x.split('/', 1)
            if len(parts) < 2:
                return None
            return {'owner': parts[0], 'repo': parts[1]}

        def _user_parser(x):
            return {'user': x}

        def _org_parser(x):
            return {'org': x}

        self.start_repos = self._parse_spider_option(start_repos, parser=_repo_parser)
        self.start_users = self._parse_spider_option(start_users, parser=_user_parser)
        self.start_orgs = self._parse_spider_option(start_orgs, parser=_org_parser)

    def start_requests(self):
        for params in self.start_repos:
            yield self._request_from_endpoint('repository', params=params, meta={'start': True})
        for params in self.start_users:
            yield self._request_from_endpoint('user', params=params, meta={'start': True})
        for params in self.start_orgs:
            yield self._request_from_endpoint('organization', params=params, meta={'start': True})
