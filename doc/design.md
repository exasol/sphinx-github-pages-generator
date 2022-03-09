# Design Decisions:

## Use GitHub
 - use subprocess to call git

## Generate documentation(move to user guide?)
 - use shpinx
 - use newly check out version of branch(check if remote is up-to-date with local repo first)
 - describe expected file structure?
 - html
 - how remove unnecessary files
 

## Generate Apidoc (move to user guide?)
 - describe expected file structure?
 - generated from the signatures and comments in the package source-files.
 - sphinx-apidoc/autodoc

## Add generated documentation to GitHub
(The generated documentation files should be added to a GitHub branch in a format that can be used 
with GitHub-Pages. If no such branch exists, one should be created. It should be possible to decide to directly push 
the generated documentation to the remote, or not.)

## Work in an isolated workspace
(The Generator should be working in an isolated temporary workspace, so no used repository folders get corrupted
or unnecessarily cluttered.)
 - (use worktrees)

## Branch selection
(It should be possible to select which branch to generate the documentation on. Generated documentation should include
information as to where it was generated from.)

## Tests Repository