import re

import pytest
from subprocess import run
from tempfile import TemporaryDirectory
import os
from pathlib import Path

import exasol_sphinx_github_pages_generator.deploy_github_pages as deploy_github_pages
from helper_test_functions import remove_branch, setup_workdir
from fixtures import setup_test_env
import shutil
from exasol_sphinx_github_pages_generator.deployer import GithubPagesDeployer

#todo add tests for tags
def test_remote_branch_creation(setup_test_env):
    branches_to_delete_in_cleanup, _, _ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)
    print(os.getcwd())
    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package"])
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

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", temp_test_branch,
                                             "--module_path", "../test_package", "../another_test_package"])
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
    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", temp_test_branch,
                                             "--module_path", "../test_package", "../another_test_package"])
    current_commit_id = run(["git", "ls-remote",
                             f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
                             target_branch], capture_output=True, check=True)
    commit_id_new = current_commit_id.stdout

    # the docu files where updated, so a new commit should be pushed to the remote
    assert not commit_id_new == ""
    assert not commit_id_old == ""
    assert not commit_id_old == commit_id_new


def test_pushing_to_existing_docu_branch_different_source(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch_one = "main"
    run(["git", "checkout", source_branch_one], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch_one,
                                             "--module_path", "../test_package", "../another_test_package"])

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        source_branch_two = "branch-with-different-docu-source-dir"
        run(["git", "checkout", source_branch_two], check=True)

        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--source_branch", source_branch_two,
                                                 "--source_dir", "/documentation/",
                                                 "--module_path", "../test_package", "../another_test_package"])
        target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                                   text=True)
        assert target_branch_exists.returncode == 0
        doc_dir_source_one_exists = run(["git", "ls-tree", "-d", f"origin/{target_branch}:{source_branch_one}"],
                                        capture_output=True, text=True, check=True)
        assert doc_dir_source_one_exists.returncode == 0
        doc_dir_source_two_exists = run(["git", "ls-tree", "-d", f"origin/{target_branch}:{source_branch_two}"],
                                        capture_output=True, text=True, check=True)
        assert doc_dir_source_two_exists.returncode == 0


def test_no_new_push_and_commit_if_no_changes(setup_test_env):
    branches_to_delete_in_cleanup, user_name, user_access_token = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package", "../another_test_package"])
    current_commit_id = run(
        ["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
         target_branch], capture_output=True, check=True)
    commit_id_old = current_commit_id.stdout

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package", "../another_test_package"])
    current_commit_id = run(
        ["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
         target_branch], capture_output=True, check=True)
    commit_id_new = current_commit_id.stdout

    # the docu files where not updated, so no new commit should be pushed to the remote
    assert commit_id_old != 0
    assert commit_id_old == commit_id_new
    assert not commit_id_new == ""


def test_verify_existence_of_generated_files_on_remote_after_push(setup_test_env):
    # generate files locally in test, and with generator, look at diff between local files and remote files?
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)
    module_path = ["../test_package", "../another_test_package"]
    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", module_path[0], module_path[1]])

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
        # meaning they have been created and successfully pushed by deploy_github_pages.deploy_github_pages
        assert "nothing to commit, working tree clean" in status.stdout


# Make sure none of Sphinx's intermediate .doctree files end up in the target branch
def test_no_doctree_files_in_remote(setup_test_env):
    branches_to_delete_in_cleanup,_,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package", "../another_test_package"])

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        target_branch = "test-docu-new-branch"
        run(["git", "checkout", target_branch], check=True)
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        repo_path = doc_dir.stdout[:-1]     # -1 to remove newline at end of output
        for root, subdirs, files in os.walk(repo_path):
            for file in files:
                assert ".doctree" not in str(file)


