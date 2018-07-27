from pytest_steps import test_steps, StepsDataHolder


def step_a(steps_data: StepsDataHolder):
    """ Step a of the test """

    # perform this step
    print("step a")
    assert not False

    # Assert that the StepsDataHolder object is a brand new one everytime we start this step
    assert not hasattr(steps_data, 'intermediate_a')

    # intermediate steps_data can be stored in steps_data
    steps_data.intermediate_a = 'some intermediate result created in step a'


def step_b(steps_data: StepsDataHolder):
    """ Step b of the test """

    # perform this step
    print("step b")

    # assert that step a has been done
    assert hasattr(steps_data, 'intermediate_a')
    # ... and that the StepsDataHolder object that we get is the one for our test suite (same parameters)
    assert steps_data.intermediate_a == 'some intermediate result created in step a'

    new_text = steps_data.intermediate_a + " ... augmented"
    print(new_text)


@test_steps(step_a, step_b)
def test_suite_with_steps_data(test_step, steps_data: StepsDataHolder):
    """This test is extremely stupid but shows the extreme case where there are parameters and fixtures all over the
    place. It asserts that a new resultholder is created for all tests but that the same object is reused across steps
    """

    # Execute the step
    test_step(steps_data)
