*****************
Design Decisions:
*****************

##########
Use Git
##########

This project uses a lot of github calls. Since not all of the are present in PyGitHub, we decided to use
:code: ´subprocess.run´ for all of them, in order to keep the git calls consistent.

######################
Generate documentation
######################

The Documentation is generated and build using

.. code::

    sphinx-apidoc -T -e -o api module_path
    sphinx-build -b html -d intermediate_dir -W currentworkdir build_dir


The intermediate .doctree files are generated into a temporary :code: ´intermediate_dir´ and are not
copied into
the resulting documentation.



###############
Generate Apidoc
###############

The :code: ´sphinx-apidoc´ is used to automatically generate api documentation in the "doc/api" directory
for all packages which are listed in the module_path parameter.
The resulting html files are generated from the signatures and comments in the package source-files.


#############################
Work in an isolated workspace
#############################

This is achieved by using separate worktrees for any branch which needs to be checked out and/or
changed during the build of the documentation. The worktrees are then deleted before termination of the process. This ensures
the local repository stays clean.
Additionally, the whole task runs in a temporary folder.

################
Branch selection
################

The parameter "source_branch" can be set to the name of the branch the documentation should be generated for.
If it is not set, the current branch is used as a source branch. If the source branch is not the current branch, the
source branch is temporarily checked out into a separate worktree, so the documentation can be built without having
to deal with uncommitted changes on the current branch.
Each documentation pushed to GitHub contains a file ".source" which contains the branch name and commit id.

################
Tests Repository
################

The tests for this project use a private `test repository <https://github.com/exasol/sphinx-github-pages-generator-test>`_
This is done in order to make the tests similar to a real use case. The test repository is private as to not be
confusing to users.

############
GitHub Pages
############

To publish to GitHub Pages, we need to build the HTML from the documentation source and commit it.
However, Github Pages expects a specific directory structure to find the HTML.

Since code directory structure often doesn't fit these requirements, we decided to create
a new Git root commit and initially set github-pages/main branch to this commit.
We then add new commits to this branch to update existing or add new versions of the documentation.

This also avoids having automatic commits to the source branch.
For each branch or tag for which we build the documentation in the CI
we add a directory to the root directory of the github-pages/main branch.

