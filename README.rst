Sphinx GitHub Pages Generator
*****************************

.. _docu_start:

Overview
========

This project provides a python library for accessing automatic generation of sphinx GitHub pages 
for a given repository. It is intended for the use with a Continuous Integration solution.
Developed using GitHub Actions.

In a Nutshell
=============

Prerequisites
-------------

- Python 3.8+

Installation
-------------
..
    _This: todo fix installation description

Install the package from Github via `pip`::

    pip install -e git://github.com/exasol/bucketfs-utils-python.git@{tag name}#egg=exasol-bucketfs-utils-python

Documentation
-------------

`Documentation for the latest release <https://exasol.github.io/sphinx-github-pages-generator/main/>`_ is hosted on the Github Pages of this project.

Features
========

* Build html documentation files using Sphinx
* Choose which remote branch to generate the documentation from
* Choose whether to automatically push the generated and committed documentation or not.
* Works with multiple packages in one repository.
* Generates main index.html containing links to all existing documentations on that branch.
