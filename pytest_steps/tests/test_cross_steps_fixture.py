import pytest
from pytest_steps import test_steps, cross_steps_fixture


usage_counter = 0


@pytest.fixture(params=[0])
@cross_steps_fixture
def my_cool_fixture():
    """A fixture that returns a new integer every time it is used. It is parametrized with a single param just to be
    sure that this is supported"""
    global usage_counter
    usage_counter += 1
    return usage_counter


@test_steps('a', 'b')
def test_gen_mode(my_cool_fixture):
    print('hello')
    yield
    print('world')
    assert my_cool_fixture == 1
    yield


def step_a():
    print('hello')


def step_b():
    print('world')


@test_steps(step_a, step_b)
def test_params_mode(test_step, my_cool_fixture):
    assert my_cool_fixture == 2
    test_step()


def test_fixture_has_been_called_once_per_fun():
    global usage_counter
    assert usage_counter == 2
