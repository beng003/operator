import sys
import os
from pathlib import Path
root_path = str(Path(__file__).resolve().parent.parent)
sys.path.append(root_path)

from utils.yaml_util import convert_yaml_to_json_str

def batch_convert_yaml_to_json():
    # 获取 JobConfig 目录的绝对路径
    job_config_dir = os.path.join(root_path, 'JobConfig')
    
    # 递归遍历 JobConfig 目录下的所有 YAML 文件
    for root, dirs, files in os.walk(job_config_dir):
        for file in files:
            if file.endswith('.yaml'):
                # 构建输入文件路径
                input_file = os.path.join(root, file)
                
                # 构建输出文件路径（保持相同目录结构）
                # 将 .yaml 扩展名改为 .json
                output_file = os.path.join(root, file.replace('.yaml', '.json'))
                
                try:
                    # 调用转换函数
                    convert_yaml_to_json_str(input_file, output_file)
                    print(f'YAML 文件 {input_file} 已转换为 JSON 字符串并保存到 {output_file}')
                except Exception as e:
                    print(f'转换文件 {input_file} 时出错: {e}')

if __name__ == '__main__':
    # 批量转换所有 YAML 文件
    batch_convert_yaml_to_json()