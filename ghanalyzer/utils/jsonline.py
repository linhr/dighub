import json


class JsonLineData(object):
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.data = open(self.path)
        return self

    def __exit__(self, type, value, traceback):
        self.data.close()

    def __iter__(self):
        self.data.seek(0)
        for line in self.data:
            yield json.loads(line)
