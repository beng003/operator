#!/usr/bin/env python3
import os
from typing import Dict

def get_project_root() -> str:
    """获取项目根目录"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)

def get_local_data_path() -> str:
    """获取local_data目录路径"""
    return os.path.join(get_project_root(), 'local_data')

def modify_path(path_dict: Dict[str, str]) -> Dict[str, str]:
    """规范化路径字典
    
    Args:
        path_dict: 包含原始路径的字典，格式为 {类别: 文件名}
    
    Returns:
        包含完整路径的新字典
    """
    return {
        category: os.path.join(get_local_data_path(), category, filename)
        for category, filename in path_dict.items()
    }
    
    
if __name__ == '__main__':
    print(get_project_root())
    print(get_local_data_path())
    print(modify_path({"prompt": "prompt.txt", "output": "output.txt"}))