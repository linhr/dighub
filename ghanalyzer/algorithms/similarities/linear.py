from sklearn.metrics.pairwise import linear_kernel


class LinearSimilarity(object):
    def __init__(self, features):
        self.features = features
        self.size, _ = self.features.shape
        self.matrix = linear_kernel(self.features)

    def __getitem__(self, pair):
        return self.matrix[pair]
        