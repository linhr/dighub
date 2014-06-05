import numpy
from nltk.corpus import stopwords
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.decomposition import PCA, NMF
from sklearn.preprocessing import normalize
from gensim.models.ldamodel import LdaModel
from gensim.matutils import Sparse2Corpus

from ghanalyzer.io import (
    load_graph,
    load_repository_languages,
    load_repository_descriptions,
)


class FeatureExtractor(object):
    def __init__(self, dataset):
        self.dataset = dataset
        self.samples = dataset.keys()
        self.sample_indices = {x: i for i, x in enumerate(self.samples)}
        

class LanguageVector(FeatureExtractor):
    def __init__(self, dataset, normalize=True):
        super(LanguageVector, self).__init__(dataset)
        self.vectorizer = DictVectorizer()
        self.features = self.vectorizer.fit_transform(dataset.values())
        if normalize:
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


def load_language_features(data_path, repos):
    languages = load_repository_languages(data_path)
    languages[None] = {}  # add dummy data item
    languages = LanguageVector(languages, normalize=False)
    default_index = languages.sample_indices[None]
    indices = [languages.sample_indices.get(r.id, default_index) for r in repos]
    return languages.features[indices, :]


def load_description_features(data_path, repos):
    descriptions = load_repository_descriptions(data_path)
    descriptions[None] = ''  # add dummy data item
    descriptions = DescriptionVector(descriptions, tfidf=True)
    default_index = descriptions.sample_indices[None]
    indices = [descriptions.sample_indices.get(r.id, default_index) for r in repos]
    return descriptions.features[indices, :]


def load_follow_features(data_path, users):
    graph = load_graph(data_path, 'follow')
    graph.add_nodes_from(users)
    vectorizer = DictVectorizer(sparse=True)
    followers = [dict.fromkeys(graph.predecessors(u), 1) for u in users]
    followers = vectorizer.fit_transform(followers)
    followees = [dict.fromkeys(graph.successors(u), 1) for u in users]
    followees = vectorizer.fit_transform(followees)
    return followers, followees
