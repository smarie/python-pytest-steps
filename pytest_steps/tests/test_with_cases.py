from pytest_cases import cases_data
from pytest_steps import test_steps


def case_dummy():
    return 'hello'


@test_steps('a', 'b')
@cases_data(cases=case_dummy)
def test_basic_modeling(case_data):
    yield 'a'
    yield 'b'
