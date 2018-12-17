import pytest

from pytest_steps import pivot_steps_on_df, handle_steps_in_results_df


@pytest.fixture(scope='function')
def session_results_df_steps_pivoted(request, session_results_df):
    """
    A pivoted version of fixture `session_results_df` from pytest_harvest.
    In this version, there is one row per test with the results from all steps in columns.
    """
    # Handle the steps
    session_results_df = handle_steps_in_results_df(session_results_df, keep_orig_id=False)

    # Pivot
    return pivot_steps_on_df(session_results_df, pytest_session=request.session)


@pytest.fixture(scope='function')
def module_results_df_steps_pivoted(request, module_results_df):
    """
    A pivoted version of fixture `module_results_df` from pytest_harvest.
    In this version, there is one row per test with the results from all steps in columns.
    """
    # Handle the steps
    module_results_df = handle_steps_in_results_df(module_results_df, keep_orig_id=False)

    # Pivot
    return pivot_steps_on_df(module_results_df, pytest_session=request.session)
