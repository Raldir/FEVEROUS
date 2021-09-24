from setuptools import find_packages, setup
import pathlib


# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# Dependencies required to use your package
with open('src/feverous/requirements.txt', 'r') as fh:

    INSTALL_REQS = [l.strip() for l in fh.readlines() if l.strip()]


setup(
    name='feverous',
    version='0.0.3',
    description="Repository for Fact Extraction and VERification Over Unstructured and Structured information (FEVEROUS), used for the FEVER Workshop Shared Task at EMNLP2021.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Raldir/FEVEROUS",
    author="Rami Aly",
    author_email="rmya2@cam.ac.uk",
    license="MIT",
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=INSTALL_REQS,
    python_requires='>=3.6',
)
