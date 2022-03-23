import os
from pathlib import Path
import sys
import glob
import re
import shutil
from subprocess import run
from jinja2 import Environment, PackageLoader, select_autoescape
import inspect
import exasol_sphinx_github_pages_generator

# todo comments, typehints
def find_index(target_worktree):
    cwd = os.getcwd()
    os.chdir(target_worktree)
    index_list = glob.glob('*/index.html')
    print(f"index_list : {index_list}")
    if len(index_list) != 1:
        sys.exit(f"""
                Your generated documentation does not include the right amount of index.html files (1).
                """)
    index_path = target_worktree.joinpath(index_list[0]) # todo just take the one closest to root if multiple?
    os.chdir(cwd)
    return index_path


def get_releases(targen_branch: str, target_branch_exists_remote, source_branch):
    cwd = os.getcwd()
    release_list = []
    if target_branch_exists_remote:
        find_index_worktree_path = os.path.join(cwd, "target-branch-for-index")
        run(["git", "worktree", "add", find_index_worktree_path,
             targen_branch, "--force"], check=True)
        # change into documentation source dir
        os.chdir(find_index_worktree_path)
        current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                             check=True)
        print(f"current_branch {current_branch} in find_index_worktree_path {find_index_worktree_path}.")

        release_list = [name for name in os.listdir(find_index_worktree_path)
                        if os.path.isdir(os.path.join(find_index_worktree_path, name))]
        print(f"release_list {release_list}")
        run(["git", "worktree", "remove", "--force", find_index_worktree_path], check=True)
    release_list_dicts = []
    for release in release_list:
        release_list_dicts.append({"release": release, "release_path": f"{release}/index.html"}) #todo use find index here?
    if source_branch not in release_list:
        release_list_dicts.append({"release": source_branch, "release_path": f"{source_branch}/index.html"})
    os.chdir(cwd)
    print(f"release_list_dicts {release_list_dicts}")
    return release_list_dicts


def find_quote_pos(static_pos, double_quote_list):
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


def alter_meta_line(original_line, source_branch):
    static_position_list = [m.start() for m in re.finditer("_static", original_line)]
    double_quote_list = [m.start() for m in re.finditer('"', original_line)]
    new_line = original_line
    for static_pos in static_position_list:
        quote_pos = find_quote_pos(static_pos, double_quote_list)
        new_line = original_line[:quote_pos+1] + f'{source_branch}/' + original_line[quote_pos+1:]
    return new_line


def get_meta_lines(index_path, source_branch):
    print("get_meta_lines")
    with open(index_path) as file:
        meta_lines = []
        for line in file.readlines():
            if "_static" in line or "<meta" in line:
                line = alter_meta_line(line, source_branch)
                meta_lines.append(line)
    print(meta_lines)
    return meta_lines


def get_footer(index_path):
    print("get_footer")
    lines = []
    open_divs = 0
    with open(index_path) as file:
        while True:
            line = file.readline()
            if '<div class="footer">' in line:
                lines.append(line)
                open_divs += 1
                break

        while open_divs > 0:
            line = file.readline()
            lines.append(line)

            if '<a href="_sources/index.rst.txt"' in line:
                lines.append(f'<a href="_sources/index_template.html.jinja2')
            if "<div" in line: #todo count how many per line?
                open_divs += 1
            if "</div>" in line: #todo count how many per line?
                open_divs -= 1
    print(lines)
    return lines


def gen_index(targen_branch: str, target_worktree: Path, source_branch, target_branch_exists_remote):

    env = Environment(
        loader=PackageLoader("exasol_sphinx_github_pages_generator"),
        autoescape=select_autoescape()
    )
    template = env.get_template("index_template.html.jinja2")

    index_path = find_index(target_worktree)
    meta = get_meta_lines(index_path, source_branch)
    releases = get_releases(targen_branch, target_branch_exists_remote, source_branch)
    footer = get_footer(index_path)
    with open(f"{target_worktree}/index.html", "w+") as file:
        file.write(template.render(meta_list=meta, releases=releases, footer=footer))
    run(["ls", "-la", ".."], check=True)

    generator_init_path = inspect.getfile(exasol_sphinx_github_pages_generator)
    sources_dir = f"{os.path.dirname(generator_init_path)}/templates"
    target_path = Path(f"{target_worktree}/_sources")
    target_path.mkdir(parents=True)
    shutil.copy(f"{sources_dir}/index_template.html.jinja2",
                f"{target_path}/index_template.jinja")

