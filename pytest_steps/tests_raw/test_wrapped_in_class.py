# META
# {'passed': 6, 'skipped': 0, 'failed': 0}
# END META
from pytest_steps import test_steps

decorator_success = False
generator_success = False


class TestX:
    def test_easy(self):
        print(2)

    @test_steps('a', 'b')
    def test_decorator(self, test_step):
        global decorator_success
        print(test_step)
        if test_step == 'a' and decorator_success is False:
            decorator_success = 0
        elif test_step == 'b' and decorator_success == 0:
            decorator_success = True

    @test_steps('a', 'b')
    def test_generator(self):
        global generator_success

        print('a')
        yield

        print('b')
        generator_success = True
        yield


def test_z():
    assert decorator_success
    assert generator_success
