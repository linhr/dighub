
__all__ = [
    'Account', 'Repository', 'User', 'Organization', 'Language',
]

class Entity(object):
    """base class for hashable entities
    (can be used as NetworkX nodes)
    """

    def __init__(self, id):
        self._id = id

    @property
    def id(self):
        return self._id

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._id == other._id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            raise NotImplementedError()
        return cmp(self._id, other._id)

    def __hash__(self):
        return hash(self._id)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, repr(self._id))


class Account(Entity):
    """account"""


class Repository(Entity):
    """repository"""


class User(Account):
    """user"""


class Organization(Account):
    """organization"""


class Language(Entity):
    """repository language"""
