from subprocess import run
import os


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


def setup_workdir():
    user_name, user_access_token = setup_test_repo()
    # change into the "tmpXXX/../branch_name/doc" directory. This is necessary for Sphinx.
    # the [:-1] removes the newline from the output
    doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    os.chdir(f"{doc_dir.stdout[:-1]}/doc")
    cwd = os.getcwd()
    return user_name, user_access_token, cwd

