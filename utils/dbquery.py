import pymysql
import redis

from utils.recordlogs import logs
import conf.configLoader as configLoader
"""
数据库连接与查询模块,封装各种数据库的初始化连接、关闭、删除(用于回撤)、查询操作
- ConnectMySQL: 封装MySQL连接、关闭、删除、查询操作
- ConnectRedis: 封装Redis连接、关闭、查询操作
- 待拓展
"""
class ConnectMySQL:
    def __init__(self):
        #从配置文件读取
        mysql_conf = configLoader.MYSQL_CONFIG

        try:
            self.conn = pymysql.connect(**mysql_conf, charset='utf8')
            # cursor=pymysql.cursors.DictCursor,将数据库表字段显示，以key-value形式展示
            self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        except Exception as e:
            logs.error(f"MySql连接异常:{e}")
            raise

    def close(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception as e:
            logs.error(f"MySQL关闭连接异常:{e}")
            raise

    def delete(self, sql):
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            logs.error(f" MySQL删除异常:{e}")
            raise

    def query(self,sql):
        """
        查询语句，返回列表格式：
        - 如果查询结果有数据，返回 [value1, value2,...]扁平列表
        - 如果查询结果为空,或sql语句错误等,返回空列表
        """
        try:
            self.cursor.execute(sql)
            query_result = self.cursor.fetchall()

            if query_result:
                return [list(row.values())[0] for row in query_result]
                
            else:return []

        except Exception as e:
            logs.error(f"MySQL语句【{sql}】查询异常:{e}")
            raise


#简单实现，未验证
class ConnectRedis:
    def __init__(self):
        # Redis连接配置，建议从配置文件读取
        redis_conf = {
            'host': '127.0.0.1',
            'port': 6379,
            'db': 0,
            'password': None,  # 如果有密码请填写
            'decode_responses': True  # 自动把字节转换成字符串，方便处理
        }

        try:
            self.client = redis.Redis(**redis_conf)
            # 测试连接是否成功
            self.client.ping()
        except Exception as e:
            logs.error(f"Redis连接异常:{e}")
            self.client = None
            raise

    def close(self):
        # redis-py 不需要显式关闭连接，连接池会管理
        # 如果用的是连接池，可以手动释放，或者直接pass
        # 这里写个占位，方便以后扩展
        try:
            if self.client:
                self.client.close()  # redis-py 4.x有close方法
        except Exception as e:
            logs.error(f"Redis关闭连接异常:{e}")
            raise

    def query(self, key):
        """
        简单查询指定key对应的值，返回列表格式：
        - 如果是字符串，返回 [value]
        - 如果是list类型，返回list内容
        - 如果是set类型，返回list内容
        - 如果是hash类型，返回hash所有field对应的value列表
        - 其它类型返回空列表
        
        你可以根据需要修改或扩展更多类型
        """
        if not self.client:
            print("Redis client not connected")
            return []

        try:
            key_type = self.client.type(key)
            if key_type == 'none':
                print(f"Key '{key}' does not exist")
                return []
            elif key_type == 'string':
                val = self.client.get(key)
                return [val] if val is not None else []
            elif key_type == 'list':
                return self.client.lrange(key, 0, -1)
            elif key_type == 'set':
                return list(self.client.smembers(key))
            elif key_type == 'hash':
                # 返回hash所有field对应的value列表
                return list(self.client.hvals(key))
            else:
                print(f"Key '{key}' type '{key_type}' is not supported in query")
                return []
        except Exception as e:
            logs.error(f"Redis查询异常:{e}")
            raise