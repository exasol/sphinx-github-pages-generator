**********
User Guide
**********

This user guide provides you with usage examples for this repository.
For a detailed explanation of the API, please refer to our :doc:`API Documentation </api/exasol_sphinx_github_pages_generator>`




===========================
Building the Documentation
===========================

We are using Sphinx for generating the documentation,
because it is the default documentation tool for Python projects.
Sphinx supports API documentation generation for Python and with plugins also for other languages.
Furthermore, it supports reStructuredText with proper cross-document references.


---------------------------
Needed Repository structure
---------------------------

This Project uses Sphinx for the generation of the documentation. Therefore, all files you want to use as a
source for your documentation have to be compatible with Spinx. You can find Sphinx's
documentation `here <https://www.sphinx-doc.org/en/master/>`_.

In general:

You will need a base directory for your documentation source files. We use "repository_root/doc",
but you can set it to another folder (Please set the source_dir parameter accordingly. It defaults to /doc/).
Inside the documentation root directory, you need at least a minimal "conf.py" to configure
Sphinx and a "index.rst"
for Sphinx to use as a root for your documentation. You can use :code:`sphinx-quickstart` to generate stubs for these.
Inside the index.rst you can link to other parts of your documentation using the :code:`toctree` directive.

You can also include plain text, or documentation for specific functions or objects by using the
:code:`autosummary`,
:code:`automodule`,
:code:`autoclass` and
:code:`autoexception` directives, which will import the docstring for the given objects automatically.
Here is the code from te index.rst of this project, which generates the documentation if the api:

.. code-block::

    .. autosummary::
        :toctree: ../api
        :recursive:

        exasol_sphinx_github_pages_generator

To see the generated pages see :ref:`api_ref_target`.

----------------------------------------------------
Testing the documentation build with Sphinx locally
----------------------------------------------------

You can use the Spinx commands for building your documentation like normal to build your documentation locally.
This can be useful for debugging purposes.

When called from your "./doc" directory, the commands below will build you html files and put them in the
"./doc/.build" directory:

.. code:: bash

    sphinx-apidoc -T -e -o api ../<your-module-name>
    sphinx-build -b html -W . .build

-----------------------------
Call the Sphinx generator
-----------------------------

Once Sphinx generator is installed in your environment, you can import and use it in a
python script like this:

.. code:: py

    import exasol_sphinx_github_pages_generator.deploy_github_pages as deploy_github_pages
    import sys

    if __name__ == "__main__":
        deploy_github_pages.deploy_github_pages(sys.argv[1:])

Then call the script using command line parameters like this:

.. code:: bash

    declare -a StringArray=("../package/module-path1" "../package/module-path2")
    python3 your_caller_script.py --target_branch "github-pages/main" --push_origin "origin" --push_enabled "push" --source_branch "main"  --module_path "${StringArray[@]}" --source_dir "/doc/"

Alternatively you can also pass the parameters directly in the python script:

.. code:: py

    deploy_github_pages.deploy_github_pages(["--target_branch", "target_branch",
                                             "--push_origin", "origin",
                                             "--push_enabled", "push",
                                             "--source_branch", "source_branch",
                                             "--source_dir", "/doc/",
                                             "--module_path", "../package/module-path1", "../package/module-path2"])

The generator has to be called from the working directory containing the index.rst file.

-------
Options
-------

Calling the module with "-h" will print the help page for the generator.

.. code:: py

    deploy_github_pages.deploy_github_pages(["-h"])

Parameters:

.. autoclass:: exasol_sphinx_github_pages_generator.deploy_github_pages.GithubPagesDeployer


======================================================
Building the Documentation in the CI
======================================================

The documentation for this project is built on GitHub Actions using this project. We will use the process as an example here.

There is an action, both for updating the documentation for the main branch, and for validating the build of the
documentation for each push not on the main branch or on documentation branches.
It uses the target branch github-pages/<feature-branch-name>,
and if the branch is not "main", the target branch is deleted immediately after generation. Your can find the yaml file
for this action in ".github/workflows/check_documentation_build.yaml".

The GitHub Action uses poethepoet task which we describe in the pyproject.toml:

.. code::

    [tool.poe.tasks]
        commit_pages_main = { shell = """cd "$(git rev-parse --show-toplevel)/doc";declare -a StringArray=("../exasol_sphinx_github_pages_generator" ); python3 ./exasol_sphinx_github_pages_generator/deploy_github_pages.py --target_branch "github-pages/main" --push_origin "origin" --push_enabled "commit" --source_branch "main"  --module_path "${StringArray[@]}" """ }
        commit_pages_current = { shell = """cd "$(git rev-parse --show-toplevel)/doc";declare -a StringArray=("../exasol_sphinx_github_pages_generator" ); python3 ./exasol_sphinx_github_pages_generator/deploy_github_pages.py --target_branch "github-pages/"$(git branch --show-current)"" --push_origin "origin" --push_enabled "commit" --module_path "${StringArray[@]}" """ }
        push_pages_main = { shell = """cd "$(git rev-parse --show-toplevel)/doc";declare -a StringArray=("../exasol_sphinx_github_pages_generator" ); python3 ./exasol_sphinx_github_pages_generator/deploy_github_pages.py --target_branch "github-pages/main" --push_origin "origin" --push_enabled "push" --source_branch "main"  --module_path "${StringArray[@]}" """ }
        push_pages_current = { shell = """cd "$(git rev-parse --show-toplevel)/doc";declare -a StringArray=("../exasol_sphinx_github_pages_generator" ); python3 ./exasol_sphinx_github_pages_generator/deploy_github_pages.py --target_branch "github-pages/"$(git branch --show-current)"" --push_origin "origin" --push_enabled "push" --module_path "${StringArray[@]}" """ }

..
    _This: todo does calling package work like this everywhere else?

These are used in the GitHub Actions like this:

.. code::

        - name: Deploy documentation to github-pages-main branch
          run: |
            git config --local user.email <e-mail>
            git config --local user.name <user>
            git fetch
            poetry run poe push_pages_current
