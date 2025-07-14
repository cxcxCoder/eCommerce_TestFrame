import os
from utils.recordlogs import logs

def clear_files_only(dir_path):
    """
    清空目录下所有文件，保留文件夹不动，递归处理所有子目录。
    :param dir_path: 目标目录路径
    """
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            os.remove(file_path)
