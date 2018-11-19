# import pandas as pd  not needed so do not import is


def pivot_steps_on_df(results_df,
                      cross_steps_columns  # type:
                      ):
    """
    Pivot the dataframe so that there is one row per pytest_obj[params except step id] containing all steps info.
    The input dataframe should have a multilevel index with two levels (test id, step id) and with names
    (`results_df.index.names` should be set). The test id should be independent on the step id.

    :param results_df:
    :param cross_steps_columns:
    :return:
    """
    # check column names provided
    non_present = set(cross_steps_columns) - set(results_df.columns)
    if len(non_present) > 0:
        raise ValueError("Columns %s are not present in the provided dataframe. Available columns: %s"
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
        raise ValueError("At least one of the columns listed in '%s' varies across steps." % cross_steps_columns)

    # --these depend on steps
    one_per_step_df = results_df.drop(cross_steps_columns, axis=1)

    # perform the pivot operation, and clean up (change levels order, drop nan columns, sort columns)
    # Note: pandas 'pivot' does not work with multiindex in many pandas versions so we use "unstack" instead
    one_per_step_df = one_per_step_df.unstack(step_id_name) \
                                     .reorder_levels([1, 0], axis=1) \
                                     .dropna(axis=1, how='all') \
                                     .reindex(columns=all_step_ids, level=0)

    # join the two
    return remaining_df.join(one_per_step_df)


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
