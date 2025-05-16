import json
import yaml

__all__ = [
    "json_to_yaml",
    "read_yaml",
    "write_yaml",
]


def json_to_yaml(json_file_path, yaml_file_path):
    """
    将 JSON 文件内容转换为 YAML 格式，并保存到指定的 YAML 文件中。

    :param json_file_path: JSON 文件的路径
    :param yaml_file_path: 保存 YAML 文件的路径
    """
    try:
        # 读取 JSON 文件
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)

        # 将 JSON 转换为 YAML
        yaml_data = yaml.dump(
            json_data, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

        # 将 YAML 写入到指定文件
        with open(yaml_file_path, "w", encoding="utf-8") as yaml_file:
            yaml_file.write(yaml_data)

        print(f"YAML 文件已保存到 {yaml_file_path}")

    except Exception as e:
        print(f"Error: {e}")

def read_yaml(target):
    # if isinstance(target, str) or isinstance(target, bytes):
    #     return yaml.load(target, Loader=yaml.FullLoader)
    with open(target, encoding="utf-8") as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)


def write_yaml(target, data):
    """
    将数据写入到指定的 YAML 文件中。

    参数:
    - target: 目标文件路径
    - data: 要写入的数据对象
    """
    with open(target, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)