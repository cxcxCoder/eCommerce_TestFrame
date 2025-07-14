import logging
import os
import time
import datetime

from logging.handlers import RotatingFileHandler

import conf.configLoader as configLoader
"""
日志处理模块,进行日志类的定义和日志对象实例化获取,其它模块通过使用实例化的logs对象进行日志输出
class:
- RecordLogs: 日志类,负责日志对象获取,初始化设置、过期日志管理
params:
- logs: 日志对象
"""
class RecordLogs:
    """
    日志类,负责日志对象获取,初始化设置、过期日志管理
    """
    def __init__(self, log_folder):
        self.log_folder = log_folder
        self.logfile_name = os.path.join(log_folder,f'test.{time.strftime("%Y%m%d")}.log')  #日志文件名,按天生成日志文件
        
        self.handle_overdue_logs()  #每次启用处理过期日志

    def handle_overdue_logs(self):
        now_time = datetime.datetime.now()  #datetime对象：2025-05-30 21:17:46.430581
        time_offset = datetime.timedelta(days=configLoader.RENTENTION_DAYS)  #时间差对象

        overdue_time = now_time - time_offset  #过期时间的datetime对象

        for file in os.listdir(self.log_folder):
            if file.endswith('.log'):
                file_ctime = os.path.getctime(os.path.join(self.log_folder, file))  #文件创建时间的Unix时间戳
                #检查是否早于过期时间
                if file_ctime < overdue_time.timestamp():  #文件创建时间早于过期时间
                    os.remove(os.path.join(self.log_folder, file))  #删除过期日志

        
    def get_logger(self):
        """
        根据config.yaml配置文件进行日志对象的获取与初始化配置
        """
        #获取logger对象,__name__动态获取模块名
        logger = logging.getLogger(__name__)

        #配置logger
        if not logger.handlers: #确保不重复添加handler
            #设置日志级别
            loglevel = logging.DEBUG    #= setting.LOG_LEVEL    #从配置文件中获取日志级别
            logger.setLevel(loglevel)

            #设置日志格式
            log_format = logging.Formatter(
                '%(levelname)s - %(asctime)s - %(filename)s:%(lineno)d -[%(module)s:%(funcName)s] - %(message)s')
            """INFO - 2025-05-20 11:58:35,604 - assertions.py:198 -[assertions:assert_result] - 测试成功"""
            
            #设置日志文件: maxBytes:控制单个日志文件的大小,单位是字节,backupCount:用于控制日志文件的数量
            fh = RotatingFileHandler(filename=self.logfile_name,
                                    mode='a',   #追加
                                    maxBytes=configLoader.LOG_MAXBYTES,  #单个日志文件大小
                                    backupCount=configLoader.LOG_BACKUPCOUNT,  #日志文件数量
                                    encoding='utf-8')
            fh.setFormatter(log_format)
            fh.setLevel(loglevel)

            #设置日志控制台输出
            stream_loglevel = configLoader.LOG_STREAM_LEVEL    #从配置文件中获取日志级别
            sh = logging.StreamHandler()
            sh.setLevel(stream_loglevel)
            sh.setFormatter(log_format)

            #载入日志处理器
            logger.addHandler(fh)
            logger.addHandler(sh)
        return logger


#设置日志存储文件夹
log_folder = configLoader.LOG_FOLDER
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

#实例化日志记录器
recordlogs = RecordLogs(log_folder)
logs = recordlogs.get_logger()      #实例化的日志对象,其它模块通过其进行日志输出
