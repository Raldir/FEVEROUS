from setuptools import find_packages, setup

# Dependencies required to use your package
with open('src/requirements.txt', 'r') as fh:

    INSTALL_REQS = [l.strip() for l in fh.readlines() if l.strip()]


setup(
    name='feverous',
    version='0.0.0',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=INSTALL_REQS,
    python_requires='>=3.6',
)
