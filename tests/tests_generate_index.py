import sys

import pytest
from subprocess import run
from tempfile import TemporaryDirectory, NamedTemporaryFile
import os
import re
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape

import exasol_sphinx_github_pages_generator.deploy_github_pages as deploy_github_pages
from helper_test_functions import remove_branch
from fixtures import setup_test_env, setup_index_tests_target_branch, setup_index_tests_integration
from exasol_sphinx_github_pages_generator.generate_index import find_index, get_meta_lines, \
    get_footer, get_releases, generate_release_dicts, alter_meta_line, gen_index


with open(
        "./test_src/correct_index_file_main_branch.html") as file:
    correct_content = file.readlines()
with open("./test_src/meta_lines_correct") as file:
    correct_meta_lines = file.readlines()

with open("./test_src/input_index.html") as file:
    input_index_html = file.readlines()

correct_releases = [{'release': 'latest', 'release_path': 'branch_name/index.html'},
                     {'release': 'test', 'release_path': 'test/index.html'},
                     {'release': 'feature-some_dir', 'release_path': 'feature-some_dir/index.html'}]


correct_footer =('<div class="footer">'
                    '&copy;2021, Exasol.'
                    '|'
                    'Powered by <a href="http://sphinx-doc.org/">Sphinx 3.5.4</a>'
                    '&amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>'
                    '|'
                    '<a href="_sources/index_template.jinja.txt"'
                    'rel="nofollow">Page source</a>'
                    '</div>')

env = Environment(
        loader=PackageLoader("exasol_sphinx_github_pages_generator"),
        autoescape=select_autoescape()
    )
template = env.get_template("index_template.html.jinja2")

def test_find_index():
    source_branch = "main"
    with TemporaryDirectory("dir") as tempdir:
        Path(f"{tempdir}/{source_branch}/").mkdir(parents=True)
        with open(f"{tempdir}/{source_branch}/index.html", "w+") as i_file:
            for line in input_index_html:
                i_file.write(line)
            i_file.flush()
        index_path = find_index(Path(tempdir), source_branch)
        assert index_path == (f"{source_branch}/index.html")


def test_get_meta_lines():
    source_branch = "main"
    import subprocess
    subprocess.run(["ls"])
    meta = get_meta_lines(Path("./test_src/input_index.html"), source_branch)
    print(meta)
    for i in range(0, len(correct_meta_lines)):
        assert correct_meta_lines[i].strip() == meta[i].strip()


def test_get_meta_lines_no_meta_lines():
    source_branch = "main"
    input_path = NamedTemporaryFile()
    with open(input_path.name, "w") as meta_input:
        meta_input.write("These are\n some lines \n of text. \n "
                         "not including any \n lines detected by \n get_meta_lines\n")
        meta = get_meta_lines(Path(input_path.name), source_branch)
    assert meta == []


def test_get_meta_lines_wrong_path():
    wrong_path = Path("./test_src/this_is_not_an_existing_file")
    with pytest.raises(FileNotFoundError) as e:
        get_meta_lines(wrong_path, "main")
    e.match(str(wrong_path))


def test_get_meta_lines_no_source_branch():
    with pytest.raises(ValueError) as e:
        get_meta_lines(Path("./test_src/correct_index_file_main_branch.html"), "")
    e.match("No source branch was given to get_meta_lines")


def test_render_template_no_meta_lines():
    meta = []
    releases = correct_releases
    footer = correct_footer

    index_content = template.render(meta_list=meta, releases=releases, footer=footer)


def test_generate_release_dicts_include_sources():
    source_branch = "branch_name"
    target_worktree = "t_worktree"
    target_branch = "t_branch"
    release_list_target = [("test", target_branch), ("feature-some_dir", target_branch), ("_sources", target_branch)]
    release_list = [item[0] for item in release_list_target]
    others = [(source_branch, target_worktree)]
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        for item in release_list_target + others:
            Path(f"{item[1]}/{item[0]}").mkdir(parents=True)
            open(f"{item[1]}/{item[0]}/index.html", 'a').close()
        target_worktree = Path(target_worktree).absolute()
        os.chdir(target_branch)
        releases = generate_release_dicts(release_list, source_branch, Path(target_worktree).absolute())

    assert releases == correct_releases


def test_generate_release_dicts_include_source_branch():
    source_branch = "branch_name"
    target_worktree = "t_worktree"
    target_branch = "t_branch"
    release_list_target = [("test", target_branch), ("feature-some_dir", target_branch), (source_branch, target_branch)]
    release_list = [item[0] for item in release_list_target]
    others = [("_sources", target_branch), (source_branch, target_worktree)]

    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        for item in release_list_target + others:
            print(item)
            Path(f"{item[1]}/{item[0]}").mkdir(parents=True)
            open(f"{item[1]}/{item[0]}/index.html", 'a').close()
        target_worktree = Path(target_worktree).absolute()
        os.chdir(target_branch)
        releases = generate_release_dicts(release_list, source_branch, target_worktree)

    assert releases == correct_releases


