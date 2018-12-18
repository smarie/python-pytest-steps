from collections import Iterable as It

import six
from six import raise_from
from wrapt import ObjectProxy

try:  # python 3.2+
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature

from inspect import isgeneratorfunction

try:  # python 3+
    from typing import Iterable, Any, Union
except ImportError:
    pass

import pytest

from pytest_steps.steps_common import create_pytest_param_str_id, get_pytest_node_hash_id
from pytest_steps.decorator_hack import my_decorate


class ExceptionHook(object):
    """
    A context manager used to register a hook for exceptions.
    This hook (a method provided in constructor) will be called if an exception is caught.
    The exception will then be raised as usual.

    Example:
    --------
    >>>with ExceptionHook(print):
    >>>    assert False

    The hook method ('print' in the above example) will be called with the type of exception, the exception value,
    and the exception traceback, before the exception is actually raised.
    """
    def __init__(self, exc_handler):
        """
        Constructor.

        :param exc_handler: the method that should be called if an exception is raised inside this context manager.
        """
        self.exc_handler = exc_handler

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.exc_handler(exc_type, exc_val, exc_tb)

        # return False so that the exception is always raised
        return False


class StepExecutionError(Exception):
    """
    Exception raised by a StepsMonitor when a step cannot be executed because the underlying generator function
    returned a StopIteration.
    """
    def __init__(self, step_name):
        self.step_name = step_name
        Exception.__init__(self)

    def __str__(self):
        return "Error executing step '%s': could not reach the next `yield` statement (received `StopIteration`). This " \
               "may be caused by use of a `return` statement instead of a `yield`, or by a missing `yield`" \
               "" % self.step_name


class StepYieldError(Exception):
    """
    Exception raised by a StepsMonitor when a step does not yield anything (None), or yields a string that is not the
    correct step name, or yields an object that is not an `optional_step`
    """
    def __init__(self, step_name, received):
        self.step_name = step_name
        self.received = received
        Exception.__init__(self)

    def __str__(self):
        return "Error collecting results from step '%s': received '%s' from the `yield` statement, which is different" \
               " from the current step or step name. Please either use `yield`, `yield '%s'` or wrap your step with " \
               "`with optional_step(...) as my_step:` and use `yield my_step`" \
               % (self.step_name, self.received, self.step_name)


class _OnePerStepFixtureProxy(ObjectProxy):
    """
    An object container for which one can change the inner instance.
    By default wrapt.ObjectProxy does the job perfectly, so this object behaves
    transparently like the fixture it wraps.

    If for some reason you still wish to access the underlying fixture object, please rely on the public API
    `get_underlying_fixture(obj)` rather than calling `obj.__wrapped__`.

    We go one step further by also proxying the representation
    """
    def __repr__(self):
        return repr(self.__wrapped__)


def is_replacable_fixture_wrapper(obj):
    """
    Returns True when the object results from a function-scoped fixture that has been decorated with @one_per_step.

    In that case the fixture value of the first step is wrapped in a `_OnePerStepFixtureProxy`, so that we can inject the
    other fixture values in it later. Indeed otherwise the fixture values for the other steps will never be injected in
    the generator test function (because its args are provided only once at the first step).

    :param obj:
    :return:
    """
    return isinstance(obj, _OnePerStepFixtureProxy)


def replace_fixture(rfw1, rfw2):
    """
    Replaces the contents of fixture obj1 with the ones from fixture obj2. This only works if both are replaceable
    fixture wrappers

    :param rfw1:
    :param rfw2:
    :return:
    """
    if is_replacable_fixture_wrapper(rfw1) and is_replacable_fixture_wrapper(rfw2):
        rfw1.__wrapped__ = rfw2.__wrapped__
    else:
        raise TypeError("both objects should come from the same fixture, decorated with @one_per_step")


def get_underlying_fixture(rfw):
    """
    Returns the underlying fixture object inside this fixture wrapper, or returns the fixture itself in case it is
    not a one_per_step fixture wrapper

    :param rfw:
    :return:
    """
    if is_replacable_fixture_wrapper(rfw):
        return rfw.__wrapped__
    else:
        return rfw


def one_per_step(*args):
    """
    A decorator for a function-scoped fixture so that it works well with generator-mode test functions.

    By default if you do not use this decorator but use the fixture in a generator-mode test function, only the
    fixture created for the first step will be injected in your test function, and all subsequent steps will see that
    same instance.

    Decorating your fixture with `@one_per_step` tells `@test_steps` to transparently replace_fixture the fixture object
    instance by the one created for each step, before each step executes in your test function. This results in all
    steps using different fixture instances, as expected.

    It is recommended that you put this decorator as the second decorator, right after `@pytest.fixture`:

    ```python
    @pytest.fixture
    @one_per_step
    def my_cool_fixture():
        return random()
    ```

    :return:
    """
    if len(args) == 1 and callable(args[0]):
        return one_per_step_decorate(args[0])
    else:
        return one_per_step_decorate


