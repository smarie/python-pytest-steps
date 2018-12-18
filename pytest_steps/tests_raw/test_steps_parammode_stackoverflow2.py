# META
# {'passed': 3, 'skipped': 0, 'failed': 0}
# END META
from pytest_steps import test_steps, depends_on


def step_instance_start():
    # assert random.choice((True, False))
    assert True


@depends_on(step_instance_start)
def step_instance_stop():
    # assert random.choice((True, False))
    assert True


@depends_on(step_instance_start)
def step_instance_delete():
    # assert random.choice((True, False))
    assert True


@test_steps(step_instance_start, step_instance_stop, step_instance_delete)
def test_suite(test_step):
    # Execute the step
    test_step()
