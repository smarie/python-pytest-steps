# import pandas as pd  not needed so do not import it
from pytest_steps import CROSS_STEPS_MARK
from pytest_steps.steps_harvest import _get_step_param_names_or_default, get_all_pytest_param_names_except_step_id, \
    remove_step_from_test_id
from pytest_harvest import get_all_pytest_fixture_names

try:  # type hints for python 3.5+
    from typing import List
except ImportError:
    pass


def pivot_steps_on_df(results_df,
                      pytest_session=None,
                      pytest_session_filter=None,  # type: Any
                      cross_steps_columns=None,    # type: List[str]
                      error_if_not_present=True    # type: bool
                      ):
    """
    Pivots the dataframe so that there is one row per pytest_obj[params except step id] containing all steps info.
    The input dataframe should have a multilevel index with two levels (test id, step id) and with names
    (`results_df.index.names` should be set). The test id should be independent on the step id.

    :param results_df: a synthesis dataframe created by `pytest-harvest`.
    :param pytest_session: If this is provided, the cross_steps_columns will be inferred from the pytest session
        information. (only one of pytest_session of cross_steps_columns should be provided).
    :param pytest_session_filter: if this is provided, the cross_steps_columns will be better inferred from the pytest
        session information, by only using the filtered elements. This has the same behaviour than `pytest-harvest`
        filters.
    :param cross_steps_columns: a list of columns in the dataframe that are stable across steps. Provide this only if
        the pytest session is not provided.
    :param error_if_not_present: a boolean (default True) indicating if the function should raise an error if a name
        provided in `cross_steps_columns` is not present in the dataframe.
    :return:
    """
    # check params
    if pytest_session is not None and cross_steps_columns is not None:
        raise ValueError("Only one of `pytest_session` and `cross_steps_columns` should be provided")

    # auto-extract from session
    if pytest_session is not None:
        # Gather all names of columns that we know are cross-steps
        pytest_other_names = ['pytest_obj']
        param_names = get_all_pytest_param_names_except_step_id(pytest_session, filter=pytest_session_filter)
        fixture_names = get_all_cross_steps_fixture_names(pytest_session, filter=pytest_session_filter)
        cross_steps_columns = pytest_other_names + param_names + fixture_names
        error_if_not_present = False

    # check column names provided or guessed from session
    non_present = set(cross_steps_columns) - set(results_df.columns)
    if error_if_not_present and len(non_present) > 0:
        raise ValueError("Columns %s are not present in the provided dataframe. If this is normal set "
                         "`error_if_not_present=False`. Available columns: %s"
                         "" % (non_present, list(results_df.columns)))
    cross_steps_cols_list = list(c for c in results_df.columns if c in cross_steps_columns)

    # extract the names of the two index levels
    test_id_name, step_id_name = results_df.index.names

    # remember the original steps order
    all_step_ids = results_df.index.get_level_values(step_id_name).unique()

    # split the df in two parts: the columns that do not depend on steps and the ones that have one value per step
    # --these do not depend on steps
    remaining_df = results_df[cross_steps_cols_list] \
                             .reset_index().set_index(test_id_name) \
                             .drop(step_id_name, axis=1)
    remaining_df.drop_duplicates(inplace=True)

    if remaining_df.index.has_duplicates:
        raise ValueError("At least one of the columns listed in '%s' varies across steps." % cross_steps_cols_list)

    # --these depend on steps
    one_per_step_df = results_df.drop(cross_steps_columns, axis=1, errors='raise' if error_if_not_present else 'ignore')

    # perform the pivot operation, and clean up (change levels order, drop nan columns, sort columns)
    # Note: pandas 'pivot' does not work with multiindex in many pandas versions so we use "unstack" instead
    one_per_step_df = one_per_step_df.unstack(step_id_name) \
                                     .reorder_levels([1, 0], axis=1) \
                                     .dropna(axis=1, how='all') \
                                     .reindex(columns=all_step_ids, level=0)

    # join the two
    return remaining_df.join(one_per_step_df)


def flatten_multilevel_columns(df,
                               sep='/'  # type: str
                               ):
    """
    Replaces the multilevel columns (typically after a pivot) with single-level ones, where the names contain all
    levels concatenated with the separator `sep`. For example when the two levels are `foo` and `bar`, the single level
    becomes `foo/bar`.

    This method is a shortcut for `df.columns = get_flattened_multilevel_columns(df)`.

    :param df:
    :param sep:
    :return:
    """
    df.columns = get_flattened_multilevel_columns(df, sep=sep)
    return df


def get_flattened_multilevel_columns(df,
                                     sep='/'  # type: str
                                     ):
    """
    Creates new column names for the provided dataframe so that it does not have multilevel columns anymore.
    For columns with multi levels, the levels are all flatten into a single string column name with separator `sep`.

    You should use the result as the new column names:

    `df.columns = get_flattened_multilevel_columns(df)`

    :param df:
    :param sep: the separator to use when joining the names of several levels into one unique name
    :return:
    """
    def flatten_multilevel_colname(col_level_names):
        if isinstance(col_level_names, str):
            return col_level_names
        else:
            try:
                return sep.join([str(c) for c in col_level_names])
            except TypeError:
                # not iterable not string: return as is
                return col_level_names

    return [flatten_multilevel_colname(cols) for cols in df.columns.values]


