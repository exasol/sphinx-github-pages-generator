import os
import sys
import click
import traceback
from subprocess import run
from inspect import cleandoc
from tempfile import TemporaryDirectory
from pathlib import Path
from exasol_sphinx_github_pages_generator.console import Console
from exasol_sphinx_github_pages_generator.deployer import GithubPagesDeployer


@click.command()
@click.option('--target-branch',
              type=str, default="github-pages/main", help="Branch to push to")
@click.option('--push-origin',
              type=str, default="origin", help="Where to push from")
@click.option('--push/--commit',
              default=False, help="Whether to commit or commit and push the documentation.")
@click.option('--source-branch',
              type=str, default="",
              help="The branch you want to generate documentation from. "
                   "If empty, defaults to current branch. Can also be "
                   "a GitHub tag")
@click.option('--source-origin',
              type=str, default="origin",
              help="Origin of source_branch. Set to 'tags' "
                   "if your source_branch is a tag")
@click.option('--source-dir',
              type=Path, default="doc/",
              help="Path to the directory inside the source_branch where the "
                   "index.rst and conf.py reside in.")
@click.option('--module-path',
              type=str, multiple=True,
              help="List of paths to all the modules the docu is "
                   "being generated for")
@click.option('--debug', is_flag=True, default=False,
              help="Prints full exception traceback")
# WARNING: These options can not be included in the autosummary for the documentation,
# if you change them you have to change the documentation manually
def main(
        target_branch: str, push_origin: str, push: bool,
        source_branch: str, source_origin: str, source_dir: Path,
        module_path: str, debug: bool):
    """
    Runs the GithubPagesDeployer inside a temp directory given the command-line
    options and arguments
    """
    global DEBUG
    DEBUG = debug

    module_path = list(module_path)
    original_workdir = os.getcwd()
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    Console.stderr(cleandoc(f"""
                   Commandline parameter
                   source_dir= {source_dir}
                   source_origin= {source_origin}
                   module_path= {str(module_path)}
                   TARGET_BRANCH= {target_branch}
                   PUSH_ORIGIN= {push_origin}
                   PUSH_ENABLED= {push} 
                   SOURCE_BRANCH= {source_branch}""") + "\n")
    with TemporaryDirectory() as tempdir:
        deployer = GithubPagesDeployer(
            source_dir, source_branch, source_origin,
            current_commit_id.stdout[:-1], module_path,
            target_branch, push_origin, push, Path(tempdir))
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


_FAILURE = 1
DEBUG = False


def _main():
    try:
        main()
    except Exception as ex:
        if DEBUG:
            Console.stderr(traceback.format_exc())
        else:
            Console.stderr(ex)
        sys.exit(_FAILURE)


if __name__ == "__main__":
    _main()
