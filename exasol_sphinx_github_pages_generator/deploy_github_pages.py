from exasol_sphinx_github_pages_generator.cli import Parser, Console
from exasol_sphinx_github_pages_generator.deployer import GithubPagesDeployer
from tempfile import TemporaryDirectory
from subprocess import run
import os
import sys
from inspect import cleandoc


def deploy_github_pages(argv):
    """
    Runs the GithubPagesDeployer inside a temp directory given the command-line options and arguments inside argv.

    :param argv: Command-line options and arguments, better described in the parser.
    """
    args = Parser(argv).args
    original_workdir = os.getcwd()
    source_dir = args.source_dir
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    Console.stderr(
        cleandoc(
            f"""
             Commandline parameter
             source_dir= {source_dir}
             source_origin= {args.source_origin}
             module_path= {str(args.module_path)}
             TARGET_BRANCH= {args.target_branch}
             PUSH_ORIGIN= {args.push_origin}
             PUSH_ENABLED= {args.push_enabled} 
             SOURCE_BRANCH= {args.source_branch}"""
        ) + "\n"
    )

    with TemporaryDirectory() as tempdir:
        deployer = GithubPagesDeployer(source_dir, args.source_branch, args.source_origin,
                                       current_commit_id.stdout[:-1], args.module_path,
                                       args.target_branch, args.push_origin, args.push_enabled,
                                       tempdir)
        os.mkdir(deployer.build_dir)
        Console.stderr(
            cleandoc(
                f"""
                Using following Directories:
                TMP= {tempdir}
                TARGET WORKTREE= {deployer.worktree_paths['target_worktree']}
                SOURCE WORKTREE= {deployer.worktree_paths['source_worktree']}
                BUILD_DIR= {deployer.build_dir}
                CURRENT_COMMIT_ID= {deployer.current_commit_id}
                """
            ) + "\n"
        )
        try:
            deployer.detect_or_verify_source_branch()
            deployer.checkout_target_branch_as_worktree()
            output_dir = deployer.build_and_copy_documentation()
            deployer.git_commit_and_push(output_dir)
        finally:
            deployer.clean_worktree(original_workdir)


_SUCCESS = 0
_FAILURE = 1


def main():
    try:
        deploy_github_pages(sys.argv[1:])
        return _SUCCESS
    except Exception as ex:
        Console.stderr(ex)
        return _FAILURE


if __name__ == "__main__":
    sys.exit(main())
