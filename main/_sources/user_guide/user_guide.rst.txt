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
source for your documentation have to be compatible with Sphinx. You can find Sphinx's
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

You can use the Sphinx commands for building your documentation like normal to build your documentation locally.
This can be useful for debugging purposes.

When called from your "./doc" directory, the commands below will build you html files and put them in the
"./doc/.build" directory:

.. code:: bash

    sphinx-apidoc -T -e -o api ../<your-module-name>
    sphinx-build -b html -W . .build

We also provide shortcuts for this as nox tasks in the noxfile.py:

.. code:: bash

    nox -s build-docs    # Builds the documentation
    nox -s open-docs     # Opens the currently build documentation in the browser
    nox -s clean-docs    # Clean existing docs artefacts


You can use similar shorthands in your project, just adjust the module path.

-----------------------------
Call the Sphinx generator
-----------------------------

Once Sphinx generator is installed in your environment, you can use the "sgpg" command to run it. Use "sgpg --help"
for an overview over parameters.

You can also import and use it in a
python script like this:

.. code:: py

    import exasol_sphinx_github_pages_generator.cli as cli
    from click.testing import CliRunner
    import sys

    if __name__ == "__main__":
        CliRunner().invoke(cli.main, sys.argv[1:])

Then call the script using command line parameters like this:

.. code:: bash

    declare -a StringArray=("../package/module-path1" "../package/module-path2")
    python3 your_caller_script.py \
        --target-branch "github-pages/main" \
        --push-origin "origin" \
        --push \
        --source-branch "main"  \
        --module-path "${StringArray[@]}" \
        --source-dir "/doc/"

Alternatively you can also pass the parameters directly in the python script:

.. code:: py

    deployer = GithubPagesDeployer(Path("doc/"), source_branch, "origin", current_commit_id.stdout[:-1], ["../test_package"],
                                       target_branch, "origin", True,
                                       Path(tempdir))

    deploy_github_pages.deploy_github_pages(["--target-branch", "target_branch",
                                             "--push-origin", "origin",
                                             "--push-enabled", "True"
                                             "--source-branch", "source_branch",
                                             "--source-dir", "/doc/",
                                             "--module-path", "../package/module-path1", "../package/module-path2"])

The generator has to be called from the working directory containing the index.rst file.

-------
Options
-------

Calling the module with "--help" will print the help page for the generator.

.. code:: bash

    sgpg --help

Options for sgpg:
  --target-branch TEXT  Branch to push to

  --push-origin TEXT    Where to push from

  --push                Commit and push the documentation.

  --commit              Only commit the documentation.

  --source-branch TEXT  The branch you want to generate documentation from. If
                        empty, defaults to current branch. Can also be a
                        GitHub tag

  --source-origin TEXT  Origin of source_branch. Set to 'tags' if your
                        source_branch is a tag

  --source-dir PATH     Path to the directory inside the source_branch where
                        the index.rst and conf.py reside in.

  --module-path TEXT    List of paths to all the modules the docu is being
                        generated for

  --debug               Prints full exception traceback

  --help                Show this message and exit.


Parameters for the Python class:

.. autoclass:: exasol_sphinx_github_pages_generator.deployer.GithubPagesDeployer
    :noindex:

