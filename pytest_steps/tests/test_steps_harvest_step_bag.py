"""
tests the step_bag fixture and serves as a demo of
the difference between step_bag and results_bag
"""
import pandas as pd
import pytest
from pytest_steps import test_steps


def fruit_counter(some_bag):
    """This silly test "counts the apples" in the first step and "counts
    the bananas" in the second step and maintains a running count of
    total_fruit over the steps."""

    some_bag["apples"] = 10
    some_bag["total_fruit"] = 10
    yield

    some_bag["bananas"] = 10
    some_bag["total_fruit"] = 20
    yield


# Run the above silly test with each type of bag


@test_steps("apples", "bananas")
def test_fruit_step_bag(step_bag):
    # This test will have a new bag per step
    for f in fruit_counter(step_bag):
        yield f


@test_steps("apples", "bananas")
def test_fruit_results_bag(results_bag):
    # This test will have a shared bag over both steps
    for f in fruit_counter(results_bag):
        yield f


@test_steps("apples", "bananas")
def test_fruit_cross_bag(cross_bag):
    # The cross_bag will be the same as results_bag
    for f in fruit_counter(cross_bag):
        yield f


# check the test results


def test_synthesis(module_results_df):
    df = module_results_df[["total_fruit", "bananas", "apples"]]

    # check the step_bag flavor -- the updates to step-bag are separated
    # the [apples] step set "apples" and "total_fruit" to 10, and the
    # the [bananas] step set "bananas" to 10 and "total_fruit" to 20
    assert df.loc["test_fruit_step_bag[apples]", "apples"] == 10
    assert pd.isna(df.loc["test_fruit_step_bag[apples]", "bananas"])
    assert df.loc["test_fruit_step_bag[apples]", "total_fruit"] == 10

    assert pd.isna(df.loc["test_fruit_step_bag[bananas]", "apples"])
    assert df.loc["test_fruit_step_bag[bananas]", "bananas"] == 10
    assert df.loc["test_fruit_step_bag[bananas]", "total_fruit"] == 20

    # check the results_bag flavor -- there is only one bag for both steps
    # The bag shows apples = 10, bananas = 10, and total_fruit = 20, and
    # the intermediate value total_fruit = 10 at the end of the first step
    # is not saved.
    assert df.loc["test_fruit_results_bag[apples]", "apples"] == 10
    assert df.loc["test_fruit_results_bag[apples]", "bananas"] == 10
    assert df.loc["test_fruit_results_bag[apples]", "total_fruit"] == 20

    # there is no results_bag data on the [bananas] row
    assert df.loc["test_fruit_results_bag[bananas]", :].isna().all()

    # Finally, cross_bag is the same as results_bag in this case
    assert df.loc["test_fruit_cross_bag[apples]", "apples"] == 10
    assert df.loc["test_fruit_cross_bag[apples]", "bananas"] == 10
    assert df.loc["test_fruit_cross_bag[apples]", "total_fruit"] == 20

    assert df.loc["test_fruit_cross_bag[bananas]", :].isna().all()
