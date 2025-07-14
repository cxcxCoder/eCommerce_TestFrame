import pytest
import os
import shutil
import conf.configLoader as configLoader
from utils.readyaml import YamlDataProcess
from conf.configLoader import ConfigLoader
from base.remove import clear_files_only
from base.env_xml_generater import AllureEnvironment

if __name__ == '__main__':
    ATD = configLoader.ALLURE_TMP_DIR       #最终合并的临时目录
    ARD = configLoader.ALLURE_REPORT_DIR   #最终合并的永久目录

    clear_files_only(ATD)
    
    #分批次执行
    yaml_processor = YamlDataProcess(r'conf/config.yaml')
    config_processor = ConfigLoader()    
    
    for i in range(1,configLoader.BATCH_LEN+1):
        yaml_processor.write_extract_data({'batch_num': i})

        batch_kind,_ = config_processor.dynamic_load_batch()

        pytest_args = [            
            '-q',           #安静模式
            '--tb=short',   #堆栈输出

            '-s',
            '-v',
            f'--alluredir={ATD}',
            #'--junitxml=./report/results.xml',
            f'testcases/test_entry.py::test_{batch_kind}',

        ]

        if i == 1:pytest_args.append('--clean-alluredir')
        
        pytest.main(pytest_args)


    #生成环境信息文件，移至报告目录下供allure使用
    AllureEnvironment().generate_environment_xml()
    shutil.copy2('environment.xml',ATD)


    merge_cmd = f'allure generate {ATD} -o {ARD} --clean'
    os.system(merge_cmd)

    os.system(f'allure open {ARD}')
    #os.system(f'allure serve ./report/temp')
