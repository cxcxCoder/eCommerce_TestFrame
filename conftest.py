import pytest
import time
import conf.configLoader as configLoader

from utils.readyaml import YamlDataProcess
from utils.recordlogs import logs
from base.cases_loader import batch_load_testcases
from base.precondition import Precondition
from conf.configLoader import ConfigLoader


global_prec = Precondition()
start_time = None

def pytest_sessionstart(session):
    """
    pytest_sessionstart会话级钩子函数，在 测试运行正式开始之前调用，用于执行一些全局初始化工作，如：清空 extract.yaml，可拓展
    """
    global start_time
    start_time = time.time()
    logs.info("*****************************TEST START*****************************")
    if configLoader.IF_BEFORE_CLEAN:
        YamlDataProcess().clean_extract_data()
    if configLoader.IF_MOCK:
        from mock.mock_server import MockServer
        MockServer().thread_run()


def pytest_generate_tests(metafunc):
    """
    参数化钩子函数，在收集测试用例阶段调用，动态生成测试用例
    metafunc代表测试函数的元信息，.fixturenames代表其参数名列表
    """
    cl = ConfigLoader()
    _,batch_data = cl.dynamic_load_batch()


    if "single_case_data" in metafunc.fixturenames:
        cases = batch_load_testcases(batch_data)

        metafunc.parametrize("single_case_data", cases)  # 注入给单接口测试

    if "workflow_case_data" in metafunc.fixturenames:
        cases = batch_load_testcases(batch_data)

        metafunc.parametrize("workflow_case_data", cases)  # 注入给工作流测试



def pytest_runtest_setup(item):
    """
    测试用例级别的前置钩子，在每个测试函数执行前 调用，用于前置条件执行
    item:测试用例对象，包含用例的函数、参数等全部信息
    """
    if hasattr(item, "callspec"):   #callspec标识参数规格pytest.CallerSpec对象，只有参数化才会有
        case_data = item.callspec.params.get("single_case_data", [])
        if case_data:
            _, base_info, _ = case_data
            preconds = base_info.get("preconditions", [])
            if preconds:
                logs.info('//////////////////开始执行前置条件//////////////////')
                for precond in preconds:
                    global_prec.precon_entry(pre_name=precond)


def pytest_sessionfinish(session, exitstatus):
    """
    会话级钩子函数，在所有测试执行完成后调用，用于收尾操作
    """
    logs.info("*****************************TEST END*****************************")
    if configLoader.IF_AFTER_CLEAN:
        YamlDataProcess().clean_extract_data()

#钩子：测试结果总结处理
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    会话结束后终端汇总钩子，定义命令行测试结果的输出格式，追加统计、失败列表、URL链接等
    """
    #生成测试结果摘要字符串
    total = terminalreporter._numcollected
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    error = len(terminalreporter.stats.get('error', []))
    skipped = len(terminalreporter.stats.get('skipped', []))
    duration = time.time() - start_time

    summary = f"""
    自动化测试结果，通知如下，请着重关注测试失败的接口，具体执行结果如下：
    测试用例总数：{total}
    测试通过数：{passed}
    测试失败数：{failed}
    错误数量：{error}
    跳过执行数量：{skipped}
    执行总时长：{duration}
    """
    print(summary)

    #执行邮件、钉钉等管理通知操作
    if configLoader.IF_SEND_EMAIL:
        pass
    if configLoader.IF_SEND_DD:
        pass