
def start_python_console(namespace=None, noipython=False, banner=''):
    """start Python console
    (borrowed from `scrapy.utils.console`)
    """
    if namespace is None:
        namespace = {}

    try:
        try: # use IPython if available
            if noipython:
                raise ImportError()

            try:
                from IPython.frontend.terminal.embed import InteractiveShellEmbed
                sh = InteractiveShellEmbed(banner1=banner)
            except ImportError:
                from IPython.Shell import IPShellEmbed
                sh = IPShellEmbed(banner=banner)

            sh(global_ns={}, local_ns=namespace)
        except ImportError:
            import code
            try: # readline module is only available on unix systems
                import readline
            except ImportError:
                pass
            else:
                import rlcompleter
                readline.parse_and_bind("tab:complete")
            code.interact(banner=banner, local=namespace)
    except SystemExit: # raised when using exit() in python code.interact
        pass
