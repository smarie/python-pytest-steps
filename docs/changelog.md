# Changelog

### 1.7.2 - warning removed

Removed import warning. Fixed [#37](https://github.com/smarie/python-pytest-steps/issues/37)

### 1.7.1 - `pyproject.toml`

Added `pyproject.toml`.

### 1.7.0 - Support for test functions located inside test classes

`@test_steps` can now be used on test functions located inside classes. Fixed [#16](https://github.com/smarie/python-pytest-steps/issues/16)

**Warning**: as a consequence of the fix above, the order of arguments has changed. this has an impact for manual execution. See [here](https://smarie.github.io/python-pytest-steps/#d-calling-decorated-functions-manually) for details.

### 1.6.4 - python 2 bugfix

Fixed issue happening with python 2 when `unicode_literals` are used in the parameters receiving string types. Fixed [#34](https://github.com/smarie/python-pytest-steps/issues/34)

### 1.6.3 - added `__version__` attribute

Added `__version__` attribute at package level

### 1.6.2 - added `six` dependency

It was missing from `setup.py`.

### 1.6.1 - Minor code improvements

Made the python 3 signature patch more readable... for those users who will enter in the code while debugging.

### 1.6.0 - Minor dependencies update

Improved docstring for `@cross_steps_fixture`.
Replaced `decorator` dependency + internal hack with proper usage of `makefun`.

### 1.5.4 - Bug fix

The test step list is now correctly taken into account when a decorated function is called manually. Fixed [#30](https://github.com/smarie/python-pytest-steps/issues/30).

### 1.5.3 - Bug fix

Fixed plugin initialization error when `pytest_harvest` is not present. Fixed [#29](https://github.com/smarie/python-pytest-steps/issues/29).

### 1.5.2 - Bug fix

`pytest_harvest` is not anymore required for install. Fixed [#28](https://github.com/smarie/python-pytest-steps/issues/28).

### 1.5.1 - Bug fix and exceptions improvement

We now detect that `@cross_step_fixture` or `@one_fixture_per_step` is applied on a fixture with the wrong scope, and raise a much more readable exception. Fixes [#25](https://github.com/smarie/python-pytest-steps/issues/25).

Improved `pivot_steps_on_df` so that we can use a filter on it, and so that only cross-step fixtures are used in the default cross-step columns. Fixes [#26](https://github.com/smarie/python-pytest-steps/issues/26)

### 1.5.0 - New `@cross_steps_fixture` decorator

`@one_per_step` renamed `@one_fixture_per_step` for clarity. Old alias will remain across at least one minor version.

New `@cross_steps_fixture` decorator to declare that a function-scoped fixture should be created once and reused across all steps. This decorator and the already existing decorator `@one_fixture_per_step` provide a consistent and very intuitive way for users to declare how fixtures should behave in presence of steps. Fixes [#24](https://github.com/smarie/python-pytest-steps/issues/24).

Minor: `_get_step_param_names_or_default` moved to `steps` submodule.

### 1.4.0 - Documentation + Possibility to call a decorated test function manually.

New features:
 - It is now possible to call a test function decorated with `@test_steps` manually, for example to run it once at the beinning of a test session in order for all imports to be done before actual execution. Fixes [#22](https://github.com/smarie/python-pytest-steps/issues/22)

Minor:
 - `steps_harvest_df_utils` submodule is now correctly listed in `__all__`.
 - Improved docstrings and documentation page for API reference.

### 1.3.0 - Default fixtures for `pytest-harvest`

When steps are present, we now offer `session_results_df_steps_pivoted` and `module_results_df_steps_pivoted` default fixtures, to align with `pytest-harvest` >= 1.1 default fixtures `session_results_df` and `module_results_df`. Fixes [#23](https://github.com/smarie/python-pytest-steps/issues/23).

Improved API to manipulate `pytest-harvest` results objects in presence of steps:
 - Renamed `handle_steps_in_synthesis_dct` into `handle_steps_in_results_dct` (old alias is kept for this version). Renamed parameter `raise_if_no_step` to `raise_if_one_test_without_step_id`. Added a parameter `keep_orig_id`, by default (True) the original test id is kept for reference. Another parameter `no_steps_policy` allows users to create_function the method transparent if no steps are found.
 - new method `handle_steps_in_results_df` to perform the same things than `handle_steps_in_results_dct` but directly on the synthesis dataframe. The parameters are almost the same.
 - New method `flatten_multilevel_columns` to diretly apply `get_flattened_multilevel_columns` on the columns of a dataframe
 - `pivot_steps_on_df` now has the ability to detect parameter and fixture names from the provided pytest session, so as not to pivot them (they should be stable across steps). It also provides an `error_if_not_present` parameter

### 1.2.1 - Alignment with pytest-harvest 1.2.1

`pytest-harvest` 1.2 provides default fixtures and fixes a few issues in the synthesis dictionary (in particular fixture and fixture parameters were overlapping each other). We aligned `pytest-steps` to leverage it.
 
Also, minor improvement: the unique id internally generated for each test now includes the pytest object. In practice this does not change anything for most use cases, but it might allow later refactoring, and better diagnostics.

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
 - 5 new utility methods to support combining this plugin with `pytest-harvest` (see documentation for details): `handle_steps_in_results_dct`, `remove_step_from_test_id`, `get_all_pytest_param_names_except_step_id`, `pivot_steps_on_df`, `get_flattened_multilevel_columns`

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