def one_per_step_decorate(fixture_fun):
    """ Implementation of the @one_per_step decorator, for manual decoration"""

    if not isgeneratorfunction(fixture_fun):
        def _steps_aware_wrapper(f, *args, **kwargs):
            """

            :return:
            """
            res = f(*args, **kwargs)
            return _OnePerStepFixtureProxy(res)
    else:
        def _steps_aware_wrapper(f, *args, **kwargs):
            """

            :return:
            """
            gen = f(*args, **kwargs)
            res = next(gen)
            yield _OnePerStepFixtureProxy(res)
            next(gen)

    _steps_aware_decorated_function = my_decorate(fixture_fun, _steps_aware_wrapper)
    return _steps_aware_decorated_function


class StepsMonitor(object):
    """
    An object responsible to _monitor execution of a test function with steps.
    The function should be a generator
    """
    def __init__(self, step_names, test_function, *first_step_args, **first_step_kwargs):
        """
        Constructor with declaration of all step names in advance,
        as well as the test function to execute and the first step args and kwargs

        Nothing will be executed here, the test function will only be called once to create the generator.

        :param step_names:
        :param test_function:
        :param first_step_args:
        :param first_step_kwargs:
        """
        self.steps = step_names
        self.exceptions = dict()

        # Remember objects that should be replaced in subsequent steps
        # -- for positional arguments, store in a dict under key=position
        self.replaceable_args = dict()
        for i, a in enumerate(first_step_args):
            if is_replacable_fixture_wrapper(a):
                self.replaceable_args[i] = a

        # -- for keyword arguments, store in a dict under key=name
        self.replaceable_kwargs = dict()
        for k, a in first_step_kwargs.items():
            if is_replacable_fixture_wrapper(a):
                self.replaceable_kwargs[k] = a

        # create the generator
        self.gen = test_function(*first_step_args, **first_step_kwargs)

    def can_execute(self, step_name):
        """
        As of today a step can execute if there are no registered exceptions (in previous mandatory steps).
        :param step_name:
        :return:
        """
        return len(self.exceptions) == 0

    def execute(self, step_name, *args, **kwargs):
        """
        Executes one iteration of the monitored generator.

        :param step_name:
        :return:
        """

        if self.can_execute(step_name):
            # Replace all objects that should be replaced
            for i, a in self.replaceable_args.items():
                replace_fixture(a, args[i])
            for k, a in self.replaceable_kwargs.items():
                replace_fixture(a, kwargs[k])

            # Execute the step
            with self._monitor(step_name):
                try:
                    res = next(self.gen)
                except StopIteration as e:
                    raise_from(StepExecutionError(step_name), e)

            # Manage exceptions in optional steps
            if res is None:
                # We now accept None yields
                # raise StepYieldError(step_name, None)
                pass

            elif isinstance(res, str):
                if res != step_name:
                    raise StepYieldError(step_name, res)

            elif isinstance(res, optional_step):
                # optional step: check if the execution went well
                if res.exec_result is None:
                    raise ValueError("Internal error: this should not happen")

                elif isinstance(res.exec_result, OptionalStepException):
                    # An exception happened in the optional step. We can now raise it safely
                    # (raising it sooner would break the generator)
                    raise six.reraise(res.exec_result.exc_type, res.exec_result.exc_val, res.exec_result.tb)

                elif isinstance(res.exec_result, _DependentTestsNotRunException):
                    # This exception has been put here to declare that the optional step did not run because a
                    # dependency is missing. >> Skip or fail
                    # TODO add fail_instead_of_skip argument like in depends_on
                    should_fail = False
                    msg = "This test step '%s' depends on other steps, and the following have failed: %s" \
                          "" % (step_name, res.exec_result.dependency_names)
                    if should_fail:
                        pytest.fail(msg)
                    else:
                        pytest.skip(msg)
                elif res.exec_result is True:
                    # normal execution success
                    pass
                else:
                    raise ValueError("Internal error: this should not happen")
            else:
                # the generator yielded a res that is not of an accepted type
                raise StepYieldError(step_name, res)
        else:
            # A mandatory step failed before this one. The generator is broken, no need to even try >> Skip or fail
            # TODO add fail_instead_of_skip argument like in depends_on
            should_fail2 = False
            failed_step = next(iter(self.exceptions.keys())) if len(self.exceptions) == 1 \
                else list(self.exceptions.keys())
            msg = "This test step '%s' is not run because non-optional previous step '%s' has failed" \
                  "" % (step_name, failed_step)
            if should_fail2:
                pytest.fail(msg)
            else:
                pytest.skip(msg)

    def _monitor(self, step_name):
        """ returns a context manager that registers all captured exceptions in self, under given step name """

        def handle_exception(exc_type, exc_val, exc_tb):
            if exc_type in {_DependentTestsNotRunException, OptionalStepException}:
                # Do not register this exception
                pass
            else:
                self.exceptions[step_name] = exc_type, exc_val, exc_tb

        return ExceptionHook(handle_exception)


