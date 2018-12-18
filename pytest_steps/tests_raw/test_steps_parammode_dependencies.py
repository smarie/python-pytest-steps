# META
# {'passed': 4, 'skipped': 1, 'failed': 2}
# END META
import pytest

from pytest_steps import test_steps, depends_on

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature


def step_a():
    """ Step a of the test """

    # perform this step
    print("step a")
    assert not False


def step_b():
    """ Step a of the test """

    # perform this step
    print("step b")
    assert False


@depends_on(step_a, step_b, fail_instead_of_skip=False)
def step_c():
    """ Step b of the test """

    # perform this step
    print("step c")
    assert not False


@test_steps(step_a, step_b, step_c)
def test_suite_no_results(request, test_step):
    """ In this test suite, the last step will be skipped because the second step failed (and there is a dependency) """

    # Execute the step
    test_step()


# test that manual call works in case of a dependency
def test_manual_call():
    """Tests that we can call the test manually with all the steps executed at once"""

    # A good way to know which parameters to fill is to use inspect
    s = signature(test_suite_no_results)
    assert list(s.parameters.keys()) == ['request', 'test_step']

    # Then fill request with blanks
    test_suite_no_results(None, step_a)
    with pytest.raises(AssertionError):
        test_suite_no_results(None, step_b)
    test_suite_no_results(None, step_c)

    # Whole suite
    with pytest.raises(AssertionError):
        test_suite_no_results(None, None)


@test_steps('step_a', 'step_b', 'step_c')
def test_suite_1(test_step):
    """ In this test suite the last step can "see" the dependency so it is still executed ..."""
    # Execute the step according to name
    if test_step == 'step_a':
        step_a()
    elif test_step == 'step_b':
        step_b()
    elif test_step == 'step_c':
        step_c()
