import random

from ghanalyzer.algorithms.graphs import *
from ghanalyzer.models import *

def separate_graph_data(graph, train_ratio=0.8, random_seed=None):
    r = random.Random()
    r.seed(random_seed)
    edges = graph.edges()
    random.shuffle(edges, random=r.random)
    p = int(len(edges) * train_ratio)
    train = graph.copy()
    train.remove_edges_from(edges[p:])
    test = graph.copy()
    test.remove_edges_from(edges[:p])
    return train, test


class RecommenderTest(object):
    def __init__(self, recommender, graph, train_ratio, n_recommendations,
            random_seed=None):
        self.recommender = recommender
        self.graph = graph
        self.train_ratio = train_ratio
        self.n_recommendations = n_recommendations
        self.train_graph, self.test_graph = separate_graph_data(self.graph,
            train_ratio=self.train_ratio, random_seed=random_seed)

    @property
    def report(self):
        if not hasattr(self, '_report'):
            self._report = {}
        return self._report

    def run(self, print_every=None):
        print 'Start training recommender...'
        self.recommender.train(self.train_graph)
        print 'Done.'

        users = get_nodes(self.test_graph, User)
        repos = get_nodes(self.test_graph, Repository)

        print 'User count: %d' % len(users)
        print 'Repository count: %d' % len(repos)
        
        recommendation = []
        for i, user in enumerate(users):
            if print_every is not None and i % print_every == 0:
                print 'Generating recommendation for user %d...' % i
            training = self.train_graph.neighbors(user)
            groundtruth = self.test_graph.neighbors(user)
            if not training or not groundtruth:
                continue
            recommended = self.recommender.recommend(user, self.n_recommendations)
            recommendation.append({
                'user': user,
                'training': training,
                'recommended': recommended,
                'groundtruth': groundtruth,
            })

        self.report.update({
            'users': users,
            'repos': repos,
            'user_count': len(users),
            'repo_count': len(repos),
            'recommendation': recommendation,
            'recommendation_length': self.n_recommendations,
        })

        print 'Finish generating recommendations for %d of %d user(s).' % (
            len(recommendation), len(users))
