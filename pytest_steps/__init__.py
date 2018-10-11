from sys import version_info as vi
if vi >= (3, 0):
    # Python 3+: load all the symbols with 'more explicit api'
    from pytest_steps.steps_py3_api import test_steps, depends_on
else:
    from pytest_steps.steps import test_steps
    from pytest_steps.steps_parametrizer import depends_on

from pytest_steps.steps_generator import optional_step, one_per_step
from pytest_steps.steps_parametrizer import StepsDataHolder

__all__ = [
    # the submodules
    'steps', 'decorator_hack', 'steps_common', 'steps_generator', 'steps_parametrizer',
    # all symbols imported above
    'test_steps',
    'StepsDataHolder', 'depends_on',
    'optional_step', 'one_per_step'
]
