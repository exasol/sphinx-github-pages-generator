import os
import click
import traceback
from subprocess import run
from inspect import cleandoc
from tempfile import TemporaryDirectory
from exasol_sphinx_github_pages_generator.console import Console
from exasol_sphinx_github_pages_generator.deployer import GithubPagesDeployer


@click.command()
@click.option('--target_branch',
              type=str, default="github-pages/main", help="branch to push to")
@click.option('--push_origin',
              type=str, default="origin", help="where to push from")
@click.option('--push_enabled',
              type=str, default="push", help="whether to push or commit")
@click.option('--source_branch',
              type=str, default="",
              help="The branch you want to generate documentation from. "
                   "If empty, defaults to current branch. Can also be "
                   "a GitHub tag")
@click.option('--source_origin',
              type=str, default="origin",
              help="origin of source_branch. Set to 'tags' "
                   "if your source_branch is a tag")
@click.option('--source_dir',
              type=str, default="/doc/",
              help="Path to the directory inside the source_branch where the "
                   "index.rst and conf.py reside in.")
@click.option('--module_path',
              type=str, multiple=True,
              help="The paths to all the modules the docu is "
                   "being generated for")
@click.option('--debug', is_flag=True, default=False,
              help="Prints full exception traceback")
def main(
        target_branch: str, push_origin: str, push_enabled: str,
        source_branch: str, source_origin: str, source_dir: str,
        module_path: str, debug: bool):
    """
    Runs the GithubPagesDeployer inside a temp directory given the command-line
    options and arguments
    """
    global DEBUG
    DEBUG = debug

    module_path = list(module_path)
    original_workdir = os.getcwd()
    source_dir = source_dir
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    Console.stderr(cleandoc(f"""
                   Commandline parameter
                   source_dir= {source_dir}
                   source_origin= {source_origin}
                   module_path= {str(module_path)}
                   TARGET_BRANCH= {target_branch}
                   PUSH_ORIGIN= {push_origin}
                   PUSH_ENABLED= {push_enabled} 
                   SOURCE_BRANCH= {source_branch}""") + "\n")
    with TemporaryDirectory() as tempdir:
        deployer = GithubPagesDeployer(
            source_dir, source_branch, source_origin,
            current_commit_id.stdout[:-1], module_path,
            target_branch, push_origin, push_enabled, tempdir)
        os.mkdir(deployer.build_dir)
        Console.stderr(cleandoc(f"""
                       Using following Directories:
                       TMP= {tempdir}
                       TARGET WORKTREE= {deployer.worktree_paths['target_worktree']}
                       SOURCE WORKTREE= {deployer.worktree_paths['source_worktree']}
                       BUILD_DIR= {deployer.build_dir}
                       CURRENT_COMMIT_ID= {deployer.current_commit_id}""") + "\n")
        try:
            deployer.detect_or_verify_source_branch()
            deployer.checkout_target_branch_as_worktree()
            output_dir = deployer.build_and_copy_documentation()
            deployer.git_commit_and_push(output_dir)
        finally:
            deployer.clean_worktree(original_workdir)


_SUCCESS = 0
_FAILURE = 1
DEBUG = False


def _main():
    try:
        main()
        return _SUCCESS
    except Exception as ex:
        if DEBUG:
            Console.stderr(traceback.format_exc())
        else:
            Console.stderr(ex)
        return _FAILURE


if __name__ == "__main__":
    _main()
