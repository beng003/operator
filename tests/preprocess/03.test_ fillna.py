import yaml
import os
import sys


# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（假设tests目录在项目根目录下）
project_root = os.path.dirname(os.path.dirname(current_dir))
# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

# 构建YAML文件的绝对路径
yaml_file_path = os.path.join(project_root, 'JobConfig', 'preprocess', 'local','fillna_data.yaml')

with open(yaml_file_path, 'r') as file:
    yaml_data = yaml.safe_load(file)

from module_task.preprocess import fillna_data

fillna_data(**yaml_data)
