import os
from pathlib import Path
import sys
import glob
import re
import shutil
from subprocess import run
from jinja2 import Environment, PackageLoader, select_autoescape
import inspect
from typing import List, Dict

import exasol_sphinx_github_pages_generator


def find_index(target_worktree: Path, source_branch: str) -> Path:
    """
    For the given source_branch find the index.html file in its documentation files,
    and return its path. Aborts if there are more or less han exactly one (1) index.html file.
    :param target_worktree: Worktree/path all generated project documentation is put into.
    :param source_branch: Name of the branch the documentation should be searched for.
    :return: Path pointing at found index.html file
    """
    cwd = os.getcwd()
    os.chdir(target_worktree)
    index_list = glob.glob(f'{source_branch}/**/index.html', recursive=True)
    if len(index_list) != 1:
        sys.exit(f"""
                Your generated documentation does not include the right amount of index.html files (1). 
                Instead it includes {len(index_list)} in path {target_worktree}/{source_branch}
                """)
    index_path = index_list[0]
    os.chdir(cwd)
    return Path(index_path)


def generate_release_dicts(release_list: List[str], source_branch: str, target_worktree: Path) \
        -> List[Dict[str, str]]:
    """
    Given a list of releases, generate a list of dictionaries containing the name of the release, and the path to its
    documentation relative to targen_worktree. The current release is titled "latest".
    :param release_list: List of release-names as strings.
    :param source_branch: The branch we are currently generating the documentation for.
    :param target_worktree:  Worktree/path all generated project documentation is put into.
    :return: List of dictionaries containing the release name and path to its index.html file.
    """
    release_list_dicts = [{"release": "latest",
                           "release_path": f"{find_index(target_worktree, source_branch)}"}]
    for release in release_list:
        if release == "_sources" or release == "_static":
            continue
        if release != source_branch:
            release_list_dicts.append({"release": release,
                                       "release_path": f"{find_index('.', release)}"})
    return release_list_dicts


def get_releases(target_branch: str, target_branch_exists_remote: bool, source_branch: str, target_worktree: Path) \
        -> List[Dict[str, str]]:
    """
    Find all releases already documented in target_branch, and return them tih the path pointing to their index.html
    file. Additionally also return the current release and index.html-file-path. The current release is titled "latest".
    Found releases are returned as a list of dictionaries.
    In order to find the releases in the target_branch, it is checked out in an additional temporary worktree.
    Takes the root-directory name for each release and returns it. Gives bad results if directory names contain slashes.
    Please remove slashes from directory names before using them to generate the root directory for your
    release-documentation.

    :param target_branch: The branch the generated documentation should end up on.
    :param target_branch_exists_remote: Bool representing whether the target_branch already exist in the remote
        repository.
    :param source_branch: The branch we are currently generating the documentation for.
    :param target_worktree: Worktree/path all generated project documentation is put into.
    :return: List of dictionaries containing the release name and path to its index.html file.
    """
    if target_branch_exists_remote:
        cwd = os.getcwd()
        find_index_worktree_path = os.path.join(cwd, "target-branch-for-index/")
        completed = run(["git", "worktree", "add", find_index_worktree_path, target_branch, "--force"])
        if completed.returncode != 0:
            sys.exit(f"""checking out target_branch {target_branch} failed, although given 
                     'target_branch_exists_remote' was 'True'. Check if target_branch really exists on remote?
                     received Error:
                        returncode: {completed.returncode},
                        stderr: {completed.stderr},
                        stdout: {completed.stdout}"""
                     )

        os.chdir(find_index_worktree_path)
        current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                             check=True)
        print(f"current_branch {current_branch.stdout} in find_index_worktree_path {find_index_worktree_path}.")
        # does not work if release branch name contains slash
        release_list = (name for name in os.listdir(find_index_worktree_path)
                        if os.path.isdir(os.path.join(find_index_worktree_path, name)))

        release_list_dicts = generate_release_dicts(release_list, source_branch, target_worktree)
        run(["git", "worktree", "remove", "--force", find_index_worktree_path], check=True)
        os.chdir(cwd)

    else:
        release_list_dicts = generate_release_dicts([], source_branch, target_worktree)

    return release_list_dicts


def gen_index(target_branch: str, target_worktree: Path, source_branch: str, target_branch_exists_remote: bool) -> None:
    """
    Generates a release index file from a given target_branch into the target_worktree.
    Uses the given source_branch to pull the newest generated index.html file to take out lines describing the style
    and the footer, in oder to keep the release index file visually close to the rest of the documentation.
    Source_branch will be called "latest" in the resulting release index.
    Also adds the template file to "_sources".
    Aborts if not currently in given source_branch.

    :param target_branch: The branch the generated documentation should end up on.
    :param target_worktree: Worktree/path all generated project documentation is put into.
    :param source_branch: The branch we are currently generating the documentation for.
    :param target_branch_exists_remote: Bool representing whether the target_branch already exist in the remote
        repository.

    """

    print("s_branch " + source_branch)
    local_source_branch_commit_id = run(["git", "rev-parse", source_branch], capture_output=True,
                                        text=True)
    if local_source_branch_commit_id.returncode != 0:
        sys.exit(f"{source_branch} not currently checked out. Please Check out branch {source_branch}"
                 f" before calling gen_index.")
    # remove slashes from branch-name, this makes parsing the release-names for the release-index much easier
    simple_source_branch_name = source_branch.replace("/", "-")
    env = Environment(
        loader=PackageLoader("exasol_sphinx_github_pages_generator"),
        autoescape=select_autoescape()
    )
    template = env.get_template("index_template.html.jinja2")
    releases = get_releases(target_branch, target_branch_exists_remote, simple_source_branch_name, target_worktree)
    with open(f"{target_worktree}/index.html", "w+") as file:
        file.write(template.render(meta_list=[], releases=releases, footer=[]))
    run(["ls", "-la", ".."], check=True)

    generator_init_path = inspect.getfile(exasol_sphinx_github_pages_generator)
    sources_dir = f"{os.path.dirname(generator_init_path)}/templates"
    target_path = Path(f"{target_worktree}/_sources")
    if not target_path.is_dir():
        target_path.mkdir(parents=True)
    shutil.copy(f"{sources_dir}/index_template.html.jinja2",
                f"{target_path}/index_template.jinja.txt")

    target_path = Path(f"{target_worktree}/_static")

    static_dir = f"{os.path.dirname(generator_init_path)}/_static"
    if not Path(static_dir).is_dir():
        shutil.copytree(static_dir, target_path)


