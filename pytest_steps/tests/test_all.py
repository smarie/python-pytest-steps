import ast
import os
import re
from distutils.version import LooseVersion
from os.path import join, dirname, pardir

import pytest

# Make the list of all tests that we will have to execute (each in an independent pytest runner)
THIS_DIR = dirname(__file__)
tests_raw_folder = join(THIS_DIR, pardir, 'tests_raw')
test_files = [f for f in os.listdir(tests_raw_folder) if f.startswith('test')]


META_REGEX = re.compile(
"""^(# META
# )(?P<asserts_dct>.*)
(# END META)
.*""")


@pytest.mark.parametrize('test_to_run', test_files, ids=str)
def test_run_all_tests(test_to_run, testdir):
    """
    This is a meta-test. It is executed for each test file in the 'tests_raw' folder.
    For each of them, the file is retrieved and the expected test results are read from its first lines.
    Then a dedicated pytest runner is run on this file, and the results are compared with the expected ones.

    See https://docs.pytest.org/en/latest/writing_plugins.html

    :param test_to_run:
    :param testdir:
    :return:
    """

    with open(join(tests_raw_folder, test_to_run)) as f:
        # Create a temporary conftest.py file
        # testdir.makeconftest("""""")

        # create a temporary pytest test file
        test_file_contents = f.read()
        testdir.makepyfile(test_file_contents)

        # Grab the expected things to check when this is executed
        m = META_REGEX.match(test_file_contents)
        if m is None:
            raise ValueError("test file '%s' does not contain the META-header" % test_to_run)
        asserts_dct_str = m.groupdict()['asserts_dct']
        asserts_dct = ast.literal_eval(asserts_dct_str)

        # Here we run pytest
        print("\nTesting that running pytest on file %s results in %s" % (test_to_run, str(asserts_dct)))
        result = testdir.runpytest()  # ("-q")

        # Here we check that everything is ok
        try:
            if LooseVersion(pytest.__version__) < "3.0.0":
                assert_outcomes_legacy(result, **asserts_dct)
            else:
                result.assert_outcomes(**asserts_dct)
        except Exception:
            print("Error while asserting that %s results in %s" % (test_to_run, str(asserts_dct)))
            raise


def assert_outcomes_legacy(result, passed=0, skipped=0, failed=0, xfailed=0):
    """in old versions of the pytester plugin, the xfailed kwarg was not present."""
    d = result.parseoutcomes()
    assert passed == d.get("passed", 0)
    assert skipped == d.get("skipped", 0)
    assert failed == d.get("failed", 0)
    assert xfailed == d.get("xfailed", 0)
