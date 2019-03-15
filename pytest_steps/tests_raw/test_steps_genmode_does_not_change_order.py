# META
# {'passed': 5, 'skipped': 0, 'failed': 0}
# END META
from pytest_harvest import get_session_synthesis_dct, create_results_bag_fixture, saved_fixture


# ---------- Tests
# A module-scoped store
from pytest_steps import test_steps


@test_steps('unique')
def test_basic_b(test_step):
    """Another test, to show how it appears in the results"""
    return


@test_steps('unique')
def test_basic_gen_b():
    """Another test, to show how it appears in the results"""
    yield


def test_synthesis(request):
    """
    Tests that this test runs in the right order (second)

    This tests that we use correctly the pytest hack "fun.place_as = func"
    See https://github.com/pytest-dev/pytest/issues/4429
    """
    # Get session synthesis
    # - filtered on the test function of interest
    # - combined with our store
    results_dct = get_session_synthesis_dct(request.session, filter=test_synthesis.__module__,
                                            durations_in_ms=True, test_id_format='function')

    # incomplete are not here so length should be 1
    assert len(results_dct) == 2
    it = list(results_dct.values())
    assert it[0]['pytest_obj'] == test_basic_b
    assert it[1]['pytest_obj'] == test_basic_gen_b


@test_steps('unique')
def test_basic_a(test_step):
    """Another test, to show how it appears in the results"""
    return


@test_steps('unique')
def test_basic_gen_a():
    """Another test, to show how it appears in the results"""
    yield