class StepMonitorsContainer(dict):
    """
    A dictionary of step monitors
    It contains all the StepsMonitor created for this function.
    there will be one StepsMonitor created for each unique function call
    """

    def __init__(self, test_func, step_ids):
        self.test_func = test_func
        self.step_ids = step_ids
        dict.__init__(self)

    def get_execution_monitor(self, pytest_node, *args, **kwargs):
        """
        Returns the StepsMonitor in charge of monitoring execution of the provided pytest node. The same StepsMonitor
        will be used to execute all steps of the generator function.

        If there is no monitor yet (first function call with this combination of parameters), then one is created,
        that will be used subsequently.

        Note: for readability we do not use a @lru_cache anymore but an explicit string id (more maintainable). Also
        this is more robust because it does not require any of *args, **kwargs to be hash-able.

        :param pytest_node:
        :param args:
        :param kwargs:
        :return:
        """
        # Get the unique id that is shared between the steps of the same execution, by removing the step parameter
        # Note: when the id was using not only param values but also fixture values we had to discard
        # 'request' and maybe some fixtures here. But that's not the case anymore,simply discard the "test step" param
        id_without_steps = get_pytest_node_hash_id(pytest_node, params_to_ignore=(GENERATOR_MODE_STEP_ARGNAME,))

        if id_without_steps not in self:
            # First time we call the function with this combination of parameters
            # print("DEBUG - creating StepsMonitor for %s" % id_without_steps)

            # create the monitor, in charge of managing the execution flow
            self[id_without_steps] = StepsMonitor(self.step_ids, self.test_func, *args, **kwargs)

        return self[id_without_steps]


GENERATOR_MODE_STEP_ARGNAME = "________step_name_"


def get_generator_decorator(steps  # type: Iterable[Any]
                            ):
    """
    Subroutine of `test_steps` used to perform the test function parametrization when mode is 'generator'.

    :param steps: a list of steps that the decorated function is supposed to perform. The decorated function should be
        a generator, and should `yield` as many steps as declared in the decorator.
    :return: a function decorator
    """
    def steps_decorator(test_func):
        """
        The test function decorator. When a function is decorated it
         - checks that the function is a generator
         - checks that the function signature does not contain our private name `GENERATOR_MODE_STEP_ARGNAME` "by chance"
         - wraps the function
        :param test_func:
        :return:
        """

        # ------VALIDATION -------
        # Check if function is a generator
        if not isgeneratorfunction(test_func):
            raise ValueError("Decorated function is not a generator. You either forgot to add `yield` statements in "
                             "its body, or you are using mode='generator' instead of mode='parametrizer' or 'auto'."
                             "See help(pytest_steps) for details")

        # check that our name for the additional 'test step' parameter is valid (it does not exist in f signature)
        f_sig = signature(test_func)
        test_step_argname = GENERATOR_MODE_STEP_ARGNAME
        if test_step_argname in f_sig.parameters:
            raise ValueError("Your test function relies on arg name %s that is needed by @test_steps in generator "
                             "mode" % test_step_argname)

        # ------CORE -------
        # Transform the steps into ids if needed
        step_ids = [create_pytest_param_str_id(f) for f in steps]

        # Create the container that will hold all execution monitors for this function
        all_monitors = StepMonitorsContainer(test_func, step_ids)

        # Create the function wrapper.
        # -- first create the logic
        def step_function_wrapper(f, request, step_name, *args, **kwargs):
            if request is None:
                # we are manually called outside of pytest. let's execute all steps at nce
                if step_name is None:
                    # print("@test_steps - decorated function '%s' is being called manually. The `%s` parameter is set "
                    #       "to None so all steps will be executed in order" % (f, test_step_argname))
                    step_names = step_ids
                else:
                    # print("@test_steps - decorated function '%s' is being called manually. The `%s` parameter is set "
                    #       "to %s so only these steps will be executed in order. Note that the order should be feasible"
                    #       "" % (f, test_step_argname, step_name))
                    if not isinstance(step_name, (list, tuple)):
                        step_names = [create_pytest_param_str_id(step_name)]
                    else:
                        step_names = [create_pytest_param_str_id(f) for f in steps]
                steps_monitor = StepsMonitor(step_ids, test_func, *args, **kwargs)
                for i, (step_name, ref_step_name) in enumerate(zip(step_names, step_ids)):
                    if step_name != ref_step_name:
                        raise ValueError("Incorrect sequence of steps provided for manual execution. Step #%s should"
                                         " be named '%s', found '%s'" % (i+1, ref_step_name, step_name))
                    steps_monitor.execute(step_name, *args, **kwargs)
            else:
                # Retrieve or create the corresponding execution monitor
                steps_monitor = all_monitors.get_execution_monitor(request.node, *args, **kwargs)

                # execute the step
                # print("DEBUG - executing step %s" % step_name)
                steps_monitor.execute(step_name, *args, **kwargs)

        # decorate it so that its signature is the same than test_func, with just an additional argument for test step
        # and if needed an additional argument for request
        wrapped_test_function = my_decorate(test_func, step_function_wrapper,
                                            additional_args=('request', test_step_argname))

        # Parametrize the wrapper function with the test step ids
        parametrizer = pytest.mark.parametrize(test_step_argname, step_ids, ids=str)
        parametrized_step_function_wrapper = parametrizer(wrapped_test_function)

        # finally return the parametrized wrapper
        return parametrized_step_function_wrapper

    return steps_decorator


