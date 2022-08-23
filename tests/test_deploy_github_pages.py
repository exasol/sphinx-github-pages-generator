import re
import pytest
from subprocess import run
from tempfile import TemporaryDirectory
import os
from pathlib import Path
from click.testing import CliRunner
from fixtures import setup_test_env
import exasol_sphinx_github_pages_generator.cli as cli
from helper_test_functions import remove_branch, setup_workdir
import shutil
import traceback
from exasol_sphinx_github_pages_generator.deployer import GithubPagesDeployer


def test_remote_branch_creation(setup_test_env):
    branches_to_delete_in_cleanup, _, _ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)
    print(os.getcwd())

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)
    assert target_branch_exists.returncode == 0


def test_pushing_to_existing_docu_branch_same_source(setup_test_env):
    branches_to_delete_in_cleanup, user_name, user_access_token = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    temp_test_branch ="temp-test-branch"
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch, temp_test_branch]
    run(["git", "checkout", "-B", temp_test_branch], check=True)
    run(["git", "push", "-u", "origin", temp_test_branch], check=True)
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    current_commit_id = run(["git", "ls-remote",
                             f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
                             target_branch], capture_output=True, check=True)
    commit_id_old = current_commit_id.stdout

    # make a change in the docu
    with open("./index.rst", "a") as file:
        file.write("\n\nThis text is a change.")
    run(["git", "add", "*"], check=True)
    run(["git", "commit", "-m", "test-commit"], check=True)
    run(["git", "push"], check=True)
    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)
    current_commit_id = run(["git", "ls-remote",
                             f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
                             target_branch], capture_output=True, check=True)
    commit_id_new = current_commit_id.stdout

    # the docu files where updated, so a new commit should be pushed to the remote
    assert (not commit_id_new == "" 
            and not commit_id_old == ""
            and not commit_id_old == commit_id_new)


