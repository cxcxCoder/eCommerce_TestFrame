import allure
import pytest
import uuid
from base.requestBase import RequestBase
"""
测试执行入口,pytest通过命令执行后,pytest_generate_tests根据配置载入参数化yaml测试用例数据
func:
- test_single: 单个测试用例执行
- test_workflow: 流程测试用例执行
"""

def test_single(single_case_data):
    """
    单接口测试入口,由pytest_generate_tests载入数据,pytest_runtest_setup处理前置条件,保证独立性
    params:
    - single_case_data: 一组单接口的测试用例数据
    """
    #解包成feature_name,base_info, test_case供后续使用
    feature_name,base_info, test_case = single_case_data
    
    #allure动态记录用例信息
    allure.dynamic.feature(feature_name)
    allure.dynamic.story(base_info['api_name'])
    allure.dynamic.title(test_case['case_name'])

    #人为动态分配uuid
    allure.dynamic.id(str(uuid.uuid4()))

    #执行测试用例
    RequestBase().excute_test(base_info,test_case)


def test_workflow(workflow_case_data):
    """
    流程测试入口,只需要载入数据,也可以进行简单前置处理,内部逐步执行测试步骤
    params:
    - workflow_case_data: 流程测试用例数据,包含多个步骤
    """
    #解包成descrip描述信息和steps步骤信息
    descrip,steps = workflow_case_data
    
    allure.dynamic.feature(descrip['feature_name'])
    allure.dynamic.story(descrip['story_name'])
    
    allure.dynamic.id(str(uuid.uuid4()))

    for case_data in steps:
        with allure.step(case_data['testCase']['case_name']):
            base_info = case_data['baseInfo']
            test_case = case_data['testCase']

            RequestBase().excute_test(base_info,test_case)

    
