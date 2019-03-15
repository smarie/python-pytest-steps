# pytest-steps

Create step-wise / incremental tests in `pytest`.

[![Python versions](https://img.shields.io/pypi/pyversions/pytest-steps.svg)](https://pypi.python.org/pypi/pytest-steps/) [![Build Status](https://travis-ci.org/smarie/python-pytest-steps.svg?branch=master)](https://travis-ci.org/smarie/python-pytest-steps) [![Tests Status](https://smarie.github.io/python-pytest-steps/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-pytest-steps/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-pytest-steps/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-pytest-steps)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-pytest-steps/) [![PyPI](https://img.shields.io/pypi/v/pytest-steps.svg)](https://pypi.python.org/pypi/pytest-steps/) [![Downloads](https://pepy.tech/badge/pytest-steps)](https://pepy.tech/project/pytest-steps) [![Downloads per week](https://pepy.tech/badge/pytest-steps/week)](https://pepy.tech/project/pytest-steps) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-pytest-steps.svg)](https://github.com/smarie/python-pytest-steps/stargazers)

**This is the readme for developers.** The documentation for users is available here: [https://smarie.github.io/python-pytest-steps/](https://smarie.github.io/python-pytest-steps/)

## Want to contribute ?

Contributions are welcome ! Simply fork this project on github, commit your contributions, and create pull requests.

Here is a non-exhaustive list of interesting open topics: [https://github.com/smarie/python-pytest-steps/issues](https://github.com/smarie/python-pytest-steps/issues)

## Running the tests

This project uses `pytest`.

```bash
pytest -v pytest_steps/tests/
```

You may need to install requirements for setup beforehand, using 

```bash
pip install -r ci_tools/requirements-test.txt
```

## Packaging

This project uses `setuptools_scm` to synchronise the version number. Therefore the following command should be used for development snapshots as well as official releases: 

```bash
python setup.py egg_info bdist_wheel rotate -m.whl -k3
```

You may need to install requirements for setup beforehand, using 

```bash
pip install -r ci_tools/requirements-setup.txt
```

## Generating the documentation page

This project uses `mkdocs` to generate its documentation page. Therefore building a local copy of the doc page may be done using:

```bash
mkdocs build -f docs/mkdocs.yml
```

You may need to install requirements for doc beforehand, using 

```bash
pip install -r ci_tools/requirements-doc.txt
```

## Generating the test reports

The following commands generate the html test report and the associated badge. 

```bash
pytest --junitxml=junit.xml -v pytest_steps/tests/
ant -f ci_tools/generate-junit-html.xml
python ci_tools/generate-junit-badge.py
```

### PyPI Releasing memo

This project is now automatically deployed to PyPI when a tag is created. Anyway, for manual deployment we can use:

```bash
twine upload dist/* -r pypitest
twine upload dist/*
```

### Merging pull requests with edits - memo

Ax explained in github ('get commandline instructions'):

```bash
git checkout -b <git_name>-<feature_branch> master
git pull https://github.com/<git_name>/python-pytest-steps.git <feature_branch> --no-commit --ff-only
```

if the second step does not work, do a normal auto-merge (do not use **rebase**!):

```bash
git pull https://github.com/<git_name>/python-pytest-steps.git <feature_branch> --no-commit
```

Finally review the changes, possibly perform some modifications, and commit.
