# META
# {'passed': 13, 'skipped': 0, 'failed': 0}
# END META

from collections import OrderedDict
from random import random

import pandas as pd
from tabulate import tabulate

import pytest
from pytest_harvest import get_session_synthesis_dct, create_results_bag_fixture, saved_fixture

from pytest_steps import test_steps, handle_steps_in_synthesis_dct, get_flattened_multilevel_columns, \
    pivot_steps_on_df, get_all_pytest_param_names_except_step_id


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
# A module-scoped store
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


@test_steps('train', 'score')
@pytest.mark.parametrize("algo_param", [1, 2], ids=str)
def test_my_app_bench(algo_param, dataset, my_results):
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
    my_results.accuracy = accuracy
    yield


def test_synthesis(request, store):
    """
    Note: we could do this at many other places (hook, teardown of a session-scope fixture...)

    Note2: we could provide helper methods in pytest_harvest to perform the code below more easily
    :param request:
    :param store:
    :return:
    """
    # Get session synthesis using `pytest-harvest`
    # - filtered on the test function of interest
    # - combined with our store
    results_dct = get_session_synthesis_dct(request.session, filter=test_synthesis.__module__,
                                            durations_in_ms=True, test_id_format='function', status_details=False,
                                            fixture_store=store, flatten=True, flatten_more='my_results')
    # separate test id from step id when needed
    results_dct = handle_steps_in_synthesis_dct(results_dct, is_flat=True)

    # print keys and first node details
    print("\nKeys:\n" + "\n".join([str(t) for t in results_dct.keys()]))
    print("\nFirst node:\n" + "\n".join(repr(k) + ": " + repr(v) for k, v in list(results_dct.values())[0].items()))

    # convert to a pandas dataframe
    results_df = pd.DataFrame.from_dict(results_dct, orient='index')
    results_df = results_df.loc[list(results_dct.keys()), :]          # fix rows order
    results_df.index.names = ['test_id', 'step_id']                   # set index name
    results_df.drop(['pytest_obj'], axis=1, inplace=True)             # drop pytest object column

    # print using tabulate
    print(tabulate(results_df, headers='keys'))

    # pivot
    param_names = get_all_pytest_param_names_except_step_id(request.session, filter=test_synthesis.__module__)
    report_df = pivot_steps_on_df(results_df, cross_steps_columns=param_names)

    # print using tabulate
    report_df.columns = get_flattened_multilevel_columns(report_df)
    print(tabulate(report_df, headers='keys'))


# ------- Output -------
# test_id                   algo_param  dataset        train/status      train/duration_ms    train/accuracy  score/status      score/duration_ms
# ----------------------  ------------  -------------  --------------  -------------------  ----------------  --------------  -------------------
# test_my_app_bench[A-1]             1  my dataset #A  passed                     0.999928          0.66057   passed                     0
# test_my_app_bench[A-2]             2  my dataset #A  passed                     0                 0.91572   passed                     0.999928
# test_my_app_bench[B-1]             1  my dataset #B  passed                     0                 0.364006  passed                     0
# test_my_app_bench[B-2]             2  my dataset #B  passed                     0.999928          0.336002  passed                     0
# test_my_app_bench[C-1]             1  my dataset #C  passed                     0.999928          0.153111  passed                     0
# test_my_app_bench[C-2]             2  my dataset #C  passed                     0                 0.656005  passed                     1.00017
#
