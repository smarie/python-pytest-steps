from random import random

import pytest

from pytest_steps import test_steps


# the fixtures we'll use below
@pytest.fixture(params=[1])
def unhashable_fixture_no_param_conflict():
    return {'foo': random()}


@pytest.fixture(params=['hello-b-foo'])
def unhashable_fixture_param_approx_conflict():
    return {'foo': random()}


@pytest.fixture(params=['b'])
def unhashable_fixture_param_conflict():
    return {'foo': random()}


# -------------------------------


@test_steps('a', 'b')
@pytest.mark.parametrize('dummy_param', ['a', 'b'], ids="p={}".format)
def test_step_id_gen_mode_approx_conflict_params(dummy_param):
    yield 'a'
    yield 'b'


@test_steps('a', 'b')
def test_step_id_gen_mode_approx_conflict_fixture(unhashable_fixture_param_approx_conflict):
    yield 'a'
    yield 'b'


@test_steps('a', 'b')
@pytest.mark.parametrize('dummy_param', ['a', 'b'], ids="p={}".format)
def test_step_id_gen_mode_approx_conflict_params_and_no_conflict_fixture(dummy_param,
                                                                         unhashable_fixture_no_param_conflict):
    print('a')
    yield 'a'
    print('b')
    yield 'b'


# -----------------
@test_steps('a', 'b')
@pytest.mark.parametrize('dummy_param', ['a', 'b'], ids=str)
def test_step_id_gen_mode_exact_conflict_with_param(dummy_param):
    print('a')
    yield 'a'
    print('b')
    yield 'b'


@test_steps('a', 'b')
def test_step_id_gen_mode_exact_conflict_with_fixture(unhashable_fixture_param_conflict):
    print('a')
    yield 'a'
    print('b')
    yield 'b'


@test_steps('a', 'b')
@pytest.mark.parametrize('dummy_param', ['a', 'b'], ids=str)
def test_step_id_gen_mode_exact_conflict_with_param_and_fixture(dummy_param, unhashable_fixture_param_conflict):
    print('a')
    yield 'a'
    print('b')
    yield 'b'


# ------------------ PARAMETRIZE MODE


@test_steps('a', 'b')
@pytest.mark.parametrize('dummy_param', ['a', 'b'], ids="p={}".format)
def test_step_id_parametrize_mode_approx_conflict(test_step, dummy_param, steps_data):
    if test_step == 'a':
        print('a')
    elif test_step == 'b':
        print('b')


@test_steps('a', 'b', steps_data_holder_name='steps_data2')
@pytest.mark.parametrize('dummy_param', ['a', 'b'], ids="p={}".format)
def test_step_id_conflicts_parametrized2(test_step, dummy_param, unhashable_fixture_no_param_conflict, steps_data2):
    if test_step == 'a':
        print('a')
    elif test_step == 'b':
        print('b')


@test_steps('a', 'b', steps_data_holder_name='steps_data3')
@pytest.mark.parametrize('dummy_param', ['a', 'b'], ids="p={}".format)
def test_step_id_conflicts_parametrized3(test_step, dummy_param, unhashable_fixture_param_conflict, steps_data3):
    if test_step == 'a':
        print('a')
    elif test_step == 'b':
        print('b')
