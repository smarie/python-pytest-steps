from pytest_steps import test_steps, depends_on
from pytest_steps.tests import DEBUG


@test_steps('step_a', 'step_b', 'step_c')
def test_suite_1(test_step):
    # Execute the step according to name
    if test_step == 'step_a':
        step_a()
    elif test_step == 'step_b':
        step_b()
    elif test_step == 'step_c':
        step_c()


def step_a():
    """ Step a of the test """

    # perform this step
    print("step a")
    assert not False


def step_b():
    """ Step a of the test """

    # perform this step
    print("step b")
    if DEBUG:
        assert False


@depends_on(step_a, step_b, fail_instead_of_skip=False)
def step_c():
    """ Step b of the test """

    # perform this step
    print("step c")
    assert not False


@test_steps(step_a, step_b, step_c)
def test_suite_no_results(test_step, request):
    """ """

    # Execute the step
    test_step()
