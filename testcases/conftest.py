import pytest
from utils.recordlogs import logs


@pytest.fixture(autouse=True)
def test_setup_and_teardown():
    """
    简单标识日志的测试开始与结束
    """
    logs.info('********************用例开始********************')
    yield
    logs.info('********************用例结束********************\n')



@pytest.fixture(scope='session', autouse=True)
def db_init():
    """
    初始化数据库表格、数据等信息
    """
    pass