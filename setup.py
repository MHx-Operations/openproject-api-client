# coding: utf-8

from setuptools import setup, find_packages  # noqa: H301

NAME = "openproject-api-client"
VERSION = "0.1.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["requests>=2.25"]

setup(
    name=NAME,
    version=VERSION,
    description="Client API for Openproject",
    author_email="markus.hof@mhx-operations.at",
    url="",
    keywords=["client api openproject"],
    install_requires=REQUIRES,
    python_requires=">=3.6.0",
    entry_points={"console_scripts": ["openproject-cli = openproject_api_client.cli:main"]},
    packages=find_packages(),
    include_package_data=True,
    long_description="""\
    provides client API to access an openproject instance, tested with Version 10
    """
)
