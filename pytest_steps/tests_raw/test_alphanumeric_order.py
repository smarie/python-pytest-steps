# META
# {'passed': 3, 'skipped': 0, 'failed': 0}
# END META
from collections import OrderedDict

import pytest
from pytest_harvest import get_session_synthesis_dct, create_results_bag_fixture, saved_fixture


# ---------- Tests
# A module-scoped store
from pytest_steps import test_steps


@pytest.fixture(scope='module', autouse=True)
def store():
    return OrderedDict()


# A module-scoped results bag fixture
my_results = create_results_bag_fixture('store', name='my_results')


@pytest.fixture(params=['A', 'B', 'C'])
@saved_fixture('store')
def dataset(request):
    """Represents a dataset fixture."""
    return "my dataset #%s" % request.param


# @test_steps('train', 'score')
@pytest.mark.parametrize('________step_name_', ['train', 'score'], ids=str)
@pytest.mark.parametrize("algo_param", [1, 2], ids=str)
def test_my_app_bench(________step_name_, algo_param, dataset, my_results):
    """
    This test applies the algorithm with various parameters (`algo_param`)
    on various datasets (`dataset`).

    Accuracies are stored in a results bag (`results_bag`)
    """
    my_results.foo = 1
    # yield
    print("nothing")
    # yield


def test_basic():
    """Another test, to show how it appears in the results"""
    pass


def test_synthesis(request, store):
    """
    Tests that this test runs last and the two others are available in the synthesis
    """
    # Get session synthesis
    # - filtered on the test function of interest
    # - combined with our store
    results_dct = get_session_synthesis_dct(request.session, filter=test_synthesis.__module__,
                                            durations_in_ms=True, test_id_format='function')

    # incomplete are not here so length should be 2
    assert len(results_dct) == 13
