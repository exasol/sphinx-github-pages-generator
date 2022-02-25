from exasol_sphinx_github_pages_generator.parser import Parser
from exasol_sphinx_github_pages_generator.deployer import GithubPagesDeployer
from tempfile import TemporaryDirectory
from subprocess import run
import os


def deploy_github_pages(argv):
    args = Parser(argv).args
    original_workdir = os.getcwd()
    source_dir = args.source_dir
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    print("Commandline parameter")
    print("source_dir= " + source_dir)
    print("module_path= " + str(args.module_path))
    print("TARGET_BRANCH=" + args.target_branch)
    print("PUSH_ORIGIN=" + args.push_origin)
    print("PUSH_ENABLED=" + args.push_enabled)
    print("SOURCE_BRANCH=" + args.source_branch + "\n")

    with TemporaryDirectory() as tempdir:
        deployer = GithubPagesDeployer(source_dir, args.module_path, args.target_branch,
                                       args.push_origin, args.push_enabled, args.source_branch,
                                       current_commit_id, tempdir)
        os.mkdir(deployer.build_dir)
        print("Using following Directories:")
        print("TMP=" + tempdir)
        print("TARGET WORKTREE=" + deployer.worktree_paths["target_worktree"])
        print("SOURCE WORKTREE=" + deployer.worktree_paths["source_worktree"])
        print("BUILD_DIR=" + deployer.build_dir)
        print("CURRENT_COMMIT_ID=" + deployer.current_commit_id + "\n")
        try:
            deployer.detect_or_verify_source_branch()
            deployer.checkout_target_branch_as_worktree()
            output_dir = deployer.build_and_copy_documentation()
            deployer.git_commit_and_push(output_dir)
        finally:
            deployer.clean_worktree(original_workdir)

