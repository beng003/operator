import sys
from pathlib import Path
root_path = str(Path(__file__).resolve().parent.parent)
sys.path.append(root_path)

from utils.yaml_util import read_yaml, write_yaml


def init_config():
    
    JobConfig = str(Path(__file__).resolve().parent)
    # InitConfig = str(Path(__file__).resolve() / "InitConfig")
    alice_data = str(Path(__file__).resolve().parent.parent / "local_data" / "alice")
    bob_data = str(Path(__file__).resolve().parent.parent / "local_data" / "bob" )
    
    # 1.psi
    # 读取配置文件
    config = read_yaml(f"{JobConfig}/output_psi_input_data.yaml")
    # 初始化配置
    config["param"]["sf_node_eval_param"]["input_path"]["alice"] = f"{alice_data}/alice.csv"
    config["param"]["sf_node_eval_param"]["input_path"]["bob"] = f"{bob_data}/bob.csv"
    config["param"]["sf_node_eval_param"]["output_path"]["alice"] = f"{alice_data}/psi-output.csv"
    config["param"]["sf_node_eval_param"]["output_path"]["bob"] = f"{bob_data}/psi-output.csv"
    # 写入配置文件
    write_yaml(f"{JobConfig}/output_psi_input_data.yaml", config)
    
    # 2.split
    # 读取配置文件
    config = read_yaml(f"{JobConfig}/output_split_input_data.yaml")
    
    config["param"]["sf_node_eval_param"]["input_path"]["alice"] = f"{alice_data}/psi-output02.csv"
    config["param"]["sf_node_eval_param"]["input_path"]["bob"] = f"{bob_data}/psi-output02.csv"
    config["param"]["sf_node_eval_param"]["train_output_path"]["alice"] = f"{alice_data}/train-dataset.csv"
    config["param"]["sf_node_eval_param"]["train_output_path"]["bob"] = f"{bob_data}/train-dataset.csv"
    config["param"]["sf_node_eval_param"]["test_output_path"]["alice"] = f"{alice_data}/test-dataset.csv"
    config["param"]["sf_node_eval_param"]["test_output_path"]["bob"] = f"{bob_data}/test-dataset.csv"
    
    # 写入配置文件
    write_yaml(f"{JobConfig}/output_split_input_data.yaml", config)


if __name__ == "__main__":
    init_config()