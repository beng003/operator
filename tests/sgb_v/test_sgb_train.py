#!/usr/bin/env python3
import yaml
import json
import os
import sys


# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（假设tests目录在项目根目录下）
project_root = os.path.dirname(os.path.dirname(current_dir))
# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

# 构建YAML文件的绝对路径
yaml_file_path = os.path.join(project_root, 'JobConfig', 'sgb_v', 'local','sgb_v_train.yaml')

# 读取YAML文件
with open(yaml_file_path, 'r') as file:
    yaml_data = yaml.safe_load(file)

yaml_data["job_uid"] = "qq"
from module_task.sgb_v import sgb_v_train

sgb_v_train(**yaml_data)
