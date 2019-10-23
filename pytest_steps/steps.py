from inspect import isgeneratorfunction
from sys import version_info
from six import string_types

from makefun import add_signature_parameters, wraps, with_signature

from pytest_steps.steps_common import get_pytest_node_hash_id, get_scope
from pytest_steps.steps_generator import get_generator_decorator, GENERATOR_MODE_STEP_ARGNAME
from pytest_steps.steps_parametrizer import get_parametrize_decorator


try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


TEST_STEP_MODE_AUTO = 'auto'
TEST_STEP_MODE_GENERATOR = 'generator'
TEST_STEP_MODE_PARAMETRIZER = 'parametrizer'
TEST_STEP_ARGNAME_DEFAULT = 'test_step'
STEPS_DATA_HOLDER_NAME_DEFAULT = 'steps_data'


# Python 3+: load the 'more explicit api' for `test_steps`
if version_info >= (3, 0):
    new_sig = """(*steps,
                  mode: str = TEST_STEP_MODE_AUTO,
                  test_step_argname: str = TEST_STEP_ARGNAME_DEFAULT,
                  steps_data_holder_name: str = STEPS_DATA_HOLDER_NAME_DEFAULT)"""
else:
    new_sig = None


@with_signature(new_sig)
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

    Everything that is placed **below** this decorator will be called only once for all steps. For example if you use
    it in combination with `@saved_fixture` from `pytest-harvest` you will get the two possible behaviours below
    depending on the order of the decorators:

    Order A (recommended):
    --------------------
    ```python
    @pytest.fixture
    @saved_fixture
    @cross_steps_fixture
    def my_cool_fixture():
        return random()
    ```

    `@saved_fixture` will be executed for *all* steps, and the saved object will be the same for all steps (since it
    will be cached by `@cross_steps_fixture`)


    Order B:
    -------
    ```python
    @pytest.fixture
    @cross_steps_fixture
    @saved_fixture
    def my_cool_fixture():
        return random()
    ```

    `@saved_fixture` will only be called for the first step. Indeed for subsequent steps, `@cross_steps_fixture`
    will directly return and prevent the underlying functions to be called. This is not a very interesting behaviour in
    this case, but with other decorators it might be interesting.

    ------

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


CROSS_STEPS_MARK = 'pytest_steps__is_cross_steps'


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

    # Create the function wrapper.
    # We will expose a new signature with additional 'request' arguments if needed, and the test step
    orig_sig = signature(fixture_fun)
    func_needs_request = 'request' in orig_sig.parameters
    if not func_needs_request:
        new_sig = add_signature_parameters(orig_sig, first=Parameter('request', kind=Parameter.POSITIONAL_OR_KEYWORD))
    else:
        new_sig = orig_sig

    def _init_and_check(request):
        """
        Checks that the current request is not session but a specific node.
        :param request:
        :return:
        """
        scope = get_scope(request)
        if scope == 'function':
            # function-scope: ok
            id_without_steps = get_pytest_node_hash_id(request.node,
                                                       params_to_ignore=_get_step_param_names_or_default(
                                                       step_param_names))
            return id_without_steps
        else:
            # session- or module-scope
            raise Exception("The `@cross_steps_fixture` decorator is only useful for function-scope fixtures. `%s`"
                            " seems to have scope='%s'. Consider removing `@cross_steps_fixture` or changing "
                            "the scope to 'function'." % (fixture_fun, scope))

    if not isgeneratorfunction(fixture_fun):
        @wraps(fixture_fun, new_sig=new_sig)
        def _steps_aware_decorated_function(*args, **kwargs):
            request = kwargs['request'] if func_needs_request else kwargs.pop('request')
            id_without_steps = _init_and_check(request)
            try:
                # already available: this is a subsequent step.
                return ref_dct[id_without_steps]
            except KeyError:
                # not yet cached, this is probably the first step
                res = fixture_fun(*args, **kwargs)
                ref_dct[id_without_steps] = res
                return res
    else:
        @wraps(fixture_fun, new_sig=new_sig)
        def _steps_aware_decorated_function(*args, **kwargs):
            request = kwargs['request'] if func_needs_request else kwargs.pop('request')
            id_without_steps = _init_and_check(request)
            try:
                # already available: this is a subsequent step.
                yield ref_dct[id_without_steps]
            except KeyError:
                # not yet cached, this is probably the first step
                gen = fixture_fun(*args, **kwargs)
                res = next(gen)
                ref_dct[id_without_steps] = res
                yield res
                # TODO this teardown hook should actually be executed after all steps...
                next(gen)

    # Tag the function as being "cross-step" for future usage
    setattr(_steps_aware_decorated_function, CROSS_STEPS_MARK, True)
    return _steps_aware_decorated_function


def _get_step_param_names_or_default(step_param_names):
    """

    :param step_param_names:
    :return: a list of step parameter names
    """
    if step_param_names is None:
        # default: cover both generator and legacy mode default names
        step_param_names = [GENERATOR_MODE_STEP_ARGNAME, TEST_STEP_ARGNAME_DEFAULT]
    elif isinstance(step_param_names, string_types):
        # singleton
        step_param_names = [step_param_names]
    return step_param_names
