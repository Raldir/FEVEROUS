from setuptools import find_packages, setup

import os
import pathlib

# Commands: 
# python setup.py sdist
# twine upload dist/*
# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# Dependencies required to use
INSTALL_REQS = [
    "regex>=2020.10.23, <= 2022.10.31",
    "numpy>=1.19.1, <= 1.21.6",
    "transformers>=4.1.1, <= 4.26.1",
    "scipy>=1.5.4, <= 1.7.3",
    "clean-text>=0.4.0, <= 0.6.0",
    "pexpect<=4.8.0",
    "spacy>=2.3.2, <= 3.5.0",
    "scikit-learn<=1.0.2",
    "jsonlines>=2.0.0, <= 3.1.0",
    "tqdm>=4.46.0, <= 4.64.1",
    "torch==1.13.1, == 1.13.1",
]

setup(
    name="feverous",
    version="0.54",
    description="Repository for Fact Extraction and VERification Over Unstructured and Structured information (FEVEROUS), used for the FEVER Workshop Shared Task at EMNLP2021.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Raldir/FEVEROUS",
    author="Rami Aly",
    author_email="rmya2@cam.ac.uk",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=INSTALL_REQS,
    python_requires=">=3.6",
)
