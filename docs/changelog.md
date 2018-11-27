# Changelog

### 1.2.0 - Internal refactoring: we now use a more robust method to identify tests that are steps of the same test. 

This fixes some bugs that were happening on edge cases where several parameters had the same string id representation (or one was a substring of the other). Fixed [#21](https://github.com/smarie/python-pytest-steps/issues/21).

### 1.1.2 - pytest-harvest is now an optional dependency

Fixed [#20](https://github.com/smarie/python-pytest-steps/issues/20)

### 1.1.1 - fixed ordering issue in generator mode

Fixed a pytest ordering issue in generator mode, by relying on [place_as](https://github.com/pytest-dev/pytest/issues/4429). Fixed [#18](https://github.com/smarie/python-pytest-steps/issues/18).

### 1.1.0 - `pytest-harvest` utilities + `@one_per_step` fix

Fixed: `@one_per_step` can now be used with generator-style fixtures.

API:
 - New method `get_underlying_fixture` to Truly get a fixture value even if it comes from a `@one_per_step`
 - internal constant `INNER_STEP_ARGNAME` is now named `GENERATOR_MODE_STEP_ARGNAME`
 - 5 new utility methods to support combining this plugin with `pytest-harvest` (see documentation for details): `handle_steps_in_synthesis_dct`, `remove_step_from_test_id`, `get_all_pytest_param_names_except_step_id`, `pivot_steps_on_df`, `get_flattened_multilevel_columns`

### 1.0.4 in progress - improved readability

Improved readability in signature-fiddling hacks: now the logic is separate from the two generated function signatures, both for generator and parametrizer modes.

### 1.0.3 - fix: request in arguments with new generator mode

Test functions using new generator mode can now use the 'request' parameter. Fixed [#12](https://github.com/smarie/python-pytest-steps/issues/12)

### 1.0.2 - fix for old version of decorator lib

 * Fixed [#11](https://github.com/smarie/python-pytest-steps/issues/11)

### 1.0.1 - removed deprecation warnings

 * Removed some deprecation warnings appearing in latest pytest 3.x, about the future pytest 4 to come. Fixed [#10](https://github.com/smarie/python-pytest-steps/issues/10)

### 1.0.0 - new "generator" mode + pytest 2.x compliance

You can now implement your test steps as `yield` statements in a generator. See documentation for details. Closes [#6](https://github.com/smarie/python-pytest-steps/issues/6)

Parametrized mode now works with older version of pytest (where `@pytest.fixture` did not have a `name=` parameter). Fixes [#9](https://github.com/smarie/python-pytest-steps/issues/9)

### 0.7.2 - minor encoding issue in setup.py

### 0.7.1 - Fixed regression on python 3

Python 3: After last tag a new bug appeared: an empty test named `test_steps` was created. Fixed it [#5](https://github.com/smarie/python-pytest-steps/issues/5).

### 0.7.0 - Python 2 support

### 0.6.0 - New `@depends_on` decorator

 * Added a first version of `@depends_on` decorator. Fixes [#1](https://github.com/smarie/python-pytest-steps/issues/1)

### 0.5.0 - First public version

 * Initial fork from [pytest-cases](https://smarie.github.io/python-pytest-cases/)
 * A few renames for readability: `ResultsHolder` becomes `StepsDataHolder`, and the default name for the holder becomes `'steps_data'`.
 * Documentation
