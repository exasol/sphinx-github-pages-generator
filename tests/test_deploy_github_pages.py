import sys

import pytest
from subprocess import run
from tempfile import TemporaryDirectory
import os
import exasol_sphinx_github_pages_generator.deploy_github_pages as deploy_github_pages

# TODO change to oauth2?
# todo write readme
# todo change source_branch to main

# Tests:


def remove_branch(branch_name):
    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{branch_name}"], capture_output=True,
                               text=True)
    # remove remote target branch if exists:
    if target_branch_exists.returncode == 0:
        run(["git", "push", "-d", "origin", branch_name], check=True)


def setup_test_repo():
    user_access_token = os.environ.get("MAuserPAT")
    user_name = os.environ.get("MAuserName")
    run(["git", "clone", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git"],
        check=True)
    os.chdir("sphinx-github-pages-generator-test")
    run(["git", "remote", "set-url", "origin",
         f"https://{user_name}:{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git"],
        check=True)

    run(["git", "config", "--local", "user.email", f"{user_name}@exasol.com"], check=True)
    run(["git", "config", "--local", "user.name", user_name], check=True)
    return user_name, user_access_token


def test_remote_branch_creation():
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        setup_test_repo()
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        os.chdir(f"{doc_dir.stdout[:-1]}/doc")
        source_branch = "5-add-tests"
        run(["git", "checkout", source_branch], check=True)
        target_branch = "test-docu-new-branch"
        remove_branch(target_branch)

        cwd = os.getcwd()
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "push",
                                                 "--source_branch", source_branch,
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../test_package", "../another_test_package"]])
        target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                                   text=True)
        assert target_branch_exists.returncode == 0
        remove_branch(target_branch)


def test_pushing_to_existing_docu_branch_same_source():
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        user_name, user_access_token = setup_test_repo()
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        os.chdir(f"{doc_dir.stdout[:-1]}/doc")
        source_branch = "5-add-tests"
        run(["git", "checkout", source_branch], check=True)
        target_branch = "test-docu-new-branch"
        remove_branch(target_branch)

        cwd = os.getcwd()
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "push",
                                                 "--source_branch", source_branch,
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../test_package", "../another_test_package"]])
        current_commit_id = run(["git", "ls-remote",
                                 f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
                                 target_branch], capture_output=True, check=True)
        commit_id_old = current_commit_id.stdout

        # make a change in the docu
        with open("./index.rst", "a") as file:
            file.write("\n\nThis text is a change.")

        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "push",
                                                 "--source_branch", source_branch,
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../test_package", "../another_test_package"]])
        current_commit_id = run(["git", "ls-remote",
                                 f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
                                 target_branch], capture_output=True, check=True)
        commit_id_new = current_commit_id.stdout

        # the docu files where updated, so a new commit should be pushed to the remote
        assert not commit_id_new == ""
        assert not commit_id_old == ""
        assert not commit_id_old == commit_id_new
        remove_branch(target_branch)


def test_pushing_to_existing_docu_branch_different_source():
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        setup_test_repo()
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        os.chdir(f"{doc_dir.stdout[:-1]}/doc")
        source_branch_one = "5-add-tests"
        run(["git", "checkout", source_branch_one], check=True)
        target_branch = "test-docu-new-branch"
        remove_branch(target_branch)

        cwd = os.getcwd()
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "push",
                                                 "--source_branch", source_branch_one,
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../test_package", "../another_test_package"]])

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_test_repo()
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        os.chdir(f"{doc_dir.stdout[:-1]}/doc")
        source_branch_two = "refactoring/1-Move-Sphinx-Documentation-scripts" # todo make second test branch in remote
        run(["git", "checkout", source_branch_two], check=True)

        cwd = os.getcwd()
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "push",
                                                 "--source_branch", source_branch_two,
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../exasol_test_code_source"]])
        target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                                   text=True)
        assert target_branch_exists.returncode == 0
        doc_dir_source_one_exists = run(["git", "ls-tree", "-d", f"origin/{target_branch}:{source_branch_one}"],
                                        capture_output=True, text=True, check=True)
        assert doc_dir_source_one_exists.returncode == 0
        doc_dir_source_two_exists = run(["git", "ls-tree", "-d", f"origin/{target_branch}:{source_branch_two}"],
                                        capture_output=True, text=True, check=True)
        assert doc_dir_source_two_exists.returncode == 0
        remove_branch(target_branch)


def test_no_new_push_and_commit_if_no_changes():
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        user_name, user_access_token = setup_test_repo()
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        os.chdir(f"{doc_dir.stdout[:-1]}/doc")
        source_branch = "5-add-tests"
        run(["git", "checkout", source_branch], check=True)
        target_branch = "test-docu-new-branch"
        remove_branch(target_branch)

        cwd = os.getcwd()
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "push",
                                                 "--source_branch", source_branch,
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../test_package", "../another_test_package"]])
        current_commit_id = run(["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git", target_branch], capture_output=True, check=True)
        commit_id_old = current_commit_id.stdout

        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "push",
                                                 "--source_branch", source_branch,
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../test_package", "../another_test_package"]])
        current_commit_id = run(["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git", target_branch], capture_output=True, check=True)
        commit_id_new = current_commit_id.stdout

        # the docu files where not updated, so no new commit should be pushed to the remote
        assert commit_id_old != 0 #todo also in other tests
        assert commit_id_old == commit_id_new
        assert not commit_id_new == ""
        remove_branch(target_branch)


def test_for_existence_of_docu_files():
    # TODO
    # generate files locally in test, and with generator, look at diff between local files and remote files?
    pass


def test_only_commit_dont_push():
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        user_name, user_access_token = setup_test_repo()
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        os.chdir(f"{doc_dir.stdout[:-1]}/doc")
        source_branch = "5-add-tests"
        run(["git", "checkout", source_branch], check=True)
        target_branch = "test-docu-new-branch"
        remove_branch(target_branch)

        cwd = os.getcwd()
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "commit",
                                                 "--source_branch", source_branch,
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../test_package", "../another_test_package"]])
        current_remote_commit_id = run(["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git", target_branch], capture_output=True, check=True)
        remote_commit_id_new = current_remote_commit_id.stdout

        current_local_commit_id = run(["git", "rev-parse", target_branch], capture_output=True, check=True)
        # the docu files where not updated, so no new commit should be pushed to the remote
        assert not remote_commit_id_new == current_local_commit_id.stdout
        assert not current_local_commit_id.stdout == ""
        target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                                   text=True)
        # target branch was not committed, so should not exist on remote
        assert not target_branch_exists.returncode == 0

        remove_branch(target_branch)


def test_selection_of_source_branch():
    # at the moment requires you to be on source branch
    # TODO implement once branch selection is implemented
    pass

