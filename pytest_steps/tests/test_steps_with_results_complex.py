import pytest

from pytest_steps import test_steps, StepsDataHolder


def step_a(steps_data: StepsDataHolder, stupid_param):
    """ Step a of the test """

    # perform this step
    print("step a - " + stupid_param)
    assert not False

    # Assert that the StepsDataHolder object is a brand new one everytime we start this step
    assert not hasattr(steps_data, 'intermediate_a')

    # intermediate results can be stored in steps_data
    steps_data.intermediate_a = 'some intermediate result created in step a for test ' + stupid_param

    assert not hasattr(steps_data, 'p')
    steps_data.p = stupid_param


def step_b(steps_data: StepsDataHolder, stupid_param):
    """ Step b of the test """

    # perform this step
    print("step b - " + stupid_param)

    # assert that step a has been done
    assert hasattr(steps_data, 'intermediate_a')
    # ... and that the StepsDataHolder object that we get is the one for our test suite (same parameters)
    assert steps_data.intermediate_a == 'some intermediate result created in step a for test ' + stupid_param

    new_text = steps_data.intermediate_a + " ... augmented"
    print(new_text)

    assert steps_data.p == stupid_param


@pytest.fixture(params=['F', 'G'])
def fix(request):
    return request.param


@pytest.mark.parametrize('really_stupid_param2', ["2A", "2B"])
@test_steps(step_a, step_b, steps_data_holder_name='results')
@pytest.mark.parametrize('stupid_param1', ["1a", "1b"])
def test_suite_with_results(test_step, stupid_param1, really_stupid_param2, fix, results: StepsDataHolder):
    """This test is extremely stupid but shows the extreme case where there are parameters and fixtures all over the
    place. It asserts that a new resultholder is created for all tests but that the same object is reused across steps
    """

    # Execute the step
    test_step(results, stupid_param1 + really_stupid_param2 + fix)
