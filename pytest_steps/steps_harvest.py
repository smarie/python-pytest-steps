from copy import copy

# WARNING do not import pytest-harvest here: it should remain optional
import six

from pytest_steps.steps import TEST_STEP_ARGNAME_DEFAULT
from pytest_steps.steps_generator import GENERATOR_MODE_STEP_ARGNAME
from pytest_steps.steps_common import remove_param_from_pytest_node_str_id

try: # python 3.5+
    from typing import Union, Iterable, Mapping, Any
except ImportError:
    pass


def handle_steps_in_results_dct(results_dct,
                                is_flat=False,  # type: bool
                                raise_if_one_test_without_step_id=False,  # type: bool
                                no_step_id='-',  # type: str
                                step_param_names=None,  # type: Union[str, Iterable[str]]
                                keep_orig_id=True,
                                no_steps_policy='raise'  # type str
                                ):
    """
    Improves the synthesis dictionary so that
     - the keys are replaced with a tuple (new_test_id, step_id) where new_test_id is a step-independent test id
     - the 'step_id' parameter is removed from the contents

    `is_flat` should be set to `True` if the dictionary has been flattened by `pytest-harvest`.

    The step id is identified by looking at the pytest parameters, and finding one with a name included in the
    `step_param_names` list (`None` uses the default names). If no step id is found on an entry, it is replaced with
    the value of `no_step_id` except if `raise_if_one_test_without_step_id=True` - in which case an error is raised.

    If all step ids are missing, for all entries in the dictionary, `no_steps_policy` determines what happens: it can
    either skip the whole function and return a copy of the input ('skip', or behave as usual ('ignore'), or raise an
    error ('raise').

    If `keep_orig_id` is set to True (default), the original id is added to each entry.

    :param results_dct: a synthesis dictionary created by `pytest-harvest`.
    :param is_flat: to declare that synth_dct was flatten or not (if it was generated using `get_session_synthesis_dct`
        with `flatten=True` or `False`).
    :param raise_if_one_test_without_step_id: if this is set to `True` and at least one step id can not be found in the
        tests, an error will be raised. By default this is set to `False`: in that case, when the step id is not found
        it is replaced with value of the `no_step_id` parameter.
    :param no_step_id: the identifier to use when the step id is not found (if `raise_if_no_step_id` is `False`)
    :param step_param_names: a singleton or iterable containing the names of the test step parameters used in the
        tests. By default the list is `[GENERATOR_MODE_STEP_ARGNAME, TEST_STEP_ARGNAME_DEFAULT]` to cover both
        generator-mode and legacy manual mode.
    :param keep_orig_id: if True (default) the original test id will appear in the dict entries under 'pytest_id'
    :param no_steps_policy: if `'ignore` the returned dictionary keys will be tuples (test id, step id) in all
        cases, even if no step is present. If 'skip' and no step is present, the method will return a copy of the input
        and will not modify anything. If 'raise' (default) and no step is present, an error is raised.
    :return: a dictionary where the keys are tuples of (new_test_id, step_id), and the values are copies of the initial
        dictionarie's ones, except that the step id parameter is not present anymore
    """

    # validate parameters
    step_param_names = _get_step_param_names_or_default(step_param_names)
    if not isinstance(no_steps_policy, str) or no_steps_policy not in {'ignore', 'raise', 'skip'}:
        raise ValueError("`no_steps_policy` should be one of {'ignore', 'raise', 'skip'}")

    # edge case of empty dict
    if len(results_dct) == 0:
        return copy(results_dct)

    # create an object of the same container type
    res_dct = type(results_dct)()

    # fill it
    one_step_id_was_present = False
    for test_id, test_info in results_dct.items():
        # copy the first level (no deepcopy because we do not want to perform copies of entries in the dict)
        new_info = copy(test_info)
        if not is_flat:
            # non-flattened: all parameters should be in a nested dict entry
            if "params" in new_info:
                where_params_dct = copy(new_info["params"])
            elif "pytest_params" in new_info:
                where_params_dct = copy(new_info["pytest_params"])
            else:
                raise KeyError("Could not find information related to parameters in provided dict. Maybe it was "
                               "created with flatten=True? In this case please set flatten=True here too")

            # if there is a 'fixtures' entry, replace it with a copy ?
            # not needed a priori
            # if 'fixtures' in new_info:
            #     new_info['fixtures'] = copy(new_info['fixtures'])
        else:
            # flattened: all parameters should be in dedicated entries at the root level
            where_params_dct = new_info

        step_name_params = set(step_param_names).intersection(set(where_params_dct.keys()))
        if len(step_name_params) == 1:
            # remember that there was at least one
            one_step_id_was_present = True

            # use the key to retrieve step id value and remove it from where it was
            step_id_key = step_name_params.pop()
            step_id = where_params_dct.pop(step_id_key)

        elif len(step_name_params) == 0:
            if raise_if_one_test_without_step_id:
                raise ValueError("The synthesis dictionary provided does not seem to contain step name parameters for "
                                 "test node '%s'" % test_id)
            else:
                # use the default id for "no step"
                step_id = no_step_id
        else:
            raise ValueError("The synthesis dictionary provided contains several step name parameters for test node "
                             "'%s': %s" % (test_id, step_name_params))

        # finally create the new id by replacing in the existing id (whatever its position in the parameters order)
        new_id = remove_step_from_test_id(test_id, step_id)

        # remember the old id
        if keep_orig_id:
            new_info['pytest_id'] = new_id
            # move it to the beginning of the dict
            new_info.move_to_end('pytest_id', last=False)

        # store the element
        res_dct[(new_id, step_id)] = new_info

    if not one_step_id_was_present:
        if no_steps_policy == 'skip':
            # do not return the modified one, and return the initial dictionary (a copy)
            return copy(results_dct)
        elif no_steps_policy == 'raise':
            raise ValueError("No step ids can be found in provided dictionary. You can ignore this error by switching "
                             "to `no_steps_policy`='ignore'")
        else:
            # 'ignore": same
            return res_dct

    return res_dct


