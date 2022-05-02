import pytest

from helper_test_functions import remove_branch, setup_workdir, \
    run_deployer_build_and_copy_documentation_without_gen_index
from exasol_sphinx_github_pages_generator.deployer import GithubPagesDeployer
from tempfile import TemporaryDirectory
from subprocess import run
import os
from pathlib import Path



@pytest.fixture()
def setup_test_env(tmp_path):
    os.chdir(tmp_path)
    user_name, user_access_token = setup_workdir()
    used_branches = []
    yield used_branches, user_name, user_access_token,

    print("clean")
    for branch in used_branches:
        remove_branch(branch)


@pytest.fixture
def setup_index_tests_integration(setup_test_env):
    branches_to_delete_in_cleanup, _, _ = setup_test_env
    original_workdir = os.getcwd()
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    branches_to_delete_in_cleanup += [target_branch]

    with TemporaryDirectory() as tempdir:
        deployer = GithubPagesDeployer("/doc/", source_branch, current_commit_id.stdout[:-1], ["../test_package"],
                                       target_branch, "origin", "push",
                                       tempdir)
        os.mkdir(deployer.build_dir)
        deployer.detect_or_verify_source_branch()
        deployer.checkout_target_branch_as_worktree()
        output_dir = run_deployer_build_and_copy_documentation_without_gen_index(deployer)
        yield target_branch, source_branch, deployer.target_branch_exists, Path(deployer.worktree_paths["target_worktree"])  # tests will run now

        deployer.clean_worktree(original_workdir)


@pytest.fixture
def setup_index_tests_target_branch(setup_test_env):
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "feature/6-test-branch-for-gen-index"
    yield target_branch, source_branch



