""" Setuptools install-file for dbasic"""
import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()


setuptools.setup(
    name="dbasic",
    version="0.0.1",
    description="A minimal programming language for learning to write compilers",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/dbaumgarten/dbasic",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
    ),
    entry_points={
        'console_scripts': ['dbc=dbc.cli:main'],
    }
)
