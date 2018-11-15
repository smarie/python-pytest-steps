# META
# {'passed': 4, 'skipped': 0, 'failed': 0}
# END META
from pytest_steps import test_steps


@test_steps('step_a', 'step_b')
def test_suite_no_results_str(test_step):
    # Execute the step according to name
    if test_step == 'step_a':
        step_a()
    elif test_step == 'step_b':
        step_b()


def step_a():
    """ Step a of the test """

    # perform this step
    print("step a")
    assert not False


def step_b():
    """ Step b of the test """

    # perform this step
    print("step b")
    assert not False


# equivalent to
# @pytest.mark.parametrize('test_step', (step_check_a, step_check_b), ids=lambda x: x.__name__)
@test_steps(step_a, step_b, test_step_argname='test_step_fun')
def test_suite_no_results_fun(test_step_fun, request):
    """ """

    # Execute the step
    test_step_fun()