handle_steps_in_synthesis_dct = handle_steps_in_results_dct
"""deprecated alias - to remove"""


def remove_step_from_test_id(test_id, step_id):
    """
    Returns a new test id where the step parameter is not present anymore.

    :param step_id:
    :param test_id:
    :return:
    """
    # from math import isnan
    # if isnan(step_id):
    #     return test_id
    return remove_param_from_pytest_node_str_id(test_id, step_id)


def get_all_pytest_param_names_except_step_id(session,
                                              filter=None,              # type: Any
                                              filter_incomplete=False,  # type: bool
                                              step_param_names=None     # type: Union[str, Iterable[str]]
                                              ):
    """
    Like pytest-harvest's `get_all_pytest_param_names` this function returns the list of all unique parameter names
    used in all items in the provided session, with given filter. However "step id" parameters are removed
    automatically.

    An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test
    functions) and/or module names.

    If this method is called before the end of the pytest session, some nodes might be incomplete, i.e. they will not
    have data for the three stages (setup/call/teardown). By default these nodes are filtered out but you can set
    `filter_incomplete=False` to make them appear. They will have a special 'pending' synthesis status.

    :param session: a pytest session object.
    :param filter: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned
        items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use
        modules or the special `THIS MODULE` item.
    :param filter_incomplete: a boolean indicating if incomplete nodes (without the three stages setup/call/teardown)
        should appear in the results (False) or not (True). Note: by default incomplete nodes DO APPEAR (this is
        different from get_session_synthesis_dct behaviour)
    :param step_param_names: a singleton or iterable containing the names of the test step parameters used in the
        tests. By default the list is `[GENERATOR_MODE_STEP_ARGNAME, TEST_STEP_ARGNAME_DEFAULT]` to cover both
        generator-mode and legacy manual mode.
    :return:
    """
    try:
        from pytest_harvest import get_all_pytest_param_names

        # test_step_param_names
        step_param_names = _get_step_param_names_or_default(step_param_names)

        return [p for p in get_all_pytest_param_names(session, filter=filter, filter_incomplete=filter_incomplete)
                if p not in step_param_names]

    except ImportError as e:
        six.raise_from(ImportError("pytest-harvest>=1.0.0 is required to use "
                                   "`get_all_pytest_param_names_except_step_id`"), e)


def _get_step_param_names_or_default(step_param_names):
    """

    :param step_param_names:
    :return: a list of step parameter names
    """
    if step_param_names is None:
        # default: cover both generator and legacy mode default names
        step_param_names = [GENERATOR_MODE_STEP_ARGNAME, TEST_STEP_ARGNAME_DEFAULT]
    elif isinstance(step_param_names, str):
        # singleton
        step_param_names = [step_param_names]
    return step_param_names
