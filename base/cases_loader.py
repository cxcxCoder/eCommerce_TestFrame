from utils.readyaml import read_testcase_from_yaml
import os
"""
批量加载收集测试用例,得到测试用例列别供generate_test使用
"""
def batch_load_testcases(file_path):
    batch_cases_list = []
    for file in os.listdir(file_path):
        batch_cases_list.extend(read_testcase_from_yaml(os.path.join(file_path, file)))

    return batch_cases_list

