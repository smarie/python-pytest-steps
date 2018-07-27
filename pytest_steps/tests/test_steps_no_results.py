from pytest_steps import test_steps


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
@test_steps(step_a, step_b)
def test_suite_no_results(test_step):
    """ """

    # Execute the step
    test_step()
