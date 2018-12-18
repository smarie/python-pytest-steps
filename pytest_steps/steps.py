from inspect import isgeneratorfunction

from pytest_steps.decorator_hack import my_decorate
from pytest_steps.steps_common import get_pytest_node_hash_id
from pytest_steps.steps_generator import get_generator_decorator, GENERATOR_MODE_STEP_ARGNAME
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

    See https://smarie.github.io/python-pytest-steps/ for examples.

    :param steps: a list of test steps. They can be anything, but typically they will be string (when mode is
        'generator') or non-test (not prefixed with 'test') functions (when mode is 'parametrizer').
    :param mode: one of {'auto', 'generator', 'parametrizer'}. In 'auto' mode (default), the decorator will detect if
        your function is a generator or not. If it is a generator it will use the 'generator' mode, otherwise it will
        use the 'parametrizer' (explicit) mode.
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


def cross_steps_fixture(step_param_names):
    """
    A decorator for a function-scoped fixture so that it is not called for each step, but only once for all steps.

    Decorating your fixture with `@cross_steps_fixture` tells `@test_steps` to detect when the fixture function is
    called for the first step, to cache that first step instance, and to reuse it instead of calling your fixture
    function for subsequent steps. This results in all steps (with the same other parameters) using the same fixture
    instance.

    It is recommended that you put this decorator as the second decorator, right after `@pytest.fixture`:

    ```python
    @pytest.fixture
    @cross_steps_fixture
    def my_cool_fixture():
        return random()
    ```

    If you use custom test step parameter names and not the default, you will have to provide an exhaustive list in
    `step_param_names`.

    :param step_param_names: a singleton or iterable containing the names of the test step parameters used in the
        tests. By default the list is `[GENERATOR_MODE_STEP_ARGNAME, TEST_STEP_ARGNAME_DEFAULT]` to cover both
        generator-mode and legacy manual mode.
    :return:
    """
    if callable(step_param_names):
        # decorator used without argument, this is the function not the param
        return cross_steps_fixture_decorate(step_param_names)
    else:
        return cross_steps_fixture_decorate


def cross_steps_fixture_decorate(fixture_fun,
                                 step_param_names=None):
    """
    Implementation of the @cross_steps_fixture decorator, for manual decoration

    :param fixture_fun:
    :param step_param_names: a singleton or iterable containing the names of the test step parameters used in the
        tests. By default the list is `[GENERATOR_MODE_STEP_ARGNAME, TEST_STEP_ARGNAME_DEFAULT]` to cover both
        generator-mode and legacy manual mode.
    :return:
    """
    ref_dct = dict()

    if not isgeneratorfunction(fixture_fun):
        def _steps_aware_wrapper(f, request, *args, **kwargs):
            id_without_steps = get_pytest_node_hash_id(request.node,
                                                       params_to_ignore=_get_step_param_names_or_default(
                                                           step_param_names))
            try:
                # already available: this is a subsequent step.
                return ref_dct[id_without_steps]
            except KeyError:
                # not yet cached, this is probably the first step
                res = f(*args, **kwargs)
                ref_dct[id_without_steps] = res
                return res
    else:
        def _steps_aware_wrapper(f, request, *args, **kwargs):
            """

            :return:
            """
            id_without_steps = get_pytest_node_hash_id(request.node,
                                                       params_to_ignore=_get_step_param_names_or_default(
                                                           step_param_names))
            try:
                # already available: this is a subsequent step.
                yield ref_dct[id_without_steps]
            except KeyError:
                # not yet cached, this is probably the first step
                gen = f(*args, **kwargs)
                res = next(gen)
                ref_dct[id_without_steps] = res
                yield res
                next(gen)

    _steps_aware_decorated_function = my_decorate(fixture_fun, _steps_aware_wrapper, additional_args=('request',))
    return _steps_aware_decorated_function


def _get_step_param_names_or_default(step_param_names):
    """

    :param step_param_names:
    :return: a list of step parameter names
    """
    if step_param_names is None:
        # default: cover both generator and legacy mode default names
        step_param_names = [GENERATOR_MODE_STEP_ARGNAME, TEST_STEP_ARGNAME_DEFAULT]
    elif isinstance(step_param_names, str):
        # singleton
        step_param_names = [step_param_names]
    return step_param_names
