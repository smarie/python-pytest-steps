# API reference

In general, using `help(symbol)` is the recommended way to get the latest documentation. In addition, this page provides an overview of the various elements in this package.

## Both modes

### `@test_steps`

```python
@test_steps(*steps, 
            mode: str = 'auto', 
            test_step_argname: str = 'step_name', 
            steps_data_holder_name: str = 'steps_data')
```

Decorates a test function so as to automatically parametrize it with all steps listed as arguments.

There are two main ways to use this decorator:

 1. decorate a test function generator and provide as many step names as there are 'yield' statements in the generator
 2. decorate a test function with a 'test_step' parameter, and use this parameter in the test function body to decide what to execute.
     
See [Home](../) for examples.

**Parameters:**

 - `steps`: a list of test steps. They can be anything, but typically they are non-test (not prefixed with 'test') functions.
 - `mode`: one of `{'auto', 'generator', 'parametrizer'}`. In `'auto'` mode (default), the decorator will detect if your function is a generator or not. If it is a generator it will use the *generator* mode, otherwise it will use the *parametrizer* (explicit) mode.
 - `test_step_argname`: the optional name of the function argument that will receive the test step object. Default is 'test_step'.
 - `test_results_argname`: the optional name of the function argument that will receive the shared `StepsDataHolder` object if present. Default is 'steps_data'.

### `@cross_steps_fixture`

A decorator for a function-scoped fixture so that it is not called for each step, but only once for all steps.

Decorating your fixture with `@cross_steps_fixture` tells `@test_steps` to detect when the fixture function is called for the first step, to cache that first step instance, and to reuse it instead of calling your fixture function for subsequent steps. This results in all steps (with the same other parameters) using the same fixture instance.

Everything that is placed **below** this decorator will be called only once for all steps. For example if you use it in combination with `@saved_fixture` from `pytest-harvest` you will get the two possible behaviours below depending on the order of the decorators:

 - Case A (recommended): `@saved_fixture` will be executed for *all* steps, and the saved object will be the same for all steps (since it will be cached by `@cross_steps_fixture`)

```python
@pytest.fixture
@saved_fixture
@cross_steps_fixture
def my_cool_fixture():
    return random()
```

 - Case B: `@saved_fixture` will only be called for the first step. Indeed for subsequent steps, `@cross_steps_fixture` will directly return and prevent the underlying functions to be called. This is not a very interesting behaviour in this case, but with other decorators it might be interesting.

```python
@pytest.fixture
@cross_steps_fixture
@saved_fixture
def my_cool_fixture():
    return random()
```
    
If you use custom test step parameter names and not the default, you will have to provide an exhaustive list in the `step_param_names` argument.


### `@one_fixture_per_step`

A decorator for a function-scoped fixture so that it works well with generator-mode test functions. You do not have to use it in parametrizer mode, although it does not hurt.

By default if you do not use this decorator but use the fixture in a generator-mode test function, only the fixture created for the first step will be injected in your test function, and all subsequent steps will see that same instance.

Decorating your fixture with `@one_fixture_per_step` tells `@test_steps` to transparently replace the fixture object instance by the one created for each step, before each step executes in your test function. This results in all steps using different fixture instances, as expected.

It is recommended that you put this decorator as the second decorator, right after `@pytest.fixture`:

```python
@pytest.fixture
@one_fixture_per_step
def my_cool_fixture():
    return random()
```

!!! note ""
    When a fixture is decorated with `@one_fixture_per_step`, the object that is injected in your test function is a transparent proxy of the fixture, so it behaves exactly like the fixture. If for some reason you want to get the "true" inner wrapped object, you can do so using `get_underlying_fixture(my_fixture)`.


## Generator mode

### `with optional_step`

```python
with optional_step(step_name: str, 
                   depends_on: Union[optional_step, Iterable[optional_step]] = None)
```

Context manager to use inside a test function body to create an optional step named `step_name` with optional dependencies on other optional steps. See [Home](../) for examples.

**Parameters:**

 - `step_name`: the name of this optional step. This name will be used in pytest failure/skip messages when other steps depend on this one and are skipped/failed because this one was skipped/failed.
 - `depends_on`: an optional dependency or list of dependencies, that should all be optional steps created with an `optional_step` context manager.

