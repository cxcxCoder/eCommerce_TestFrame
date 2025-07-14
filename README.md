# 数据驱动接口自动化测试框架
## 框架简介
本框架基于pytest+yaml+reuqests+allure实现的数据驱动接口测试框架

## 核心功能
1.yaml数据驱动：通过yaml进行测试数据导出、转化、重加载，动态处理测试
2.前置条件处理：基于钩子函数进行测试前置条件处理，实现前置条件独立执行以保证用例独立性
3.接口请求执行：通过requests库执行接口请求，获取响应内容
4.数据提取：根据yaml测试数据需求进行数据上下文存储、提取，辅助数据驱动和上下文管理
5.断言执行：封装状态码断言、包含断言、相等断言等断言操作
6.数据库操作：提供数据库查询，配合数据库断言执行
7.日志记录：全面详细记录日志，便于测试管理与问题排查
8.allure报告生成：记录测试重点信息，结合allure生成可视化测试报告
9.mock服务器：支持mock服务器模拟接口请求
10.全局配置管理：通过conf.yaml进行快速全局配置，管理难度低
11.测试分批次执行：支持单接口用例、工作流用例的分批次执行，提高测试效率


## 环境准备

## 项目结构
整体结构：
- base 整体性工具，例如用例加载、environment.xml生成、前置条件处理等，以及用例执行的实际主体
- conf 配置文件，包含yaml数据配置和数据的动静态加载
- data 测试使用的yaml测试数据，可以按照批次进行划分
- logs 日志文件，由logs生成进行存储
- mock mock服务器模块，用于模拟接口请求
- reports 由allure记录的测试报告内容，包含临时文件夹和持久测试报告
- testcases 测试用例入口，和用例级conftest，用例入口主要是包含高抽象级别的单用例接口和流程用例入口
- utils 测试用例工具大模块，包含yaml文件用例加载、extract的写入与读取、断言执行、数据库操作、日志初始化与记录、接口请求执行等，由base.requestBase统合使用实现测试逻辑
- conftest.py 全局conftest，主要是通过钩子函数进行用例的主动收集、加载、注入，以及前置条件的处理等
- extract.yaml 上下文存储文件，用于前置条件中间数据存储，同时提供${}进行数据替换
- pytest.ini 用于pytest配置
- run.py 框架运行入口，主要进行用例的批次管理、报告展示

## 具体使用
**配置文件**
运行配置文件置于conf/congig.yaml，主要配置好文件夹、运行参数等信息，可以依照目前格式修改即可，需要新增需要对应加载器和具体使用时导入

**用例设计**
设计测试用例时，遵循下面模板，根据实际情况进行调整，设计完成的用例推荐放在data文件夹进行存储，且需要把单接口与工作流分开存储且需要分批次运行，如果不想分批次可以自行调整generate_test钩子的
逻辑，同时调整run.py即可

单接口用例模板：
单接口用例为一个文件多个用例，各个用例共享一个基础信息
----------------------------------------------------------------------------------------------------------------------------------------------------  
.yaml:
- baseInfo:                                            #用例基本信息，所有用例共用
    api_name: 购物车添加商品接口                        #接口名称
    preconditions: 
      - 'goodsList'                                     #前置条件，可以是按顺序的多个，需要与precon.yaml对应
    url: /coupApply/cms/shoppingJoinCart               #接口地址，注意前面开始带/
    method: POST                                       #请求方法
    headers:                                            #请求头
      Content-Type: application/json;charset=UTF-8

  testCase:                                               #用例集，可以包含多个用例
    - case_name: 正常添加商品                               #用例名称
      json:                                                 #请求参数，可以是json、data、params的一个或多个
        goods_id: ${get_extract_data('goodsList',0)}        #数据提取，${}函数需要对应debugtalk的类函数
        count: 2
        price: '128'
        timeStamp: 2169232689
      validation:                                       #验证结果，可以支持状态码、包含、等、不等、数据库断言，基本格式为左侧展示，具体可看utils.assertions.py
        - status_code: 200
        - equal: { 'error': ''}
        - contains: { 'error_code': '0000' }
        - contains: { 'error_code': '0000' }
        - db: { expected:'200034', sql:'SELECT good_id FROM goods WHERE good_name = "iPhone X"' }


    - case_name: 有效添加-缺少非必须参数timeStamp
      json:
        goods_id: ${get_extract_data('goodsList',0)}
        ...
      validation:
        - status_code: 200
        ...
----------------------------------------------------------------------------------------------------------------------------------------------------        
工作流用例模板：
工作流用例模板为一个文件标识一个用例，主要包含descrip与steps字段，分别标识基础表述和用例步骤。具体steps内步骤与单用例一致
.yaml:
----------------------------------------------------------------------------------------------------------------------------------------------------  
descrip:
  feature_name: 业务流程
  story_name: 提交订单-支付订单
steps:
  - baseInfo:
      api_name: 提交订单接口
      url: /coupApply/cms/placeAnOrder
      method: POST
      headers:
        Content-Type: application/json;charset=UTF-8
    testCase:
      case_name: 正常提交订单
      json:
        goods_id: '18382788819'
        ...
      validation:
        - status_code: 200
        ...
      extract:
        orderNumber: $..orderNumber
        userId: $..userId

  - baseInfo:
      api_name: 订单支付接口
      url: /coupApply/cms/orderPay
      method: POST
      headers:
        Content-Type: application/json;charset=UTF-8
    testCase:
      case_name: 正常支付订单
      json:
        orderNumber: ${get_extract_data('orderNumber')}
      validation:
        - status_code: 200
----------------------------------------------------------------------------------------------------------------------------------------------------        
**前置条件模板**
前置条件文件治愈base/precon.yaml内可以包含多个前置条件，各个条件的字段与测试用例preconditions内对应即可实现前置条件的执行。
.yaml:
----------------------------------------------------------------------------------------------------------------------------------------------------  
login:                                          #前置条件名称，下面内容与前面基本一致
  baseInfo:
    api_name: 用户登录
    max_call: 1
    url: /dar/user/login
    method: post
    headers:
      Content-Type: application/x-www-form-urlencoded;charset=UTF-8
  testCase:
    case_name: 用户名和密码正确登录验证
    data:
      user_name: test01
      passwd: admin123
    extract:
      token: $.token

placeAnOrder:
  ...
---------------------------------------------------------------------------------------------------------------------------------------------------- 
**mock数据模板**
mock数据文件置于mock/mock.yaml中，response和name以外的字段是自定义的用于进行详细匹配的内容，配合mock_server.py的匹配进行定制化处理，例如详细对比请求参数，此外response的返回内容
也可以自行根据实际情况进行动态配置，目前仅提供骨架
.yaml:
- name: 登录                               #接口名称,可随意
  method: post                              #请求方法
  url: /dar/user/login                      #请求地址
  json: 
  data: 
  response:
    status_code: 200
    body:
      error_code: null
      msg: 登录成功
      msg_code: 200
      orgId: "4140913758110176843"
      token: "13Db9f9f2A0Bf0ee583AB3E51a7eF"
      userId: "3501704179608244733"

- name: 提交订单
  ....

**框架运行**
run.py为框架运行的入口，右键运行即可