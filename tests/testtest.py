import pytest
from subprocess import run
from tempfile import TemporaryDirectory
import os
import exasol_sphinx_github_pages_generator.deploy_github_pages as deploy_github_pages

# TODO change to oauth2?
# todo write readme

# Tests:

"""
in action: install python, poetry
temp folder
run git check out test-repo, install
run scripts with test repo path ? on test repo.
run git commit/push new/existing branch/??
assert with git api : pushed files are as expected
delete branch


needed:
test branch push right branch
test existence of files
test commit only
test deletion of temp files?
test for main branch
test for other branch
test for branch not curretly on?
test for branch curretly on?
"""


def test_remote_branch_creation():
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        user_access_token = os.environ.get("MAuserPAT")
        user_name = os.environ.get("MAuserName")
        run(["git", "clone", f"https://{user_access_token}@github.com/exasol/sphinx-github-pages-generator-test.git"], check=True)
        os.chdir("sphinx-github-pages-generator-test")
        #run(["git", "config", "--local", "user.email", "'opensource@exasol.com'"], check=True)
        #run(["git", "config", "--local", "user.name", "'GitHub Action'"], check=True)  # this work? different user?

        #run(["git", "clone", "https://github.com/exasol/sphinx-github-pages-generator-test.git"], check=True)
        doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        os.chdir(f"{doc_dir.stdout[:-1]}/doc")
        source_branch = "5-add-tests"
        run(["git", "checkout",source_branch], check=True)
        target_branch = "test-docu-new-branch"
        target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                                   text=True)

        # remove remote target branch if exists:
        if target_branch_exists.returncode == 0: #todo fix
            run(["git", "push", "-d", "origin", target_branch], check=True)
            # run([git branch - d < branchname >], check=True)

        cwd = os.getcwd()
        deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                                 "--push_origin", "origin",
                                                 "--push_enabled", "push",
                                                 "--source_branch", "5-add-tests",
                                                 "--source_dir", cwd,
                                                 "--module_path", ["../test_package", "../another_test_package"]])
        target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True,
                                   text=True)
        assert target_branch_exists.returncode == 0
        # remove remote target branch if exists:
        if target_branch_exists.returncode == 0:
            run(["git", "push", "-d", "origin", target_branch], check=True)