**********
User Guide
**********

# add beispiele?
# wie muss repo aufgebaut sein um generated zu nutzen (link to shpinx )

This user guide provides you with usage examples for this repository.
For a detailed explanation of the API, please refer to our :doc:`API Documentation </api/exasol_sphinx_github_pages_generator>`


- need for sphinx: 
* conf.py
* index.rst



**********************************************
Überschrift
**********************************************

explanation

 * :doc:`Upload API </api/exasol_bucketfs_utils_python.upload>` link to file


################################################
unter überschrift
################################################


Example:

.. literalinclude:: upload_download_file.py
   :language: python3 codebeispiiel

#######################################################
Uploading and downloading data from and to file-objects
#######################################################

A more sophisticated version of the previous function allows you
to upload from or download into a
`file-object <https://docs.python.org/3/glossary.html#term-file-object>`_.
:py:func:`open` function or
:py:class:`io.BytesIO`.
:py:meth:`socket.socket.makefile()`

**************************
Building the Documentation
**************************

We are using Sphinx for generating the documentation,
because it is the default documentation tool for Python projects.
Sphinx supports API documentation generation for Python and with plugins also for other languages.
Furthermore, it supports reStructuredText with proper cross-document references.

########################
Call the Sphinx generator
########################

Once Sphinx generator is installed in your environment, you can import and use it in a python script like this:

    import exasol_sphinx_github_pages_generator.deploy_github_pages as deploy_github_pages
    import sys

    if __name__ == "__main__":
        deploy_github_pages.deploy_github_pages(sys.argv[1:])

Then call the Script using command line parameters like this:

    declare -a StringArray=("../package/module-path1" "../package/module-path2")
    python3 your_caller_script.py --target_branch "github-pages/main" --push_origin "origin" --push_enabled "push" --source_branch "main"  --module_path "${StringArray[@]}" --source_dir $PWD

Alternatively you can also pass the parameters directly in the python script:

    deploy_github_pages.deploy_github_pages(["--target_branch", "target_branch",
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", "source_branch",
                                             "--source_dir", cwd,
                                             "--module_path", "../package/module-path1", "../package/module-path2"])
#######
Options
#######

Calling the module with "-h" will print the help page for the generator.

    deploy_github_pages.deploy_github_pages(["-h"])

Parameters:

.. currentmodule:: exasol_sphinx_github_pages_generator/deployer.py
.. autofunction:: __init__

For a closer look see:
:doc:`Generator documentation </api/deployer.py>`

######################################################
Building the Documentation interactively during coding
######################################################

We defined several commands in the project.toml in poethepoet
which allow you to build the documentation during coding::
#todo add view, say to copy? or import somehow?

    poetry run poe build-html-doc # Builds the documentation
    poetry run poe open-html-doc # Opens the currently build documentation in the browser
    poetry run poe build-and-open-html-doc # Builds and opens the documentation
    #todo

    poetry run poe commit_pages_main
    poetry run poe commit_pages_current
    poetry run poe push_pages_main
    poetry run poe push_pages_current

All three build commands use the generated documentation located in /doc/_build/
which is excluded in gitignore. If you want to build the documentation for other formats than HTML,
you find a Makefile in /doc which allows you to run the sphinx build with other goals.

####################################
Building the Documentation in the CI
####################################

Building the documentation in the CI is a bit different to the steps you can use during coding,
because it also contains the preparations for publishing. At the moment, we publish
the documentation on Github Pages.

To publish it there, we need to build the HTML from the documentation source and commit it.
However, Github Pages expects a specific directory structure to find the HTML.
Our usual directory structure doesn't fit these requirements, so we decided to create
a new Git root commit and initially set github-pages/main branch to this commit.
We then add new commits to this branch to update existing or add new versions of the documentation.

This also avoid having automatic commits to the source branch.
For each branch or tag for which we build the documentation in the CI
we add a directory to the root directory of the github-pages/main branch.

With each merge into the main branch the CI updates the documentation for the main branch in github-pages/main.
For feature branches the CI checks this deployment process by creating a branch github-pages/<feature-branch-name>.
but it removes the branch directly after pushing it. However, you can run this also locally for testing purposes or
checking the branch with Github Pages in a fork of the main repostory.
The scripts which are responsible for the deployment are::

    deploy-to-github-pages-current # creates or updates github-pages/<current-branch-name>
    deploy-to-github-pages-main.sh # only applicable for the main branch and creates or updates github-pages/main


We also provide a few shortcuts defined in our project.toml for poethepoet::

    poetry run poe commit-html-doc-to-github-pages-main # creates or updates github-pages/main locally
    poetry run poe push-html-doc-to-github-pages-main  # creates or updates github-pages/main and pushes it to origin
    poetry run poe commit-html-doc-to-github-pages-current  # creates or updates github-pages/<current-branch-name> locally
    poetry run poe push-html-doc-to-github-pages-current  # creates or updates github-pages/<current-branch-name> and pushes it to origin

