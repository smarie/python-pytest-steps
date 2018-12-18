# META
# {'passed': 3, 'skipped': 0, 'failed': 0}
# END META
from pytest_steps import test_steps, StepsDataHolder


class mylib:
    @classmethod
    def get_a(cls):
        return 'a'

    @classmethod
    def convert_a_to_b(cls, a):
        return 'b'

    @classmethod
    def works_with(cls, a, b):
        return True


def step_first(steps_data):
    steps_data.a = mylib.get_a()


def step_conversion(steps_data):
    steps_data.b = mylib.convert_a_to_b(steps_data.a)


def step_a_works_with_b(steps_data):
    assert mylib.works_with(steps_data.a, steps_data.b)


@test_steps(step_first, step_conversion, step_a_works_with_b)
def test_suite_with_shared_results(test_step,
                                   steps_data  # type: StepsDataHolder
                                   ):

    # Execute the step with access to the steps_data holder
    test_step(steps_data)
