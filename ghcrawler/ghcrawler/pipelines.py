import os.path
import shelve
from scrapy.contrib.exporter import JsonLinesItemExporter
from scrapy.exceptions import DropItem

import items

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
        for name in items.__all__:
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
        name = type(item).__name__
        if name in self.exporters:
            self.exporters[name].export_item(item)
        return item


class GitHubItemFilterPipeline(object):
    def __init__(self, path):
        self.path = path
    
    @classmethod
    def from_crawler(cls, crawler):
        path = crawler.settings.get('FILTER_STORAGE_PATH')
        return cls(path)

    def open_spider(self, spider):
        filename = os.path.join(self.path, 'items.db')
        self.db = shelve.open(filename, 'c')
    
    def close_spider(self, spider):
        self.db.close()
    
    def process_item(self, item, spider):
        if not isinstance(item, (items.AccountSummary, items.RepositorySummary)):
            return item
        key = '%s/%s' % (type(item).__name__, item.get('id'))
        stored = self.db.get(key, False)
        if stored:
            raise DropItem()
        self.db[key] = True # mark crawled account or repository summary
        return item
