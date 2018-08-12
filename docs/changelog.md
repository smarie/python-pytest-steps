# Changelog

### 0.7.1 - Fixed regression on python 3

Python 3: After last tag a new bug appeared: an empty test named `test_steps` was created. Fixed it [#5](https://github.com/smarie/python-pytest-steps/issues/5).

### 0.7.0 - Python 2 support

### 0.6.0 - New `@depends_on` decorator

 * Added a first version of `@depends_on` decorator. Fixes [#1](https://github.com/smarie/python-pytest-steps/issues/1)

### 0.5.0 - First public version

 * Initial fork from [pytest-cases](https://smarie.github.io/python-pytest-cases/)
 * A few renames for readability: `ResultsHolder` becomes `StepsDataHolder`, and the default name for the holder becomes `'steps_data'`.
 * Documentation
