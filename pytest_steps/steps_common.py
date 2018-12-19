try:  # python 3+
    from typing import Tuple
except ImportError:
    pass


def create_pytest_param_str_id(f):
    # type: (...) -> str
    """
    Returns an id that can be used as a pytest id, from an object.

    :param f:
    :return:
    """
    if callable(f) and hasattr(f, '__name__'):
        return f.__name__
    else:
        return str(f)


# def get_pytest_node_str_id_approximate(pytest_node,
#                                        remove_params=None  # type: List[str]
#                                        ):
#     # type: (...) -> str
#     """
#     Returns the unique id string associated with current parametrized pytest node, skipping parameters listed in
#     `remove_params`.
#
#     Note: this only works if the id associated with the listed parameters to remove are obtained from the parameter
#     value using the 'str' function ; and if several parameters have the exact same string id it does not work.
#
#     :param pytest_node:
#     :param remove_params:
#     :return:
#     """
#     if remove_params is None:
#         remove_params = []
#
#     if len(remove_params) == 0:
#         return pytest_node.id
#     else:
#         # Unfortunately there seem to be no possibility in the pytest api to eliminate a named parameter from a node id,
#         # because the node ids are generated at collection time and the link between ids and parameter names are
#         # forgotten.
#         #
#         # The best we can do seems to be:
#         #   unparametrized_node_id = node.parent.nodeid + '::' + node.function.__name__
#         #   current_parametrization_id = node.callspec.id
#         #
#         # The goal would be to replace current_parametrization_id with a new one (w/o the selected params) from the
#         # callspec object. This object (a CallSpec2)
#         # - has a list of ids (in node.callspec._idlist)
#         # - has a dictionary of parameter names and values (in node.callspec.params)
#         # - But unfortunately there is no way to know which parameter name corresponds to which id (no order)
#         #
#         # Note: a good way to explore this part of pytest is to put a breakpoint in _pytest.python.Function init()
#
#         # So we made the decision to rely only on string parsing, not objects
#         node_id_base, node_id_params = split_pytest_node_str_id(pytest_node.nodeid)
#
#         # Create a new id from the current one, by "removing" the ids of the selected parameters
#         param_values_dct = get_pytest_node_current_param_values(pytest_node)
#         for p_name in remove_params:
#             if p_name not in param_values_dct:
#                 raise ValueError("Parameter %s is not a valid parameter name in node %s"
#                                  "" % (p_name, pytest_node.nodeid))
#             else:
#                 # Strong assumption: assume that the id will be str(param_value) of param_value.__name__
#                 param_id = create_pytest_param_str_id(param_values_dct[p_name])
#
#                 if param_id in node_id_params:
#                     node_id_params = remove_param_from_pytest_node_str_id(node_id_params, param_id)
#                 else:
#                     raise ValueError("Parameter value %s (for parameter %s) cannot be found in node %s"
#                                      "" % (param_id, p_name, pytest_node.nodeid))
#
#         return node_id_base + node_id_params


def remove_param_from_pytest_node_str_id(test_id, param_id_str):
    """
    Returns a new test id where the step parameter is not present anymore.

    :param test_id:
    :param param_id_str:
    :return:
    """
    # from math import isnan
    # if isnan(step_id):
    #     return test_id
    new_id = test_id.replace('-' + param_id_str + '-', '-', 1)
    # only continue if previous replacement was not successful to avoid cases where the step id is identical to
    # another parameter
    if len(new_id) == len(test_id):
        new_id = test_id.replace('[' + param_id_str + '-', '[', 1)
    if len(new_id) == len(test_id):
        new_id = test_id.replace('-' + param_id_str + ']', ']', 1)

    return new_id


# def split_pytest_node_str_id(node_id_str  # type: str
#                              ):
#     # type: (...) -> Tuple[str, str]
#     """
#     Splits a pytest node id string into base and parametrization ids
#
#     :param node_id_str:
#     :return:
#     """
#     result = re.compile('(?P<base_node_id>.*)\[(?P<parametrization>.*)\]\Z').match(node_id_str)
#     if result is None:
#         raise ValueError("pytest node id does not match pytest pattern - cannot split it")
#
#     # Unpack
#     unparametrized_node_id = result.group('base_node_id')
#     current_parametrization_id = result.group('parametrization')
#
#     return unparametrized_node_id, '[' + current_parametrization_id + ']'


