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

# todo comments, typehints


def find_index(target_worktree: Path, source_branch: str) -> Path:
    cwd = os.getcwd()
    os.chdir(target_worktree)
    index_list = glob.glob(f'{source_branch}/**/index.html', recursive=True)
    print(f"index_list : {index_list}")  # todo in actions does not find index
    if len(index_list) != 1:
        sys.exit(f"""
                Your generated documentation does not include the right amount of index.html files (1). 
                Instead it includes {len(index_list)} in path {target_worktree}
                """)
    # todo check if file is empty?
    index_path = index_list[0]#target_worktree.joinpath(index_list[0])  # todo just take the one closest to root if multiple?
    os.chdir(cwd)
    return index_path


def generate_release_dicts(release_list: List[str], source_branch: str, target_worktree: Path) \
        -> List[Dict[str, str]]:
    if "_sources" in release_list:
        release_list.remove("_sources")
    release_list_dicts = [{"release": "latest",
                           "release_path": f"{find_index(target_worktree, source_branch)}"}]
    for release in release_list:
        if release is not source_branch:
            release_list_dicts.append({"release": release,
                                       "release_path": f"{find_index('.', release)}"})

    print(f"release_list_dicts {release_list_dicts}")
    return release_list_dicts


def get_releases(target_branch: str, target_branch_exists_remote: bool, source_branch: str, target_worktree: Path) \
        -> List[Dict[str, str]]:
    cwd = os.getcwd()
    if target_branch_exists_remote:
        find_index_worktree_path = os.path.join(cwd, "target-branch-for-index/")
        completed = run(["git", "worktree", "add", find_index_worktree_path,
             target_branch, "--force"])
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

        release_list_dicts = generate_release_dicts(release_list, source_branch, target_worktree)#target_worktree)
        print(f"release_list {release_list}")
        run(["git", "worktree", "remove", "--force", find_index_worktree_path], check=True)
        os.chdir(cwd)
    else:
        release_list_dicts = generate_release_dicts([], source_branch, target_worktree)  # target_worktree)

    return release_list_dicts


def find_quote_pos(static_pos: int, double_quote_list: List[int]) -> int:
    """
    find the occurence of " closest to "_static" from the left
    :return: found position
    """
    found_pos = 0
    for pos in double_quote_list:
        if pos < static_pos:
            found_pos = pos
        elif pos > static_pos:
            break
    return found_pos


def alter_meta_line(original_line: str, source_branch: str) -> str:
    static_position_list = [m.start() for m in re.finditer("_static", original_line)]
    double_quote_list = [m.start() for m in re.finditer('"', original_line)]
    new_line = original_line
    for static_pos in static_position_list:
        quote_pos = find_quote_pos(static_pos, double_quote_list)
        new_line = original_line[:quote_pos+1] + f'{source_branch}/' + original_line[quote_pos+1:]
    return new_line


def get_meta_lines(index_path: Path, source_branch: str) -> List[str]:
    print("get_meta_lines")
    if not source_branch:
        raise ValueError("No source branch was given to get_meta_lines")
    with open(index_path) as file:
        meta_lines = []
        for line in file.readlines():
            if "_static" in line or "<meta" in line: # todo get keywords from conf.py "html_static_path"
                line = alter_meta_line(line, source_branch)
                meta_lines.append(line)
    return meta_lines


def get_footer(index_path: Path) -> List[str]:
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
            if '<a href="_sources/index.rst.txt"' in line: #todo
                lines.append(f'<a href="_sources/index_template.jinja.txt"')
            else:
                lines.append(line)
            if "<div" in line: #todo count how many per line?
                open_divs += 1
            if "</div>" in line: #todo count how many per line?
                open_divs -= 1
    print(lines)
    return lines

# todo add cleanup-trap?

# todo note somweher about slaches in branch names
def gen_index(target_branch: str, target_worktree: Path, source_branch: str, target_branch_exists_remote: bool):
    print("s_branch " + source_branch)
    local_source_branch_commit_id = run(["git", "rev-parse", source_branch], capture_output=True,
                                        text=True)
    if local_source_branch_commit_id.returncode != 0:
        sys.exit(f"{source_branch} not currently checked out. Please Check out branch {source_branch}"
                 f" before calling gen_index.")
    env = Environment(
        loader=PackageLoader("exasol_sphinx_github_pages_generator"),
        autoescape=select_autoescape()
    )
    template = env.get_template("index_template.html.jinja2")
    print(os.getcwd())
    index_path = find_index(target_worktree, source_branch)
    meta = get_meta_lines(target_worktree.joinpath(index_path), source_branch)
    releases = get_releases(target_branch, target_branch_exists_remote, source_branch, target_worktree)
    footer = get_footer(target_worktree.joinpath(index_path))
    with open(f"{target_worktree}/index.html", "w+") as file:
        file.write(template.render(meta_list=meta, releases=releases, footer=footer))
    run(["ls", "-la", ".."], check=True)

    generator_init_path = inspect.getfile(exasol_sphinx_github_pages_generator)
    sources_dir = f"{os.path.dirname(generator_init_path)}/templates"
    target_path = Path(f"{target_worktree}/_sources")
    target_path.mkdir(parents=True)
    shutil.copy(f"{sources_dir}/index_template.html.jinja2",
                f"{target_path}/index_template.jinja.txt")

