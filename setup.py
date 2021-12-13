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
    'long_description': '#####################\nSphinx Github-pages generator\n#####################\n\n********\nOverview\n********\n\nGenerates Sphinx GitHub pages for a given Git Repository.\n\nIn a Nutshell\n=============\n\nPrerequisites\n-------------\n\n- Python 3.6+\n\nInstallation\n-------------\n\nInstall the package from Github via `pip`::\n\n    pip install -e git://github.com/exasol/bucketfs-utils-python.git@{tag name}#egg=exasol-bucketfs-utils-python\n\nDocumentation\n-------------\n\n`Documentation for the latest release <https://exasol.github.io/bucketfs-utils-python/main>`_ is hosted on the Github Pages of this project.\n\nFeatures\n========\n\n* Download or upload files from/to the Exasol BucketFS\n* Supported sources and targets for the uploads and downloads:\n\n  * Files on the local Filesystem\n  * Python file objects\n  * Python Strings\n  * Python objects ((De-)Serialization with [Joblib](https://joblib.readthedocs.io/en/latest/persistence.html))\n\n* Loading an artefact from a public Github Release into the BucketFS\n',
    'author': 'Marlene Kreß', # tODO update long desc
    'author_email': 'marlene.kress@exasol.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/exasol/sphinx-github-pages-generator',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6.1,<4.0',
}


setup(**setup_kwargs)
