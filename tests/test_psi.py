#!/usr/bin/env python3
import yaml
import json
import os

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（假设tests目录在项目根目录下）
project_root = os.path.dirname(current_dir)
# 构建YAML文件的绝对路径
yaml_file_path = os.path.join(project_root, 'JobConfig', 'output_psi_input_data.yaml')

# 读取YAML文件
with open(yaml_file_path, 'r') as file:
    yaml_content = yaml.safe_load(file)


yaml_data = yaml_content["param"]

# 转换为JSON字符串
json_string = json.dumps(yaml_data, ensure_ascii=True)

# 输出JSON字符串
print(json_string)


aa = {"ay":json_string}

ac= json.dumps(aa)
print(ac)

# print(json.loads(json_string))
# 如果需要保存到文件
# with open('output.json', 'w') as json_file:
#     json_file.write(json_string)