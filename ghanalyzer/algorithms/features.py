import numpy
from sklearn.feature_extraction import DictVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize


class LanguagePCA(object):
    def __init__(self, dataset, n_components='mle'):
        self.dataset = dataset
        self.n_components = n_components
        self.vectorizer = DictVectorizer()
        self.samples = dataset.keys()
        self.features = self.vectorizer.fit_transform(dataset.values())
        self.features = normalize(self.features, norm='l1')
        self.transformer = PCA(n_components=n_components)
        self.transformer.fit(self.features.toarray())

    def get_components(self):
        names = self.vectorizer.get_feature_names()
        names = numpy.array(names, dtype=object)
        indices = numpy.argsort(-numpy.absolute(self.transformer.components_))
        return names[indices]
