from functools import lru_cache
import pytest


# ------------------- The same code than what is generated dynamically by @test_steps
class StepsDataHolder:
    pass


@lru_cache(maxsize=None)
def get_results_holder(**kwargs):
    """
    A factory for the StepsDataHolder objects. Since it uses @lru_cache, the same StepsDataHolder will be returned when
    the keyword arguments are the same.

    :param kwargs:
    :return:
    """
    return StepsDataHolder()


@pytest.fixture
def results(request):
    """
    The fixture for the StepsDataHolder
    :param request:
    :return:
    """
    kwargs = {argname: request.getfuncargvalue(argname)
              for argname in request.funcargnames
              if argname not in {'test_step', 'results', 'request'}}
    return get_results_holder(**kwargs)
# -------------------------------------


def step_a(results: StepsDataHolder, stupid_param):
    """ Step a of the test """

    # perform this step
    print("step a - " + stupid_param)
    assert not False

    # Assert that the StepsDataHolder object is a brand new one everytime we start this step
    assert not hasattr(results, 'intermediate_a')

    # intermediate results can be stored in results
    results.intermediate_a = 'some intermediate result created in step a for test ' + stupid_param

    assert not hasattr(results, 'p')
    results.p = stupid_param


def step_b(results: StepsDataHolder, stupid_param):
    """ Step b of the test """

    # perform this step
    print("step b - " + stupid_param)

    # assert that step a has been done
    assert hasattr(results, 'intermediate_a')
    # ... and that the stepsdataholder object that we get is the one for our test suite (same parameters)
    assert results.intermediate_a == 'some intermediate result created in step a for test ' + stupid_param

    new_text = results.intermediate_a + " ... augmented"
    print(new_text)

    assert results.p == stupid_param


@pytest.fixture(params=['F', 'G'])
def fix(request):
    return request.param


@pytest.mark.parametrize('really_stupid_param2', ["2A", "2B"])
@pytest.mark.parametrize('test_step', [step_a, step_b])
@pytest.mark.parametrize('stupid_param1', ["1a", "1b"])
def test_manual_pytest_equivalent(test_step, stupid_param1, really_stupid_param2, fix, results: StepsDataHolder):
    """This test performs the same thing than @test_steps but manually.
    See the test_steps_with_results.py for details"""

    # Execute the step
    test_step(results, stupid_param1 + really_stupid_param2 + fix)
