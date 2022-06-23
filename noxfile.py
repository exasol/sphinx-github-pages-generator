from pathlib import Path
from shutil import rmtree
from subprocess import PIPE, run

import nox

nox.options.sessions = ["clean-docs", "build-docs", "open-docs"]

PROJECT_ROOT = Path(__file__).parent
DOC = PROJECT_ROOT / "doc"
DOC_SCRIPTS = DOC / "scripts"
DOC_BUILD = DOC / "build"
PACKAGE = PROJECT_ROOT / "exasol_sphinx_github_pages_generator"
ENTRY_POINT = "exasol_sphinx_github_pages_generator.deploy_github_pages"


def _tags():
    """
    Returns a list of all tags, sorted from [0] oldest to [-1] newest.

    PreConditions:
    - the git cli tool needs to be installed
    - the git cli tool can be found via $PATH
    - the code is executed where the working directory is within a git repository
    """
    command = ["git", "tag", "--sort=committerdate"]
    result = run(command, stdout=PIPE, stderr=PIPE, check=True)
    tags = (tag.strip() for tag in result.stdout.decode("utf-8").splitlines())
    return list(tags)


def _current_branch():
    """
    Returns the current branch name.

    PreConditions:
    - the git cli tool needs to be installed
    - the git cli tool can be found via $PATH
    - the code is executed where the working directory is within a git repository
    """
    command = ["git", "branch", "--show-current"]
    result = run(command, stdout=PIPE, stderr=PIPE, check=True)
    branch_name = result.stdout.decode("utf-8").strip()
    return branch_name


@nox.session(python=False, name='clean-docs')
def clean(session):
    """Remove all documentation artifacts"""
    build_directory = DOC / "build"
    if build_directory.exists():
        rmtree(build_directory.resolve())
        session.log(f"Removed {build_directory}")


@nox.session(python=False, name='build-docs')
def build(session):
    """Build the documentation"""
    with session.chdir(DOC):
        session.run(
            "sphinx-apidoc",
            "-T",
            "-e",
            "-o",
            "api",
            f"{PACKAGE.resolve()}",
            external=True,
        )
        session.run("sphinx-build", "-b", "html", "-W", ".", "build", external=True)


@nox.session(python=False, name='open-docs')
def open(session):
    """Open the documentation in the browser"""
    index_page = DOC / "build" / "index.html"
    if not index_page.exists():
        session.error(
            (f"File {index_page} does not exist." "Please run `nox -s build` first")
        )
    session.run(
        "python", "-m", "webbrowser", "-t", f"{index_page.resolve()}", external=True
    )


@nox.session(python=False)
def tests(session):
    """Run all unit tests"""
    session.run("pytest", f"{PROJECT_ROOT / 'tests'}")


@nox.session(python=False, name="commit-pages")
@nox.parametrize("branch", ["current", "main"])
def commit(session, branch):
    """Generates documentation for the specified branch commits it to appropriate target branch"""

    target_branch = {
        "main": "github-pages/main",
        "current": f"github-pages/{_current_branch()}",
    }
    branch_specific_arguments = {
        "main": ["--source_branch", "main"],
        "current": ["--source_branch", f"{_current_branch()}"],
    }
    args = [
        "python",
        "-m",
        ENTRY_POINT,
        "--module_path",
        f"{PACKAGE}",
        "--push_origin",
        "origin",
        "--push_enabled",
        "commit",
        "--target_branch",
        target_branch[branch],
    ]
    args += branch_specific_arguments[branch]
    session.run(*args, external=True)


@nox.session(python=False, name="push-pages")
@nox.parametrize("target", ["current", "main", "release"])
def push(session, target):
    """Generates documentation for the specified branch commits it to appropriate target branch"""
    target_branch = {
        "main": "github-pages/main",
        "current": f"github-pages/{_current_branch()}",
        "release": f"github-pages/{_tags()[-1]}",
    }
    target_specific_arguments = {
        "main": ["--source_branch", "main"],
        "current": ["--source_branch", f"{_current_branch()}"],
        "release": ["--source_branch", _tags()[-1], "--source_origin", "tags"],
    }
    args = [
        "python",
        "-m",
        ENTRY_POINT,
        "--module_path",
        f"{PACKAGE}",
        "--push_origin",
        "origin",
        "--push_enabled",
        "push",
        "--target_branch",
        target_branch[target],
    ]
    args += target_specific_arguments[target]
    session.run(*args, external=True)
