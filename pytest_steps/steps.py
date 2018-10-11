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
