import os
from contextlib import contextmanager
from pathlib import Path
import sys
import glob
import shutil
from subprocess import run

import importlib_resources
from jinja2 import Environment, PackageLoader, select_autoescape
import inspect
from typing import List, Dict, Generator, Union, Any
from importlib_resources import files

import exasol_sphinx_github_pages_generator


@contextmanager
def change_and_restore(directory: Path):
    old_working_dir = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(old_working_dir)


def find_index(target_worktree: Path, source_branch: str) -> Path:
    """
    For the given source_branch find the index.html file in its documentation files,
    and return its path. Aborts if there are more or less than exactly one (1) index.html file.
    :param target_worktree: Worktree/path all generated project documentation is put into.
    :param source_branch: Name of the branch the documentation should be searched for.
    :return: Path pointing at found index.html file
    """
    with change_and_restore(target_worktree):
        index_list = glob.glob(f'{source_branch}/**/index.html', recursive=True)
        if len(index_list) != 1:
            sys.exit(inspect.cleandoc(f"""
                    Your generated documentation does not include the right amount of index.html files (1). 
                    Instead it includes {len(index_list)} in path {target_worktree}/{source_branch}
                    """))
        index_path = index_list[0]
    return Path(index_path)


def generate_release_dicts(release_list: Union[Generator[str, None, Any], List[str]], source_branch: str, target_worktree: Path) \
        -> List[Dict[str, str]]:
    """
    Given a list of releases, generate a list of dictionaries containing the name of the release, and the path to its
    documentation relative to target_worktree. The current release is titled "latest".
    :param release_list: List or Generator of release-names as strings.
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
                                       "release_path": f"{find_index(Path('.'), release)}"})
    return release_list_dicts


def get_releases(target_branch: str, target_branch_exists_remote: bool, source_branch: str, target_worktree: Path) \
        -> List[Dict[str, str]]:
    """
    Find all releases already documented in target_branch, and return them with the path pointing to their index.html
    file. Additionally, also return the current release and index.html-file-path. The current release is titled "latest".
    Found releases are returned as a list of dictionaries.
    In order to find the releases in the target_branch, it is checked out in an additional temporary worktree.
    Takes the root-directory name for each release and returns it.
    Gives bad results if branch names contain slashes, because these result in nested directories instead of
    one directory, therefore only the first part of the branch name is found by this function.
    Please remove slashes from branch names before using them to generate the root directory for your
    release-documentation.

    :param target_branch: The branch the generated documentation should end up on.
    :param target_branch_exists_remote: Bool representing whether the target_branch already exist in the remote
        repository.
    :param source_branch: The branch we are currently generating the documentation for.
    :param target_worktree: Worktree/path all generated project documentation is put into.
    :return: List of dictionaries containing the release name and path to its index.html file.
    """
    if target_branch_exists_remote:
        find_index_worktree_path = Path(os.getcwd()) / "target-branch-for-index/"
        completed = run(["git", "worktree", "add", find_index_worktree_path, target_branch, "--force"])
        if completed.returncode != 0:
            sys.exit(inspect.cleandoc(f"""checking out target_branch {target_branch} failed, although given 
                     'target_branch_exists_remote' was 'True'. Check if target_branch really exists on remote?
                     received Error:
                        returncode: {completed.returncode},
                        stderr: {completed.stderr},
                        stdout: {completed.stdout}"""
                     ))
        with change_and_restore(find_index_worktree_path):
            current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                                 check=True)
            print(f"current_branch {current_branch.stdout} in find_index_worktree_path {find_index_worktree_path}.")
            release_list = (name for name in os.listdir(find_index_worktree_path)
                            if os.path.isdir(os.path.join(find_index_worktree_path, name)))

            release_list_dicts = generate_release_dicts(release_list, source_branch, target_worktree)
            run(["git", "worktree", "remove", "--force", find_index_worktree_path], check=True)

    else:
        release_list_dicts = generate_release_dicts([], source_branch, target_worktree)

    return release_list_dicts


def copy_importlib_resources_file(src_file: importlib_resources.abc.Traversable, target_file: Path) -> None:
    """
    Uses a given source path "src_file" given as an importlib_resources.abc.Traversable to copy the file it points to
    into the destination denoted by target_path.
    :param src_file: Location of the file to be copied, given as importlib_resources.abc.Traversable.
    :param target_file: Path object the location file should be copied to.
    """
    content = src_file.read_bytes()
    with open(target_file, "wb") as file:
        file.write(content)


def copy_importlib_resources_dir_tree(src_path: importlib_resources.abc.Traversable, target_path: Path) -> None:
    """
    Uses a given source path "scr_path" given as an importlib_resources.abc.Traversable to copy all files/directories
    in the directory tree whose root is scr_path into target_path.
    :param src_path: Root of the dir tree to be copied, given as importlib_resources.abc.Traversable.
    :param target_path: Path object the dir tree should be copied to.
    """
    if not target_path.is_dir():
        target_path.mkdir()
    for file in src_path.iterdir():
        file_target = target_path / file.name
        if file.is_file():
            copy_importlib_resources_file(file, file_target)
        else:
            file_target.mkdir()
            copy_importlib_resources_dir_tree(file, file_target)


def generate_release_index(target_branch: str, target_worktree: Path,
                           source_branch: str, target_branch_exists_remote: bool) -> None:
    """
    Generates a release index file from a given target_branch into the target_worktree.
    Uses the "furo" theme for the generated release index file.
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
                 f" before calling generate_release_index.")
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

    generator_init_path = files(exasol_sphinx_github_pages_generator)
    sources_dir = generator_init_path / "templates"
    target_path = Path(f"{target_worktree}/_sources")
    copy_importlib_resources_dir_tree(sources_dir, target_path)

    target_path = Path(f"{target_worktree}/_static")
    static_dir = generator_init_path / "_static"
    if not Path(target_path).is_dir():
        copy_importlib_resources_dir_tree(static_dir, target_path)



