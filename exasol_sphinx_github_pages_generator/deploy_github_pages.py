import subprocess
import sys
from pathlib import Path
from exasol_sphinx_github_pages_generator.parser import Parser
from tempfile import TemporaryDirectory
from subprocess import run
import shutil
import os


# TODO remove debug outputs
# todo add typing, docu comments

#todo make worktree paths better
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
        self.worktree_path = tempdir + "/worktrees"
        self.build_dir = tempdir + "/build"
        self.intermediate_dir = tempdir + "/intermediate"
        self.staged_changes = False

    def check_for_local_changes_on_current_branch(self): #todo test
        local_changes_exists_on_current_branch = run(["git", "diff-index", "--quiet", "HEAD", "--"],
                                                     capture_output=True, text=True)
        if 1 == local_changes_exists_on_current_branch.returncode:
            print(f"staging changes because local_changes_exists_on_current_branch "
                  f"is {local_changes_exists_on_current_branch.returncode}")
            run(["git", "stash", "push"])
            self.staged_changes = True

    def check_out_source_branch_as_worktree(self,
                                            source_branch_exists_in_worktree: bool,
                                            source_branch_commit_id):
        # Need to switch branches to source_branch/fix working tree
        source_branch_exists_remote = run(["git", "show-branch", f"remotes/origin/{self.source_branch}"],
                                          capture_output=True, text=True)
        print("source_branch_exists_remote : " + str(source_branch_exists_remote))
        if source_branch_exists_remote.returncode == 0:
            try:
                # "If <branch> does exist, it will be checked out in the new working tree, if it’s not checked out
                # anywhere else, otherwise the command will refuse to create the working tree (unless --force is used)."
                #self.check_for_local_changes_on_current_branch()
                # Create <path> and checkout <commit-ish> into it.
                #todo only do this, if source does not exist locally, or loaall version of source is up to date with remote
                run(["git", "worktree", "add", self.worktree_path + "1", self.source_branch, "--force"], check=True)
                print(f"Successfully added new temp worktree for source branch {self.source_branch}, and checked out.")
                print(os.getcwd())
                os.chdir(self.worktree_path + "1/doc")
                current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                                     check=True)
                print("new current_branch : " + str(current_branch.stdout))
            except subprocess.CalledProcessError as e:
                print("Problem with adding worktree for source")
                print(e)
                sys.exit()
            #except subprocess.CalledProcessError as e:
            #    print(f"source branch {self.source_branch} already exists locally.")
            #    print("source branch exists remote and locally")
            #    self.check_for_local_changes_on_current_branch()
            #    run(["git", "checkout", self.source_branch]) # does this
                # if source_branch_commit_id == current_commit_id:
                #    print(f"source branch {source_branch} exists locally and is up to date with remote, so just check out")
                #    run(["git", "checkout", source_branch])

        elif source_branch_exists_in_worktree:  # todo rm source_branch_exists_in_worktree? #tests
            print("Source branch exists locally, but not on remote. Checking out,"
                  "and setting 'push_enabled' to commit so no docu for unpublished branch is pushed to repository")
            self.check_for_local_changes_on_current_branch() # todo copy this branch into new worktree in this case?
            push_enabled = "commit"
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
            # todo return here

        source_branch_commit_id = run(["git", "rev-parse", self.source_branch], capture_output=True, text=True)
        print("source_branch_exists_in_worktree/source_branch_commit_id : " + str(source_branch_commit_id))
        if source_branch_commit_id.returncode != 0:
            source_branch_exists_in_worktree = False  # todo better
        else:
            source_branch_exists_in_worktree = True
        # the [:-1] removes the newline from the output
        if current_branch.stdout[:-1] != self.source_branch:  # todo always fails because current_branch.stdout includes origin?
            print("Current branch is not source branch. Need to switch branches")
            self.check_out_source_branch_as_worktree(source_branch_exists_in_worktree, source_branch_commit_id)
        else:  # current branch is source branch or no source branch was given

            if source_branch_commit_id.stdout != self.current_commit_id:  # todo can this happen here?
                sys.exit(f"Abort. Current commit id {self.current_commit_id} and commit id of source "
                         f"branch {source_branch_commit_id} are not equal.")
        print(f"Detected source branch {self.source_branch}")

    def checkout_target_branch_as_worktree(self):
        target_branch_exists = run(["git", "show-branch", f"remotes/origin/{self.target_branch}"], capture_output=True,
                                   text=True)
        print("target_branch_exists : " + target_branch_exists.stdout + str(
            target_branch_exists.returncode) + target_branch_exists.stderr)
        if target_branch_exists.returncode == 0:
            print(f"Create worktree from existing branch {self.target_branch}")
            run(["git", "worktree", "add", self.worktree_path + "2", self.target_branch], check=True)
        else:
            print(f"Create worktree from new branch {self.target_branch}")
            # We need to create the worktree directly with the TARGET_BRANCH,
            # because every other branch could be already checked out
            run(["git", "branch", self.target_branch], check=True)
            run(["git", "worktree", "add", self.worktree_path + "2", self.target_branch], check=True)
            currentworkdir = os.getcwd()
            print(currentworkdir)
            print(self.worktree_path + "2")
            os.chdir(self.worktree_path + "2")
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
        currentworkdir = os.getcwd() #todo does not have doc if changed branch
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
        print("sorce dir = " + self.source_dir)
        run(["sphinx-build", "-b", "html", "-d", self.intermediate_dir, "-W", currentworkdir, self.build_dir], check=True) #todo edit source_dir?(was self.source_dir before)
        print("Generated HTML Output")
        print(f"Using html_output_dir={self.build_dir}")
        run(["ls", "-la", self.build_dir], check=True)

        output_dir = Path(self.worktree_path + "2" + "/" + self.source_branch)
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
        open(f"{self.worktree_path + '2'}/.nojekyll", "w").close()
        run(["ls", "-la", output_dir], check=True)

        return output_dir

    def git_commit_and_push(self, output_dir):
        currentworkdir = os.getcwd()
        print(currentworkdir)
        os.chdir(self.worktree_path + "2")
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
        # todo change back to original cuurent workdir
        #run(["git", "checkout", self.current_commit_id], capture_output=True, text=True, check=True) #todo needs branch name
        if self.staged_changes:
            run(["git", "stash", "pop"], capture_output=True, text=True, check=True) #todo needed if switch brach to only locally existing branch
            pass
        wt1 = Path(self.worktree_path + "1")
        wt2 = Path(self.worktree_path + "2")
        if wt1.exists():
            print(f"Cleanup git worktree {self.worktree_path + '1'}")
            run(["git", "worktree", "remove", "--force", self.worktree_path + "1"], check=True) # todo all checked out repos are in tem -> deleted automatically, right?
        if wt2.exists():
            print(f"Cleanup git worktree {self.worktree_path + '2'}")
            run(["git", "worktree", "remove", "--force", self.worktree_path + "2"], check=True) # todo all checked out repos are in tem -> deleted automatically, right?


