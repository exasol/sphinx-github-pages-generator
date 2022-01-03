# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['exasol_sphinx_github_pages_generator']

package_data = \
{'': ['*']}

install_requires = \
[]

setup_kwargs = {
    'name': 'exasol-sphinx-github-pages-generator',
    'version': '0.1.0',
    'description': 'Generates Sphinx GitHub pages for a given Git Repository',
    'long_description': '#####################\nSphinx Github-pages generator\n#####################\n\n********\nOverview\n********\n\nGenerates Sphinx GitHub pages for a given Git Repository and branch.\n\nIn a Nutshell\n=============\n\nPrerequisites\n-------------\n\n- Python 3.8+\n\nInstallation\n-------------\n\nInstall the package from Github ::\n\n    git = "https://github.com/exasol/sphinx-github-pages-generator", branch = "refactoring/1-Move-Sphinx-Documentation-scripts"\n\nDocumentation\n-------------\n\n`Documentation for the latest release <https://exasol.github.io/sphinx-github-pages-generator/main>`_ is hosted on the Github Pages of this project.\n\nFeatures\n========\n\n* Generate GitHub Pages in your repository for a given branch using Sphinx.\n\n Commit or commit and push them to a specified existing or new documentation-branch.\n ',
    'author': 'Marlene Kreß, Torsten Kilias',
    'author_email': 'marlene.kress@exasol.com, torsten.kilias@exasol.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/exasol/sphinx-github-pages-generator',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6.1,<4.0',
}


setup(**setup_kwargs)
