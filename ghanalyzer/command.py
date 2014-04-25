

class AnalyzerCommand(object):
    """base class for analyzer command"""
    
    exitcode = 0

    def description(self):
        return ''

    def define_arguments(self, parser):
        return

    def run(self, args):
        raise NotImplementedError()
