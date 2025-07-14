import random
import time
from utils.readyaml import YamlDataProcess
from utils.recordlogs import logs

class DebugTalk:
    """
    动态参数类,用于为yaml测试数据提供动态的数据替换
    """
    def __init__(self):
        self.extract_reader = YamlDataProcess()

    def get_extract_data(self,node_name,controller=None):
        """
        根据节点名称和控制器,调用YamlDataProcess类获取节点数据,根据controller有如下处理:
        1.数字:表明节点取出的内容为列表,再根据数字取值对列表进行操作
            a.-2,返回列表
            b.-1,返回字符串
            c.0,随机返回一个值
            d.自然数,表示取出列表的第controller个值
        2.其它：表明去除内容为正常的字典内容
            a.空,表明node_name已经可以取出值
            b.非空,即controller表示二级节点,通过嵌套字典取值
        
        """
        #读数据异常由read_extract_data记录及抛出,只需处理controller为数字时异常
        if controller is None or isinstance(controller,str):
            data = self.extract_reader.read_extract_data(node_name,controller)
        elif isinstance(controller,int):
            list_data = self.extract_reader.read_extract_data(node_name)
            
            try:
                if isinstance(list_data,list):
                    if controller == -2:
                        #data = list_data    #['a', 'b', 'c'] -> ['a', 'b', 'c']
                        data = ','.join(map(str, list_data)).split(',')  #[1, 2, 3] -> ['1', '2', '3']
                    elif controller == -1:
                        data = ','.join(map(str, list_data))  #['a', 'b', 'c'] -> 'a,b,c'
                    elif controller == 0:
                        data = random.choice(list_data)
                    elif controller > 0:
                        data = list_data[controller-1]
                    else:
                        data = None
                        logs.error("不支持的参数值")
                else:
                    data = list_data
            except Exception as e:
                logs.error(f'contoller【{controller}】数字处理出现异常:{e}')
                raise

        else:
            data = None
            logs.error("不支持的参数类型")
            raise Exception(f"不支持的参数【{str(controller)}】-类型【{str(type(controller))}】")
        return data
        
    def md5_encryption(self, params):
        """参数MD5加密"""
        pass


    def sha1_encryption(self, params):
        """参数sha1加密"""
        pass


    def base64_encryption(self, params):
        """base64加密"""
        pass


    def timestamp(self):
        """获取当前时间戳，10位"""
        t = int(time.time())  # 获取当前时间的秒数并转为整数
        return t

    def start_time(self):
        """获取当前时间的前一天标准时间"""
        pass


    def end_time(self):
        """获取当前时间标准时间格式"""
        pass


    def start_forward_time(self):
        """获取当前时间的前15天标准时间，年月日"""
        pass


    def start_after_time(self):
        """获取当前时间的后7天标准时间，年月日"""
        pass


    def end_year_time(self):
        """获取当前时间标准时间格式，年月日"""
        pass


    def today_zero_tenstamp(self):
        """获取当天00:00:00时间戳，10位时间戳"""
        pass


    def specified_zero_tamp(self, days):
        """获取当前日期指定日期的00:00:00时间戳，days：往前为负数，往后为整数"""
        pass






