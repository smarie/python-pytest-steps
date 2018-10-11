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

## Generator mode

### `@optional_step`

```python
@optional_step(step_name: str, 
               depends_on: Union[optional_step, Iterable[optional_step]] = None)
```

Context manager to use inside a test function body to create an optional step named `step_name` with optional dependencies on other optional steps. See [Home](../) for examples.

**Parameters:**

 - `step_name`: the name of this optional step. This name will be used in pytest failure/skip messages when other steps depend on this one and are skipped/failed because this one was skipped/failed.
 - `depends_on`: an optional dependency or list of dependencies, that should all be optional steps created with an `optional_step` context manager.

### `@one_per_step`

A decorator for a function-scoped fixture. By default if you do not use this decorator, only the fixture created  for the first step will be injected in your function, and all steps will see that same instance. 
    
Decorating your fixture with `@one_per_step` tells `@test_steps` to transparently replace the fixture object instance by the one created for each step, before each step executes. This results in all steps using different fixture instances.

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
