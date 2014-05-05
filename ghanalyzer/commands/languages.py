from matplotlib import pyplot

from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.algorithms.graphs import filter_edges
from ghanalyzer.algorithms.features import LanguagePCA
from ghanalyzer.io import (
    load_repository_languages,
    load_language_co_occurrence,
)
from ghanalyzer.visualization.languages import (
    draw_co_occurrence_graph,
    draw_co_occurrence_matrix,
)


class Command(AnalyzerCommand):
    def description(self):
        return 'analyze repository languages'

    def define_arguments(self, parser):
        parser.add_argument('type', choices=['graph', 'matrix', 'pca'])
        parser.add_argument('-d', '--data-path', required=True)
        parser.add_argument('--language-count', type=int)
        parser.add_argument('--min-co-occurrence', type=int)

    def run(self, args):
        languages = load_repository_languages(args.data_path)
        graph = load_language_co_occurrence(args.data_path)
        if args.min_co_occurrence:
            graph = filter_edges(graph, lambda u, v, d: d['weight'] >= args.min_co_occurrence)

        context = {}

        if args.type == 'graph':
            draw_co_occurrence_graph(graph)
        elif args.type == 'matrix':
            draw_co_occurrence_matrix(graph, language_count=args.language_count)
        elif args.type == 'pca':
            analyzer = LanguagePCA(languages)
            context.update({'analyzer': analyzer})
        
        if args.type in ['graph', 'matrix']:
            pyplot.show(block=not args.interactive)

        context.update({'languages': languages, 'graph': graph})
        return context
