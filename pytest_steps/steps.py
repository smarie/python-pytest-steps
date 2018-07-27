from functools import lru_cache
from inspect import signature, getmodule

import pytest

from pytest_steps.decorator_hack import my_decorate


class StepsDataHolder:
    """
    An object that is passed along the various steps of your tests.
    You can put intermediate results in here, and find them in the following steps.

    Note: you can use `vars(results)` to see the available results.
    """
    pass


STEP_SUCCESS_FIELD = "__test_step_successful_for__"


class HashableDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def test_steps(*steps, test_step_name: str= 'test_step', steps_data_holder_name: str= 'steps_data'):
    """
    Decorates a test function so as to automatically parametrize it with all steps listed as arguments.

    When the steps are functions, this is equivalent to
    `@pytest.mark.parametrize(test_step_name, steps, ids=lambda x: x.__name__)`

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

    You can add a 'results' parameter to your test function if you wish to share a `StepsDataHolder` object between your
    steps.

    ```python
    def step_a(results: StepsDataHolder):
        # perform this step
        print("step a")
        assert not False

        # intermediate results can be stored in results
        results.intermediate_a = 'some intermediate result created in step a'

    def step_b(results: StepsDataHolder):
        # perform this step, leveraging the previous step's results
        print("step b")
        new_text = results.intermediate_a + " ... augmented"
        print(new_text)
        assert len(new_text) == 56

    @test_steps(step_a, step_b)
    def test_suite_with_results(test_step, results: StepsDataHolder):
        # Execute the step with access to the results holder
        test_step(results)
    ```

    You can add as many `@pytest.mark.parametrize` and pytest fixtures in your test suite function, it should work as
    expected: the steps_data object will be created everytime a new parameter/fixture combination is created, but will
    be shared across steps with the same parameters and fixtures.

    :param steps: a list of test steps. They can be anything, but typically they are non-test (not prefixed with 'test')
        functions.
    :param test_step_name: the optional name of the function argument that will receive the test step object.
        Default is 'test_step'.
    :param steps_data_holder_name: the optional name of the function argument that will receive the shared `StepsDataHolder`
        object if present. Default is 'results'.
    :return:
    """
    def steps_decorator(test_func):
        """
        The generated test function decorator.

        It is equivalent to @mark.parametrize('case_data', cases) where cases is a tuple containing a CaseDataGetter for
        all case generator functions

        :param test_func:
        :return:
        """
        # Step ids
        def get_id(f):
            if callable(f) and hasattr(f, '__name__'):
                return f.__name__
            else:
                return str(f)

        step_ids = [get_id(f) for f in steps]

        # Depending on the presence of steps_data_holder_name in signature, create a cached fixture for steps data
        s = signature(test_func)
        if steps_data_holder_name in s.parameters:
            # the user wishes to share results across test steps. Create a cached fixture
            @lru_cache(maxsize=None)
            def get_results_holder(**kwargs):
                """
                A factory for the StepsDataHolder objects. Since it uses @lru_cache, the same StepsDataHolder will be
                returned when the keyword arguments are the same.

                :param kwargs:
                :return:
                """
                return StepsDataHolder()  # TODO use Munch or MaxiMunch from `mixture` project, when publicly available ?

            @pytest.fixture(name=steps_data_holder_name)
            def results(request):
                """
                The fixture for the StepsDataHolder. It implements an intelligent cache so that the same StepsDataHolder
                object is used across test steps.

                :param request:
                :return:
                """
                # The object should be different everytime anything changes, except when the test step changes
                dont_change_when_these_change = {test_step_name}

                # We also do not want the 'results' itself nor the pytest 'request' to be taken into account, since
                # the first is not yet defined and the second is an internal pytest variable
                dont_change_when_these_change.update({steps_data_holder_name, 'request'})

                # List the values of all the test function parameters that matter
                kwargs = {argname: request.getfuncargvalue(argname)
                          for argname in request.funcargnames
                          if argname not in dont_change_when_these_change}

                # Get or create the cached Result holder for this combination of parameters
                return get_results_holder(**kwargs)

            # Add the fixture dynamically: we have to add it to the function holder module as explained in
            # https://github.com/pytest-dev/pytest/issues/2424
            module = getmodule(test_func)
            if steps_data_holder_name not in dir(module):
                setattr(module, steps_data_holder_name, results)
            else:
                raise ValueError("The {} fixture already exists in module {}: please specify a different "
                                 "`steps_data_holder_name` in `@test_steps`".format(steps_data_holder_name, module))

        # Parametrize the function with the test steps
        parametrizer = pytest.mark.parametrize(test_step_name, steps, ids=step_ids)

        # Finally, if there are some steps that are marked as having a dependency,
        use_dependency = any(hasattr(step, DEPENDS_ON_FIELD) for step in steps)
        if use_dependency:
            # Create a test function wrapper that will replace the test steps with wrapped ones before injecting them
            def dependency_mgr_wrapper(f, *args, **kwargs):
                # first check the request
                f_sig = signature(f)
                if 'request' not in f_sig.parameters:
                    # easy: that's the first positional arg since we have added it (see `my_decorate`)
                    request = args[0]
                    args = args[1:]
                else:
                    # harder: request is in the args and/or kwargs. Thanks, inspect package !
                    request = f_sig.bind(*args, **kwargs).arguments['request']

                # (a) retrieve the current step and parameters/fixtures combination
                current_step = request.getfuncargvalue(test_step_name)
                params = {n: request.getfuncargvalue(n)
                          for n in request.funcargnames if n not in {test_step_name, steps_data_holder_name, 'request'}}
                params = HashableDict(params)

                # Make sure that all steps have a field indicating their execution success
                if not hasattr(current_step, STEP_SUCCESS_FIELD):
                    setattr(current_step, STEP_SUCCESS_FIELD, dict())

                # (b) skip or fail it if needed
                dependencies, should_fail = getattr(current_step, DEPENDS_ON_FIELD, ([], False))
                if not all(hasattr(step, STEP_SUCCESS_FIELD) for step in dependencies):
                    raise ValueError("Test step {} depends on another step that has not yet been executed. In current "
                                     "version the steps execution order is manual, make sure it is correct."
                                     "".format(current_step.__name__))
                deps_successess = {step: getattr(step, STEP_SUCCESS_FIELD).get(params, False) for step in dependencies}
                failed_deps = [d.__name__ for d, res in deps_successess.items() if res is False]
                if not all(deps_successess.values()):
                    msg = "This test step depends on other steps, and the following have failed: " + str(failed_deps)
                    if should_fail:
                        pytest.fail(msg)
                    else:
                        pytest.skip(msg)

                # (c) execute the function as usual
                res = f(*args, **kwargs)

                getattr(current_step, STEP_SUCCESS_FIELD)[params] = True

                return res

            # wrap the test function
            wrapped_test_function = my_decorate(test_func, dependency_mgr_wrapper, additional_args=['request'])

            wrapped_parametrized_test_function = parametrizer(wrapped_test_function)
            return wrapped_parametrized_test_function
        else:
            # no dependencies: no need to do complex things
            parametrized_test_func = parametrizer(test_func)
            return parametrized_test_func

    return steps_decorator


test_steps.__test__ = False  # to prevent pytest to think that this is a test !


def get_nonsuccessful_dependencies(step):
    """

    :param step:
    :return:
    """


DEPENDS_ON_FIELD = '__depends_on__'


def depends_on(*steps, fail_instead_of_skip: bool = False):
    """
    Decorates a test step object so as to automatically mark it as skipped (default) or failed if the dependency
    has not succeeded.

    :param steps: a list of test steps that this step depends on. They can be anything, but typically they are non-test
        (not prefixed with 'test') functions.
    :param fail_instead_of_skip: if set to True, the test will be marked as failed instead of skipped when the
        dependencies have not succeeded.
    :return:
    """
    def depends_on_decorator(step_func):
        """
        The generated test function decorator.

        :param step_func:
        :return:
        """
        if not callable(step_func):
            raise TypeError("@depends_on can only be used on test steps that are callables")

        # Remember the dependencies so that @test_steps knows
        setattr(step_func, DEPENDS_ON_FIELD, (steps, fail_instead_of_skip))

        return step_func

    return depends_on_decorator
