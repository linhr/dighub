
from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.algorithms.features import DescriptionLDA, DescriptionNMF
from ghanalyzer.io import load_repository_descriptions

class Command(AnalyzerCommand):
    def description(self):
        return 'analyze repository descriptions'

    def define_arguments(self, parser):
        parser.add_argument('type', choices=['lda', 'nmf'])
        parser.add_argument('-d', '--data-path', required=True)
        parser.add_argument('--topic-count', type=int, default=10)
        parser.add_argument('--vocabulary-size', type=int, default=None)
        parser.add_argument('--show-fork', action='store_true')

    def run(self, args):
        descriptions = load_repository_descriptions(args.data_path,
            show_fork=bool(args.show_fork))

        if args.type == 'lda':
            analyzer = DescriptionLDA(descriptions, n_topics=args.topic_count,
                vocabulary_size=args.vocabulary_size)
        elif args.type == 'nmf':
            analyzer = DescriptionNMF(descriptions, n_topics=args.topic_count,
                vocabulary_size=args.vocabulary_size)

        return {'descriptions': descriptions, 'analyzer': analyzer}
