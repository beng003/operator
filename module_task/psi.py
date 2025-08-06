## 初始化sf集群，pyu和spu
import secretflow as sf
from utils.yaml_util import read_yaml
from utils.sf_init import SecretFlowConfigurator
from utils.path_util import modify_path
from module_task.decorator_task import capture_errors_to_queue

__all__ = ["psi_csv"]

@capture_errors_to_queue
def psi_csv(job_uid, sf_cluster_desc, sf_node_eval_param, **kwargs):
    
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        sf_node_eval_param["input_path"] = modify_path(sf_node_eval_param["input_path"])
        sf_node_eval_param["output_path"] = modify_path(sf_node_eval_param["output_path"])
        
        psi_csv_param = sf_config.replace_keys(sf_node_eval_param)

        # import time
        # time.sleep(200)
        sf.wait(spu.psi_csv(**psi_csv_param))
        # time.sleep(100)