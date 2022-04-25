***************
Developer Guide
***************

In this developer guide we explain how you can build this project, build the documentation and run the tests.

#################################################
Installation and Build/Setup
#################################################
First, you need to clone the Repository:

.. code::

    git clone https://github.com/exasol/sphinx-github-pages-generator.git

Then, got to the project root and use poetry to install your dependencies:

.. code::

    poetry install
    poetry update

Now, you can run the project using the poethepoet task defined in the `pyproject.toml`_:

.. code::

    poetry run poe commit_pages_current


#############
Documentation
#############

This repository also uses itself to generate the documentation for the Generator. The Source Files for the documentation
can be found in the `doc folder`_. Here is the :ref:`generated documentation <docu_start>` (You are already here ;) ).
To build the documentation manually for testing, you can use:

.. code:: bash

    sphinx-apidoc -T -e -o api PathToProject/sphinx-github-pages-generator/exasol_sphinx_github_pages_generator
    sphinx-build -b html -W PathToProject/sphinx-github-pages-generator/doc .build

#####
Tests
#####

Tests are located in the `tests folder`_. Run them with

    poetry run pytest tests

The tests use a `test repository <https://github.com/exasol/sphinx-github-pages-generator-test>`_
with a Machine user which is private in order not to confuse users. In order to run them,
the environment variables "MAuserPAT" and "MAuserName" have to be set to the Machine Users Personal Access Token and
Name respectively. If you need to change the names of these environment variables you can do so in `setup_test_repo`_, but don't commit
these changes in order not to break the CI tests.

For running your own tests, you can change the tests Repository, User and Password in `setup_test_repo`_.

.. _pyproject.toml: https://github.com/exasol/sphinx-github-pages-generator/blob/main/pyproject.toml
.. _doc folder: https://github.com/exasol/sphinx-github-pages-generator/tree/main/doc
.. _tests folder: https://github.com/exasol/sphinx-github-pages-generator/tree/main/tests
.. _setup_test_repo: https://github.com/exasol/sphinx-github-pages-generator/blob/7235e9577531bb3992425ffd200004dc4a7fee32/tests/helper_test_functions.py#L13

