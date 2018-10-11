from inspect import isgeneratorfunction

from pytest_steps.steps_generator import get_generator_decorator
from pytest_steps.steps_parametrizer import get_parametrize_decorator


TEST_STEP_MODE_AUTO = 'auto'
TEST_STEP_MODE_GENERATOR = 'generator'
TEST_STEP_MODE_PARAMETRIZER = 'parametrizer'
TEST_STEP_ARGNAME_DEFAULT = 'test_step'
STEPS_DATA_HOLDER_NAME_DEFAULT = 'steps_data'


def test_steps(*steps, **kwargs):
    """
    Decorates a test function so as to automatically parametrize it with all steps listed as arguments.

    There are two main ways to use this decorator:
     1. decorate a test function generator and provide as many step names as there are 'yield' statements in the
    generator
     2. decorate a test function with a 'test_step' parameter, and use this parameter in the test function body to
     decide what to execute.

    Usage with a generator:
    -----------------------
    Simply put as many `yield` statements in the decorated test function, as there are declared steps in the decorator:

    ```python
    from pytest_steps import test_steps

    @test_steps('step_a', 'step_b', 'step_c')
    def test_suite():
        # Step A
        assert not False  # replace with your logic
        intermediate_a = 'hello'
        yield

        # Step B
        assert not False  # replace with your logic
        yield

        # Step C
        new_text = intermediate_a + " ... augmented"
        assert len(new_text) == 56
        yield
    ```

    You can `yield <step_name>` in order to activate the automatic check that each step is the right one.

    By default all steps depend on all previous steps in order. Optional steps should be wrapped with `optional_step`
    and should yield the associated context. You can also declare that they depend on other optional steps:

    ```python
    from pytest_steps import test_steps, optional_step

    @test_steps('step_a', 'step_b', 'step_c', 'step_d')
    def test_suite_opt():
        # Step A
        assert not False
        yield

        # Step B
        with optional_step('step_b') as step_b:
            assert False
        yield step_b

        # Step C depends on step B
        with optional_step('step_c', depends_on=step_b) as step_c:
            if step_c.should_run():
                assert True
        yield step_c

        # Step D
        assert not False
        yield
    ```

    Finally if you use a function-scoped fixture and would like it to be different for each step, wrap that fixture in
    `@one_per_step`:

    ```python
    from pytest_steps import one_per_step

    @pytest.fixture
    @one_per_step
    def my_fixture():
        '''Simple function-scoped fixture that return a new instance each time'''
        return MyFixture()
    ```

    Usage with a normal function with a parameter:
    ----------------------------------------------

    By default in this mode all steps are independent

    ```python
    from pytest_steps import test_steps

    @test_steps('step_a', 'step_b')
    def test_suite_1(test_step):
        # Execute the step according to name
        if test_step == 'step_a':
            step_a()
        elif test_step == 'step_b':
            step_b()

    def step_a():
        # perform this step ...
        print("step a")
        assert not False  # replace with your logic

    def step_b():
        # perform this step
        print("step b")
        assert not False  # replace with your logic
    ```

    You can add a 'results' parameter to your test function if you wish to share a `StepsDataHolder` object between your
    steps.

    ```python
    def step_a(steps_data: StepsDataHolder):
        # perform this step
        print("step a")
        assert not False

        # intermediate results can be stored in results
        results.intermediate_a = 'some intermediate result created in step a'

    def step_b(steps_data: StepsDataHolder):
        # perform this step, leveraging the previous step's results
        print("step b")
        new_text = results.intermediate_a + " ... augmented"
        print(new_text)
        assert len(new_text) == 56

    @test_steps(step_a, step_b)
    def test_suite_with_results(test_step, steps_data: StepsDataHolder):
        # Execute the step with access to the results holder
        test_step(steps_data)
    ```

    You can add as many `@pytest.mark.parametrize` and pytest fixtures in your test suite function, it should work as
    expected: the `steps_data` object will be created everytime a new parameter/fixture combination is created, but will
    be shared across steps with the same parameters and fixtures.

    :param steps: a list of test steps. They can be anything, but typically they will be string (when mode is
        'generator') or non-test (not prefixed with 'test') functions (when mode is 'parametrizer').
    :param mode: one of {'auto', 'generator', 'parametrizer'}. In 'auto'
    :param test_step_argname: the optional name of the function argument that will receive the test step object.
        Default is 'test_step'.
    :param steps_data_holder_name: the optional name of the function argument that will receive the shared `StepsDataHolder`
        object if present. Default is 'results'.
    :return:
    """
    # python 2 compatibility: no keyword arguments can follow a *args.
    step_mode = kwargs.pop('mode', TEST_STEP_MODE_AUTO)
    test_step_argname = kwargs.pop('test_step_argname', TEST_STEP_ARGNAME_DEFAULT)
    steps_data_holder_name = kwargs.pop('steps_data_holder_name', STEPS_DATA_HOLDER_NAME_DEFAULT)
    if len(kwargs) > 0:
        raise ValueError("Invalid argument(s): " + str(kwargs.keys()))

    # create decorator according to mode
    if step_mode == TEST_STEP_MODE_GENERATOR:
        steps_decorator = get_generator_decorator(steps)

    elif step_mode == TEST_STEP_MODE_PARAMETRIZER:
        steps_decorator = get_parametrize_decorator(steps, steps_data_holder_name, test_step_argname)

    elif step_mode == TEST_STEP_MODE_AUTO:
        # in this mode we decide later, when seeing the function
        def steps_decorator(test_fun):
            # check if the function is a generator function or not
            if isgeneratorfunction(test_fun):
                decorator = get_generator_decorator(steps)
            else:
                decorator = get_parametrize_decorator(steps, steps_data_holder_name, test_step_argname)

            return decorator(test_fun)
    else:
        raise ValueError("Invalid step mode: %s" % step_mode)

    return steps_decorator


test_steps.__test__ = False  # to prevent pytest to think that this is a test !