# ----------- optional steps

class _DependentTestsNotRunException(Exception):
    """
    An internal exception that is actually never raised: it is used by the optional_step context manager
    """

    def __init__(self, step_name, dependency_name):
        self.step_name = step_name
        self.dependency_names = [dependency_name]


class OptionalStepException(Exception):
    """ A wrapper for an exception caught during an optional step execution """

    def __init__(self, exc_type, exc_val, tb):
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.tb = tb


class optional_step(object):
    """
    A context manager that you can use in *generator* mode in order to declare a step as independent, so that next
    steps in the generator can continue to execute even if this one fails.

    When this context manager is used you should not forget to yield the context object ! Otherwise the test step will
    be marked as successful even if it was not.

    You can optionally declare dependencies using the `depends_on=` argument in the constructor. If so, you should use
    the .should_execute() method if you wish your code block to be properly skipped.

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
    """

    def __init__(self,
                 step_name,       # type: str
                 depends_on=None  # type: Union[optional_step, Iterable[optional_step]]
                 ):
        """
        Creates the context manager for an optional step named `step_name` with optional dependencies on other
        optional steps.

        :param step_name: the name of this optional step. This name will be used in pytest failure/skip messages when
            other steps depend on this one and are skipped/failed because this one was skipped/failed.
        :param depends_on: an optional dependency or list of dependencies, that should all be optional steps created
            with an `optional_step` context manager.
        """
        # default values
        self.step_name = step_name
        self.exec_result = None
        self.depends_on = depends_on or []

        # coerce depends_on to a list
        if not isinstance(self.depends_on, It):
            self.depends_on = [self.depends_on]

        # dependencies should be optional steps too
        for dependency in self.depends_on:
            if not isinstance(dependency, optional_step):
                raise ValueError("depends_on should only contain optional_step instances")

    def __str__(self):
        return self.step_name

    def __enter__(self):
        # check that all dependencies have run
        for dependency in self.depends_on:
            if not dependency.ran_with_success():
                if self.exec_result is None:
                    self.exec_result = _DependentTestsNotRunException(self.step_name, dependency.step_name)
                else:
                    self.exec_result.dependency_names.append(dependency.step_name)

        # Unfortunately if we raise an exception here it will not be caught by the __exit__ method
        # So there is absolutely no way to prevent the code block to execute,
        # - even with an ExitStack (I tried !): indeed the ExitStack is nothing more than a context manager so if an
        # error is raised during its __enter__ method, then its __exit__ stack will not be called
        # - A PEP 377 was created for that but was rejected
        # - A hack also exists but it interferes with the debugger so it is too complex
        # See https://stackoverflow.com/questions/12594148/skipping-execution-of-with-block

        return self

    def should_run(self):
        """
        Return True if there are no exceptions, false otherwise
        :return:
        """
        return self.exec_result is None

    def __exit__(self, exc_type, exc_val, traceback):
        # Store this step's execution result for later
        if exc_type is None:
            if self.exec_result is None:
                # Success !
                self.exec_result = True
            else:
                # there was a dependency that had a failure, we can not forget it
                pass
        else:
            # Failure: remember the exception
            self.exec_result = OptionalStepException(exc_type, exc_val, traceback)

        # We have to *cancel* the exception in the stack of the test function since it is a generator and we need to
        # be able to execute subsequent steps
        # see https://docs.python.org/3/reference/datamodel.html#object.__exit__
        return True

    def ran_with_success(self):
        """
        Return True if self.exec_result is True
        :return:
        """
        return self.exec_result is True
