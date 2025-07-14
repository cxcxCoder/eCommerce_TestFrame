import os
import platform
import xml.etree.ElementTree as ET
import conf.configLoader as configloader
from datetime import datetime

class AllureEnvironment:
    """
    allure环境配置生成类，处理生成environment.xml文件供allure使用
    """
    def __init__(self, output_dir="./"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.env_file = os.path.join(self.output_dir, "environment.xml")

    def collect_info(self):
        #核心内容配置
        info = {
            "excuter": configloader.EXCUTOR,
            "excute_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "OS": f"{platform.system()} {platform.release()} {platform.version()}",
            "Platform": platform.platform(),
            "Python Version": platform.python_version(),
            "Base URL":configloader.API_HOST,
            }
        return info
    
    def indent(self,elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for child in elem:
                self.indent(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


    def generate_environment_xml(self):
        info = self.collect_info()
        root = ET.Element("environment")

        for key, value in info.items():
            param = ET.SubElement(root, "parameter")
            name = ET.SubElement(param, "key")
            name.text = key
            val = ET.SubElement(param, "value")
            val.text = value

        self.indent(root)
        tree = ET.ElementTree(root)
        tree.write(self.env_file, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    env = AllureEnvironment()
    env.generate_environment_xml()
