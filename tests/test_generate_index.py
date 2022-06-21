import pytest
from subprocess import run
from tempfile import TemporaryDirectory
import os
import re
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
from fixtures import setup_test_env, setup_index_tests_target_branch, setup_index_tests_integration
import exasol_sphinx_github_pages_generator.deploy_github_pages as deploy_github_pages
from helper_test_functions import remove_branch
from exasol_sphinx_github_pages_generator.generate_index import find_index, \
    get_releases, generate_release_dicts, generate_release_index
from importlib_resources import files
import exasol_sphinx_github_pages_generator

source_files = files(exasol_sphinx_github_pages_generator)
correct_index_file_main_branch = source_files / "../tests/test_src/correct_index_file_main_branch.html"
correct_content = (correct_index_file_main_branch.read_text()).splitlines(keepends=True)

correct_releases = [{'release': 'latest', 'release_path': 'branch_name/index.html'},
                     {'release': 'test', 'release_path': 'test/index.html'},
                     {'release': 'feature-some_dir', 'release_path': 'feature-some_dir/index.html'}]


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
            i_file.write("sometext \n")
            i_file.flush()
        index_path = find_index(Path(tempdir), source_branch)
        assert index_path == Path(f"{source_branch}/index.html")


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


def test_generate_release_dict_include_only_unknown_dirs():
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
    correct_releases_local = [{'release': "latest", 'release_path': f'{source_branch}/index.html'},
                        {'release': 'feature-some-feature', 'release_path': 'feature-some-feature/index.html'},
                        {'release': 'another_branch', 'release_path': 'another_branch/index.html'}]
    not_existing_releases = [release for release in releases
                             if release not in correct_releases_local]
    assert len(releases) == len(correct_releases_local) \
           and not not_existing_releases


def test_get_releases_no_target_branch():
    target_branch, source_branch = "t_branch", "s_branch"
    with TemporaryDirectory() as direc:
        os.chdir(direc)
        Path(f"{direc}/target_worktree/{source_branch}/").mkdir(parents=True)
        open(f"{direc}/target_worktree/{source_branch}/index.html", 'a').close()
        releases = get_releases(target_branch, False, source_branch, Path(f"{direc}/target_worktree"))
        print(releases)
        assert releases == [{'release': "latest", 'release_path': f'{source_branch}/index.html'}]


def test_get_releases_empty_target_branch(): #todo would need empty test branch or generation and deletion of empty test branch
    pass


def test_generate_release_index(setup_index_tests_integration):
    target_branch, source_branch, target_branch_exists, target_worktree = setup_index_tests_integration
    generate_release_index(target_branch, Path(target_worktree), source_branch, target_branch_exists_remote=True)

    with open(f"{target_worktree}/index.html") as index_file:
        index_content = index_file.readlines()

    stripped_correct_content = sorted([correct_content[i].strip()
                                       for i in range(0, len(correct_content))])
    stripped_index_content = sorted([index_content[i].strip()
                                     for i in range(0, len(index_content))])
    assert stripped_correct_content == stripped_index_content


def test_abort_generate_release_index_wrong_target_branch(setup_index_tests_integration):
    _, source_branch, target_branch_exists, target_worktree = setup_index_tests_integration
    target_branch_exists_remote = True
    target_branch_wrong = "not_an_existing_branch"
    with pytest.raises(SystemExit) as e:
        generate_release_index(target_branch_wrong, Path(target_worktree),
                               source_branch, target_branch_exists_remote)

    regex = r"checking out target_branch .* failed, although given.*'target_branch_exists_remote' was 'True'. " \
            r"Check if target_branch really exists on remote?.*received Error:.*returncode: .*stderr: .*stdout: .*"
    print(e.value)
    comp_regex = re.compile(regex, flags=re.DOTALL)
    assert e.match(comp_regex) \
           and e.type == SystemExit


def test_abort_generate_release_index_worktree_not_a_dir(setup_index_tests_integration):
    target_branch, source_branch, target_branch_exists, _ = setup_index_tests_integration
    not_target_worktree = "not_a_dir"
    with pytest.raises(FileNotFoundError) as e:
        generate_release_index(target_branch, Path(not_target_worktree), source_branch, target_branch_exists_remote = True)

    assert e.match(f"No such file or directory: '{not_target_worktree}'") \
           and e.type == FileNotFoundError

def test_abort_generate_release_index_source_branch_not_exists(setup_index_tests_integration):
    target_branch, _, target_branch_exists, target_worktree = setup_index_tests_integration
    not_source_branch = "not_a_branch"
    with pytest.raises(SystemExit) as e:
        generate_release_index(target_branch, Path(target_worktree), not_source_branch, target_branch_exists_remote = True)

    assert e.match(f".* not currently checked out. Please Check out branch .*"
                   f" before calling generate_release_index.") \
           and e.type == SystemExit

def test_generate_release_index_target_branch_not_exists(setup_index_tests_integration):
    _, source_branch, target_branch_exists, target_worktree = setup_index_tests_integration
    target_branch_new = "new_target"
    generate_release_index(target_branch_new, Path(target_worktree), source_branch, target_branch_exists_remote = False)

def test_generate_release_index_abort_missing_index_file(setup_test_env):
    source_branch = "main"
    run(["git", "checkout", source_branch], check=True)
    target_branch = "test-docu-new-branch-"
    with TemporaryDirectory("dir") as tempdir:
        with pytest.raises(SystemExit) as e:
            generate_release_index(target_branch, tempdir, source_branch, target_branch_exists_remote=False)

        regex = r".*Your generated documentation does not include the right amount of index.html files.*" \
                r"Instead it includes 0 in path.*"
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
    index_source_exists = run(["git", "ls-tree", "-d", f"origin/{target_branch}", "_sources/index_template.jinja"],
                                    capture_output=True, text=True, check=True)

    run(["git", "checkout", target_branch], check=True)
    with open("index.html") as index_file:
        index_content = index_file.readlines()

    stripped_correct_content = sorted([correct_content[i].strip()
                                       for i in range(0, len(correct_content))])
    stripped_index_content = sorted([index_content[i].strip()
                                     for i in range(0, len(index_content))])

    assert index_exists.returncode == 0 \
           and index_source_exists.returncode == 0 \
           and stripped_correct_content == stripped_index_content

    remove_branch(target_branch)


def test_exsiting_releases(setup_test_env):
    # - replaces index.html
    #todo first add index.html to test-branch
    pass


