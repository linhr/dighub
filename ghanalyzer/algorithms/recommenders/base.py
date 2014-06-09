

class Recommender(object):
    """recommender base class"""
    parameters = []

    def get_parameters(self):
        return {k: getattr(self, k, None) for k in self.parameters}

    def recommend(self, user, n=None):
        raise NotImplementedError()
