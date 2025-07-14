import jsonpath
import allure

from utils.dbquery import ConnectMySQL
from utils.recordlogs import logs

class Assertions:
    """
    断言类，提供断言方法，通过标志位进行断言管理，日志与allure记录断言信息
    func:
    - none_process: 处理None值
    - status_code_assert: 断言http状态码
    - contains_assert: 断言字段内容是否包含
    - equal_assert: 断言字段内容是否相等
    - nequal_assert: 断言字段内容是否不相等
    - any_assert: 断言响应中是否存在任意字段内容相等
    - db_assert: 断言数据库查询结果是否符合预期
    - assert_result: 整体断言入口，分发断言类型执行，收集结果并返回
    """

    def none_process(self,value):
        """
        处理None值，便于断言处理
        """
        n_set = {'NONE','NULL',''}
        if str(value).upper() in n_set:
            return None
        else:
            return value


    def status_code_assert(self,val_value, sc):
        """
        比较http状态码，yaml validation格式如下：
        - status_code: 200
        """
        assert_info = f'预期状态码：【{val_value}】,实际状态码：【{sc}】'
        if sc == val_value:
            logs.info(f'✅http状态码断言**通过**，{assert_info}')
            allure.attach(assert_info,'✅状态码断言通过',allure.attachment_type.TEXT)
            return 0
        else:
            logs.error(f'❌http状态码断言**失败**，{assert_info}')
            allure.attach(assert_info,'❌状态码断言失败',allure.attachment_type.TEXT)
            return 1

    def contains_assert(self,val_value, res_js):
        """
        比较字段内容是否包含,单值要求字符串包含,列表要求集合包含,返回0表示通过,
        yaml格式如下:
        - contains: { 'msg': '成功' }
        - contains: { 'goodsId': ['1222', '1223'] }
        - contains: { 'msg': '成功','goodsId': ['1222', '1223'] }
        """
        contain_flag = 0    #整体标志位
        for expected,v_value in val_value.items():
            c_flag = 0
            v_value = self.none_process(v_value)

            extract_list = jsonpath.jsonpath(res_js, f'$..{expected}')  #jsonpath得到的一个包含键对应的值组成的列表[[xx,xx],xx]
            #列表为空，找不到值，视为错误
            if not extract_list:
                if v_value:
                    c_flag +=1                    
                continue
            
            if isinstance(v_value,list):    #列表,要求集合包含
                extract_list = extract_list[0]
                if not set(v_value).issubset(set(extract_list)):
                    c_flag += 1
            else:
                #单值，要求结果内至少有一个包含预期值                     
                if not any(str(v_value) in str(self.none_process(exact_value)) for exact_value in extract_list):    #str()也可以处理None值
                    c_flag += 1
                
            #根据c_flag判断单条验证是否通过
            if len(extract_list) == 1:extract_list = extract_list[0]
            assert_info = f'【{expected}】预期值：【{v_value}】,实际值：【{extract_list}】'
            if c_flag:
                logs.error(f'❌包含断言**失败**，{assert_info}')
                allure.attach(assert_info,'❌包含断言失败',allure.attachment_type.TEXT)
            else:
                logs.info(f'✅包含断言**通过**，{assert_info}')
                allure.attach(assert_info,'✅包含断言成功',allure.attachment_type.TEXT)

            contain_flag += c_flag
        return contain_flag



    def equal_assert(self,val_value, res_js):
        """
        比较字段内容是否相等,列表要求完全相同,单值要求至少存在一个完全相同,返回0表示通过,
        yaml格式如下:
        - equal: { 'goodsId': '1888120' }
        - eqaul: { 'goodsId': ['1222', '1223'] }
        - equal: { 'goodsId': '1888120' ,'goodsId': ['1222', '1223']}
        """
        equal_flag = 0
        for expected,v_value in val_value.items():
            e_flag = 0
            v_value = self.none_process(v_value)


            #extract_list = jsonpath.jsonpath(res_js, f'$.{expected}')   #只检查一级字典
            extract_list = jsonpath.jsonpath(res_js, f'$..{expected}')
            if not extract_list:
                if v_value:
                    e_flag +=1
                continue

            #处理列表和单值情形：列表要求预期列表和响应结果排序后相等；单值要求响应结果至少有一个等于预期值
            if isinstance(v_value,list):    #列表
                extract_list = extract_list[0]
                if sorted(v_value) != sorted(extract_list):
                    e_flag += 1
            else:
                if not any(self.none_process(exact_value) == v_value for exact_value in extract_list):
                    e_flag += 1
                

            #根据e_flag判断单条验证是否通过
            if len(extract_list) == 1:extract_list = extract_list[0]
            assert_info = f'【{expected}】预期值：【{v_value}】,实际值：【{extract_list}】'
            if e_flag:
                logs.error(f'❌相等断言**失败**，{assert_info}')
                allure.attach(assert_info,'❌相等断言失败',allure.attachment_type.TEXT)
            else:
                logs.info(f'✅相等断言**通过**，{assert_info}')
                allure.attach(assert_info,'✅相等断言成功',allure.attachment_type.TEXT)
            equal_flag += e_flag
        return equal_flag



    def nequal_assert(self,val_value, res_js):
        """
        比较字段内容是否不相等,必须每个匹配到的响应结果都不等于才通过,返回0表示通过,
        yaml格式如下:
        - nequal: { 'goodsId': '1888120' }
        - neqaul: { 'goodsId': ['1222', '1223'] }
        - nequal: { 'goodsId': '1888120' ,'goodsId': ['1222', '1223']}
        """
        nequal_flag = 0
        for expected,v_value in val_value.items():
            ne_flag = 0
            v_value = self.none_process(v_value)

            #extract_list = jsonpath.jsonpath(res_js, f'$.{expected}')   #只检查一级字典
            extract_list = jsonpath.jsonpath(res_js, f'$..{expected}')
            if not extract_list:
                if not v_value:
                    ne_flag +=1
                continue

             #处理列表和单值情形：列表要求预期列表和响应结果排序后不相等；单值要求响应结果每一个都不等于
            if isinstance(v_value,list):    #列表
                extract_list = extract_list[0]
                if sorted(v_value) == sorted(extract_list):
                    ne_flag += 1
            else:
                if any(self.none_process(exact_value) == v_value for exact_value in extract_list):
                    ne_flag += 1                

            #根据ne_flag判断单条验证是否通过
            if len(extract_list) == 1:extract_list = extract_list[0]
            assert_info = f'【{expected}】预期值：【{v_value}】,实际值：【{extract_list}】'
            if ne_flag:
                logs.error(f'❌不等断言**失败**，{assert_info}')
                allure.attach(assert_info,'❌不等断言失败',allure.attachment_type.TEXT)
            else:
                logs.info(f'✅不等断言**通过**，{assert_info}')
                allure.attach(assert_info,'✅不等断言成功',allure.attachment_type.TEXT)
            nequal_flag += ne_flag
        return nequal_flag
    

    def any_assert(self,val_value, res_js):
        """
        比较响应中是否存在任意字段内容相等,可以检查更多层级,目前与equal重复,且只处理单值
        yaml格式如下:
        - any: { 'user': '奶龙' }
        """
        any_flag = 0
        for expected,v_value in val_value.items():
            a_flag = 0
            v_value = self.none_process(v_value)

            extract_list = jsonpath.jsonpath(res_js, f'$..{expected}')
            if not extract_list:
                a_flag +=1
                continue
            #只要有一个匹配到的等于就通过
            if not any(self.none_process(exact_value) == v_value for exact_value in extract_list):
                a_flag += 1

            #根据a_flag判断单条验证是否通过
            assert_info = f'【{expected}】预期值：【{v_value}】,实际值：【{extract_list}】'
            if a_flag:
                #allure
                logs.error(f'❌任意断言**失败**，{assert_info}')
                allure.attach(assert_info,'❌任意断言失败',allure.attachment_type.TEXT)
            else:
                logs.info(f'✅任意断言**通过**，{assert_info}')
                allure.attach(assert_info,'✅任意断言成功',allure.attachment_type.TEXT)
            any_flag += a_flag
        return any_flag


    def db_assert(self,val_value):
        """
        比较数据库查询结果是否相等,单次只能比较一条，支持列表对比
        yaml格式如下:
        - db: { expected:'200034', sql:'SELECT good_id FROM goods WHERE good_name = "iPhone X"' }
        """
        flag = 0
        sql_db = ConnectMySQL()
        expected = val_value.get('expected',None)
        if not (sql := val_value.get('sql',None)):
            logs.error(f'数据库断言失败，sql语句为空')
            return 1

        query_list = sql_db.query(sql)  #得到查询结果的列表
        #空值
        none_set = {'NONE','NULL','[]',''}
        if not query_list:
            #预期与得到皆为空
            if str(expected).upper() in none_set:pass
            #预期非空，得到为空            
            else:flag += 1
        #单值
        elif not isinstance(expected,list) and query_list:
            if expected == query_list[0]:  pass#只检查第一个值;其中一个满足即可：if expected in query_list:
            else:flag += 1
        #列表
        elif isinstance(expected,list) and query_list:
            if sorted(expected) != sorted(query_list):#列表排序后比较
                flag += 1
        #其它
        else:flag += 1
        
        sql_db.close()

        assert_info = f'sql语句：【{sql}】\n预期结果：【{expected}】,实际结果：【{query_list}】'
        if flag:
            logs.error(f'❌数据库断言**失败**，{assert_info}')
            allure.attach(assert_info,'❌数据库断言失败',allure.attachment_type.TEXT)
        else:
            logs.info(f'✅数据库断言**通过**，{assert_info}')
            allure.attach(assert_info,'✅数据库断言成功',allure.attachment_type.TEXT)

        return flag

    def assert_result(self,validations,res):
        """
        传入validations的验证字典列表，根据列表元素的键决定处理方式，如下：
        'status_code':判断response的http状态码
        'contains':判断字段内容是否包含
        'equal':判断字段内容是否相等
        'nequal':判断字段内容是否不相等
        'any':判断任意字段内容是否相等，可以进入嵌套字典
        'db':数据库断言        
        """
        #logs.info(f'开始执行断言\n预期结果：{validations}\n实际结果：{res.json()}')
        sucess_flag = 0
        res_data = res.json()

        for val in validations:
            for key,value in val.items():
                if key == 'status_code':
                    sucess_flag += self.status_code_assert(value, res.status_code)
                elif key == 'contains':
                    sucess_flag += self.contains_assert(value, res_data)
                elif key == 'equal':
                    sucess_flag += self.equal_assert(value, res_data)
                elif key == 'nequal':
                    sucess_flag += self.nequal_assert(value, res_data)
                elif key == 'any':
                    sucess_flag += self.any_assert(value, res_data)
                elif key == 'db':
                    sucess_flag += self.db_assert(value)
                else:
                    raise ValueError(f'未知验证类型：【{key}】')

        return not bool(sucess_flag)
