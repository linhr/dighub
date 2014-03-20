import os.path
from scrapy.contrib.exporter import JsonLinesItemExporter

from items import GITHUB_ITEM_TYPES

class GitHubItemStoragePipeline(object):
    def __init__(self, path):
        self.path = path

    @classmethod
    def from_crawler(cls, crawler):
        path = crawler.settings.get('GITHUB_ITEM_STORAGE_PATH')
        return cls(path)

    def open_spider(self, spider):
        self.files = {}
        self.exporters = {}
        for name in GITHUB_ITEM_TYPES:
            path = os.path.join(self.path, name + '.jsonl')
            output = open(path, 'a+')
            self.files[name] = output
            self.exporters[name] = JsonLinesItemExporter(output)
        for e in self.exporters.itervalues():
            e.start_exporting()

    def close_spider(self, spider):
        for e in self.exporters.itervalues():
            e.finish_exporting()
        for f in self.files.itervalues():
            f.close()

    def process_item(self, item, spider):
        name = type(item).__name__.lower()
        if name in self.exporters:
            self.exporters[name].export_item(item)
        return item