## Explicit/parametrizer mode

### `@depends_on`

```python
@depends_on(*steps, 
            fail_instead_of_skip: bool = False)
```

Decorates a test step object/function so as to automatically mark it as skipped (default) or failed if the dependency has not succeeded. This only works if the decorated object is directly used as argument in the main `@test_steps` decorator. Otherwise you can still use the shared results holder to skip manually, see [Home](../) for examples.

**Parameters:**

 - `steps`: a list of test steps that this step depends on. They can be anything, but typically they are non-test (not prefixed with 'test') functions.
 - `fail_instead_of_skip`: if set to True, the test will be marked as failed instead of skipped when the dependencies have not succeeded.


## `pytest-harvest` utility methods

### `handle_steps_in_results_dct`

```python
def handle_steps_in_results_dct(results_dct,
                                is_flat=False,
                                raise_if_one_test_without_step_id=False,
                                no_step_id='-',
                                step_param_names=None,
                                keep_orig_id=True,
                                no_steps_policy='raise'
                                )
```

Improves the synthesis dictionary so that

 - the keys are replaced with a tuple (new_test_id, step_id) where new_test_id is a step-independent test id
 - the 'step_id' parameter is removed from the contents

`is_flat` should be set to `True` if the dictionary has been flattened by `pytest-harvest`.

The step id is identified by looking at the pytest parameters, and finding one with a name included in the `step_param_names` list (`None` uses the default names). If no step id is found on an entry, it is replaced with the value of `no_step_id` except if `raise_if_one_test_without_step_id=True` - in which case an error is raised.
    
If all step ids are missing, for all entries in the dictionary, `no_steps_policy` determines what happens: it can either skip the whole function and return a copy of the input ('skip', or behave as usual ('ignore'), or raise an error ('raise'). 

If `keep_orig_id` is set to True (default), the original id is added to each entry.

### `handle_steps_in_results_df`

```python
def handle_steps_in_results_df(results_df,
                               raise_if_one_test_without_step_id=False,  # type: bool
                               no_step_id='-',  # type: str
                               step_param_names=None,  # type: Union[str, Iterable[str]]
                               keep_orig_id=True,  # type: bool
                               no_steps_policy='raise',  # type: str
                               inplace=False
                               ):
```

Improves the synthesis dataframe so that

 - the test_id index is replaced with a multilevel index (new_test_id, step_id) where new_test_id is a step-independent test id. A 'pytest_id' column remains with the original id except if keep_orig_id=False
 (default=True)
 - the 'step_id' parameter is removed from the contents

The step id is identified by looking at the columns, and finding one with a name included in the `step_param_names` list (`None` uses the default names). If no step id is found on an entry, it is replaced with the value of `no_step_id` except if `raise_if_one_test_without_step_id=True` - in which case an error is raised.
    
If all step ids are missing, for all entries in the dictionary, `no_steps_policy` determines what happens: it can either skip the whole function and return a copy of the input ('skip', or behave as usual ('ignore'), or raise an error ('raise').

If `keep_orig_id` is set to True (default), the original id is added as a new column.

If `inplace` is `False` (default), a new dataframe will be returned. Otherwise the input dataframe will be modified inplace and nothing will be returned.

### `pivot_steps_on_df`

```python
def pivot_steps_on_df(results_df,
                      pytest_session=None,
                      cross_steps_columns=None,  # type: List[str]
                      error_if_not_present=True  # type: bool
                      ):
```

Pivots the dataframe so that there is one row per pytest_obj[params except step id] containing all steps info. The input dataframe should have a multilevel index with two levels (test id, step id) and with names
(`results_df.index.names` should be set). The test id should be independent on the step id. 

### `flatten_multilevel_columns`

```python
def flatten_multilevel_columns(df,
                               sep='/'  # type: str
                               ):
```

Replaces the multilevel columns (typically after a pivot) with single-level ones, where the names contain all levels concatenated with the separator `sep`. For example when the two levels are `foo` and `bar`, the single level becomes `foo/bar`.

This method is a shortcut for `df.columns = get_flattened_multilevel_columns(df)`.

### Lower-level methods

#### `remove_step_from_test_id`

#### `get_all_pytest_param_names_except_step_id`

#### `get_flattened_multilevel_columns`
