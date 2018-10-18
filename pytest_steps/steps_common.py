import re

try:  # python 3+
    from typing import Tuple
except ImportError:
    pass


def get_pytest_id(f):
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


def split_node_id(node_id  # type: str
                  ):
    # type: (...) -> Tuple[str, str]
    """
    Splits a pytest node id into base and parametrization ids

    :param node_id:
    :return:
    """
    result = re.compile('(?P<base_node_id>.*)\[(?P<parametrization>.*)\]\Z').match(node_id)
    if result is None:
        raise ValueError("pytest node id does not match pytest pattern - cannot split it")

    # Unpack
    unparametrized_node_id = result.group('base_node_id')
    current_parametrization_id = result.group('parametrization')

    return unparametrized_node_id, current_parametrization_id


def get_id(pytest_node,
           remove_params=None  # type: List[str]
           ):
    # type: (...) -> str
    """
    Returns the unique id associated with current parametrized pytest node, skipping parameters listed in remove_params

    Note: this only works if the id associated with the listed parameters are obtained from the parameter
    value using the 'str' function.

    :param request:
    :param remove_params:
    :return:
    """
    if remove_params is None:
        remove_params = []

    if len(remove_params) == 0:
        return pytest_node.id
    else:
        # Unfortunately there seem to be no possibility in the pytest api to eliminate a named parameter from a node id,
        # because the node ids are generated at collection time and the link between ids and parameter names are
        # forgotten.
        #
        # The best we can do seems to be:
        #   unparametrized_node_id = node.parent.nodeid + '::' + node.function.__name__
        #   current_parametrization_id = node.callspec.id
        #
        # The goal would be to replace current_parametrization_id with a new one (w/o the selected params) from the
        # callspec object. This object (a CallSpec2)
        # - has a list of ids (in node.callspec._idlist)
        # - has a dictionary of parameter names and values (in node.callspec.params)
        # - But unfortunately there is no way to know which parameter name corresponds to which id (no order)
        #
        # Note: a good way to explore this part of pytest is to put a breakpoint in _pytest.python.Function init()

        # So we made the decision to rely only on string parsing, not objects
        node_id_base, node_id_params = split_node_id(pytest_node.nodeid)

        # Create a new id from the current one, by "removing" the ids of the selected parameters
        for p_name in remove_params:
            if p_name not in pytest_node.callspec.params:
                raise ValueError("Parameter %s is not a valid parameter name in node %s"
                                 "" % (p_name, pytest_node.nodeid))
            else:
                # Strong assumption: assume that the id will be str(param_value)
                param_id = str(pytest_node.callspec.params[p_name])
                if param_id in node_id_params:
                    node_id_params = node_id_params.replace(param_id, '*')
                else:
                    raise ValueError("Parameter value %s (for parameter %s) cannot be found in node %s"
                                     "" % (param_id, p_name, pytest_node.nodeid))

        return node_id_base + '[' + node_id_params + ']'


def get_fixture_value(request, fixture_name):
    """
    Returns the value associated with fixture named `fixture_name`, in provided request context.
    This is just an easy way to use `getfixturevalue` or `getfuncargvalue` according to whichever is availabl in
    current pytest version

    :param request:
    :param fixture_name:
    :return:
    """
    try:
        # Pytest 4+ or latest 3.x (to avoid the deprecated warning)
        return request.getfixturevalue(fixture_name)
    except AttributeError:
        # Pytest 3-
        return request.getfuncargvalue(fixture_name)
