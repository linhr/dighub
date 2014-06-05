
from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.io import read_json_graph, write_json_report, write_pickle_report
from ghanalyzer.algorithms.recommenders import (
    RandomRecommender,
    UserCFRecommender,
    ItemCFRecommender,
    LanguageBasedRecommender,
    DescriptionBasedRecommender,
    QuasiUserCFRecommender,
    QuasiItemCFRecommender,
    FollowerBasedRecommender,
    FolloweeBasedRecommender,
    NMFRecommender,
    PersonalRankRecommender,
    SupervisedRWRecommender,
)
from ghanalyzer.evaluation.experiments import RecommenderTest
from ghanalyzer.evaluation.metrics import get_frequencies, precision_recall_curve


class Command(AnalyzerCommand):
    def description(self):
        return 'evaluate recommendation algorithms'

    def define_arguments(self, parser):
        parser.add_argument('recommender',
            choices=['Random', 'UserCF', 'ItemCF', 'LanguageBased', 'DescriptionBased',
                'QuasiUserCF', 'QuasiItemCF', 'FollowerBased', 'FolloweeBased',
                'NMF', 'RandomWalk', 'SupervisedRW'])
        parser.add_argument('-p', '--path', required=True)
        parser.add_argument('-f', '--format', choices=['json'], default='json')
        parser.add_argument('-o', '--output')
        parser.add_argument('--output-format', choices=['json', 'pickle'], default='json')

        group = parser.add_argument_group('experiment options')
        group.add_argument('--train-ratio', type=float, default=0.8)
        group.add_argument('--recommendation-count', type=int, default=1)
        group.add_argument('--random-seed', type=int, default=None)
        group.add_argument('--print-every', type=int, default=None)

        group = parser.add_argument_group('recommender parameters')
        group.add_argument('--neighbor-count', type=int, default=None)
        group.add_argument('--component-count', type=int, default=10)
        group.add_argument('--alpha', type=float, default=0.85)
        group.add_argument('--lambda-w', type=float, default=0.01)
        group.add_argument('--epsilon', type=float, default=0.01)
        group.add_argument('--loss-width', type=float, default=1.0)
        group.add_argument('--weight-key', nargs='+', default=())
        group.add_argument('--max-steps', type=int, default=10)
        group.add_argument('--data-path', default='')
        group.add_argument('--graph-path', nargs='+', default=())

    def run(self, args):
        recommender = self._create_recommender(args)
        graph = self._load_dataset(args)
        
        test = RecommenderTest(recommender, graph,
            train_ratio=args.train_ratio, n_recommendations=args.recommendation_count,
            random_seed=args.random_seed)
        test.run(print_every=args.print_every)
        
        test.report['name'] = args.recommender
        self._write_report(test.report, args)
        
        frequencies = get_frequencies(test.report)
        precision, recall = precision_recall_curve(frequencies)
        print 'Precision: %f' % precision
        print 'Recall: %f' % recall

        return {'graph': graph, 'recommender': recommender, 'test': test}

    def _create_recommender(self, args):
        if args.recommender == 'Random':
            recommender = RandomRecommender()
        elif args.recommender == 'UserCF':
            recommender = UserCFRecommender(n_neighbors=args.neighbor_count)
        elif args.recommender == 'ItemCF':
            recommender = ItemCFRecommender(n_neighbors=args.neighbor_count)
        elif args.recommender == 'LanguageBased':
            recommender = LanguageBasedRecommender(data_path=args.data_path)
        elif args.recommender == 'DescriptionBased':
            recommender = DescriptionBasedRecommender(data_path=args.data_path)
        elif args.recommender == 'QuasiUserCF':
            recommender = QuasiUserCFRecommender(data_path=args.data_path)
        elif args.recommender == 'QuasiItemCF':
            recommender = QuasiItemCFRecommender(data_path=args.data_path)
        elif args.recommender == 'FollowerBased':
            recommender = FollowerBasedRecommender(data_path=args.data_path)
        elif args.recommender == 'FolloweeBased':
            recommender = FolloweeBasedRecommender(data_path=args.data_path)
        elif args.recommender == 'NMF':
            recommender = NMFRecommender(n_components=args.component_count)
        elif args.recommender == 'RandomWalk':
            recommender = PersonalRankRecommender(alpha=args.alpha, max_steps=args.max_steps)
            recommender.add_other_graphs(*self._load_graphs(args))
        elif args.recommender == 'SupervisedRW':
            recommender = SupervisedRWRecommender(data_path=args.data_path,
                alpha=args.alpha, max_steps=args.max_steps, lambda_=args.lambda_w,
                epsilon=args.epsilon, loss_width=args.loss_width,
                weight_key=args.weight_key)
        return recommender

    def _load_dataset(self, args):
        if args.format == 'json':
            return read_json_graph(args.path)

    def _load_graphs(self, args):
        if not args.graph_path:
            return []
        if args.format == 'json':
            return [read_json_graph(path) for path in args.graph_path]

    def _write_report(self, report, args):
        if not args.output:
            return
        if args.output_format == 'json':
            write_json_report(args.output, report, indent=4)
        elif args.output_format == 'pickle':
            write_pickle_report(args.output, report)
