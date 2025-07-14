import yaml
import conf.configLoader as configLoader
import requests
import copy

from utils.recordlogs import logs
from utils.readyaml import YamlDataProcess


class Precondition:
    """
    前置条件执行类,负责动态处理precon.yaml内提供的前置条件请求,保存上下文extract数据
    
    """
    def __init__(self):
        self.yaml_data_process = YamlDataProcess()

        with open(configLoader.PRE_DATA, 'r',encoding='utf-8') as f:
            self.pre_data = yaml.safe_load(f)
        

    def preconBase(self,base_info,test_case):
        """
        类似requestBase的excute_test,但是主要复制请求与上下文存储,无断言与报告内容
        """
        try:
            #base_info处理
            api_url = base_info['url']
            method = base_info['method']
            headers = base_info['headers']

            
            #test_case--case_name处理用例名称
            test_case.pop('case_name',None)
    
            #test_case--extract处理上下文存储数据
            extract = test_case.pop('extract',None)
            extract_list = test_case.pop('extract_list',None)

                    
            #执行requests请求
            res = requests.request(url=configLoader.API_HOST+api_url,
                                    method=method,
                                    headers=headers,
                                    verify=False,
                                    **test_case)
            
            
            #extract上下文写入            
            if extract:
                self.yaml_data_process.extract_data(extract,res)
            if extract_list:
                self.yaml_data_process.extract_data_list(extract_list,res)
            
        except Exception as e:
            logs.error(e)
            raise e
        
 
    def precon_entry(self,pre_name):
        """
        根据字段内容,动态执行precon.yaml内的前置条件请求
        """
        logs.info(f"执行前置条件:{pre_name}")

        if self.pre_data.get(pre_name,None):
            login_data = copy.deepcopy(self.pre_data[pre_name])

            self.preconBase(login_data['baseInfo'],login_data['testCase'])
        else:
            logs.error(f"不存在【{pre_name}】的前置条件")




