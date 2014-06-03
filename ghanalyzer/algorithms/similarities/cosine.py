from sklearn.metrics.pairwise import cosine_similarity


class CosineSimilarity(object):
    def __init__(self, features):
        self.features = features
        self.size, _ = self.features.shape
        self.matrix = cosine_similarity(self.features)

    def __getitem__(self, pair):
        return self.matrix[pair]
        