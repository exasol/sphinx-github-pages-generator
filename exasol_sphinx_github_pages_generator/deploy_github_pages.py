import sys
from pathlib import Path
from exasol_sphinx_github_pages_generator.Parser import Parser
from tempfile import TemporaryDirectory
from subprocess import run
import shutil
import os
# TODO toml set tass correctly?
# tODO call the scipts from generator here istead of using them directly


def detect_or_verify_source_branch(source_branch, current_commit_id):
    # tODO test
    current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    if source_branch == "" :
        if current_branch.stdout == "" :
            "Abort. Could not detect current branch and no source branch given."
            # TODO throw error?
            sys.exit() # TODo status
        source_branch = current_branch
    source_branch_commit_id = run(["git", "rev-parse", source_branch], capture_output=True, text=True)
    if source_branch_commit_id.stdout != current_commit_id:
        print(f"Abort. Current commit id {current_commit_id} and commit id of source branch {source_branch_commit_id}"
              f" are not equal.")
        # TODO throw error?
        sys.exit()  # TODo status
    print(f"Detected source branch {source_branch}")
    return source_branch


def checkout_target_branch_as_worktree(target_branch, worktree, push_origin):
    target_branch_exists = run(["git", "show-branch", f"remotes/origin/{target_branch}"], capture_output=True, text=True)
    print("target_branch_exists : " + target_branch_exists.stdout + str(target_branch_exists.returncode) + target_branch_exists.stderr)
    if target_branch_exists.returncode != 0: #TODO better
        print(f"Create worktree from existing branch {target_branch}")
        run(["git", "worktree", "add", worktree, target_branch])
    else:
        print(f"Create worktree from new branch {target_branch}")
        # We need to create the worktree directly with the TARGET_BRANCH,
        # because every other branch could be already checked out
        print("dbug1")
        run(["git", "branch", target_branch])
        print("dbug2")
        run(["git", "worktree", "add", worktree, target_branch])
        currentworkdir = os.getcwd()
        print(currentworkdir)
        print(worktree)
        os.chdir(worktree)
        currentworkdir = os.getcwd()
        print(currentworkdir)
        # We need to set the TARGET_BRANCH to the default branch
        # The default branch from github for pages is gh-pages, but you can change that.
        # Not using the default branch actually has benefits, because the branch gh-pages enforces some things.
        # We use github-pages/main with separate history for Github Pages,
        # because automated commits to the main branch can cause problems and
        # we don't want to mix the generated documentation with sources.
        # Furthermore, Github Pages expects a certain directory structure in the repository
        # which we only can provide with a separate history.
        gh_pages_root_branch = "github-pages/root" # is needed to temporarly create a new root commit
        gh_pages_main_branch = "github-pages/main"
        gh_pages_main_branch_exists = run(["git", "show-ref", f"refs/heads/{push_origin}/{gh_pages_main_branch}", "||", "echo"], capture_output=True, text=True)
        if gh_pages_main_branch_exists.stdout != "":
            run(["git", "reset",  "--hard", f"{push_origin}/{gh_pages_main_branch}"])
        else:
            print(f"Creating a new empty root commit for the Github Pages in root branch {gh_pages_root_branch}.")
            run(["git", "checkout", "--orphan", gh_pages_root_branch])
            run(["git", "reset", "--hard"])
            run(["git", "commit", "--no-verify", "--allow-empty", "-m", "'Initial empty commit for Github Pages'"])
            print(f"Reset target branch {target_branch} to root branch {gh_pages_root_branch}")
            run(["git", "checkout", target_branch])
            run(["git", "reset", "--hard", gh_pages_root_branch])
            print(f"Delete root branch {gh_pages_root_branch}")
            run(["git", "branch", "-D", gh_pages_root_branch])
        # popd ?


def build_and_copy_documentation(build_dir, worktree, source_branch, source_dir):
    print("Build with sphinx")
    run(["sphinx-build", "-M", "html", source_dir, build_dir, "-W"])
    print("Generated HTML Output")
    html_output_dir = build_dir + "/html/"
    print(f"Using html_output_dir={html_output_dir}")
    #run([ls -la "$HTML_OUTPUT_DIR"])

    output_dir = Path(worktree + "/" + source_branch)
    print(f"Using output_dir={output_dir}")
    if output_dir.exists() and output_dir.is_dir():
        print(f"Removing existing output directory {output_dir}")
        shutil.rmtree(output_dir)
    print(f"(Re)Creating output directory {output_dir}")
    output_dir.mkdir(parents=True)
    print(f"Copying HTML output {html_output_dir} to the output directory {output_dir}")
    # TODO find "$HTML_OUTPUT_DIR" -mindepth 1 -maxdepth 1 -exec mv -t "$OUTPUT_DIR" -- {} +
    print(f"Content of output directory {output_dir}")

    # touch "$WORKTREE/.nojekyll"
    # run([ls -la "$OUTPUT_DIR"])
    return output_dir

def git_commit_and_push(push_origin, push_enabled, source_branch, output_dir, current_commit_id, target_branch):
    #pushd "$WORKTREE"
    print("Current directory before commit and push $PWD") #TODO
    print("Git commit")
    with open (f"{output_dir}/.source", "w+") as file:
        file.write(f"BRANCH={source_branch}")
        file.write(f"COMMIT_ID={current_commit_id}")
    run(["git", "add", "."])
    run(["git", "diff-index", "--quiet", "HEAD", "--", "||", "git", "commit", "--no-verify", "-m", f"Update documentation from source branch {source_branch} with commit id {current_commit_id}"])
    if push_origin != "" and push_enabled == "push":
        print(f"Git push {push_origin} {target_branch}")
        run(["git", "push", push_origin, target_branch])
    #popd

def deploy_github_pages(argv):
    #TODO add errors for wrong arguments?
    #sys.argv[1:]
    args = Parser(argv).args
    script_dir = Path(__file__).parent
    source_dir = script_dir.joinpath("doc") # this is where the docs are. TODO make dynamic
    print(source_dir)
    print("Commandline parameter")
    print("TARGET_BRANCH=" + args.target_branch)
    print("PUSH_ORIGIN=" + args.push_origin)
    print("PUSH_ENABLED=" + args.push_enabled)
    print("SOURCE_BRANCH=" + args.source_branch + "\n")

    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True) # TODO gets id of THIS repo. change to other repo(everywhere).
    with TemporaryDirectory() as tempdir:
        worktree = tempdir + "/worktree"
        build_dir = tempdir + "/build"

        print("Using following Directories:")
        print("TMP=" + tempdir)
        print("WORKTREE=" + worktree)
        print("BUILD_DIR=" + build_dir)
        print("CURRENT_COMMIT_ID=" + current_commit_id.stdout + "\n")

        source_branch = detect_or_verify_source_branch(args.source_branch, current_commit_id.stdout)
        checkout_target_branch_as_worktree(args.target_branch, worktree, args.push_origin)
        output_dir = build_and_copy_documentation(build_dir, worktree, source_branch, source_dir)
        git_commit_and_push(args.push_origin, args.push_enabled, source_branch, output_dir, current_commit_id.stdout, args.target_branch)

