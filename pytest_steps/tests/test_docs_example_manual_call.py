import pytest

from pytest_steps import test_steps, depends_on


@test_steps('first', 'second')
def test_dummy_gen():
    print('hello')
    yield
    print('world')
    yield


def first():
    print('hello')


@depends_on(first)
def second():
    print('world')


@test_steps(first, second)
def test_dummy_param_deps(test_step):
    test_step()


@test_steps('first', 'second')
def test_dummy_param(test_step):
    if test_step == 'first':
        print('hello')
    elif test_step == 'second':
        print('world')


@pytest.mark.parametrize('test_dummy', [test_dummy_gen, test_dummy_param_deps, test_dummy_param],
                         ids=lambda f: f.__name__)
def test_manual_call(test_dummy):
    print(help(test_dummy))

    test_dummy(None, None)

    test_dummy(None, 'first')

    test_dummy(None, ['first', 'second'])

    if test_dummy is test_dummy_gen:
        # in generator mode it is not allowed: all steps sequences have to start from the top
        with pytest.raises(ValueError):
            test_dummy(None, 'second')
    else:
        # in parametrizer mode it is allowed
        test_dummy(None, 'second')
