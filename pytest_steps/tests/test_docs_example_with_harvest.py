from random import random
from tabulate import tabulate

import pytest

from pytest_harvest import saved_fixture
from pytest_steps import test_steps, flatten_multilevel_columns, handle_steps_in_results_df


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


def test_synthesis_df(module_results_df, module_results_df_steps_pivoted):
    """
    Create the benchmark synthesis table.
    Note: we could do this at many other places (hook, teardown of a session-scope fixture...). See pytest-harvest
    """
    # print the RAW synthesis dataframe
    assert len(module_results_df) == 12
    module_results_df = handle_steps_in_results_df(module_results_df, keep_orig_id=False)  # hande step id column
    module_results_df.drop(['pytest_obj'], axis=1, inplace=True)                           # drop pytest object column
    print("\n   `module_results_df` dataframe:\n")
    print(module_results_df)
    try:
        # if tabulate is present use it
        print(tabulate(module_results_df, headers='keys'))
    except ImportError:
        pass

    # print the PIVOTED synthesis dataframe
    assert len(module_results_df_steps_pivoted) == 6
    module_results_df_steps_pivoted.drop(['pytest_obj'], axis=1, inplace=True)  # drop pytest object column
    flatten_multilevel_columns(module_results_df_steps_pivoted)
    print("\n   `module_results_df_steps_pivoted` dataframe:\n")
    print(module_results_df_steps_pivoted)
    try:
        # if tabulate is present use it
        print(tabulate(module_results_df_steps_pivoted, headers='keys'))
    except ImportError:
        pass


# ------- Output -------
# `module_results_df` dataframe:
#                                      status      duration_ms    algo_param  dataset_param    dataset          accuracy
# -----------------------------------  --------  -------------  ------------  ---------------  -------------  ----------
# ('test_my_app_bench[A-1]', 'train')  passed         0                    1  A                my dataset #A    0.119054
# ('test_my_app_bench[A-1]', 'score')  passed         0                    1  A                my dataset #A  nan
# ('test_my_app_bench[A-2]', 'train')  passed         0                    2  A                my dataset #A    0.509598
# ('test_my_app_bench[A-2]', 'score')  passed         0                    2  A                my dataset #A  nan
# ('test_my_app_bench[B-1]', 'train')  passed         0                    1  B                my dataset #B    0.586591
# ('test_my_app_bench[B-1]', 'score')  passed         0                    1  B                my dataset #B  nan
# ('test_my_app_bench[B-2]', 'train')  passed         0                    2  B                my dataset #B    0.792301
# ('test_my_app_bench[B-2]', 'score')  passed         0                    2  B                my dataset #B  nan
# ('test_my_app_bench[C-1]', 'train')  passed         0.999928             1  C                my dataset #C    0.298909
# ('test_my_app_bench[C-1]', 'score')  passed         0                    1  C                my dataset #C  nan
# ('test_my_app_bench[C-2]', 'train')  passed         1.00017              2  C                my dataset #C    0.638993
# ('test_my_app_bench[C-2]', 'score')  passed         1.00017              2  C                my dataset #C  nan
#
#
# `module_results_df_steps_pivoted` dataframe:
#
# test_id                   algo_param  dataset_param    dataset        train/status      train/duration_ms    train/accuracy  score/status      score/duration_ms
# ----------------------  ------------  ---------------  -------------  --------------  -------------------  ----------------  --------------  -------------------
# test_my_app_bench[A-1]             1  A                my dataset #A  passed                     0.999928          0.483194  passed                     0
# test_my_app_bench[A-2]             2  A                my dataset #A  passed                     0                 0.102445  passed                     0
# test_my_app_bench[B-1]             1  B                my dataset #B  passed                     0.999928          0.19643   passed                     0
# test_my_app_bench[B-2]             2  B                my dataset #B  passed                     0.999928          0.527477  passed                     0.999928
# test_my_app_bench[C-1]             1  C                my dataset #C  passed                     1.00017           0.229576  passed                     1.00017
# test_my_app_bench[C-2]             2  C                my dataset #C  passed                     0.999928          0.577052  passed                     0
