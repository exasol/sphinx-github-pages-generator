Sphinx GitHub Pages Generator
*****************************

.. _docu_start:

**This Repository is archived and not in active development anymore, please use the** `Exasol Python Toolbox <https://github.com/exasol/python-toolbox>`_ **instead.**

Overview
========

This project provides a python library for accessing automatic generation of sphinx GitHub pages 
for a given repository. It is intended for the use with a Continuous Integration solution.
Developed using GitHub Actions.
We are using Sphinx for generating the documentation,
because it is the default documentation tool for Python projects.
Sphinx supports reStructuredText with appropriate cross-document references.
We use the MyST-Parser to also integrate markdown files into the documentation.

In a Nutshell
=============

Motivation
----------

Using Sphinx for building the documentation of a project in the CI is a bit different to the steps you can use during coding,
because it also contains the preparations for publishing. At the moment, we publish
the documentation on Github Pages.

To publish it there, the HTML needs to be built from the documentation source and committed. It also needs to be ensured
it adheres to the file structure expected by GitHub Pages.
Our usual directory structure doesn't fit these requirements, so we decided to create
a new Git root commit and initially set github-pages/main branch to this commit.
We then add new commits to this branch to update existing or add new versions of the documentation.

This has the additional benefit, that we don't have automatic commits to the source branch.
For each branch or tag for which we build the documentation in the CI
we add a directory to the root directory of the github-pages/main branch.

For simplification of this process, we build the Sphinx_GitHub-Pages-Generator.

Prerequisites
-------------

- Python 3.8+

Installation
-------------
..
    _This: todo fix installation description

Install the package from Github via `pip`::

    pip install -e git://github.com/exasol/sphinx-github-pages-generator.git@{tag name}#egg=exasol-sphinx-github-pages-generator

Documentation
-------------

`Documentation for the latest release <https://exasol.github.io/sphinx-github-pages-generator/main/>`_ is hosted on the Github Pages of this project.

Features
========

* Build html documentation files using Sphinx
* Choose which remote branch to generate the documentation from
* Choose whether to automatically push the generated and committed documentation or not.
* Works with multiple packages in one repository.
* Generates a index.html file containing links to all existing documentations on that branch.
  This file is generated using the "furo" theme.