def test_generate_release_dict_include_only_unkown_dirs():
    source_branch = "branch_name"
    target_worktree = "t_worktree"
    target_branch = "t_branch"
    release_list_target = [("test", target_branch), ("feature-some_dir", target_branch)]
    release_list = [item[0] for item in release_list_target]
    others = [("_sources", target_branch), (source_branch, target_worktree)]
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        for item in release_list_target + others:
            print(item)
            Path(f"{item[1]}/{item[0]}").mkdir(parents=True)
            open(f"{item[1]}/{item[0]}/index.html", 'a').close()

        target_worktree = Path(target_worktree).absolute()
        os.chdir(target_branch)
        releases = generate_release_dicts(release_list, source_branch, target_worktree)
    assert releases == correct_releases


def test_generate_release_dicts_no_releases():
    source_branch = "branch_name"
    target_worktree = "t_worktree"
    target_branch = "t_branch"
    release_list = []
    others = [("_sources", target_branch), (source_branch, target_worktree)]
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        for item in release_list + others:
            Path(f"{item[1]}/{item[0]}").mkdir(parents=True)
            open(f"{item[1]}/{item[0]}/index.html", 'a').close()
        target_worktree = Path(target_worktree).absolute()
        os.chdir(target_branch)
        releases = generate_release_dicts(release_list, source_branch, target_worktree)

    assert releases == [{'release':  "latest", 'release_path': f'{ source_branch}/index.html'}]


def test_get_releases(setup_index_tests_target_branch):
    target_branch, source_branch = setup_index_tests_target_branch

    Path(f"target_worktree/{source_branch}/").mkdir(parents=True)
    open(f"target_worktree/{source_branch}/index.html", 'a').close()
    releases = get_releases(target_branch, True, source_branch, Path(f"target_worktree").absolute())
    assert releases == [{'release': "latest", 'release_path': f'{source_branch}/index.html'},
                        {'release': 'feature-some-feature', 'release_path': 'feature-some-feature/index.html'},
                        {'release': 'another_branch', 'release_path': 'another_branch/index.html'}]


def test_get_releases_no_target_branch():
    target_branch, source_branch = "t_branch", "s_branch"
    with TemporaryDirectory() as dir:

        Path(f"{dir}/target_worktree/{source_branch}/").mkdir(parents=True)
        open(f"{dir}/target_worktree/{source_branch}/index.html", 'a').close()
        releases = get_releases(target_branch, False, source_branch, Path(f"{dir}/target_worktree"))
        print(releases)
        assert releases == [{'release': "latest", 'release_path': f'{source_branch}/index.html'}]


def test_get_releases_empty_target_branch(): #todo would need empty test branch or generation and deletion of empty test branch
    pass


# this test fails locally for me if run with the other test with "FileNotFoundError" for "test_src/input_index.html".
# it succeeds if run as a single test or in the CI.
# cwd :
    # /home/marlene/PycharmProjects/sphinx-github-pages-generator/tests                          single
    # /tmp/pytest-of-marlene/pytest-74/test_get_releases0/sphinx-github-pages-generator-test     all
def test_get_footer():
    index_path = Path("test_src/input_index.html")
    footer = get_footer(index_path)
    feet = "".join(map(lambda foot: (foot.replace("\n", "")).strip(), footer))

    assert feet.strip() == ('<div class="footer">'
                            '&copy;2021, Exasol.'
                            '|'
                            'Powered by <a href="http://sphinx-doc.org/">Sphinx 3.5.4</a>'
                            '&amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>'
                            '|'
                            '<a href="_sources/index_template.jinja.txt"'
                            'rel="nofollow">Page source</a>'
                            '</div>')


def test_no_footer():
    with NamedTemporaryFile("a+") as i_file:
        i_file.write("some text")
        i_file.flush()
        index_path = Path(i_file.name)
        footer = get_footer(index_path)
        feet = "".join(map(lambda foot: (foot.replace("\n", "")).strip(), footer))
    assert feet.strip() == ''


