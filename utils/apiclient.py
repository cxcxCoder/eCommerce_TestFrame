import requests
import urllib3
import allure
import json

from urllib3.exceptions import InsecureRequestWarning
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.recordlogs import logs

import conf.configLoader as configLoader

class ApiClient:
    """
    ApiClient类，封装了发送请求的逻辑
    params:
    - base_url: 接口地址
    func:
    - send_request: 实际调用request发送请求
    - run_request: 中间函数，用于收集日志、报告信息
    """
    def __init__(self, base_url= None):
        if base_url:
            self.base_url = base_url
        elif configLoader.IF_MOCK:
            self.base_url = ' http://'+configLoader.MOCK_HOST+':'+str(configLoader.MOCK_PORT)
        else:
            self.base_url = configLoader.API_HOST

        self.session = requests.Session()

        retry_strategy = Retry(
            total=3, 
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)


    def send_request(self, **kwargs):
        """
        实际请求函数，可以进行session管理
        """
        try:
            response = requests.session.request(**kwargs)
        except Timeout:
            logs.error('请求超时--Timeout')
        except ConnectionError:
            logs.error('连接错误--ConnectionError')
        except HTTPError:
            logs.error('HTTP错误--HTTPError')
        except RequestException:
            logs.error('请求异常--RequestException')

        return response
    
    def run_request(self, api_name,
                    url_endpoint,
                    method,
                    case_name,
                    headers,
                    **tc_kwargs):
        """
        记录请求日志信息、allure报告信息，调用send_request发送请求，返回响应
        """
        try:
            full_url = f"{self.base_url}/{url_endpoint}"
            logs.info(f'接口名称：{api_name}')
            logs.info(f'接口地址：{full_url}')
            logs.info(f'接口方法：{method}')            
            logs.info(f'请求头：{headers}')
            logs.info(f'用例名称：{case_name}')

            allure.attach(str(api_name), '接口名称', allure.attachment_type.TEXT)
            allure.attach(str(full_url), '接口地址', allure.attachment_type.TEXT)
            allure.attach(str(method), '接口请求方法', allure.attachment_type.TEXT)
            allure.attach(json.dumps(headers, indent=2, ensure_ascii=False), '接口请求头', allure.attachment_type.JSON)
            allure.attach(str(case_name), '用例名称', allure.attachment_type.TEXT)

            if any(k in tc_kwargs for k in ['params', 'data', 'json']):
                logs.info(f'请求参数：{tc_kwargs}')
                allure.attach(json.dumps(tc_kwargs, indent=2, ensure_ascii=False), '接口请求参数', allure.attachment_type.JSON)

            #禁止 InsecureRequestWarning 警告输出，配合verify=False使用，避免证书验证失败，仅限测试环境使用
            urllib3.disable_warnings(InsecureRequestWarning)
            res = self.send_request(url=full_url,
                                    method=method,
                                    headers=headers,
                                    timeout=configLoader.API_TIMEOUT,
                                    verify=False,
                                    **tc_kwargs)
            
            allure.attach(json.dumps(res.json(), indent=2, ensure_ascii=False), '接口响应内容', allure.attachment_type.JSON)
        
        except Exception as e:
            logs.error(f'接口请求发送失败：{e}')
            raise

        return res

        