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

PROJECT_URLS = {
    # "Documentation": "",  #TODO
    "Source Code": "https://github.com/breadum/kiwoom",
}
LICENSE = "MIT License"
CLASSIFIERS = [
    "Development Status :: 2 - Pre-Alpha",
    "License :: OSI Approved :: MIT License",
    "Operating System :: Microsoft :: Windows",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Topic :: Office/Business :: Financial :: Investment"
]


def setup_package():
    kwargs = {
        "install_requires": [

        ],
        "setup_requires": [

        ],
        'zip_safe': False
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
        license=LICENSE,
        **kwargs
    )


if __name__ == '__main__':
    setup_package()
