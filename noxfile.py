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
ENTRY_POINT = "exasol_sphinx_github_pages_generator.cli"


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
    if DOC_BUILD.exists():
        rmtree(DOC_BUILD.resolve())
        session.log(f"Removed {DOC_BUILD}")


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
    session.run("sphinx-build", "-b", "html", "-W", f"{DOC}", f"{DOC_BUILD}", external=True)


@nox.session(python=False, name='open-docs')
def open_docs(session):
    """Open the documentation in the browser"""
    index_page = DOC_BUILD / "index.html"
    if not index_page.exists():
        session.error(
            (f"File {index_page} does not exist." "Please run `nox -s build-docs` first")
        )
    session.run(
        "python", "-m", "webbrowser", "-t", f"{index_page.resolve()}", external=True
    )


@nox.session(python=False)
def tests(session):
    """Run all unit tests"""
    session.run("pytest", "--pdb", f"{PROJECT_ROOT / 'tests'}")


@nox.session(python=False, name="commit-pages")
@nox.parametrize("branch", ["current", "main"])
def commit(session, branch):
    """Generates documentation for the specified branch commits it to appropriate target branch"""

    target_branch = {
        "main": "github-pages/main",
        "current": f"github-pages/{_current_branch()}",
    }
    branch_specific_arguments = {
        "main": ["--source-branch", "main"],
        "current": ["--source-branch", f"{_current_branch()}"],
    }
    args = [
        "python",
        "-m",
        ENTRY_POINT,
        "--module-path",
        f"{PACKAGE}",
        "--push-origin",
        "origin",
        "--push-enabled",
        "commit",
        "--target-branch",
        target_branch[branch],
    ]
    args += branch_specific_arguments[branch]
    session.run(*args, external=True)


@nox.session(python=False, name="push-pages")
@nox.parametrize("target", ["current", "main", "release"])
def push(session, target):
    """Generates documentation for the specified branch pushes it to appropriate target branch"""
    try:
        latest_tag = _tags()[-1]
    except IndexError as e:
        if "release" in target:
            raise Exception("Couldn't find any tag") from e
        else:
            latest_tag = ""
    target_branch = {
        "main": "github-pages/main",
        "current": f"github-pages/{_current_branch()}",
        "release": f"github-pages/main",    # This has to be main because github-pages expects all documentation to be
                                            # in the same source branch.
    }
    target_specific_arguments = {
        "main": ["--source-branch", "main"],
        "current": [],
        "release": ["--source-branch", latest_tag, "--source-origin", "tags"],
    }
    args = [
        "python",
        "-m",
        ENTRY_POINT,
        "--module-path",
        f"{PACKAGE}",
        "--push-origin",
        "origin",
        "--push-enabled",
        "push",
        "--target-branch",
        target_branch[target],
    ]
    args += target_specific_arguments[target]
    session.run(*args, external=True)
