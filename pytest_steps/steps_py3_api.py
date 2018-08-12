from decorator import decorate

import pytest_steps.steps as py2_steps


def new_signature_of(f_with_old_api):
    """
    Decorator to declare that a decorated function should be identical to `f_with_old_api`, except for the declared
    signature. It :
     - copies the documentation of `f_with_old_api` onto the decorated function
     - fills the body of the decorated function with a call to f_with_old_api(*args, **kwargs)

    :param f_with_old_api:
    :return:
    """
    def signature_changer_decorator(f_with_new_api):

        # First update the documentation:
        f_with_new_api.__doc__ = f_with_old_api.__doc__

        # then update fields
        if hasattr(f_with_old_api, '__test__'):
            f_with_new_api.__test__ = f_with_old_api.__test__

        # Then create the final function that will be executed when the user calls
        def _execute_self_and_inner(f_with_new_api, *args, **kwargs):
            # First execute the function with the new api
            # Typically that function will be empty but this ensures that python does the args checking:
            # error messages will be the 'python 3' ones in case of mistake.
            #
            # In addition the new api functions can do further checks (not recommended, for consistency with inner func)
            # note that they should not produce results - they will be discarded if so.
            f_with_new_api(*args, **kwargs)

            # then execute the inner function
            return f_with_old_api(*args, **kwargs)

        return decorate(f_with_new_api, _execute_self_and_inner)

    return signature_changer_decorator


@new_signature_of(py2_steps.test_steps)
def test_steps(*steps,
               test_step_name: str= py2_steps._TEST_STEP_NAME_DEFAULT,
               steps_data_holder_name: str= py2_steps._STEPS_DATA_HOLDER_NAME_DEFAULT):
    pass


@new_signature_of(py2_steps.depends_on)
def depends_on(*steps,
               fail_instead_of_skip: bool = py2_steps._FAIL_INSTEAD_OF_SKIP_DEFAULT):
    pass
