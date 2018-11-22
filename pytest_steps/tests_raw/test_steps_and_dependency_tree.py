# META
# {'passed': 8, 'skipped': 5, 'failed': 1}
# END META

# This is the example in https://github.com/smarie/python-pytest-steps/issues/17
import pytest
from pytest_steps import test_steps


@pytest.fixture(scope='module')
def results_dct():
    return dict()


@test_steps('step1', 'step2')
def test_1_2(results_dct):
    # step 1
    results_dct['step1'] = 1
    yield
    # step 2
    results_dct['step2'] = 'hello'
    yield


@test_steps('step3', 'step4')
@pytest.mark.parametrize('p', ['a', 'b'], ids="p={}".format)
def test_3_4(p, results_dct):
    if 'step2' not in results_dct:
        pytest.skip("Can not start step 3: step 2 has not run successfuly")
    # step 3
    results_dct.setdefault('step3', dict())[p] = 'bla'
    if p == 'b':
        assert False
    yield
    # step 4
    results_dct.setdefault('step4', dict())[p] = 'blabla'
    yield


@test_steps('step5', 'step6')
@pytest.mark.parametrize('q', ['a', 'b'], ids="q={}".format)
@pytest.mark.parametrize('p', ['a', 'b'], ids="p={}".format)
def test_5_6(p, q, results_dct):
    if 'step4' not in results_dct:
        pytest.skip("Can not start step 5: step 4 has not run successfuly")
    elif p not in results_dct['step4']:
        pytest.skip("Can not start step 5: step 4 has not run successfuly for this value of p=%s" % p)
    # step 5
    yield
    # step 6
    yield
