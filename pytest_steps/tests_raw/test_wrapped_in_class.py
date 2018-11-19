# META
# {'passed': 1, 'skipped': 0, 'failed': 0}
# END META
from pytest_harvest import get_session_synthesis_dct

from pytest_steps import test_steps


class TestX:
    def test_easy(self):
        print(2)

#     @test_steps('fit', 'predict', 'eval')
#     def test_poly_fit(self):
#         print(1)
#         yield
#
#         print(2)
#         yield
#
#         print(3)
#         yield
#
#
# def test_synthesis(request):
#     """
#     Note: we could do this at many other places (hook, teardown of a session-scope fixture...)
#
#     Note2: we could provide helper methods in pytest_harvest to perform the code below more easily
#     :param request:
#     :param store:
#     :return:
#     """
#     # Get session synthesis
#     # - filtered on the test function of interest
#     results_dct = get_session_synthesis_dct(request.session, filter=test_synthesis.__module__)
#     print(list(results_dct.keys())[0])
