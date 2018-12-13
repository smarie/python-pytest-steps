# META
# {'passed': 14, 'skipped': 0, 'failed': 0}
# END META
from collections import OrderedDict
from random import random
from warnings import warn

import pandas as pd
# make 'assert_frame_equal', 'assert_series_equal', etc. become available too:
try:
    # pandas 0.20+
    pandas_testing = pd.testing
except:
    try:
        # pandas 0.18
        pandas_testing = pd.util.testing
    except ImportError as e:
        pandas_testing = None
        warn('Could not re-export pandas.testing routines for this version of pandas ({})'.format(pd.__version__))


from tabulate import tabulate

import pytest
from pytest_harvest import get_session_synthesis_dct, create_results_bag_fixture, saved_fixture, \
    get_all_pytest_fixture_names

from pytest_steps import test_steps, handle_steps_in_synthesis_dct, get_flattened_multilevel_columns, pivot_steps_on_df, \
    get_all_pytest_param_names_except_step_id, remove_step_from_test_id
from pytest_steps.steps_generator import GENERATOR_MODE_STEP_ARGNAME


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
def my_store():
    return OrderedDict()


# A module-scoped results bag fixture
my_results = create_results_bag_fixture('my_store', name='my_results')


@pytest.fixture(params=['A', 'B', 'C'])
@saved_fixture('my_store')
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


def test_basic():
    """Another test, to show how it appears in the results"""
    pass


def test_synthesis(request, my_store):
    """
    Tests that users can create a pivoted syntesis table, both by hand (only using pytest-harvest's
    get_session_synthesis_dct) or using the provided utility functions from pytest-steps.
    Note: we could do this at many other places (hook, teardown of a session-scope fixture...)
    """
    # Get session synthesis
    # - filtered on the test function of interest
    # - combined with our store
    results_dct = get_session_synthesis_dct(request, filter=test_synthesis.__module__,
                                            durations_in_ms=True, test_id_format='function', status_details=False,
                                            fixture_store=my_store, flatten=True, flatten_more='my_results')

    # print keys and first node details
    assert len(results_dct) > 0
    print("\nKeys:\n" + "\n".join(list(results_dct.keys())))
    print("\nFirst node:\n" + "\n".join(repr(k) + ": " + repr(v) for k, v in list(results_dct.values())[0].items()))

    # ---------- First version "all by dataframe processing" -----------
    param_names = {'algo_param', 'dataset_param', 'dataset'}
    tmp_df = build_df_from_raw_synthesis(results_dct, cross_steps_columns=param_names)
    report_df = pivot_steps_on_df(tmp_df, cross_steps_columns=param_names)
    # --report
    report_df.columns = get_flattened_multilevel_columns(report_df)
    print("\nPivoted table:\n" + tabulate(report_df, headers='keys'))

    # ---------- second version "relying on `handle_steps_in_synthesis_dct`"---------
    param_names = get_all_pytest_param_names_except_step_id(request.session, filter=test_synthesis.__module__)
    fixture_names = get_all_pytest_fixture_names(request.session, filter=test_synthesis.__module__)
    results_dct2 = handle_steps_in_synthesis_dct(results_dct, is_flat=True)
    tmp_df = build_df_from_processed_synthesis(results_dct2)
    report_df2 = pivot_steps_on_df(tmp_df, cross_steps_columns=param_names + fixture_names)
    # --report
    report_df2.columns = get_flattened_multilevel_columns(report_df2)
    print("\nPivoted table (2):\n" + tabulate(report_df2, headers='keys'))

    assert list(report_df2.columns) == ['algo_param', 'dataset_param', 'dataset',
                                        'train/status', 'train/duration_ms', 'train/accuracy',
                                        'score/status', 'score/duration_ms',
                                        '-/status', '-/duration_ms']
    pandas_testing.assert_frame_equal(report_df, report_df2)

    # create a csv report
    # results_df.to_csv("all_results.csv")   # TODO how to flatten multilevel column names in csv ?


def build_df_from_processed_synthesis(results_dct):

    # convert to a pandas dataframe
    results_df = pd.DataFrame.from_dict(results_dct, orient='index')  # this does not preserve rows order
    results_df = results_df.loc[list(results_dct.keys()), :]          # update rows order
    results_df.index.names = ['test_id', 'step_id']

    results_df.drop(['pytest_obj'], axis=1, inplace=True)  # drop pytest object column

    return results_df


def build_df_from_raw_synthesis(results_dct, cross_steps_columns, no_step_id='-'):
    """
    Converts the 'raw' synthesis dct into a pivoted dataframe where steps are a level in multilevel columns

    :param results_dct:
    :return:
    """
    # convert to a pandas dataframe
    results_df = pd.DataFrame.from_dict(results_dct, orient='index')  # this does not preserve rows order
    results_df = results_df.loc[list(results_dct.keys()), :]          # update rows order

    # (a) rename step id
    results_df.rename(columns={GENERATOR_MODE_STEP_ARGNAME: 'step_id'}, inplace=True)

    # (b) create a column with the new id and use it as index in combination with step id
    # -- check column names provided
    non_present = set(cross_steps_columns) - set(results_df.columns)
    if len(non_present) > 0:
        raise ValueError("Columns %s are not present in the resulting dataframe. Available columns: %s"
                         "" % (non_present, list(results_df.columns)))
    cross_steps_cols_list = list(c for c in results_df.columns if c in cross_steps_columns)
    # -- create the new id
    # def create_new_name(r):
    #     return r[0].__name__ + '[' + '-'.join(str(o) for o in r[1:].values) + ']'
    # results_df['test_id'] = results_df[['pytest_obj'] + cross_steps_cols_list].apply(create_new_name, axis=1)
    def create_new_name(test_id_series):
        test_id, step_id = test_id_series.name, test_id_series.values[0]
        return remove_step_from_test_id(test_id, step_id) if not pd.isnull(step_id) else test_id
    results_df['test_id'] = results_df[['step_id']].apply(create_new_name, axis=1)
    results_df['step_id'].fillna(value=no_step_id, inplace=True)
    results_df = results_df.reset_index(drop=True).set_index(['test_id', 'step_id'])

    # now we can drop
    results_df.drop(['pytest_obj'], axis=1, inplace=True)  # drop pytest object column

    return results_df


def test_synthesis_not_flat(request, my_store):
    """Additional test to improve coverage"""

    results_dct = get_session_synthesis_dct(request.session, filter=test_synthesis.__module__,
                                            durations_in_ms=True, test_id_format='function', status_details=False,
                                            flatten=False)
    assert len(results_dct) > 0

    # put a stupid step param name so that we can easily do the asserts below
    results_dct2 = handle_steps_in_synthesis_dct(results_dct, is_flat=False, step_param_names=['hohoho'])
    assert [(k, '-') for k in results_dct.keys()] == list(results_dct2.keys())
    assert list(results_dct2.values()) == list(results_dct.values())
