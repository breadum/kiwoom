from setuptools import setup

VERSION = "1.0"
DISTNAME = "kiwoom"
DESCRIPTION = "Python API of Kiwoom OPEN API+"
LONG_DESCRIPTION = """
This module provides a python wrapper for Kiwoom OPEN API+ module.
The project aims to one who wants to develop own trading system by oneself.
Considering the purpose, the package tries to be simple as possible.


"""

AUTHOR = "Breadum"
EMAIL = "breadum.kr@gmail.com"
LICENSE = "MIT"

"""
PROJECT_URLS = {
    "Documentation": "",
    "Source Code": "https://github.com/breadum/kiwoom",
}
"""
CLASSIFIERS = [
    "Operating System :: ",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Topic :: trading-systems/algorithmic-trading"
]


def setup_package():
    kwargs = {
        "install_requires": [

        ],
        "setup_requires": [

        ]
    }

    setup(
        name=DISTNAME,
        author=AUTHOR,
        author_email=EMAIL,
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        platforms="",
        python_requires=">=3.7",
        **kwargs
    )


if __name__ == '__main__':
    setup_package()
