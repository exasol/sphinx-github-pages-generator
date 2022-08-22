from subprocess import run
import os
import shutil
from pathlib import Path


def run_deployer_build_and_copy_documentation_without_gen_index(deployer):
    currentworkdir = os.getcwd()
    print(currentworkdir)
    for module in deployer.module_path:
        out = run(["sphinx-apidoc", "-T", "-e", "-o", "api", module])
        print(module)
        print(out)
    run(["sphinx-build", "-b", "html", "-d", deployer.intermediate_dir, "-W", currentworkdir, deployer.build_dir], check=True)

    output_dir = Path(f"{deployer.worktree_paths['target_worktree']}/{deployer.source_branch}")

    if output_dir.exists() and output_dir.is_dir():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    for obj in os.listdir(deployer.build_dir):
        shutil.move(str(deployer.build_dir / str(obj)), output_dir)

    return output_dir


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
    # change into the "tmpXXX/../branch_name" directory.
    # the [:-1] removes the newline from the output
    doc_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    os.chdir(f"{doc_dir.stdout[:-1]}")
    return user_name, user_access_token

