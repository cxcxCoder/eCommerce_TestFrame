import os
import yaml
import logging
"""
配置加载模块,负责动静态加载数据配置等。
"""
DIR_BASE = os.path.dirname(os.path.dirname(__file__))

class ConfigLoader:
    """
    配置加载类,提供数据接在和一些特殊配置的加载
    """
    def __init__(self, config_file = r"conf\config.yaml"):
        self.config_file = config_file
        self.batch_list = self.load_data('file','batch_data')

    def load_data(self,fst_node, snd_node = None, thd_node = None,file = None):
        """
        类似readyaml的数据读取,本质为数据加载为字典后进行访问,此处提供最多三级的节点访问。
        """
        if file is None:
            file = self.config_file
        try:
            with open(file, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                if snd_node is None and thd_node is None:
                    return extract_data[fst_node]
                elif snd_node is not None and thd_node is None:
                    return extract_data[fst_node][snd_node]
                else:
                    return extract_data[fst_node][snd_node][thd_node]
        except Exception as e:
            return None

    def get_log_level(self, level_name):
        """
        获取日志级别,由于不是字符类型,需要getattr进行转换
        """
        level_str = self.load_data("logs", level_name)
        return getattr(logging, level_str.upper(), logging.INFO)    
      
    def dynamic_load_batch(self):
        """
        动态加载batch数据,避免不同批次懒加载
        """
        batch_num = self.load_data('batch_num')
    
        batch_kind,batch_data = self.batch_list[batch_num-1]
        return batch_kind,batch_data


"""
对于一些固定的数据进行懒加载,提前初始化好
"""
configloader = ConfigLoader()

BATCH_LEN =len(configloader.batch_list)

EXCUTOR = configloader.load_data('excutor')

#是否启用的操作
IF_MOCK = configloader.load_data('conf','use_mock')
IF_BEFORE_CLEAN = configloader.load_data('conf','clean_before_test')
IF_AFTER_CLEAN = configloader.load_data('conf','clean_after_test')
IF_SEND_EMAIL = configloader.load_data('conf','send_email')
IF_SEND_DD = configloader.load_data('conf','send_DD')


#文件路径
PRE_DATA = os.path.join(DIR_BASE, configloader.load_data('file','pre_data'))

EXTRACT_YAML = os.path.join(DIR_BASE, configloader.load_data('file','extract','fpath'))

ALLURE_TMP_DIR = os.path.join(DIR_BASE, configloader.load_data('file','allure','tmp_dir'))
ALLURE_REPORT_DIR = os.path.join(DIR_BASE, configloader.load_data('file','allure','pers_dir'))


#api基础配置
API_HOST =  configloader.load_data("api", "base_url")
API_TIMEOUT =  configloader.load_data("api", "timeout")

#mock配置
if IF_MOCK:
    MOCK_HOST = configloader.load_data("mock", "host")
    MOCK_PORT = configloader.load_data("mock", "port")

#logs日志配置
LOG_FOLDER = os.path.join(DIR_BASE, configloader.load_data("logs", "folder"))
LOG_LEVEL = configloader.get_log_level("level")
LOG_STREAM_LEVEL = configloader.get_log_level("stream_level")
LOG_MAXBYTES = configloader.load_data("logs", "file_max_bytes")
LOG_BACKUPCOUNT = configloader.load_data("logs", "file_backup_count")
RENTENTION_DAYS = configloader.load_data("logs", "rentention_days")

#MySql数据库整体配置
MYSQL_CONFIG = configloader.load_data("MySql")