def test_pushing_to_existing_docu_branch_different_source(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch_one = "main"
    run(["git", "checkout", source_branch_one], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch_one,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        source_branch_two = "branch-with-different-docu-source-dir"
        run(["git", "checkout", source_branch_two], check=True)

        args_list = [
            "--target-branch", target_branch,
            "--source-branch", source_branch_two,
            "--source-dir", "documentation/",
            "--module-path", "../test_package",
            "--module-path", "../another_test_package",
            "--push"]
        result = CliRunner().invoke(cli.main, args_list)
        traceback.print_exception(*result.exc_info)

        target_branch_exists = run(
            ["git", "show-branch", f"remotes/origin/{target_branch}"],
            capture_output=True, text=True)
        doc_dir_source_one_exists = run(
            ["git", "ls-tree", "-d",
             f"origin/{target_branch}:{source_branch_one}"],
            capture_output=True, text=True, check=True)
        doc_dir_source_two_exists = run(
            ["git", "ls-tree", "-d",
             f"origin/{target_branch}:{source_branch_two}"],
            capture_output=True, text=True, check=True)

        assert (target_branch_exists.returncode == 0
                and doc_dir_source_one_exists.returncode == 0
                and doc_dir_source_two_exists.returncode == 0)


def test_no_new_push_and_commit_if_no_changes(setup_test_env):
    branches_to_delete_in_cleanup, user_name, user_access_token = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    current_commit_id = run(
        ["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
         target_branch], capture_output=True, check=True)
    commit_id_old = current_commit_id.stdout

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    current_commit_id = run(
        ["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
         target_branch], capture_output=True, check=True)
    commit_id_new = current_commit_id.stdout

    # the docu files where not updated, so no new commit should be pushed to the remote
    assert (commit_id_old != 0 
            and commit_id_old == commit_id_new
            and not commit_id_new == "")


def test_verify_existence_of_generated_files_on_remote_after_push(setup_test_env):
    # generate files locally in test, and with generator, look at diff between local files and remote files?
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)
    module_path = ["../test_package", "../another_test_package"]

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", module_path[0],
        "--module-path", module_path[1],
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        source_branch = "main"
        run(["git", "checkout", source_branch], check=True)
        os.chdir("./doc/")
        cwd = os.getcwd()
        build_dir = tempdir2 + "/Spinxbuild"
        intermediate_dir = tempdir2 + "/intermediate"
        for module in module_path:
            run(["sphinx-apidoc", "-T", "-e", "-o", "api", module], check=True)
        run(["sphinx-build", "-b", "html", "-d", intermediate_dir, "-W", cwd, build_dir], check=True)
        run(["git", "checkout", target_branch], check=True)
        os.chdir("..")
        cwd = os.getcwd()
        # in this special test_case, github actions generates __pycache__'s and they end up in the build directory.
        # This prevents them from ending up in the target branch
        with open(".gitignore", mode="w") as file:
            file.write("**/__pycache__")
        run(["git", "add", ".gitignore"], check=True)
        run(["git", "commit", "-m", "add gitignore"])
        run(["git", "push"])
        target_dir = cwd + "/" + source_branch
        shutil.copytree(build_dir, target_dir, dirs_exist_ok=True)
        shutil.rmtree(build_dir)
        run(["git", "add", "*"], check=True)
        status = run(["git", "status"], check=True, capture_output=True, text=True)
        # checks that all files do already exist in target branch,
        # meaning they have been created and successfully pushed by cli.cli
        assert "nothing to commit, working tree clean" in status.stdout


# Make sure none of Sphinx's intermediate .doctree files end up in the target branch
def test_no_doctree_files_in_remote(setup_test_env):
    branches_to_delete_in_cleanup,_,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        target_branch = "test-docu-new-branch"
        run(["git", "checkout", target_branch], check=True)
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        repo_path = doc_dir.stdout[:-1]     # -1 to remove newline at end of output
        doctree_files = []
        for root, subdirs, files in os.walk(repo_path):
            doctree_files += [str(file) for file in files
                              if ".doctree" in str(file)]
        assert not doctree_files


def test_no__pycache__files_in_remote(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        target_branch = "test-docu-new-branch"
        run(["git", "checkout", target_branch], check=True)
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        repo_path = doc_dir.stdout[:-1]     # -1 to remove newline at end of output
        pycache_dirs = []
        for root, subdir, files in os.walk(repo_path):
            pycache_dirs += [str(subdirs) for subdirs in files
                             if ".__pycache__" in str(subdirs)]
        assert not pycache_dirs


def test_only_commit_dont_push(setup_test_env):
    branches_to_delete_in_cleanup, user_name, user_access_token = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--commit"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    current_remote_commit_id = run(
        ["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
         target_branch], capture_output=True, check=True)

    remote_commit_id_new = current_remote_commit_id.stdout

    # the docu files where not updated, so no new commit should be pushed to the remote
    current_local_commit_id = run(
        ["git", "rev-parse", target_branch],
        capture_output=True, check=True)

    # target branch was not committed, so should not exist on remote
    target_branch_exists = run(
        ["git", "show-branch", f"remotes/origin/{target_branch}"],
        capture_output=True, text=True)

    assert (not remote_commit_id_new == current_local_commit_id.stdout
            and not current_local_commit_id.stdout == ""
            and not target_branch_exists.returncode == 0)


def test_select_different_source_branch_which_does_exists_locally(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    local_branch = "branch-with-different-docu-source-dir"

    run(["git", "checkout", local_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)
    assert target_branch_exists.returncode == 0


def test_select_different_source_branch_which_does_not_exists_locally(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    local_branch = "branch-with-different-docu-source-dir"
    source_branch = "main"

    run(["git", "checkout", local_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)
    assert target_branch_exists.returncode == 0


def test_select_different_source_branch_does_not_delete_local_changes(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    local_branch = "branch-with-different-docu-source-dir"
    run(["git", "checkout", local_branch], check=True)
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    # make local changes is local_branch
    with open("./index.rst", "a") as file:
        file.write("\n\nThis text is a change.")
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    # check if we are on starting branch and correct commit
    current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                         check=True)
    new_current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)

    # check if our local changes still exist
    with open("./index.rst", "r") as file:
        content = file.read()

    assert (current_branch.stdout[:-1] == local_branch
            and current_commit_id.stdout == new_current_commit_id.stdout
            and "\n\nThis text is a change." in content)


def test_infer_source_branch(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)

    # check if docu for this branch exists in target branch
    run(["git", "checkout", target_branch], check=True)
    path = Path(f"./{source_branch}")

    assert (target_branch_exists.returncode == 0
            and path.is_dir())


def test_abort_if_given_source_branch_does_not_exist(setup_test_env):
    source_branch = "this-is-not-a-branch"
    actual_branch = "main"
    run(["git", "checkout", actual_branch], check=True)
    target_branch = "test-docu-new-branch"


    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list, catch_exceptions=False)
    traceback.print_exception(*result.exc_info)

    assert (isinstance(result.exception, SystemExit)
            and bool(re.match(f"source branch {source_branch} does not exist",
                              result.exception.code)))


def test_abort_local_uncommitted_changes_exist_in_source_branch(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    # make local changes in source_branch
    with open("./index.rst", "a") as file:
        file.write("\n\nThis text is a change.")
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch] # in case something is wrongly pushed for some reason
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    assert (isinstance(result.exception, SystemExit)
            and bool(re.match(f"Abort, you have uncommitted changes in source "
                              f"branch  {source_branch}, please commit and push"
                              f" the following files:\n .*",
                              result.exception.code))
            )

    

def test_abort_local_committed_changes_exist_in_source_branch(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    with open("./index.rst", "a") as file:
        file.write("\n\nThis text is a change.")
    run(["git", "add", "*"], check=True)
    run(["git", "commit", "-m", "test-commit"], check=True)
    new_current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)
    assert (isinstance(result.exception, SystemExit)
            and bool(re.match("Abort. Local commit id .* and commit id of "
                              "remote source branch .* are not equal. Please "
                              "push your changes or pull new commits from "
                              "remote.", result.exception.code))
            )


def test_abort_source_branch_only_exists_locally(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    a_branch = "main"
    run(["git", "checkout", a_branch], check=True)
    temp_test_branch = "temp-test-branch"
    remove_branch(temp_test_branch)
    run(["git", "checkout", "-B", temp_test_branch], check=True)
    run(["git", "checkout", a_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [temp_test_branch, target_branch]

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", temp_test_branch,
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)
    assert (isinstance(result.exception, SystemExit)
            and bool(re.match(f"Source branch exists locally, but not on "
                              f"remote, and source branch is not current "
                              f"branch.Please push your source branch to "
                              f"remote.", result.exception.code))
            )



def test_abort_if_no_source_branch_detected(setup_test_env):
    branches_to_delete_in_cleanup, _, _ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    os.chdir("./doc/")
    cwd = os.getcwd()
    # break the local git repository
    os.remove("../.git/HEAD")
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    with pytest.raises(SystemExit) as e:
        with TemporaryDirectory() as tempdir:
            thisIsABrokenID = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
            deployer = GithubPagesDeployer("/doc/", "", thisIsABrokenID.stdout[:-1], "origin",
                                           ["../test_package", "../another_test_package"],
                                           target_branch, "origin", "push",
                                           Path(tempdir))
            try:
                deployer.detect_or_verify_source_branch()
            finally:
                deployer.clean_worktree(cwd)

    assert (e.match(f"Abort. Could not detect current branch and no source branch given.")
            and e.type == SystemExit)


def test_use_different_source_dir(setup_test_env):
    branches_to_delete_in_cleanup, _ ,_ = setup_test_env
    source_branch = "branch-with-different-docu-source-dir"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--source-dir", "documentation/",
        "--module-path", "../test_package",
        "--module-path", "../another_test_package",
        "--push"]
    result = CliRunner(mix_stderr=False).invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)

    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)

    assert target_branch_exists.returncode == 0


def test_abort_if_invalid_source_dir(setup_test_env):
    branches_to_delete_in_cleanup, _, _ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)
    with pytest.raises(FileNotFoundError) as e:
        args_list = [
            "--target-branch", target_branch,
            "--source-branch", source_branch,
            "--source-dir", "not_a_source_dir/",
            "--module-path", "../test_package",
            "--module-path", "../another_test_package",
            "--push"]
        result = CliRunner().invoke(cli.main, args_list, catch_exceptions=False)
        traceback.print_exception(*result.exc_info)

    assert e.match(re.escape("[Errno 2] No such file or directory:") + ".*/not_a_source_dir'")
    remove_branch(target_branch)


def test_source_branch_is_tag(setup_test_env):
    branches_to_delete_in_cleanup, _, _ = setup_test_env
    source_branch = "test-release-tag"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)
    print(os.getcwd())
    args_list = [
        "--target-branch", target_branch,
        "--source-branch", source_branch,
        "--source-origin", "tags",
        "--module-path", "../test_package",
        "--push"]
    result = CliRunner().invoke(cli.main, args_list)
    traceback.print_exception(*result.exc_info)
    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)
    assert target_branch_exists.returncode == 0
