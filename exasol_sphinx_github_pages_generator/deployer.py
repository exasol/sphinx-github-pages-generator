import subprocess
import sys
from pathlib import Path
from subprocess import run
import shutil
import os
from exasol_sphinx_github_pages_generator.generate_index import gen_index

class GithubPagesDeployer:
    """
    Builds and deploys GitHub Pages using Sphinx given a branch.

    :param source_dir: Path to the directory inside the source_branch where the index.rst and conf.py reside in.
    :param source_branch: The branch the documentation files should be generated for. Will use remote branch
           for generation. Local unpushed changes will cause program exit or be ignored.
    :param current_commit_id: CommitID of the current branch.
    :param module_path: List of modules/packages in the source_branch that should be documented.
    :param target_branch: Branch the documentation should be generated into.
    :param push_origin: origin of the Git Repository.
    :param push_enabled: Set to "push" if generated files should be pushed to the remote, otherwise set to "commit".
    :param tempdir: Path of the temporary directory this Generator runs in.

    """
    def __init__(self, source_dir: str, source_branch: str, current_commit_id: str,
                 module_path: list,
                 target_branch: str, push_origin: str, push_enabled: str,
                 tempdir: str):
        self.source_dir = source_dir
        self.source_branch = source_branch
        self.current_commit_id = current_commit_id
        self.module_path = module_path

        self.target_branch = target_branch
        self.push_origin = push_origin
        self.push_enabled = push_enabled

        self.worktree_paths = {"target_worktree": tempdir + "/worktrees/worktree_target",
                               "source_worktree": tempdir + "/worktrees/worktree_source"}
        self.build_dir = tempdir + "/build"
        self.intermediate_dir = tempdir + "/intermediate"
        self.target_branch_exists = run(["git", "show-branch", f"remotes/origin/{self.target_branch}"],
                                        capture_output=True, text=True)

    def check_out_source_branch_as_worktree(self,
                                            source_branch_exists_locally: int) -> None:
        """
        Creates a separate Git worktree for the source_branch if the existing worktree has a different branch
        currently checked out. This way, the local current Git Repository is kept in its original state.
        The new worktree is created at self.worktree_paths["source_worktree"].
        !! Uses remote branch for generating the documentation, all stashed or unpushed changes will be ignored !!
        Exits with error if source_branch does not exist in the remote repository.
        :param source_branch_exists_locally: Indicates if the source_branch exists in the local repository.
        If 0, it exists, else it does not
        """
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
                      f"and checked out (Local or stashed changes will be ignored in this build).")
                # change into documentation source dir
                os.chdir(f"{self.worktree_paths['source_worktree']}{self.source_dir}")
                current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                                     check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(f"""
                        Problem with adding worktree for source.
                        From git worktree add documentation: ' If <branch> does exist, it will be checked out in the 
                        new working tree,
                        if it’s not checked out anywhere else, otherwise the command will refuse to create 
                        the working tree (unless --force is used).'
                        Error from subprocess: {str(e)}"
                        """)

        elif source_branch_exists_locally == 0:
            sys.exit("Source branch exists locally, but not on remote, and source branch is not current branch."
                     "Please push your source branch to remote.")
        else:
            sys.exit(f"source branch {self.source_branch} does not exist")

    def detect_or_verify_source_branch(self) -> None:
        """
        Tries to find a valid source_branch.
        If source_branch is set, checks if it is equal to the current branch. If not, switches branches.
        Tries to use the current branch if source_branch is not set. Exits if this fails.
        Also fails if the detected source branch has local uncommitted/pushed changes or is not
        up-to-date with the remote.
        """
        current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        if self.source_branch == "":
            if current_branch.stdout == "":
                sys.exit("Abort. Could not detect current branch and no source branch given."
                         "Please check the state of your local git repository.")
            print(f"No source branch given. Using Current branch {current_branch.stdout[:-1]} as source.")
            self.source_branch = current_branch.stdout[:-1]
        remote_source_branch_commit_id = run(["git", "rev-parse", f"remotes/origin/{self.source_branch}"], capture_output=True, text=True)
        # the [:-1] removes the newline from the output
        if current_branch.stdout[:-1] != self.source_branch:
            print("Current branch is not source branch. Need to switch branches.")
            local_source_branch_commit_id = run(["git", "rev-parse", self.source_branch], capture_output=True,
                                                text=True)
            self.check_out_source_branch_as_worktree(local_source_branch_commit_id.returncode)
            return
        if remote_source_branch_commit_id.stdout[:-1] != self.current_commit_id:
            sys.exit(f"Abort. Local commit id {self.current_commit_id} and commit id of remote "
                     f"source branch {remote_source_branch_commit_id.stdout[:-1]} are not equal. "
                     f"Please push your changes or pull new commits from remote.")
        uncommitted_changes = run(["git", "status", "--porcelain"], capture_output=True, check=True, text=True)
        if uncommitted_changes.stdout != "":
            sys.exit(f"Abort, you have uncommitted changes in source branch  {self.source_branch}, "
                     f"please commit and push the following files:\n "
                     f"{uncommitted_changes.stdout}")
        os.chdir(f".{self.source_dir}")
        print(f"Detected source branch {self.source_branch}")

    def checkout_target_branch_as_worktree(self) -> None:
        """
        Creates a separate worktree for the target branch and checks it out.
        If the target_branch already exists in remote, it is checked out into a new local worktree.
        Else, target_branch is added as a new branch with a separate worktree and set as default for GitHub Pages.
        """

        if self.target_branch_exists.returncode == 0:
            print(f"Create worktree from existing branch {self.target_branch}")
            run(["git", "worktree", "add", self.worktree_paths["target_worktree"], self.target_branch], check=True)
        else:
            print(f"Create worktree from new branch {self.target_branch}")
            # We need to create the worktree directly with the TARGET_BRANCH,
            # because every other branch could be already checked out
            run(["git", "branch", self.target_branch], check=True)
            run(["git", "worktree", "add", self.worktree_paths["target_worktree"], self.target_branch], check=True)
            currentworkdir = os.getcwd()
            os.chdir(self.worktree_paths["target_worktree"])
            # We need to set the TARGET_BRANCH to the default branch
            # The default branch from github for pages is gh-pages, but you can change that.
            # Not using the default branch actually has benefits, because the branch gh-pages enforces some things.
            # We use github-pages/main with separate history for Github Pages,
            # because automated commits to the main branch can cause problems and
            # we don't want to mix the generated documentation with sources.
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

    def build_and_copy_documentation(self) -> Path:
        """
        Build the html documentation files using "sphinx-apidoc" and "sphinx-build",
        then copies them into the target branch. If an older version of the files exist for the source branch, on the
        target_branch, these are deleted first.
        :returns the path of the generated files inside the target_branch worktree.
        """
        print("Build with sphinx")
        currentworkdir = os.getcwd()
        print(currentworkdir)
        # automatically generates Sphinx sources inside the "api" directory that document
        # the package found in "module_path"
        # -T: not table of contents
        # -e: put documentation for each module on own page
        for module in self.module_path:
            out = run(["sphinx-apidoc", "-T", "-e", "-o", "api", module])
            print(module)
            print(out)
        # Builds the Sphinx documentation. Generates html files inside "build_dir" using "source_dir"
        # -W: Turns warnings into errors
        run(["sphinx-build", "-b", "html", "-d", self.intermediate_dir, "-W", currentworkdir, self.build_dir], check=True)
        print("Generated HTML Output")
        print(f"Using html_output_dir={self.build_dir}")

        # remove slashes from branch-name, this makes parsing the release-names for the release-index much easier
        simple_source_branch_name = self.source_branch.replace("/", "-")
        output_dir = Path(self.worktree_paths['target_worktree']) / simple_source_branch_name


        print(f"Using output_dir={output_dir}")
        if output_dir.exists() and output_dir.is_dir():
            print(f"Removing existing output directory {output_dir}")
            shutil.rmtree(output_dir)
        print(f"(Re)Creating output directory {output_dir}")
        output_dir.mkdir(parents=True)
        print(f"Copying HTML output {self.build_dir} to the output directory {output_dir}")
        for obj in os.listdir(self.build_dir):
            shutil.move(self.build_dir + "/" + str(obj), output_dir)
        open(f"{self.worktree_paths['target_worktree']}/.nojekyll", "w").close()

        print(f"Content of output directory {output_dir}")
        run(["ls", "-la", output_dir], check=True)

        return output_dir

    def git_commit_and_push(self, output_dir: Path) -> None:
        """
        Commits and pushes the generated documentation files to the remote GitHUb repository.
        Also adds a file describing the source branch and commit of the generated files, and
        generates a release index file using functions in generate_index.py.

        Does nothing if no changes occurred.
        :param output_dir: Path of the generated files inside the target_branch worktree.
        """
        currentworkdir = os.getcwd()
        os.chdir(self.worktree_paths['target_worktree'])
        print("Git commit")
        with open(f"{output_dir}/.source", "w+") as file:
            file.write(f"BRANCH={self.source_branch} \n")
            file.write(f"COMMIT_ID={self.current_commit_id} \n")
        run(["git", "add", "-v", "."], check=True)
        changes_exists = run(["git", "diff-index", "--quiet", "HEAD", "--"], capture_output=True, text=True)
        if 1 == changes_exists.returncode:
            print("Start generating/updating release_index.html")
            gen_index(self.target_branch, target_worktree=Path(self.worktree_paths["target_worktree"]),
                      source_branch=self.source_branch, target_branch_exists_remote=bool(self.target_branch_exists.stdout))
            run(["git", "add", "-v", "."], check=True)
            print(f"committing changes because changes exist.")
            run(["git", "commit", "--no-verify", "-m",
                 f"Update documentation from source branch {self.source_branch} with commit id"
                 f" {self.current_commit_id}"], check=True)
            if self.push_origin != "" and self.push_enabled == "push":
                print(f"Git push {self.push_origin} {self.target_branch}")
                run(["git", "push", self.push_origin, self.target_branch], check=True)
        elif 0 == changes_exists.returncode:
            print("No changes to commit.")
        else:
            sys.exit(f"""An error occurred in run(["git", "diff-index", "--quiet", "HEAD", "--"]. Nothing was committed.'
                    'capture_output=True, text=True), 
                    returncode: {changes_exists.returncode}, 
                    stderr: {changes_exists.stderr}, 
                    stdout: {changes_exists.stdout}
                    """)
        os.chdir(currentworkdir)

    def clean_worktree(self, original_workdir: str) -> None:
        """
        Deletes the temporary worktrees and resets the working directory to the given working directory in order to
        ensure it points to an existing directory.
        :param original_workdir: A directory that can be used as the working directory after the generator finishes.
        Preferably the original working-directory.
        """
        print("Starting cleanup.")
        os.chdir(original_workdir)
        print(f"Set working directory back to original {original_workdir}")
        for worktree_path in self.worktree_paths:
            path = Path(self.worktree_paths[worktree_path])
            if path.exists():
                print(f"Cleanup git worktree {path}")
                run(["git", "worktree", "remove", "--force", path], check=True)
