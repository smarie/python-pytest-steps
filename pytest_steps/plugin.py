# Authors: Sylvain MARIE <sylvain.marie@se.com>
#          + All contributors to <https://github.com/smarie/python-pytest-steps>
#
# License: 3-clause BSD, <https://github.com/smarie/python-pytest-steps/blob/master/LICENSE>
import pytest
from pytest_steps.steps import cross_steps_fixture
from pytest_steps.steps_generator import one_fixture_per_step

try:
    from pytest_steps import pivot_steps_on_df, handle_steps_in_results_df
except ImportError:
    # this is normal if pytest-harvest is not installed
    pass
else:
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

    @pytest.fixture
    @one_fixture_per_step
    def step_bag(results_bag):
        """
        Provides a separate pytest-harvest "results_bag" per step
        """
        return results_bag

    @pytest.fixture
    @cross_steps_fixture
    def cross_bag(results_bag):
        """
        Provides a cross-step pytest-harvest "results_bag" for explicit mode
        """
        return results_bag
