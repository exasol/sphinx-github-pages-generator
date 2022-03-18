# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['exasol_sphinx_github_pages_generator']

package_data = \
{'': ['*']}

install_requires = \
['Sphinx>=3.5.3,<4.0.0',
 'myst-parser>=0.14.0,<0.15.0',
 'poethepoet>=0.10.0,<0.11.0']

setup_kwargs = {
    'name': 'exasol-sphinx-github-pages-generator',
    'version': '0.1.0',
    'description': 'Generates Sphinx GitHub pages for a given Git Repository',
    'long_description': 'Sphinx GitHub Pages Generator\n*****************************\n\n.. _docu_start:\n\nOverview\n========\n\nThis project provides a python library for accessing automatic generation of sphinx GitHub pages \nfor a given repository. It is intended for the use with a Continuous Integration solution.\nDeveloped using GitHub Actions.\n\nIn a Nutshell\n=============\n\nPrerequisites\n-------------\n\n- Python 3.8+\n\nInstallation\n-------------\n#todo fix link\nInstall the package from Github via `pip`:: #todo make pip package\n\n    pip install -e git://github.com/exasol/bucketfs-utils-python.git@{tag name}#egg=exasol-bucketfs-utils-python\n\nDocumentation\n-------------\n\n`Documentation for the latest release <https://exasol.github.io/sphinx-github-pages-generator/main>`_ is hosted on the Github Pages of this project.\n\nFeatures\n========\n\n* Build html documentation files using Sphinx\n* Choose which remote branch to generate the documentation from\n* Choose whether to automatically push the generated and committed documentation or not.\n* Works with multiple packages in one repository.',
    'author': 'Marlene Kreß',
    'author_email': 'marlene.kress@exasol.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/exasol/sphinx-github-pages-generator',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
