# META
# {'passed': 3, 'skipped': 1, 'failed': 2}
# END META
from pytest_steps import test_steps, depends_on


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
def test_suite_no_results(test_step, request):
    """ In this test suite, the last step will be skipped because the second step failed (and there is a dependency) """

    # Execute the step
    test_step()


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
