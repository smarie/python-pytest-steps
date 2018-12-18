# META
# {'passed': 3, 'skipped': 0, 'failed': 0}
# END META
from pytest_harvest import get_session_synthesis_dct, create_results_bag_fixture, saved_fixture


# ---------- Tests
# A module-scoped store
from pytest_steps import test_steps


@test_steps('unique')  # -> ne passe pas devant en mode parametrizer
def test_basic_a(test_step):
    """Another test, to show how it appears in the results"""
    return


def test_synthesis(request):
    """
    Tests that this test runs last and the two others are available in the synthesis
    """
    # Get session synthesis
    # - filtered on the test function of interest
    # - combined with our store
    results_dct = get_session_synthesis_dct(request.session, filter=test_synthesis.__module__,
                                            durations_in_ms=True, test_id_format='function')

    # incomplete are not here so length should be 2
    assert len(results_dct) == 1


@test_steps('unique')  # -> passe devant en mode generator
def test_basic_gen():
    """Another test, to show how it appears in the results"""
    yield
