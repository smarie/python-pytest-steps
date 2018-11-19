# META
# {'passed': 3, 'skipped': 0, 'failed': 0}
# END META
import pytest
from pytest_harvest import get_session_synthesis_dct


@pytest.mark.parametrize("dummy", [1], ids=str)
def test_my_app_bench(dummy):
    pass


def test_basic():
    """Another test, to show how it appears in the results"""
    pass


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
    assert len(results_dct) == 2
