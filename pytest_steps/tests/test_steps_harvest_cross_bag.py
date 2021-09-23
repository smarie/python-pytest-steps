"""
tests the step_bag fixture and serves as a demo of
the difference between step_bag and results_bag
"""
import pandas as pd
import pytest
from pytest_steps import test_steps

# This silly test "counts the apples" in the first step and "counts
# the bananas" in the second step and maintains a running count of
# total_fruit over the steps.


def apples(some_bag):
    some_bag["apples"] = 10
    some_bag["total_fruit"] = 10


def bananas(some_bag):
    some_bag["bananas"] = 10
    some_bag["total_fruit"] = 20


# Run the above silly test with each type of bag


@test_steps(apples, bananas)
def test_fruit_results_bag(results_bag, test_step):
    # This test will have a new bag per step
    test_step(results_bag)


@test_steps(apples, bananas)
def test_fruit_cross_bag(cross_bag, test_step):
    # This test will have a shared bag over both steps
    test_step(cross_bag)


@test_steps(apples, bananas)
def test_fruit_step_bag(step_bag, test_step):
    # In explicit mode, the step_bag is exactly the same as results_bag
    test_step(step_bag)


# check the test results


def test_synthesis(module_results_df):
    df = module_results_df[["total_fruit", "bananas", "apples"]]

    # check the results_bag flavor -- the updates are separated:
    # the [apples] step set "apples" and "total_fruit" to 10, and the
    # the [bananas] step set "bananas" to 10 and "total_fruit" to 20
    assert df.loc["test_fruit_results_bag[apples]", "apples"] == 10
    assert pd.isna(df.loc["test_fruit_results_bag[apples]", "bananas"])
    assert df.loc["test_fruit_results_bag[apples]", "total_fruit"] == 10

    assert pd.isna(df.loc["test_fruit_results_bag[bananas]", "apples"])
    assert df.loc["test_fruit_results_bag[bananas]", "bananas"] == 10
    assert df.loc["test_fruit_results_bag[bananas]", "total_fruit"] == 20

    #
    # Expect step bag to be the same as results bag
    #
    assert df.loc["test_fruit_step_bag[apples]", "apples"] == 10
    assert pd.isna(df.loc["test_fruit_step_bag[apples]", "bananas"])
    assert df.loc["test_fruit_step_bag[apples]", "total_fruit"] == 10

    assert pd.isna(df.loc["test_fruit_step_bag[bananas]", "apples"])
    assert df.loc["test_fruit_step_bag[bananas]", "bananas"] == 10
    assert df.loc["test_fruit_step_bag[bananas]", "total_fruit"] == 20

    # check the cross_bag flavor -- there is only one bag for both steps
    # The bag shows apples = 10, bananas = 10, and total_fruit = 20, and
    # the intermediate value total_fruit = 10 at the end of the first step
    # is not saved.
    assert df.loc["test_fruit_cross_bag[apples]", "apples"] == 10
    assert df.loc["test_fruit_cross_bag[apples]", "bananas"] == 10
    assert df.loc["test_fruit_cross_bag[apples]", "total_fruit"] == 20

    # there is no cross_bag data on the [bananas] row
    assert df.loc["test_fruit_cross_bag[bananas]", :].isna().all()
