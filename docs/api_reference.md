# API reference

In general, using `help(symbol)` is the recommended way to get the latest documentation. In addition, this page provides an overview of the various elements in this package.

### `@test_steps`

Decorates a test function so as to automatically parametrize it with all steps listed as arguments.

Test steps can be function as shown below, or anything else.

```python
from pytest_steps import test_steps

def step_a():
    # perform this step
    print("step a")
    assert not False

def step_b():
    # perform this step
    print("step b")
    assert not False

@test_steps(step_a, step_b)
def test_suite_no_results(test_step):
    # Execute the step
    test_step()
```

You can add a 'steps_data' parameter to your test function if you wish to share a `StepsDataHolder` object between your steps.

```python    
def step_a(steps_data):
    # perform this step
    print("step a")
    assert not False

    # intermediate results can be stored in steps_data
    steps_data.intermediate_a = 'some intermediate result created in step a'

def step_b(steps_data):
    # perform this step, leveraging the previous step's results
    print("step b")
    new_text = steps_data.intermediate_a + " ... augmented"
    print(new_text)
    assert len(new_text) == 56

@test_steps(step_a, step_b)
def test_suite_with_results(test_step, steps_data: StepsDataHolder):
    # Execute the step with access to the steps_data holder
    test_step(steps_data)
```

You can add as many `@pytest.mark.parametrize` and pytest fixtures in your test suite function, it should work as expected: a new `steps_data` instance will be created everytime a new parameter/fixture combination is created, and this instance will be shared across all steps with the same parameters and fixtures.

**Parameters:**

 - `steps`: a list of test steps. They can be anything, but typically they are non-test (not prefixed with 'test') functions.
 - `test_step_argname`: the optional name of the function argument that will receive the test step object. Default is 'test_step'.
 - `test_results_argname`: the optional name of the function argument that will receive the shared `StepsDataHolder` object if present. Default is 'steps_data'.


### `@depends_on`

`@depends_on(*steps, fail_instead_of_skip: bool = False)`

Decorates a test step object/function so as to automatically mark it as skipped (default) or failed if the dependency has not succeeded.

**Parameters:**

 - `steps`: a list of test steps that this step depends on. They can be anything, but typically they are non-test (not prefixed with 'test') functions.
 - `fail_instead_of_skip`: if set to True, the test will be marked as failed instead of skipped when the dependencies have not succeeded.
