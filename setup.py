# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['exasol_sphinx_github_pages_generator']

package_data = \
{'': ['*'],
 'exasol_sphinx_github_pages_generator': ['_static/*',
                                          '_static/scripts/*',
                                          '_static/styles/*',
                                          'templates/*']}

install_requires = \
['Jinja2>=3.0.3,<4.0.0',
 'Sphinx>=4.5,<5.0',
 'click>=8.1.3,<9.0.0',
 'furo>=2022.02.14.1,<2023.0.0.0',
 'importlib_resources>=5.4.0',
 'myst-parser>=0.17.0,<0.18.0']

entry_points = \
{'console_scripts': ['sgpg = exasol_sphinx_github_pages_generator.cli:main']}

setup_kwargs = {
    'name': 'exasol-sphinx-github-pages-generator',
    'version': '0.1.1',
    'description': 'Generates Sphinx GitHub pages for a given Git Repository',
    'long_description': 'Sphinx GitHub Pages Generator\n*****************************\n\n.. _docu_start:\n\nOverview\n========\n\nThis project provides a python library for accessing automatic generation of sphinx GitHub pages \nfor a given repository. It is intended for the use with a Continuous Integration solution.\nDeveloped using GitHub Actions.\nWe are using Sphinx for generating the documentation,\nbecause it is the default documentation tool for Python projects.\nSphinx supports reStructuredText with appropriate cross-document references.\nWe use the MyST-Parser to also integrate markdown files into the documentation.\n\nIn a Nutshell\n=============\n\nMotivation\n----------\n\nUsing Sphinx for building the documentation of a project in the CI is a bit different to the steps you can use during coding,\nbecause it also contains the preparations for publishing. At the moment, we publish\nthe documentation on Github Pages.\n\nTo publish it there, the HTML needs to be built from the documentation source and committed. It also needs to be ensured\nit adheres to the file structure expected by GitHub Pages.\nOur usual directory structure doesn\'t fit these requirements, so we decided to create\na new Git root commit and initially set github-pages/main branch to this commit.\nWe then add new commits to this branch to update existing or add new versions of the documentation.\n\nThis has the additional benefit, that we don\'t have automatic commits to the source branch.\nFor each branch or tag for which we build the documentation in the CI\nwe add a directory to the root directory of the github-pages/main branch.\n\nFor simplification of this process, we build the Sphinx_GitHub-Pages-Generator.\n\nPrerequisites\n-------------\n\n- Python 3.8+\n\nInstallation\n-------------\n..\n    _This: todo fix installation description\n\nInstall the package from Github via `pip`::\n\n    pip install -e git://github.com/exasol/sphinx-github-pages-generator.git@{tag name}#egg=exasol-sphinx-github-pages-generator\n\nDocumentation\n-------------\n\n`Documentation for the latest release <https://exasol.github.io/sphinx-github-pages-generator/main/>`_ is hosted on the Github Pages of this project.\n\nFeatures\n========\n\n* Build html documentation files using Sphinx\n* Choose which remote branch to generate the documentation from\n* Choose whether to automatically push the generated and committed documentation or not.\n* Works with multiple packages in one repository.\n* Generates a index.html file containing links to all existing documentations on that branch.\n  This file is generated using the "furo" theme.\n',
    'author': 'Marlene Kreß',
    'author_email': 'marlene.kress@exasol.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://github.com/exasol/sphinx-github-pages-generator',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
