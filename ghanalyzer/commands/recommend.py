
from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.io import read_json_graph, write_json_report, write_pickle_report
from ghanalyzer.algorithms.recommenders import RandomRecommender
from ghanalyzer.evaluation.experiments import RecommenderTest
from ghanalyzer.evaluation.metrics import iter_precision, iter_recall, average_metric


class Command(AnalyzerCommand):
    def description(self):
        return 'evaluate recommendation algorithms'

    def define_arguments(self, parser):
        parser.add_argument('recommender', choices=['Random'])
        parser.add_argument('-p', '--path', required=True)
        parser.add_argument('-f', '--format', choices=['json'], default='json')
        parser.add_argument('-o', '--output')
        parser.add_argument('--output-format', choices=['json', 'pickle'], default='json')

        group = parser.add_argument_group('experiment options')
        group.add_argument('--train-ratio', type=float, default=0.8)
        group.add_argument('--recommendation-count', type=int, default=1)
        group.add_argument('--random-seed', type=int, default=None)
        group.add_argument('--print-every', type=int, default=None)

    def run(self, args):
        recommender = self._create_recommender(args)
        graph = self._load_dataset(args)
        
        test = RecommenderTest(recommender, graph,
            train_ratio=args.train_ratio, n_recommendations=args.recommendation_count,
            random_seed=args.random_seed)
        test.run(print_every=args.print_every)
        
        test.report['name'] = args.recommender
        self._write_report(test.report, args)
        
        print 'Precision: %f' % average_metric(iter_precision(test.report))
        print 'Recall: %f' % average_metric(iter_recall(test.report))

        return {'graph': graph, 'recommender': recommender, 'test': test}

    def _create_recommender(self, args):
        if args.recommender == 'Random':
            return RandomRecommender()

    def _load_dataset(self, args):
        if args.format == 'json':
            return read_json_graph(args.path)

    def _write_report(self, report, args):
        if not args.output:
            return
        if args.output_format == 'json':
            write_json_report(args.output, report, indent=4)
        elif args.output_format == 'pickle':
            write_pickle_report(args.output, report)
