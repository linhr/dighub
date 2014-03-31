import sys
import scrapy.commands.crawl
from scrapy import log

class Command(scrapy.commands.crawl.Command):
    """override default `crawl` command
    support writing log to stderr and files
    """

    def add_options(self, parser):
        super(Command, self).add_options(parser)
        parser.add_option('--logstderr', action='store_true',
            help='write log to stderr as well as log files')

    def run(self, args, opts):
        if opts.logstderr:
            level = log._get_log_level(self.settings['LOG_LEVEL'])
            observer = log.ScrapyFileLogObserver(sys.stderr, level=level)
            observer.start()
        super(Command, self).run(args, opts)