def test_no__pycache__files_in_remote(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package", "../another_test_package"])

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        target_branch = "test-docu-new-branch"
        run(["git", "checkout", target_branch], check=True)
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        repo_path = doc_dir.stdout[:-1]     # -1 to remove newline at end of output
        for root, subdir, files in os.walk(repo_path):
            for subdirs in files:
                assert "__pycache__" not in str(subdirs)


def test_only_commit_dont_push(setup_test_env):
    branches_to_delete_in_cleanup, user_name, user_access_token = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--push_enabled", "commit",
                                             "--module_path", "../test_package", "../another_test_package"])
    current_remote_commit_id = run(
        ["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
         target_branch], capture_output=True, check=True)

    remote_commit_id_new = current_remote_commit_id.stdout

    current_local_commit_id = run(["git", "rev-parse", target_branch], capture_output=True, check=True)
    # the docu files where not updated, so no new commit should be pushed to the remote
    assert not remote_commit_id_new == current_local_commit_id.stdout
    assert not current_local_commit_id.stdout == ""
    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)
    # target branch was not committed, so should not exist on remote
    assert not target_branch_exists.returncode == 0


def test_select_different_source_branch_which_does_exists_locally(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    local_branch = "branch-with-different-docu-source-dir"

    run(["git", "checkout", local_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package", "../another_test_package"])
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

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package", "../another_test_package"])
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

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package", "../another_test_package"])

    current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                         check=True)
    new_current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    # check if we are on starting branch and correct commit
    assert current_branch.stdout[:-1] == local_branch
    assert current_commit_id.stdout == new_current_commit_id.stdout
    # check if our local changes still exist
    with open("./index.rst", "r") as file:
        content = file.read()
        assert "\n\nThis text is a change." in content


def test_infer_source_branch(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--module_path", "../test_package", "../another_test_package"])
    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)
    assert target_branch_exists.returncode == 0
    run(["git", "checkout", target_branch], check=True)
    path = Path(f"./{source_branch}")
    # check if docu for this branch exists in target branch
    assert path.is_dir()


def test_abort_if_given_source_branch_does_not_exist(setup_test_env):
    source_branch = "this-is-not-a-branch"
    actual_branch = "main"
    run(["git", "checkout", actual_branch], check=True)
    target_branch = "test-docu-new-branch"

    with pytest.raises(SystemExit) as e:
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--source_branch", source_branch,
                                                 "--module_path", "../test_package", "../another_test_package"])
    assert e.match(f"source branch {source_branch} does not exist")
    assert e.type == SystemExit


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

    with pytest.raises(SystemExit) as e:
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--source_branch", source_branch,
                                                 "--module_path", "../test_package", "../another_test_package"])
    assert e.match(f"Abort, you have uncommitted changes in source branch  {source_branch}, "
                     f"please commit and push the following files:\n .*")
    assert e.type == SystemExit


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

    with pytest.raises(SystemExit) as e:
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--source_branch", source_branch,
                                                 "--module_path", "../test_package", "../another_test_package"])
    assert e.match(f"Abort. Local commit id .* and commit id of remote source branch"
                   f" .* are not equal. Please push your changes or pull new commits from remote.")
    assert e.type == SystemExit


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
    with pytest.raises(SystemExit) as e:
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--source_branch", temp_test_branch,
                                                 "--module_path", "../test_package", "../another_test_package"])

    assert e.match(f"Source branch exists locally, but not on remote, and source branch is not current branch."
                   f"Please push your source branch to remote.")
    assert e.type == SystemExit


def test_abort_if_no_source_branch_detected(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
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
                                           tempdir)
            try:
                deployer.detect_or_verify_source_branch()
            finally:
                deployer.clean_worktree(cwd)

    assert e.match(f"Abort. Could not detect current branch and no source branch given.")
    assert e.type == SystemExit


def test_use_different_source_dir(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "branch-with-different-docu-source-dir"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    #branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--source_dir", "/documentation/",
                                             "--module_path", "../test_package", "../another_test_package"])
    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)
    assert target_branch_exists.returncode == 0


def test_abort_if_invalid_source_dir(setup_test_env):
    branches_to_delete_in_cleanup, _,_ = setup_test_env
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch"
    branches_to_delete_in_cleanup += [target_branch]
    remove_branch(target_branch)
    with pytest.raises(FileNotFoundError) as e:
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--source_branch", source_branch,
                                                 "--source_dir", "/not_a_source_dir/",
                                                 "--module_path", "../test_package", "../another_test_package"])

    assert e.match(re.escape("[Errno 2] No such file or directory: './not_a_source_dir/'"))
    remove_branch(target_branch)
