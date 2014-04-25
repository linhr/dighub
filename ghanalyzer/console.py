"""
GitHub Analyzer console
(inspired by `scrapy.cmdline`)
"""

import sys
import argparse
from importlib import import_module
from pkgutil import iter_modules
import inspect
import StringIO

from ghanalyzer.command import AnalyzerCommand
from ghanalyzer.utils.console import start_python_console

def _load_commands():
    modules = {}
    prefix = 'ghanalyzer.commands'
    package = import_module(prefix)
    for _, name, _ in iter_modules(package.__path__):
        path = prefix + '.' + name
        module = import_module(path)
        for obj in vars(module).itervalues():
            if inspect.isclass(obj) and issubclass(obj, AnalyzerCommand) \
                    and obj.__module__ == module.__name__:
                modules[name] = obj()
    return modules

def _get_commands_description(commands):
    output = StringIO.StringIO()
    for name, command in commands.iteritems():
        print >> output, '%-16s %s' % (name, command.description())
    content = output.getvalue()
    output.close()
    return content

def _show_locals(context):
    print
    print 'Available local variables:'
    for k, v in context.iteritems():
        print '    %s <%s>' % (k, type(v).__name__)
    
def execute():
    commands = _load_commands()

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--interactive',
        help='open Python console after running commands',
        action='store_true')
    parser.add_argument('--noipython',
        help='do not use IPython for interactive console',
        action='store_true')
    subparsers = parser.add_subparsers(
        title='available commands',
        description=_get_commands_description(commands),
        dest='command',
        metavar='COMMAND',
        help='analyzer command to run')
    for name, command in commands.iteritems():
        command_parser = subparsers.add_parser(name,
            description=command.description())
        command.define_arguments(command_parser)

    args = parser.parse_args()

    which = commands.get(args.command)
    if not which:
        print 'command not found'
        sys.exit(0)
    context = which.run(args)
    if args.interactive:
        if context is not None:
            _show_locals(context)
            start_python_console(namespace=context, noipython=bool(args.noipython))
        else:
            print 'interactive mode is not supported by the command'
    sys.exit(which.exitcode)


if __name__ == '__main__':
    execute()
