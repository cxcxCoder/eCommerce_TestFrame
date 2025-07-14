import yaml
import os
import jsonpath
import re


import conf.configLoader as configLoader
from utils.recordlogs import logs
from utils.recordlogs import logs
from requests.utils import dict_from_cookiejar
"""
yaml数据的处理模块,包括yaml用例的读取,extract.yaml的写入、清空、提取数据等功能
- read_testcase_from_yaml: 从yaml文件中读取测试用例数据
- YamlDataProcess: 处理(extract)yaml数据类
"""


def read_testcase_from_yaml(file):
    """
    根据yaml加载测试数据,其中:
    - 单接口测试为一个文件多个用例,提取描述、基础信息、具体用例信息返回
    - 工作流为一个文件一个用例,提取描述、步骤直接返回
    """
    print(f"读取测试用例文件: {file}")
    test_list = []
    try:
        with open(file, 'r',encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
            if len(yaml_data) == 1:
                #基础信息共用

                #获取模块标题
                base_name = os.path.basename(file)
                underscore_index = base_name.find('_')
                featurename = base_name[:underscore_index] if underscore_index != -1 else base_name

                data = yaml_data[0]
                base_info = data['baseInfo']

                testcase_list = data['testCase']
                #用例信息提取
                for tc in testcase_list:
                    test_list.append([featurename.upper(),base_info,tc])
                logs.info(f"成功读取YAML文件测试数据【{file}】")
                return test_list
            else:
                descrip = yaml_data['descrip']
                steps = yaml_data['steps']
                return [[descrip,steps]]    #与单接口测试用例格式一致
    except UnicodeDecodeError:
        logs.error(f"[{file}]文件编码格式错误,--尝试使用utf-8编码解码YAML文件时发生了错误,请确保你的yaml文件是UTF-8格式！")
        raise
    except FileNotFoundError:
        logs.error(f'[{file}]文件未找到,请检查路径是否正确')
        raise
    except Exception as e:
        logs.error(f'获取【{file}】文件数据时出现未知错误: {e}')
        raise

class YamlDataProcess:
    """
    yaml数据处理类,默认处理extract.yaml文件
    params:
    - yaml_file: 处理的yaml文件路径,默认为extract.yaml
    func:
    - read_extract_data: 从yaml文件中读取节点数据
    - write_extract_data: 写入yaml文件
    - extract_data: 从响应内容中提取数据
    - extract_data_list: 从响应内容中提取列表数据
    - clean_extract_data: 清空yaml文件
    """
    def __init__(self, yaml_file = configLoader.EXTRACT_YAML):
        self.extract_yaml_path = yaml_file

    def read_extract_data(self,node_name,scd_node_name = None):
        """
        从extract.yaml读出节点数据,存在二级节点说明为嵌套字典,否则直接一级读取
        """
        try:
            with open(self.extract_yaml_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                if scd_node_name is None:
                    return extract_data[node_name]
                else:
                    return extract_data[node_name][scd_node_name]
        except Exception as e:
            logs.error(f"读取【{self.extract_yaml_path}】文件【{node_name}】【{scd_node_name}】时出现错误: {e}")
            raise
     

    def write_extract_data(self,data):
        """
        写入extract.yaml文件,读出字典解析更新数据后再写入,避免键重复
        """
        logs.info(f'{self.extract_yaml_path}写入数据: 【{data}】')
        try:
            if isinstance(data,dict):
                if os.path.exists(self.extract_yaml_path):
                    with open(self.extract_yaml_path, 'r', encoding='utf-8') as f:
                        try:
                            yaml_data = yaml.safe_load(f)
                            if yaml_data is None:
                                yaml_data = {}
                        except yaml.YAMLError:
                            yaml_data = {}
                else:
                    yaml_data = {}

                yaml_data.update(data)

                with open(self.extract_yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False)

            else:
                logs.error("data is not a dict")
        except Exception as e:
            logs.error(f"【{data}】写入{self.extract_yaml_path}文件时出现错误: {e}")
            raise


    def extract_data(self,extract,res):
        """
        输入extract字典,响应内容,通过extract的value表达式从响应内容中提取数据,并写入yaml文件
        支持多种响应内容提取:
        - header. :直接提取的头部的json字段
        - cookies :直接从响应对象获取,而不是从响应头提取,进行拍平存储,便于直接读出
        - cookies. :从cookies中取出字段存储,一般处理cookies内的token等信息
        - jsonpath :使用jsonpath从响应体获取信息,得到且只需要得到[aa]这样的内容,取出aa写入
        - 正则 :使用正则表达式从响应体中提取信息
        yaml格式:
        extract:
          csrf: headers.X-CSRF-Token
          cookies: cookies
          token: cookies.token
          userId: $..userId
          userAge: '"token"\s*:\s*"([^"]+)"'
        """
        
        for key,value in extract.items():
            extract_data = {}
            try:
                #headers提取,例如：csrf: headers.X-CSRF-Token
                if value.startswith('headers.'):
                    header_key = value.split('.', 1)[1]
                    if (res_data := res.headers.get(header_key)):
                        extract_data = {key:res_data}
                    else:
                        raise Exception(f"【{value}】 未在--响应头--找到字段【{header_key}】,响应头为：{res.headers}:")
                
                #处理整个cookie提取,例如：cookies: cookies
                elif value == 'cookies':
                    if (cookie_dict := dict_from_cookiejar(res.cookies)):
                        res_data = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                        extract_data = {key:res_data}
                    else:
                        raise Exception(f"【{value}】 未在--响应头--找到cookies,响应头为：{res.headers}")
                
                #处理从cookies中提取数据,例如：token: cookies.token
                elif value.startswith('cookies.'):
                    cookie_key = value.split('.', 1)[1]
                    if (res_data := res.cookies.get(cookie_key)):
                        extract_data = {key:res_data}
                    else:
                        raise Exception(f"【{value}】未在--响应头cookies--找到字段【{cookie_key}】,响应头为：{res.headers}")

                #jsonpath提取数据
                elif '$' in value:
                    if (res_data_list := jsonpath.jsonpath(res.json(),value)):
                        if res_data_list[0] is not None:
                            extract_data = {key:res_data_list[0]}
                    else:
                        raise Exception(f"【{value}】--jsonpath--未在响应内容中找到字段【{key}】数据,响应体为：{res.text}")

                #正则提取数据
                else:                    
                    if (match_data := re.search(value, res.text)):
                        if r'(\d)' in value or r'(\d*)' in value:
                            res_data = int(match_data.group(1))
                        else:
                            res_data = match_data.group(1)
                        extract_data = {key:res_data}
                    else:
                        raise Exception(f"【{value}】--正则表达式--未在响应内容中找到字段【{key}】数据,响应体为：{res.text}")
                
            except Exception as e:
                logs.error(f'extract写入出现异常：{e}')
                raise
            
            if extract_data:
                self.write_extract_data(extract_data)


    def extract_data_list(self,extract_list,res):
        """
        输入extract字典,响应内容,通过extract的value表达式从响应内容中提取列表数据,并写入yaml文件
        支持jsonpath与正则表达式显示提取:
        正则:正则表达式提取,处理得到列表全部写入
        jsonpath:jsonpath提取,得到例如[aa,bb,cc],把整个匹配内容列表写入
        """
        for key,value in extract_list.items():
            extract_data = {}
            try:                
                #正则提取数据
                if "(.+?)" in value or "(.*?)" in value:                
                    if (res_data := re.findall(value, res.text, re.S)):
                        extract_data = {key:res_data}                       
                    else:
                        raise Exception(f"【{value}】--正则表达式--未在响应内容中找到字段【{key}】列表数据,响应体为：{res.text}")
                        
                #jsonpath提取数据
                elif '$' in value:
                    if (res_data := jsonpath.jsonpath(res.json(),value)):
                        extract_data = {key:res_data}
                    else:
                        raise Exception(f"【{value}】--jsonpath--未在响应内容中找到字段【{key}】列表数据,响应体为：{res.text}")
            except Exception as e:
                logs.error(f'extract_list写入出现异常：{e}')
                raise

            if extract_data:
                self.write_extract_data(extract_data)

    def clean_extract_data(self):
        """
        清空extract.yaml文件
        """
        open(self.extract_yaml_path, 'w').close()
        logs.info(f"清空extract.yaml文件")

