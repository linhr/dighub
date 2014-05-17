import numpy
from nltk.corpus import stopwords
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.decomposition import PCA, NMF
from sklearn.preprocessing import normalize
from gensim.models.ldamodel import LdaModel
from gensim.matutils import Sparse2Corpus


class LanguageVector(object):
    def __init__(self, dataset):
        self.dataset = dataset
        self.vectorizer = DictVectorizer()
        self.samples = dataset.keys()
        self.features = self.vectorizer.fit_transform(dataset.values())
        self.features = normalize(self.features, norm='l1')


class LanguagePCA(LanguageVector):
    def __init__(self, dataset, n_components='mle'):
        super(LanguagePCA, self).__init__(dataset)
        self.n_components = n_components
        self.transformer = PCA(n_components=n_components)
        self.transformer.fit(self.features.toarray())

    def get_components(self):
        names = self.vectorizer.get_feature_names()
        names = numpy.array(names, dtype=object)
        indices = numpy.argsort(-numpy.absolute(self.transformer.components_))
        return names[indices]


class DescriptionLDA(object):
    def __init__(self, dataset, n_topics):
        self.dataset = dataset
        self.n_topics = n_topics
        self.vectorizer = CountVectorizer(stop_words=stopwords.words('english'))
        self.samples = dataset.keys()
        self.features = self.vectorizer.fit_transform(dataset.values())
        
        id2word = {i: w for w, i in self.vectorizer.vocabulary_.iteritems()}
        corpus = Sparse2Corpus(self.features, documents_columns=False)
        self.transformer = LdaModel(corpus=corpus, id2word=id2word, num_topics=n_topics)


class DescriptionNMF(object):
    def __init__(self, dataset, n_topics=None, vocabulary_size=None):
        self.dataset = dataset
        self.n_topics = n_topics
        self.vectorizer = CountVectorizer(max_features=vocabulary_size,
            stop_words=stopwords.words('english'))
        self.samples = dataset.keys()
        self.features = self.vectorizer.fit_transform(dataset.values())
        self.features = TfidfTransformer().fit_transform(self.features)
        self.transformer = NMF(n_components=n_topics)
        self.transformer.fit(self.features)
        
    def get_components(self):
        words = self.vectorizer.get_feature_names()
        words = numpy.array(words, dtype=object)
        indices = numpy.argsort(-numpy.absolute(self.transformer.components_))
        return words[indices]
