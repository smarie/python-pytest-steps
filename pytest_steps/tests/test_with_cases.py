from pytest_cases import parametrize_with_cases
from pytest_steps import test_steps


def case_dummy():
    return 'hello'


@test_steps('a', 'b')
@parametrize_with_cases("c", cases=case_dummy)
def test_basic_modeling(c):
    yield 'a'
    yield 'b'