def test_alter_mea_line():
    source_branch = "source_branch"
    original_lines = [
        'some text ="_static/doctools.js" some more text ',
        'some text ="_static/doctools.js" some more text containing "quotes" ',
        'some text containing "quotes" ="_static/doctools.js" some more text ',
        'some text containing "quotes" ="_static/doctools.js" some more text containing "quotes" ',
        'some text containing "quotes" ="another_dict/_static/doctools.js" some more text containing "quotes" ',
        'just some text not containing the keyword',
        'just some text not containing the keyword but with "quotes"',
        '"this whole line is in quotes"',
        '',
        ' this text contains "_static" multiple times because "_static" is a keyword'
    ]
    correct_altered_lines =[
        'some text ="source_branch/_static/doctools.js" some more text ',
        'some text ="source_branch/_static/doctools.js" some more text containing "quotes" ',
        'some text containing "quotes" ="source_branch/_static/doctools.js" some more text ',
        'some text containing "quotes" ="source_branch/_static/doctools.js" some more text containing "quotes" ',
        'some text containing "quotes" ="source_branch/another_dict/_static/doctools.js" some more text containing "quotes" ',
        'just some text not containing the keyword',
        'just some text not containing the keyword but with "quotes"',
        '"this whole line is in quotes"',
        '',
        ' this text contains "source_branch/_static" multiple times because "source_branch/_static" is a keyword'
    ]
    altered_lines = [alter_meta_line(original_line, source_branch) for original_line in original_lines]
    assert altered_lines == correct_altered_lines


def test_gen_index(setup_index_tests_integration):
    target_branch, source_branch, target_branch_exists, target_worktree = setup_index_tests_integration
    gen_index(target_branch, Path(target_worktree), source_branch, target_branch_exists_remote = True)

    with open(f"{target_worktree}/index.html") as index_file:
        index_content = index_file.readlines()
    for i in range(0, len(correct_content)):
        assert correct_content[i].strip() == index_content[i].strip()


def test_abort_gen_index_wrong_target_branch(setup_index_tests_integration):
    _, source_branch, target_branch_exists, target_worktree = setup_index_tests_integration
    target_branch_exists_remote = True
    target_branch_wrong = "not_an_existing_branch"
    with pytest.raises(SystemExit) as e:
        gen_index(target_branch_wrong, Path(target_worktree), source_branch, target_branch_exists_remote = True)

    regex = r"""checking out target_branch .* failed, although given.*
                     'target_branch_exists_remote' was 'True'. Check if target_branch really exists on remote?.*
                     received Error:.*
                        returncode: .*
                        stderr: .*
                        stdout: .*"""
    comp_regex = re.compile(regex, flags=re.DOTALL)
    assert e.match(comp_regex)
    assert e.type == SystemExit


def test_abort_gen_index_worktree_not_a_dir(setup_index_tests_integration):
    target_branch, source_branch, target_branch_exists, _ = setup_index_tests_integration
    not_target_worktree = "not_a_dir"
    with pytest.raises(FileNotFoundError) as e:
        gen_index(target_branch, Path(not_target_worktree), source_branch, target_branch_exists_remote = True)

    assert e.match(f"No such file or directory: '{not_target_worktree}'")
    assert e.type == FileNotFoundError

def test_abort_gen_index_source_branch_not_exists(setup_index_tests_integration):
    target_branch, _, target_branch_exists, target_worktree = setup_index_tests_integration
    not_source_branch = "not_a_branch"
    with pytest.raises(SystemExit) as e:
        gen_index(target_branch, Path(target_worktree), not_source_branch, target_branch_exists_remote = True)

    assert e.match(f".* not currently checked out. Please Check out branch .*"
                   f" before calling gen_index.")
    assert e.type == SystemExit

def test_gen_index_target_branch_not_exists(setup_index_tests_integration):
    _, source_branch, target_branch_exists, target_worktree = setup_index_tests_integration
    target_branch_new = "new_target"
    gen_index(target_branch_new, Path(target_worktree), source_branch, target_branch_exists_remote = False)

def test_gen_index_abort_missing_index_file(setup_test_env):
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch-"
    with TemporaryDirectory("dir") as tempdir:
        with pytest.raises(SystemExit) as e:
            gen_index(target_branch, tempdir, source_branch, target_branch_exists_remote=True)

        regex = r""".*Your generated documentation does not include the right amount of index.html files.*Instead it includes 0 in path.*"""
        comp_regex = re.compile(regex, flags=re.DOTALL)
        assert e.match(comp_regex)


def test_index_no_existing_releases(setup_test_env): #todo move these tests?
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch-"
    remove_branch(target_branch)

    deploy_github_pages.deploy_github_pages(["--target_branch", target_branch,
                                             "--source_branch", source_branch,
                                             "--module_path", "../test_package", "../another_test_package"])
    index_exists = run(["git", "ls-tree", "-d", f"origin/{target_branch}", "index.html"],
                                    capture_output=True, text=True, check=True)
    assert index_exists.returncode == 0
    index_source_exists = run(["git", "ls-tree", "-d", f"origin/{target_branch}", "_sources/index_template.jinja"],
                                    capture_output=True, text=True, check=True)
    assert index_source_exists.returncode == 0

    run(["git", "checkout", target_branch], check=True)
    with open("index.html") as index_file:
        index_content = index_file.readlines()
    for i in range(0, len(correct_content)):
        assert correct_content[i].strip() == index_content[i].strip()
    remove_branch(target_branch)


def test_exsiting_releases(setup_test_env):
    # - replaces index.html
    #todo first add index.html to test-branch
    pass


