import subprocess
import sys
from pathlib import Path
from subprocess import run
import shutil
import os


# TODO remove debug outputs
# todo add typing, docu comments

class GithubPagesDeployer:
    def __init__(self, source_dir, module_path, target_branch, push_origin, push_enabled, source_branch,
                 current_commit_id, tempdir):
        self.source_dir = source_dir
        self.module_path = module_path
        self.target_branch = target_branch
        self.push_origin = push_origin
        self.push_enabled = push_enabled
        self.source_branch = source_branch
        self.current_commit_id = current_commit_id.stdout
        self.worktree_paths = {"target_worktree": tempdir + "/worktrees/worktree_target",
                              "source_worktree": tempdir + "/worktrees/worktree_source"}
        self.build_dir = tempdir + "/build"
        self.intermediate_dir = tempdir + "/intermediate"
        self.staged_changes = False

    def check_out_source_branch_as_worktree(self,
                                            source_branch_commit_id):
        source_branch_exists_remote = run(["git", "show-branch", f"remotes/origin/{self.source_branch}"],
                                          capture_output=True, text=True)
        print("source_branch_exists_remote : " + str(source_branch_exists_remote))
        if source_branch_exists_remote.returncode == 0:
            try:
                # "If <branch> does exist, it will be checked out in the new working tree, if it’s not checked out
                # anywhere else, otherwise the command will refuse to create the working tree (unless --force is used)."
                run(["git", "worktree", "add", self.worktree_paths["source_worktree"],
                     self.source_branch, "--force"], check=True)
                print(f"Successfully added new temp worktree for source branch {self.source_branch}, "
                      f"and checked out (Local or stashed changes will be ignored in this build).")#todo check if stashed changes exist, abort if yes?
                os.chdir(f"{self.worktree_paths['source_worktree']}/doc")
                current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                                     check=True)
                print("new current_branch/detected source branch : " + str(current_branch.stdout))
            except subprocess.CalledProcessError:
                sys.exit("Problem with adding worktree for source")

        elif source_branch_commit_id.returncode == 0:
            sys.exit("Source branch exists locally, but not on remote, and source branch is not current branch."
                     "Please push your source branch to remote.")
        else:
            sys.exit(f"source branch {self.source_branch} does not exist")

    def detect_or_verify_source_branch(self):
        current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
        print(current_branch.stdout)
        print(f"source branch before detect: {self.source_branch}")
        if self.source_branch == "":
            if current_branch.stdout == "":
                sys.exit("Abort. Could not detect current branch and no source branch given.")
            print(f"No source branch given. Using Current branch {current_branch.stdout[:-1]} as source.")
            self.source_branch = current_branch.stdout[:-1]

        source_branch_commit_id = run(["git", "rev-parse", self.source_branch], capture_output=True, text=True)
        # the [:-1] removes the newline from the output
        if current_branch.stdout[:-1] != self.source_branch:
            print("Current branch is not source branch. Need to switch branches")
            self.check_out_source_branch_as_worktree(source_branch_commit_id)
            return
        if source_branch_commit_id.stdout != self.current_commit_id:
            sys.exit(f"Abort. Current commit id {self.current_commit_id} and commit id of source "
                     f"branch {source_branch_commit_id} are not equal. Please commit your changes.")
        print(f"Detected source branch {self.source_branch}")

    def checkout_target_branch_as_worktree(self):
        target_branch_exists = run(["git", "show-branch", f"remotes/origin/{self.target_branch}"], capture_output=True,
                                   text=True)
        print("target_branch_exists : " + target_branch_exists.stdout + str(
            target_branch_exists.returncode) + target_branch_exists.stderr)
        if target_branch_exists.returncode == 0:
            print(f"Create worktree from existing branch {self.target_branch}")
            run(["git", "worktree", "add", self.worktree_paths["target_worktree"], self.target_branch], check=True)
        else:
            print(f"Create worktree from new branch {self.target_branch}")
            # We need to create the worktree directly with the TARGET_BRANCH,
            # because every other branch could be already checked out
            run(["git", "branch", self.target_branch], check=True)
            run(["git", "worktree", "add", self.worktree_paths["target_worktree"], self.target_branch], check=True)
            currentworkdir = os.getcwd()
            print(currentworkdir)
            os.chdir(self.worktree_paths["target_worktree"])
            # We need to set the TARGET_BRANCH to the default branch
            # The default branch from github for pages is gh-pages, but you can change that.
            # Not using the default branch actually has benefits, because the branch gh-pages enforces some things.
            # We use github-pages/main with separate history for Github Pages,
            # because automated commits to the main branch can cause problems and
            # we don't want to mix the generated documentation with sources. todo currently it mixes
            # Furthermore, Github Pages expects a certain directory structure in the repository
            # which we only can provide with a separate history.
            gh_pages_root_branch = "github-pages/root"  # is needed to temporarly create a new root commit
            gh_pages_main_branch = "github-pages/main"
            gh_pages_main_branch_exists = run(
                ["git", "show-ref", f"refs/heads/{self.push_origin}/{gh_pages_main_branch}", "||", "echo"], capture_output=True,
                text=True)
            if gh_pages_main_branch_exists.returncode == 0:
                run(["git", "reset", "--hard", f"{self.push_origin}/{gh_pages_main_branch}"], check=True)
            else:
                print(f"Creating a new empty root commit for the Github Pages in root branch {gh_pages_root_branch}.")
                run(["git", "checkout", "--orphan", gh_pages_root_branch], check=True)
                run(["git", "reset", "--hard"], check=True)
                run(["git", "commit", "--no-verify", "--allow-empty", "-m", "'Initial empty commit for Github Pages'"],
                    check=True)
                print(f"Reset target branch {self.target_branch} to root branch {gh_pages_root_branch}")
                run(["git", "checkout", self.target_branch], check=True)
                run(["git", "reset", "--hard", gh_pages_root_branch], check=True)
                print(f"Delete root branch {gh_pages_root_branch}")
                run(["git", "branch", "-D", gh_pages_root_branch], check=True)
            os.chdir(currentworkdir)

    def build_and_copy_documentation(self):
        print("Build with sphinx")
        currentworkdir = os.getcwd()
        print("currentworkdir :" + currentworkdir)
        os.chdir(currentworkdir)
        run(["ls", "-la", currentworkdir], check=True)
        # automatically generates Sphinx sources inside the "api" directory that document
        # the package found in "module_path"
        # -T: not table of contents
        # -e: put documentation for ech module on own page
        for module in self.module_path:
            out = run(["sphinx-apidoc", "-T", "-e", "-o", "api", module])
            print(str(out))
        # Builds the Sphinx documentation. Generates html files inside "build_dir" using "source_dir"
        # -W: Turns warnings into errors
        run(["sphinx-build", "-b", "html", "-d", self.intermediate_dir, "-W", currentworkdir, self.build_dir], check=True)
        print("Generated HTML Output")
        print(f"Using html_output_dir={self.build_dir}")
        run(["ls", "-la", self.build_dir], check=True)

        output_dir = Path(f"{self.worktree_paths['target_worktree']}/{self.source_branch}")
        print(f"Using output_dir={output_dir}")
        if output_dir.exists() and output_dir.is_dir():
            print(f"Removing existing output directory {output_dir}")
            shutil.rmtree(output_dir)
        print(f"(Re)Creating output directory {output_dir}")
        output_dir.mkdir(parents=True)
        print(f"Copying HTML output {self.build_dir} to the output directory {output_dir}")
        for obj in os.listdir(self.build_dir):
            shutil.move(self.build_dir + "/" + str(obj), output_dir)
        print(f"Content of output directory {output_dir}")
        open(f"{self.worktree_paths['target_worktree']}/.nojekyll", "w").close()
        run(["ls", "-la", output_dir], check=True)

        return output_dir

    def git_commit_and_push(self, output_dir):
        currentworkdir = os.getcwd()
        print(currentworkdir)
        os.chdir(self.worktree_paths['target_worktree'])
        print(f"Current directory before commit and push {os.getcwd()}")
        print("Git commit")
        with open(f"{output_dir}/.source", "w+") as file:
            file.write(f"BRANCH={self.source_branch} \n")
            file.write(f"COMMIT_ID={self.current_commit_id}")
        run(["git", "add", "-v", "."], check=True)
        changes_exists = run(["git", "diff-index", "--quiet", "HEAD", "--"], capture_output=True, text=True)
        if 1 == changes_exists.returncode:
            print(f"committing changes because changes_exist is {changes_exists.returncode}")
            run(["git", "commit", "--no-verify", "-m",
                 f"Update documentation from source branch {self.source_branch} with commit id {self.current_commit_id}"], check=True)
            if self.push_origin != "" and self.push_enabled == "push":
                print(f"Git push {self.push_origin} {self.target_branch}")
                run(["git", "push", self.push_origin, self.target_branch], check=True)
        elif 0 == changes_exists.returncode:
            print("No changes to commit.")
        else:
            print('A Error occurred in run(["git", "diff-index", "--quiet", "HEAD", "--"],'
                  'capture_output=True, text=True)')
            print(f" changes_exists.returncode: {changes_exists.returncode}")
            print(f" changes_exists.stderr: {changes_exists.stderr}")
            print(f" changes_exists.stdout: {changes_exists.stdout}")
        os.chdir(currentworkdir)

    def clean_worktree(self, original_workdir):
        os.chdir(original_workdir)
        print(f"set workdir back to {original_workdir}")
        for text in self.worktree_paths:
            print(text)
            path = Path(self.worktree_paths[text])
            if path.exists():
                print(f"Cleanup git worktree {path}")
                run(["git", "worktree", "remove", "--force", path], check=True)
