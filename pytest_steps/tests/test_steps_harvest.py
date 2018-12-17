import pandas as pd
from random import random
from tabulate import tabulate

import pytest
from pytest_harvest import get_session_synthesis_dct, saved_fixture
from pytest_steps import test_steps, pivot_steps_on_df, flatten_multilevel_columns, handle_steps_in_results_df


# ---------- The function to test -------
class DummyModel:
    pass


def my_train(param, data):
    # let's return a dummy model object
    return DummyModel()


def my_score(model, data):
    # let's return a random accuracy !
    return random()


# ---------- Tests
@pytest.fixture(params=['A', 'B', 'C'])
@saved_fixture
def dataset(request):
    """Represents a dataset fixture."""
    return "my dataset #%s" % request.param


@test_steps('train', 'score')
@pytest.mark.parametrize("algo_param", [1, 2], ids=str)
def test_my_app_bench(algo_param, dataset, results_bag):
    """
    This test applies the algorithm with various parameters (`algo_param`)
    on various datasets (`dataset`).

    Accuracies are stored in a results bag (`results_bag`)
    """
    # train the algorithm with param `algo_param` on dataset `dataset`
    model = my_train(algo_param, dataset)
    yield

    # score the model on dataset `dataset`
    accuracy = my_score(model, dataset)

    # store accuracy in the results bag
    results_bag.accuracy = accuracy
    yield


def test_basic():
    """Another test, to show how it appears in the results"""
    pass


def test_synthesis(request, fixture_store):
    """
    Tests that users can create a pivoted syntesis table manually by combining pytest-harvest and pytest-steps.

    Note: we could do this at many other places (hook, teardown of a session-scope fixture...)
    """
    # Get session synthesis
    # - filtered on the test function of interest
    # - combined with default fixture store and results bag
    results_dct = get_session_synthesis_dct(request, filter=test_synthesis.__module__,
                                            durations_in_ms=True, test_id_format='function', status_details=False,
                                            fixture_store=fixture_store, flatten=True, flatten_more='results_bag')

    # We could use this function to perform the test id split here, but we will do it directly on the df
    # results_dct = handle_steps_in_results_dct(results_dct, is_flat=True, keep_orig_id=False)

    # convert to a pandas dataframe
    results_df = pd.DataFrame.from_dict(results_dct, orient='index')
    results_df = results_df.loc[list(results_dct.keys()), :]     # fix rows order
    results_df.index.name = 'test_id'
    # results_df.index.names = ['test_id', 'step_id']              # set multiindex names
    results_df.drop(['pytest_obj'], axis=1, inplace=True)        # drop pytest object column

    # extract the step id and replace the index by a multiindex
    results_df = handle_steps_in_results_df(results_df, keep_orig_id=False)

    # Pivot but do not raise an error if one of the above columns is not present - just in case.
    pivoted_df = pivot_steps_on_df(results_df, pytest_session=request.session)

    # print using tabulate
    flatten_multilevel_columns(pivoted_df)
    print(tabulate(pivoted_df, headers='keys'))


# test_id                   algo_param  dataset_param    dataset        train/status      train/duration_ms    train/accuracy  score/status      score/duration_ms  -/status      -/duration_ms
# ----------------------  ------------  ---------------  -------------  --------------  -------------------  ----------------  --------------  -------------------  ----------  ---------------
# test_my_app_bench[A-1]             1  A                my dataset #A  passed                            0         0.0324809  passed                     0                                 nan
# test_my_app_bench[A-2]             2  A                my dataset #A  passed                            0         0.771141   passed                     0                                 nan
# test_my_app_bench[B-1]             1  B                my dataset #B  passed                            0         0.318179   passed                     0                                 nan
# test_my_app_bench[B-2]             2  B                my dataset #B  passed                            0         0.952537   passed                     0.999928                          nan
# test_my_app_bench[C-1]             1  C                my dataset #C  passed                            0         0.7479     passed                     0                                 nan
# test_my_app_bench[C-2]             2  C                my dataset #C  passed                            0         0.841485   passed                     0                                 nan
# test_basic                       nan  nan              nan                                            nan       nan                                   nan         passed                    0
