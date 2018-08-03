from sys import version_info as vi
if vi >= (3, 0):
    # Python 3+: load all the symbols with 'more explicit api'
    from pytest_steps.steps_py3_api import test_steps, depends_on
    from pytest_steps.steps import StepsDataHolder
else:
    from pytest_steps.steps import test_steps, StepsDataHolder, depends_on


__all__ = [
    # the submodules
    'steps', 'decorator_hack',
    # all symbols imported above
    'test_steps', 'StepsDataHolder', 'depends_on'
]
