try:  # python 3.2+
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature

from inspect import getmodule

import pytest

from pytest_steps.decorator_hack import my_decorate
from pytest_steps.steps_common import get_pytest_id, get_fixture_value


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


def get_parametrize_decorator(steps, steps_data_holder_name, test_step_argname):
    """
    Subroutine of `pytest_steps` used to perform the test function parametrization when test step mode is 'parametrize'.
    See `pytest_steps` for details.

    :param steps:
    :param steps_data_holder_name:
    :param test_step_argname:
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
        step_ids = [get_pytest_id(f) for f in steps]

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
                return StepsDataHolder()  # TODO use Munch or MaxiMunch from `mixture` project, when publicly available?

            def results(request):
                """
                The fixture for the StepsDataHolder. It implements an intelligent cache so that the same StepsDataHolder
                object is used across test steps.

                :param request:
                :return:
                """
                # The object should be different everytime anything changes, except when the test step changes
                dont_change_when_these_change = {test_step_argname}

                # We also do not want the 'results' itself nor the pytest 'request' to be taken into account, since
                # the first is not yet defined and the second is an internal pytest variable
                dont_change_when_these_change.update({steps_data_holder_name, 'request'})

                # List the values of all the test function parameters that matter
                kwargs = {argname: get_fixture_value(request, argname)
                          for argname in request.funcargnames
                          if argname not in dont_change_when_these_change}

                # Get or create the cached Result holder for this combination of parameters
                return get_results_holder(**kwargs)

            # Create a fixture with custom name : this seems to work also for old pytest versions
            results.__name__ = steps_data_holder_name
            results = pytest.fixture(results)

            # Add the fixture dynamically: we have to add it to the function holder module as explained in
            # https://github.com/pytest-dev/pytest/issues/2424
            module = getmodule(test_func)
            if steps_data_holder_name not in dir(module):
                setattr(module, steps_data_holder_name, results)
            else:
                raise ValueError("The {} fixture already exists in module {}: please specify a different "
                                 "`steps_data_holder_name` in `@test_steps`".format(steps_data_holder_name, module))

        # Parametrize the function with the test steps
        parametrizer = pytest.mark.parametrize(test_step_argname, steps, ids=step_ids)

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
                current_step = get_fixture_value(request, test_step_argname)
                params = {n: get_fixture_value(request, n)
                          for n in request.funcargnames if n not in {test_step_argname, steps_data_holder_name, 'request'}}
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


def get_nonsuccessful_dependencies(step):
    """

    :param step:
    :return:
    """


DEPENDS_ON_FIELD = '__depends_on__'
_FAIL_INSTEAD_OF_SKIP_DEFAULT = False


def depends_on(*steps, **kwargs):
    """
    Decorates a test step object so as to automatically mark it as skipped (default) or failed if the dependency
    has not succeeded.

    :param steps: a list of test steps that this step depends on. They can be anything, but typically they are non-test
        (not prefixed with 'test') functions.
    :param fail_instead_of_skip: if set to True, the test will be marked as failed instead of skipped when the
        dependencies have not succeeded.
    :return:
    """
    # python 2 compatibility: no keyword arguments can follow an *args.
    fail_instead_of_skip = kwargs.pop('fail_instead_of_skip', _FAIL_INSTEAD_OF_SKIP_DEFAULT)
    if len(kwargs) > 0:
        raise ValueError("Invalid argument(s): " + str(kwargs.keys()))

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
