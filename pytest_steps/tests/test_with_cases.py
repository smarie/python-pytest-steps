from pytest_cases import parametrize_with_cases
from pytest_steps import test_steps


def case_dummy():
    return 'hello'


@test_steps('a', 'b')
@parametrize_with_cases('case_data', cases=".")
def test_basic_modeling(case_data):
    yield 'a'
    yield 'b'
