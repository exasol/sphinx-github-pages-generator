from exasol_sphinx_github_pages_generator.parser import Parser
from exasol_sphinx_github_pages_generator.deployer import GithubPagesDeployer
from tempfile import TemporaryDirectory
from subprocess import run
import os
import sys
from inspect import cleandoc


def deploy_github_pages(argv):
    args = Parser(argv).args
    original_workdir = os.getcwd()
    source_dir = args.source_dir
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    print(cleandoc("Commandline parameter \n"
                   f"source_dir= {source_dir} \n"
                   f"module_path= {str(args.module_path)} \n"
                   f"TARGET_BRANCH= {args.target_branch} \n"
                   f"PUSH_ORIGIN= {args.push_origin} \n"
                   f"PUSH_ENABLED= {args.push_enabled} \n"
                   f"SOURCE_BRANCH= {args.source_branch} \n"))

    with TemporaryDirectory() as tempdir:
        deployer = GithubPagesDeployer(source_dir, args.source_branch, current_commit_id, args.module_path,
                                       args.target_branch, args.push_origin, args.push_enabled,
                                       tempdir)
        os.mkdir(deployer.build_dir)
        print(cleandoc(f"Using following Directories: \n"
                       f"TMP= {tempdir}\n"
                       f"TARGET WORKTREE= {deployer.worktree_paths['target_worktree']} \n"
                       f"SOURCE WORKTREE= {deployer.worktree_paths['source_worktree']} \n"
                       f"BUILD_DIR= {deployer.build_dir} \n"
                       f"CURRENT_COMMIT_ID= {deployer.current_commit_id} \n"))
        try:
            deployer.detect_or_verify_source_branch()
            deployer.checkout_target_branch_as_worktree()
            output_dir = deployer.build_and_copy_documentation()
            deployer.git_commit_and_push(output_dir)
        finally:
            deployer.clean_worktree(original_workdir)

