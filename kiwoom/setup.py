from setuptools import setup, find_packages


# Project Information
VERSION = "1.0"
DISTNAME = "kiwoom"
DESCRIPTION = "Python API of Kiwoom OPEN API+"
LONG_DESCRIPTION = open('README.md').read()
PROJECT_URLS = {
    # TODO "Documentation": "",
    "Source Code": "https://github.com/breadum/kiwoom",
}

# Author Information
AUTHOR = "Breadum"
EMAIL = "breadum.kr@gmail.com"

# Miscellaneous
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
            'PyQt5 >= 5.15'
        ],
        "setup_requires": [],
        'zip_safe': False
    }

    setup(
        name=DISTNAME,
        author=AUTHOR,
        author_email=EMAIL,
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        python_requires=">=3.7",
        license=LICENSE,
        classifiers=CLASSIFIERS,
        **kwargs
    )


if __name__ == '__main__':
    setup_package()
