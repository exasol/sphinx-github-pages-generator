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
    if "_sources" in release_list:
        release_list.remove("_sources")
    release_list_dicts = [{"release": "latest",
                           "release_path": f"{find_index(target_worktree, source_branch)}"}]
    for release in release_list:
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
    cwd = os.getcwd()
    if target_branch_exists_remote:
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
        release_list = [name for name in os.listdir(find_index_worktree_path)
                        if os.path.isdir(os.path.join(find_index_worktree_path, name))]

        release_list_dicts = generate_release_dicts(release_list, source_branch, target_worktree)
        run(["git", "worktree", "remove", "--force", find_index_worktree_path], check=True)

        os.chdir(cwd)
    else:
        release_list_dicts = generate_release_dicts([], source_branch, target_worktree)

    return release_list_dicts


def find_quote_pos(static_pos: int, double_quote_list: List[int]) -> int:
    """
    Given an integer and a sorted lists of integers, returns the entry in
    the second list closest to but smaller than the given integer.
    :param static_pos: Integer the matching entry from the double_quote_list should be found for.
    :param double_quote_list: Sorted list of integers to be searched.
    :return: Integer from the input list closest to but smaller than the input integer.
    """
    found_pos = 0
    for pos in double_quote_list:
        if pos < static_pos:
            found_pos = pos
        elif pos > static_pos:
            break
    return found_pos


def alter_meta_line(original_line: str, source_branch: str) -> str:
    """
    Given a input string original_line and a insert string source_branch, inserts the insert string directly behind
    double quotes closest from the left to the keyword "_static" for each occurrence of the keyword in the input string.
    So
        'this text contains "_static" multiple times because "_static" is a keyword and can
        be used in context "quotes" ="another_dict/_static/doctools.js"'
    will be turned into
        'this text contains "source_branch/_static" multiple times because "source_branch/_static" is a keyword'
        and can be used in context "quotes" ="source_branch/another_dict/_static/doctools.js"'
    :param original_line: String that should be changed to include "source_branch".
    :param source_branch: string that should be inserted before "_static".
    :return: altered input string with the inclusion of "source_branch".
    """
    static_position_list = [m.start() for m in re.finditer("_static", original_line)]
    double_quote_list = [m.start() for m in re.finditer('"', original_line)]
    new_line = original_line
    # find where new path needs to be inserted
    quote_pos = [find_quote_pos(static_pos, double_quote_list) for static_pos in static_position_list]
    # insert in reverse order, so the positions don't need to be adjusted after each insertion
    for pos in quote_pos[::-1]:
        new_line = new_line[:pos+1] + f'{source_branch}/' + new_line[pos+1:]
    return new_line


def get_meta_lines(index_path: Path, source_branch: str) -> List[str]:
    """
    Given the path to a file, reads each line of the file, and extracts meta_lines. Aborts if source_branch is an
    empty string. If a meta_line contains the
    keyword "_static", the given source_branch string is added to the line using the "alter_meta_line" function.

    This is done because Sphinx puts all style sheets or script files for themes in the "_static"
    directory inside the build-output directory. We want to use these to make the release-index the
    same/similar style as the rest of the documentation.
    So we steal the lines describing them from the source-branch/index.html,
    but since the new index.html is in another directory, we need to adjust the paths.

    Meta_lines are defined as lines containing the keywords "_static" or "<meta".
    :param index_path: Path to a file to be read.
    :param source_branch: String to be inserted into the meta_lines.
    :return: List of strings containing all extracted and altered meta_lines.
    """
    print("get_meta_lines")
    if not source_branch:
        raise ValueError("No source branch was given to get_meta_lines")
    with open(index_path) as file:
        meta_lines = []
        for line in file.readlines():
            if "_static" in line or "<meta" in line:
                line = alter_meta_line(line, source_branch)
                meta_lines.append(line)
    return meta_lines


def get_footer(index_path: Path) -> List[str]:
    """
    Given the path to a file, reads each line of the file, and extracts the footer which Sphinx generates if it exists.
    We want to use this footer to make the release-index page of a similar style as the rest of the documentation.
    So we steal the lines describing tefooter from source-branch/index.html.
    We need to adjust the paths ponting to the source for this file. Since it is a new file.
    Ths footer is found by:
        - Starts with line '<div class="footer">'
        - All opened divs after this line have to be closed. If this is the case, it is assumed the last line
        of the footer is found.

    :param index_path: Path to the file the footer should be searched in.
    :return: List of all found footer-lines as strings.
    """
    print("get_footer")
    lines = []
    open_divs = 0
    with open(index_path) as file:
        while True:
            line = file.readline()
            if line == "":
                break
            if '<div class="footer">' in line:
                lines.append(line)
                open_divs += 1
                break

        while open_divs > 0:
            line = file.readline()
            if '<a href="_sources/index.rst.txt"' in line:
                lines.append(f'<a href="_sources/index_template.jinja.txt"')
            else:
                lines.append(line)
            if "<div" in line:
                open_divs += 1
            if "</div>" in line:
                open_divs -= 1
    return lines


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
    index_path = find_index(target_worktree, simple_source_branch_name)
    meta = get_meta_lines(target_worktree.joinpath(index_path), simple_source_branch_name)
    releases = get_releases(target_branch, target_branch_exists_remote, simple_source_branch_name, target_worktree)
    footer = get_footer(target_worktree.joinpath(index_path))
    with open(f"{target_worktree}/index.html", "w+") as file:
        file.write(template.render(meta_list=meta, releases=releases, footer=footer))
    run(["ls", "-la", ".."], check=True)

    generator_init_path = inspect.getfile(exasol_sphinx_github_pages_generator)
    sources_dir = f"{os.path.dirname(generator_init_path)}/templates"
    target_path = Path(f"{target_worktree}/_sources")
    if not target_path.is_dir():
        target_path.mkdir(parents=True)
    shutil.copy(f"{sources_dir}/index_template.html.jinja2",
                f"{target_path}/index_template.jinja.txt")
