
# Requirements this Software aims to fulfill:

## Generate documentation
Generate documentation using the Python documentation Generator Sphinx. 
The Generated files should be html files, and unnecessary intermediate or source files should not be included 
in the documentation.

## Generate Apidoc
Use sphinx-apidoc/autodoc to Generate apidoc sources for automatic documentation of the package 
generated from the signatures and comments in the package source-files.

## Add generated documentation to GitHub
The generated documentation files should be added to a GitHub branch in a format that can be used 
with GitHub-Pages. If no such branch exists, one should be created. It should be possible to decide to directly push 
the generated documentation to the remote, or not.

## Work in an isolated workspace
The Generator should be working in an isolated temporary workspace, so no used repository folders get corrupted
or unnecessarily cluttered.

## Branch selection
It should be possible to select which branch to generate the documentation on. Generated documentation should include
information as to where it was generated from.