import json
import re
import ast

from utils.apiclient import ApiClient
from utils.debugtalk import DebugTalk
from utils.readyaml import YamlDataProcess
from utils.assertions import Assertions
from utils.recordlogs import logs


class RequestBase:
    """
    测试实际执行类,统一合并管理测试用例执行
    func:
    - reload_yaml_function: 处理yaml文件中的$函数,并返回处理后的数据
    - excute_test: 执行测试用例的核心函数,负责
        1.从base_info,test_case读出用例名称、发送请求的相关内容、验证内容、提取内容,以及上述内容的$替换
        2.发送请求,获取响应内容
        3.根据验证内容进行断言验证
        4.根据提取内容进行数据提取,并写入yaml文件
    """
    def __init__(self):
        self.apiclient = ApiClient()
        self.assertions = Assertions()
        self.yaml_data_process = YamlDataProcess()

    def reload_yaml_function(self,data):
        """
        通过json.dump将数据转化成json字符串,便于使用字符串的replace把$函数替换,然后通过json.load将数据还原
        """
        str_data = data
        try:
            #data数据转化成json字符串,用于$函数的替换
            if not isinstance(data,str):
                str_data = json.dumps(data,ensure_ascii=False)

            #$函数替换
            pattern = r"\$\{(\w+)\((.*?)\)\}"
            matches = re.findall(pattern, str_data)

            for raw_name,raw_args in matches:
                #ast.literal_eval将字符串转换成python对象,raw_args加上()变成元组；不支持关键字传参
                args = ast.literal_eval(f'({raw_args},)') if raw_args else []
                func = getattr(DebugTalk(),raw_name)
                result = func(*args)
                
                #替换表达式
                orgin_exstr = f"${{{raw_name}({raw_args})}}"
                str_data = str_data.replace(orgin_exstr,str(result))

                logs.info(f'【{orgin_exstr}】替换称为【{result}】')
            #还原json字符串为数据
            data = json.loads(str_data)

        except Exception as e:
            logs.error(f'yaml $ 数据重载处理出现异常：{e}')
            raise

        return data

        
    def excute_test(self,base_info,test_case):
        """
        执行用例的核心函数,负责
        1.从base_info,test_case读出用例名称、发送请求的相关内容、验证内容、提取内容,以及上述内容的$替换
        2.发送请求,获取响应内容
        3.根据验证内容进行断言验证
        4.根据提取内容进行数据提取,并写入yaml文件
        """
        try:
            #base_info处理
            api_name = base_info['api_name']
            api_url = base_info['url']
            method = base_info['method']
            headers = self.reload_yaml_function(base_info['headers'])

            #test_case--case_name处理用例名称
            case_name = test_case.pop('case_name',None)

            #test_case--validation处理验证数据
            validations = test_case.pop('validation',None)

            #test_case--extract处理上下文存储数据
            extract = test_case.pop('extract',None)
            extract_list = test_case.pop('extract_list',None)

            #test_case--case_data处理各个类型的参数
            data_type = ['json','data','params']
            for key,value in test_case.items():
                if key in data_type:
                    test_case[key] = self.reload_yaml_function(value)
                    
            #执行requests请求
            res = self.apiclient.run_request(api_name,api_url, method, case_name,headers,**test_case)


            #extract上下文写入
            if extract:
                self.yaml_data_process.extract_data(extract,res)
            if extract_list:
                self.yaml_data_process.extract_data_list(extract_list,res)
            
        except Exception as e:
            logs.error(e)
            raise e

        #断言只做判断,不错异常处理,直接决定用例是否通过,日志在内部记录
        try:
            if validations:
                assert self.assertions.assert_result(validations,res)
                logs.info(f'用例【{api_name}--{case_name}】执行成功✅✅✅✅✅✅✅✅✅✅')
        except Exception as e:
            logs.error(f'用例【{api_name}--{case_name}】执行失败❌❌❌❌❌❌❌❌❌❌')
            raise e




