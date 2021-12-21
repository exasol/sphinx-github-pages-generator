import argparse


class Parser:
    def __init__(self, argv):
        parser = argparse.ArgumentParser(description='Process some integers.')
        parser.add_argument('--target_branch', type=str,
                            default="main_doc_test",
                            help='branch to push to')
        parser.add_argument('--push_origin', type=str,
                            default="origin",
                            help='where to push from')
        parser.add_argument('--push_enabled',  type=str,
                            default="push",
                            help='weather to push or not, set to "commit" or "push"')
        parser.add_argument('--source_branch', type=str,
                            default="main",
                            help='current branch')
        parser.add_argument('--source_dir', type=str, default="./doc/", help="The doc directory your documentation files and conf.py reside in")
        parser.add_argument('--module_path', type=str, default="../module_name", help="The path to the module the docu is beeing generated for")
        self.args = parser.parse_args(argv)