def deploy_github_pages(argv):
    args = Parser(argv).args
    original_workdir = os.getcwd()
    source_dir = args.source_dir
    current_commit_id = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    print("Commandline parameter")
    print("source_dir= " + source_dir)
    print("module_path= " + str(args.module_path))
    print("TARGET_BRANCH=" + args.target_branch)
    print("PUSH_ORIGIN=" + args.push_origin)
    print("PUSH_ENABLED=" + args.push_enabled)
    print("SOURCE_BRANCH=" + args.source_branch + "\n")

    with TemporaryDirectory() as tempdir:
        deployer = GithubPagesDeployer(source_dir, args.module_path, args.target_branch,
                                       args.push_origin, args.push_enabled, args.source_branch,
                                       current_commit_id, tempdir)
        os.mkdir(deployer.build_dir)
        print("Using following Directories:")
        print("TMP=" + tempdir)
        print("WORKTREE=" + deployer.worktree_path)
        print("BUILD_DIR=" + deployer.build_dir)
        print("CURRENT_COMMIT_ID=" + deployer.current_commit_id + "\n")
        try:
            deployer.detect_or_verify_source_branch()
            deployer.checkout_target_branch_as_worktree()
            output_dir = deployer.build_and_copy_documentation()
            deployer.git_commit_and_push(output_dir)
        finally:
            deployer.clean_worktree(original_workdir)