def handle_steps_in_results_df(results_df,
                               raise_if_one_test_without_step_id=False,  # type: bool
                               no_step_id='-',  # type: str
                               step_param_names=None,  # type: Union[str, Iterable[str]]
                               keep_orig_id=True,  # type: bool
                               no_steps_policy='raise',  # type: str
                               inplace=False
                               ):
    """
    Equivalent of `handle_steps_in_results_dct`

    Improves the synthesis dataframe so that
     - the test_id index is replaced with a multilevel index (new_test_id, step_id) where new_test_id is a
     step-independent test id. A 'pytest_id' column remains with the original id except if keep_orig_id=False
     (default=True)
     - the 'step_id' parameter is removed from the contents

    The step id is identified by looking at the columns, and finding one with a name included in the
    `step_param_names` list (`None` uses the default names). If no step id is found on an entry, it is replaced with
    the value of `no_step_id` except if `raise_if_one_test_without_step_id=True` - in which case an error is raised.

    If all step ids are missing, for all entries in the dictionary, `no_steps_policy` determines what happens: it can
    either skip the whole function and return a copy of the input ('skip', or behave as usual ('ignore'), or raise an
    error ('raise').

    If `keep_orig_id` is set to True (default), the original id is added as a new column.

    If `inplace` is `False` (default), a new dataframe will be returned. Otherwise the input dataframe will
    be modified inplace and nothing will be returned.

    :param results_df:
    :param raise_if_one_test_without_step_id: if this is set to `True` and at least one step id can not be found in the tests, an
        error will be raised. By default this is set to `False`: in that case, when the step id is not found it is
        replaced with value of the `no_step_id` parameter.
    :param no_step_id: the identifier to use when the step id is not found (if `raise_if_no_step_id` is `False`)
    :param step_param_names: a singleton or iterable containing the names of the test step parameters used in the
        tests. By default the list is `[GENERATOR_MODE_STEP_ARGNAME, TEST_STEP_ARGNAME_DEFAULT]` to cover both
        generator-mode and legacy manual mode.
    :param keep_orig_id: if True (default) the original test id will appear in the df under 'pytest_id' column
    :param no_steps_policy: if `'ignore` the returned dataframe will be multilevel (test id, step id) in all
        cases, even if no step is present. If 'skip' and no step is present, the method will not modify anything in the
        dataframe. If 'raise' (default) and no step column is present, an error is raised.
    :param inplace: if this is `False` (default), a new dataframe will be returned. Otherwise the input dataframe will
        be modified inplace and None will be returned
    :return:
    """
    import pandas as pd

    # validate parameters
    step_param_names = _get_step_param_names_or_default(step_param_names)
    if not isinstance(no_steps_policy, str) or no_steps_policy not in {'ignore', 'raise', 'skip'}:
        raise ValueError("`no_steps_policy` should be one of {'ignore', 'raise', 'skip'}")

    if not inplace:
        results_df = results_df.copy()

    # find the unique column containing "step id" parameter
    step_name_columns = set(step_param_names).intersection(set(results_df.columns))
    if len(step_name_columns) == 1:
        step_name_col = step_name_columns.pop()
    elif len(step_name_columns) == 0:
        if no_steps_policy == 'raise':
            raise ValueError("The synthesis dataframe provided does not seem to contain step name columns. You can "
                             "ignore this error by switching to `no_steps_policy`='ignore'. Available "
                             "columns: %s" % list(results_df.columns))
        elif no_steps_policy == 'skip':
            if inplace:
                return
            else:
                return results_df
        else:
            # no steps column - create one with only none values
            step_name_col = '__step_id'
            results_df[step_name_col] = None
    else:
        raise ValueError("The synthesis dataframe provided contains several 'step name' columns: %s"
                         "" % step_name_columns)

    # check that the column has at least one non-null value
    null_steps_indexer = results_df[step_name_col].isnull()
    nb_without_step_id = null_steps_indexer.sum()
    if nb_without_step_id > 0:
        if raise_if_one_test_without_step_id:
            raise ValueError("The synthesis DataFrame provided does not seem to contain step name parameters for "
                             "test nodes %s" % list(results_df.loc[null_steps_indexer, 'pytest_id']))
        # elif nb_without_step_id == len(df):
        #     # no test has steps, simply return without change
        #     if inplace:
        #         return
        #     else:
        #         return df
        else:
            # replace missing values with `no_step_id`
            results_df.loc[null_steps_indexer, step_name_col] = no_step_id

    # original test id column is the current index
    results_df.index.name = 'pytest_id'
    results_df.reset_index(inplace=True)

    # split the id in two and use it as multiindex
    def _remove_step_from_test_id(s):
        test_id, step_id = s
        if pd.isnull(step_id):
            step_id = no_step_id
        return remove_step_from_test_id(test_id, step_id)
    results_df['test_id'] = results_df[['pytest_id', step_name_col]].apply(_remove_step_from_test_id, axis=1, raw=True)
    results_df.rename(columns={step_name_col: 'step_id'}, inplace=True)
    results_df.set_index(['test_id', 'step_id'], inplace=True)

    # drop original id if required
    if not keep_orig_id:
        results_df.drop('pytest_id', axis=1, inplace=True)

    # return
    if not inplace:
        return results_df


def get_all_cross_steps_fixture_names(pytest_session, filter=None):
    """
    Returns a list of all fixtures used in the session, filtered so as to only use
    :param pytest_session:
    :return:
    """
    fixture_names = get_all_pytest_fixture_names(pytest_session,
                                                 filter=filter)
    returned_set = set()
    for name in fixture_names:
        all_fixtures = pytest_session._fixturemanager._arg2fixturedefs[name]

        for f in all_fixtures:
            # get the fixture function
            fixture_function = f.func

            # if it is cross-steps, add its name
            if hasattr(fixture_function, CROSS_STEPS_MARK):
                returned_set.add(name)
                break

    return list(returned_set)