# class HashableDict(dict):
#     def __hash__(self):
#         return hash(tuple(sorted(self.items())))
#
#
def get_pytest_node_hash_id(pytest_node,
                            params_to_ignore=None):
    """

    :param pytest_node:
    :param ignore_params:
    :return:
    """
    # Default value
    if params_to_ignore is None:
        params_to_ignore = []

    # No need to remove parameters: the usual id can do the job
    if len(params_to_ignore) == 0:
        return pytest_node.callspec.id

    # Method 0: use the string id and replace the params to ignore. Not reliable enough
    # id_without_steps = get_pytest_node_str_id_approximate(request.node, remove_params=(test_step_argname,))

    # Method 1: rely on parameter indices to build the id
    # NOT APPROPRIATE: indices might not be always set (according to pytest comments in source)
    # AND indices do not represent unique values
    #
    # # Retrieve the current indice for all parameters
    # params_indices_dct = get_pytest_node_current_param_indices(pytest_node)
    #
    # # Use the same order to build the list of tuples to hash
    # tpl = tuple((p, params_indices_dct[p]) for p in get_pytest_node_current_param_values(pytest_node)
    #             if p not in params_to_ignore)

    # Method 2
    # create a hashable dictionary from the list of parameters AND fixtures VALUES
    # params = get_pytest_node_current_param_and_fixture_values(request, params_to_ignore={test_step_argname,
    #                                                                              steps_data_holder_name, 'request'})
    # test_id_without_steps = HashableDict(params)
    # >> "too much", not necessary

    # Method 3
    # Hash a tuple containing the parameter names with a hash of their value
    params_dct = get_pytest_node_current_param_values(pytest_node)
    # first include the pytest object (the test function)
    l = [pytest_node.obj]
    for p, v in params_dct.items():
        if p not in params_to_ignore:
            try:
                hash_o_v = hash(v)
            except TypeError:
                # not hashable, try at least the following for dictionary
                try:
                    hash_o_v = hash(repr(sorted(v.items())))
                except AttributeError:
                    raise TypeError("Unable to hash test parameter '%s'. Hashable parameters are required to use steps "
                                    "reliably." % v)
            l.append((p, hash_o_v))

    # Hash
    return hash(tuple(l))


# def get_pytest_node_current_param_indices(pytest_node):
#     """
#     Returns a dictionary containing all parameter indices in the parameter matrix.
#     Problem: these indices do not represent unique parameter values !
#
#     Indeed if you have a parameter with two values 'a' and 'b', and use also a second parameter with values 1 and 2,
#     then both indices will go from 0 to 3... at least in pytest 3.4.2
#
#     :param pytest_node:
#     :return:
#     """
#     return pytest_node.callspec.indices


def get_pytest_node_current_param_values(pytest_node):
    """
    Returns a dictionary containing all parameters and their values for the given call.
    Like `get_pytest_node_current_param_and_fixture_values` it contains all direct parameters
    (@pytest.mark.parametrize), but it contains no fixture - instead it contains the fixture *parameters*, and only
    for parametrized fixtures.

    Note: it seems that it is the same than `request.node.funcargs`   pytest_node.funcargnames

    :param pytest_node:
    :return:
    """
    return pytest_node.callspec.params


def get_pytest_node_current_param_and_fixture_values(request,
                                                     params_to_ignore=None):
    """
    Returns a dictionary containing all fixtures and parameters values available in a given test `request`.

    As opposed to `get_pytest_node_current_param_values`, this contains fixture VALUES and non-parametrized fixtures,
    whereas `get_pytest_node_current_param_values` only contains the parameters.

    :param request:
    :param params_to_ignore: an iterable of parameter or fixture names to ignore in the returned dictionary
    :return:
    """
    # Default value
    if params_to_ignore is None:
        params_to_ignore = []

    # List the values of all the test function parameters that matter
    kwargs = {argname: get_fixture_or_param_value(request, argname)
              for argname in request.funcargnames
              if argname not in params_to_ignore}

    return kwargs


def get_fixture_or_param_value(request, fixture_or_param_name):
    """
    Returns the value associated with parameter or fixture named `fixture_name`, in provided request context.
    This is just an easy way to use `getfixturevalue` or `getfuncargvalue` according to whichever is available in
    current pytest version.

    Note: it seems that this is the same than `request.node.callspec.params[fixture_or_param_name]` but maybe it is
    less 'internal' as an api ?

    :param request:
    :param fixture_or_param_name:
    :return:
    """
    try:
        # Pytest 4+ or latest 3.x (to avoid the deprecated warning)
        return request.getfixturevalue(fixture_or_param_name)
    except AttributeError:
        # Pytest 3-
        return request.getfuncargvalue(fixture_or_param_name)


def get_scope(request):
    """
    Utility method to return the scope of a pytest request
    :param request:
    :return:
    """
    if request.node is request.session:
        return 'session'
    elif hasattr(request.node, 'function'):
        return 'function'
    else:
        return 'module'
