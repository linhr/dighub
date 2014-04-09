from scrapy.item import Item, Field

__all__ = [
    'Account', 'Repository', 'Membership', 'Collaborator', 'Contributor', 'Languages',
    'Follow', 'Stargazer', 'Subscriber', 'AccountSummary', 'RepositorySummary',
    'Commit',
]

class GitHubItem(Item):
    @classmethod
    def from_dict(cls, d):
        item = cls()
        for k, v in d.iteritems():
            if k in item.fields:
                item[k] = v
        return item

    def __setitem__(self, key, value):
        if key in self.fields and 'converter' in self.fields[key]:
            value = self.fields[key]['converter'](value)
        super(GitHubItem, self).__setitem__(key, value)


class EntityMixin(object):
    @classmethod
    def keep_id(cls, d):
        if d is None:
            return None
        if 'id' in d:
            return cls(id=d['id'])
        return cls()


class Account(GitHubItem, EntityMixin):
    """user/organization account information"""
    login = Field()
    id = Field()
    type = Field()
    site_admin = Field()
    name = Field()
    company = Field()
    blog = Field()
    location = Field()
    email = Field()
    hireable = Field()
    public_repos = Field()
    public_gists = Field()
    followers = Field()
    following = Field()
    created_at = Field()
    updated_at = Field()


class AccountSummary(Account):
    """account summary"""


class Repository(GitHubItem, EntityMixin):
    """repository information"""
    id = Field()
    name = Field()
    full_name = Field()
    owner = Field(converter=Account.keep_id)
    organization = Field(converter=Account.keep_id)
    private = Field()
    description = Field()
    fork = Field()
    created_at = Field()
    updated_at = Field()
    pushed_at = Field()
    homepage = Field()
    size = Field()
    language = Field()
    has_issues = Field()
    has_downloads = Field()
    has_wiki = Field()
    stargazers_count = Field()
    subscribers_count = Field()
    forks_count = Field()
    network_count = Field()
    open_issues_count = Field()
    default_branch = Field()

Repository.parent = Field(converter=Repository.keep_id)
Repository.source = Field(converter=Repository.keep_id)


class RepositorySummary(Repository):
    """repository summary"""


class Membership(GitHubItem):
    """organization membership"""
    org = Field(converter=Account.keep_id)
    user = Field(converter=Account.keep_id)


class Follow(GitHubItem):
    """user follow relation"""
    follower = Field(converter=Account.keep_id)
    followee = Field(converter=Account.keep_id)


class Contributor(GitHubItem):
    """repository contributor"""
    repo = Field(converter=Repository.keep_id)
    user = Field(converter=Account.keep_id)
    contributions = Field()


class Collaborator(GitHubItem):
    """repository collaborator"""
    repo = Field(converter=Repository.keep_id)
    user = Field(converter=Account.keep_id)


class Languages(GitHubItem):
    """repository languages"""
    repo = Field(converter=Repository.keep_id)
    languages = Field()


class Stargazer(GitHubItem):
    """repository stargazer"""
    repo = Field(converter=Repository.keep_id)
    user = Field(converter=Account.keep_id)


class Subscriber(GitHubItem):
    """repository subscriber"""
    repo = Field(converter=Repository.keep_id)
    user = Field(converter=Account.keep_id)


def build_commit(commit):
    if 'tree' in commit:
        commit['tree'].pop('url', None)
    commit.pop('url', None)
    return commit

def build_commit_parents(parents):
    return [{'sha': x.get('sha')} for x in parents]

class Commit(GitHubItem):
    """repository commit"""
    repo = Field(converter=Repository.keep_id)
    sha = Field()
    commit = Field(converter=build_commit)
    author = Field(converter=Account.keep_id)
    committer = Field(converter=Account.keep_id)
    parents = Field(converter=build_commit_parents)
