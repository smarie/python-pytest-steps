# META
# {'passed': 15, 'skipped': 2, 'failed': 2}
# END META
import pytest

from pytest_steps import test_steps, optional_step, one_fixture_per_step

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature


@test_steps('step_a', 'step_b', 'step_c')
def test_suite_shared_results_no_yield_names():
    """ """

    # Step A
    print("step a")
    assert not False  # replace with your logic
    intermediate_a = 'some intermediate result created in step a'
    yield

    # Step B
    print("step b")
    assert not False  # replace with your logic
    yield

    # Step C
    print("step c")
    new_text = intermediate_a + " ... augmented"
    print(new_text)
    assert len(new_text) == 56
    yield


def test_manual_call():
    """Tests that we can call the WHOLE test suite manually with all the steps executed at once"""

    # A good way to know which parameters to fill is to use inspect
    s = signature(test_suite_shared_results_no_yield_names)
    assert list(s.parameters.keys()) == ['request', '________step_name_']

    # Then fill with blanks
    test_suite_shared_results_no_yield_names(None, None)


@test_steps('step_a', 'step_b', 'step_c')
def test_suite_exception_on_mandatory_step():
    """ """

    # Step A
    print("step a")
    assert not False  # replace with your logic
    yield 'step_a'

    # Step B
    print("step b")
    assert False  # replace with your logic
    yield 'step_b'

    # Step C
    print("step c")
    assert not False  # replace with your logic
    yield 'step_c'


@test_steps('step_a', 'step_b', 'step_c', 'step_d')
def test_suite_optional_and_dependent_steps():
    """ """

    # Step A
    print("step a")
    assert not False
    yield 'step_a'

    # Step B
    with optional_step('step_b') as step_b:
        print("step b")
        assert False
    yield step_b

    # Step C depends on step B
    with optional_step('step_c', depends_on=step_b) as step_c:
        if step_c.should_run():
            print("step c")
            assert True
    yield step_c

    # Step D
    print("step d")
    assert not False
    yield 'step_d'


@test_steps('step_a', 'step_b')
@pytest.mark.parametrize('i', range(2), ids=lambda i: "i=%i" % i)
def test_suite_parametrized(i):
    # Step A
    print("step a, i=%i" % i)
    assert not False  # replace with your logic
    yield

    # Step B
    print("step b, i=%i" % i)
    assert not False  # replace with your logic
    yield


class MyFixture(object):
    def __init__(self):
        print("created new fixture %i" % id(self))
        self.i = 0

    def call(self):
        self.i += 1
        print("%i called for the %i-th time" % (id(self), self.i))


@pytest.fixture
@one_fixture_per_step
def my_fixture2():
    """Simple function-scoped fixture that return a new instance each time"""
    return MyFixture()


@test_steps('step_a', 'step_b')
def test_suite_one_fixture_per_step1(my_fixture2, request):
    # Step A
    print("step a")
    assert not False  # replace with your logic
    my_fixture2.call()
    yield

    # Step B
    print("step b")
    assert not False  # replace with your logic
    my_fixture2.call()
    yield


usage_counter = 0


@pytest.fixture
@one_fixture_per_step
def my_fixture():
    """Simple function-scoped fixture that return a new instance each time"""
    global usage_counter
    usage_counter += 1
    print("created my_fixture %s" % usage_counter)
    return usage_counter


@test_steps('step_a', 'step_b')
def test_suite_one_fixture_per_step2(my_fixture):
    # Step A
    print("step a")
    assert my_fixture == 1
    yield

    # Step B
    print("step b")
    assert my_fixture == 2
    yield
