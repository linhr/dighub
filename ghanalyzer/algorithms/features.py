import numpy
from nltk.corpus import stopwords
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.decomposition import PCA, NMF
from sklearn.preprocessing import normalize
from gensim.models.ldamodel import LdaModel
from gensim.matutils import Sparse2Corpus


class FeatureExtractor(object):
    def __init__(self, dataset):
        self.dataset = dataset
        self.samples = dataset.keys()
        self.sample_indices = {x: i for i, x in enumerate(self.samples)}
        

class LanguageVector(FeatureExtractor):
    def __init__(self, dataset):
        super(LanguageVector, self).__init__(dataset)
        self.vectorizer = DictVectorizer()
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


class DescriptionVector(FeatureExtractor):
    def __init__(self, dataset, vocabulary_size=None, tfidf=True):
        super(DescriptionVector, self).__init__(dataset)
        self.vectorizer = CountVectorizer(max_features=vocabulary_size,
            stop_words=stopwords.words('english'))
        self.features = self.vectorizer.fit_transform(dataset.values())
        if tfidf:
            self.features = TfidfTransformer().fit_transform(self.features)
        

class DescriptionLDA(DescriptionVector):
    def __init__(self, dataset, n_topics, vocabulary_size=None):
        super(DescriptionLDA, self).__init__(dataset, vocabulary_size, tfidf=False)
        self.n_topics = n_topics
        
        id2word = {i: w for w, i in self.vectorizer.vocabulary_.iteritems()}
        corpus = Sparse2Corpus(self.features, documents_columns=False)
        self.transformer = LdaModel(corpus=corpus, id2word=id2word, num_topics=n_topics)


class DescriptionNMF(DescriptionVector):
    def __init__(self, dataset, n_topics=None, vocabulary_size=None):
        super(DescriptionNMF, self).__init__(dataset, vocabulary_size)
        self.n_topics = n_topics
        
        self.transformer = NMF(n_components=n_topics)
        self.transformer.fit(self.features)
        
    def get_components(self):
        words = self.vectorizer.get_feature_names()
        words = numpy.array(words, dtype=object)
        indices = numpy.argsort(-numpy.absolute(self.transformer.components_))
        return words[indices]
