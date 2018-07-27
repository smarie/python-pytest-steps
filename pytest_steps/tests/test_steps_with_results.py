import pytest

from pytest_steps import test_steps, ResultsHolder


def step_a(results: ResultsHolder, stupid_param):
    """ Step a of the test """

    # perform this step
    print("step a - " + stupid_param)
    assert not False

    # Assert that the ResultsHolder object is a brand new one everytime we start this step
    assert not hasattr(results, 'intermediate_a')

    # intermediate results can be stored in results
    results.intermediate_a = 'some intermediate result created in step a for test ' + stupid_param

    assert not hasattr(results, 'p')
    results.p = stupid_param


def step_b(results: ResultsHolder, stupid_param):
    """ Step b of the test """

    # perform this step
    print("step b - " + stupid_param)

    # assert that step a has been done
    assert hasattr(results, 'intermediate_a')
    # ... and that the resultsholder object that we get is the one for our test suite (same parameters)
    assert results.intermediate_a == 'some intermediate result created in step a for test ' + stupid_param

    new_text = results.intermediate_a + " ... augmented"
    print(new_text)

    assert results.p == stupid_param


@pytest.fixture(params=['F', 'G'])
def fix(request):
    return request.param


@pytest.mark.parametrize('really_stupid_param2', ["2A", "2B"])
@test_steps(step_a, step_b)
@pytest.mark.parametrize('stupid_param1', ["1a", "1b"])
def test_suite_with_results(test_step, stupid_param1, really_stupid_param2, fix, results: ResultsHolder):
    """This test is extremely stupid but shows the extreme case where there are parameters and fixtures all over the
    place. It asserts that a new resultholder is created for all tests but that the same object is reused across steps
    """

    # Execute the step
    test_step(results, stupid_param1 + really_stupid_param2 + fix)
