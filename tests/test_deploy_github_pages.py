import pytest
from subprocess import run
from tempfile import TemporaryDirectory
import os
from pathlib import Path

import exasol_sphinx_github_pages_generator.deploy_github_pages as deploy_github_pages
from helper_test_functions import remove_branch, setup_workdir
from fixtures import setup_test_env
import shutil
# TODO change to oauth2?


def test_remote_branch_creation(setup_test_env):
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

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


def test_pushing_to_existing_docu_branch_same_source(setup_test_env):
    user_name, user_access_token = setup_test_env
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

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


def test_pushing_to_existing_docu_branch_different_source(setup_test_env):
    source_branch_one = "5-add-tests"
    run(["git", "checkout", source_branch_one], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", source_branch_one,
                                             "--source_dir", cwd,
                                             "--module_path", ["../test_package", "../another_test_package"]])

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        source_branch_two = "refactoring/1-Move-Sphinx-Documentation-scripts"
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


def test_no_new_push_and_commit_if_no_changes(setup_test_env):
    user_name, user_access_token = setup_test_env
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", source_branch,
                                             "--source_dir", cwd,
                                             "--module_path", ["../test_package", "../another_test_package"]])
    current_commit_id = run(
        ["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
         target_branch], capture_output=True, check=True)
    commit_id_old = current_commit_id.stdout

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", source_branch,
                                             "--source_dir", cwd,
                                             "--module_path", ["../test_package", "../another_test_package"]])
    current_commit_id = run(
        ["git", "ls-remote", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git",
         target_branch], capture_output=True, check=True)
    commit_id_new = current_commit_id.stdout

    # the docu files where not updated, so no new commit should be pushed to the remote
    assert commit_id_old != 0
    assert commit_id_old == commit_id_new
    assert not commit_id_new == ""
    remove_branch(target_branch)


def test_verify_existence_of_generated_files_on_remote_after_push(setup_test_env):
    # generate files locally in test, and with generator, look at diff between local files and remote files?
    user_name , user_access_token = setup_test_env
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)
    module_path = ["../test_package", "../another_test_package"]
    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", source_branch,
                                             "--source_dir", cwd,
                                             "--module_path", module_path])

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        source_branch = "5-add-tests"
        run(["git", "checkout", source_branch], check=True)
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
        print(f"Copying HTML output {build_dir} to the output directory {target_dir}")
        shutil.copytree(build_dir, target_dir, dirs_exist_ok=True)
        shutil.rmtree(build_dir)
        run(["git", "add", "*"], check=True)
        status = run(["git", "status"], check=True, capture_output=True, text=True)
        # checks that all files do already exist in target branch,
        # meaning they have been created and successfully pushed by deploy_github_pages.deploy_github_pages
        assert "nothing to commit, working tree clean" in status.stdout
        remove_branch(target_branch)


# Make sure none of Sphinx's intermediate .doctree files end up in the target branch
def test_no_doctree_files_in_remote(setup_test_env):
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", source_branch,
                                             "--source_dir", cwd,
                                             "--module_path", ["../test_package", "../another_test_package"]])

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        target_branch = "test-docu-new-branch"
        os.chdir(os.getcwd() + "/..")
        run(["git", "checkout", target_branch], check=True)
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        repo_path = doc_dir.stdout[:-1]     # -1 to remove newline at end of output
        for root, subdirs, files in os.walk(repo_path):
            for file in files:
                assert ".doctree" not in str(file)
        remove_branch(target_branch)

def test_no__pycache__files_in_remote(setup_test_env):
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", source_branch,
                                             "--source_dir", cwd,
                                             "--module_path", ["../test_package", "../another_test_package"]])

    with TemporaryDirectory() as tempdir2:
        os.chdir(tempdir2)
        setup_workdir()
        target_branch = "test-docu-new-branch"
        os.chdir(os.getcwd() + "/..")
        run(["git", "checkout", target_branch], check=True)
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        repo_path = doc_dir.stdout[:-1]     # -1 to remove newline at end of output
        for root, subdirs, files in os.walk(repo_path):
            for subdirs in files:
                assert "__pycache__" not in str(subdirs)
        remove_branch(target_branch)


def test_only_commit_dont_push(setup_test_env):
    user_name, user_access_token = setup_test_env
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "commit",
                                             "--source_branch", source_branch,
                                             "--source_dir", cwd,
                                             "--module_path", ["../test_package", "../another_test_package"]])
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

    remove_branch(target_branch)


def test_select_different_source_branch_which_does_exists_locally(setup_test_env):
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    local_branch = "refactoring/1-Move-Sphinx-Documentation-scripts" # todo make second test branch in remote

    run(["git", "checkout", local_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

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


def test_select_different_source_branch_which_does_not_exists_locally(setup_test_env):
    local_branch = "refactoring/1-Move-Sphinx-Documentation-scripts" # todo make second test branch in remote
    source_branch = "5-add-tests"

    run(["git", "checkout", local_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

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


def test_select_different_source_branch_does_not_delete_local_changes(setup_test_env):
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    local_branch = "refactoring/1-Move-Sphinx-Documentation-scripts"  # todo make second test branch in remote
    run(["git", "checkout", local_branch], check=True)
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    cwd = os.getcwd()
    # make local changes is local_branch
    with open("./index.rst", "a") as file:
        file.write("\n\nThis text is a change.")
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", source_branch,
                                             "--source_dir", cwd,
                                             "--module_path", ["../test_package", "../another_test_package"]])

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
    remove_branch(target_branch)


def test_infer_source_branch(setup_test_env):
    source_branch = "5-add-tests"
    run(["git", "checkout", source_branch], check=True)
    cwd = os.getcwd()
    target_branch = "test-docu-new-branch"
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_dir", cwd,
                                             "--module_path", ["../test_package", "../another_test_package"]])
    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                               text=True)
    assert target_branch_exists.returncode == 0
    # removes last directory from current working dir, because int does not exist in the target branch,
    # resulting in file_not_found error in os.getcwd() after checkout
    new_cwd = "/".join(os.getcwd().split("/")[:-1])
    os.chdir(new_cwd)
    run(["git", "checkout", target_branch], check=True)
    run(["ls", "-la", new_cwd], check=True)
    path = Path(f"./{source_branch}")
    # check if docu for this branch exists in target branch
    assert path.is_dir()
    remove_branch(target_branch)
