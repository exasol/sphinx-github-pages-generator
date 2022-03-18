import argparse


class Parser:
    """
    Parses the given command-line options and arguments.
    """
    def __init__(self, argv):
        parser = argparse.ArgumentParser(description='Process some integers.')
        parser.add_argument('--target_branch', type=str,
                            default="github-pages/main",
                            help='branch to push to')
        parser.add_argument('--push_origin', type=str,
                            default="origin",
                            help='where to push from')
        parser.add_argument('--push_enabled',  type=str,
                            default="push",
                            help='whether to push or not, set to "commit" or "push"')
        parser.add_argument('--source_branch', type=str,
                            default="",
                            help='The branch you want to generate documentation from. '
                                 'If empty, defaults to current branch')
        parser.add_argument('--source_dir', type=str, default="/doc/",
                            help="Path to the directory inside the source_branch where the index.rst "
                                 "and conf.py reside in.")
        parser.add_argument('--module_path', nargs='*', default="",
                            help="The paths to all the modules the docu is being generated for")
        self.args = parser.parse_args(argv)
