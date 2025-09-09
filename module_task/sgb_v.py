from secretflow.ml.boost.sgb_v import (
    Sgb,
    get_classic_XGB_params,
)
from secretflow.ml.boost.sgb_v.model import load_model
from utils.sf_init import SecretFlowConfigurator
from utils.path_util import modify_path
from secretflow.data.vertical import read_csv as v_read_csv


__all__ = ["sgb_v_train", "sgb_v_predict"]

def sgb_v_train(sf_cluster_desc, sf_node_eval_param, **kwargs):
    # 导入wait函数到函数内部，避免在进程池初始化时被序列化
    from secretflow.device.driver import wait
    
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        heu = sf_config.heu

        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        psi_keys = sf_config.replace_keys(sf_node_eval_param.pop("keys", None))
        psi_protocl = sf_config.replace_keys(
            sf_node_eval_param.pop("psi_protocl", None)
        )
        saving_path_dict = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("saving_path_dict", None))
        )

        if not (psi_input_path and psi_keys and psi_protocl and saving_path_dict):
            # 抛出错误
            raise ValueError("psi_input_path, psi_keys, psi_protocl must be set")

        vdf = v_read_csv(
            filepath=psi_input_path,
            spu=spu,
            keys=psi_keys,
            drop_keys=psi_keys,
            psi_protocl=psi_protocl,
        )

        train_x = vdf.drop(columns=["y"])
        train_y = vdf["y"]

        sgb_params = sf_config.replace_keys(sf_node_eval_param.pop("xgb_param", None))

        if not sgb_params:
            sgb_params = get_classic_XGB_params()
            sgb_params["num_boost_round"] = 3
            sgb_params["max_depth"] = 3

        sgb = Sgb(heu)
        model = sgb.train(params=sgb_params, dtrain=train_x, label=train_y)

        r = model.save_model(saving_path_dict)
        wait(r)

def sgb_v_predict(sf_cluster_desc, sf_node_eval_param, **kwargs):
    # 导入wait函数到函数内部，避免在进程池初始化时被序列化
    from secretflow.device.driver import wait
    
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        # spu = sf_config.spu

        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        psi_keys = sf_config.replace_keys(sf_node_eval_param.pop("keys", None))
        psi_protocl = sf_config.replace_keys(
            sf_node_eval_param.pop("psi_protocl", None)
        )
        saving_path_dict = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("saving_path_dict", None))
        )
        output_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("output_path", None))
        )
        
        label_holder = sf_config.replace_keys(
            sf_node_eval_param.pop("label_holder", None)
        )

        if not (psi_input_path and psi_keys and psi_protocl and saving_path_dict):
            # 抛出错误
            raise ValueError("psi_input_path, psi_keys, psi_protocl must be set")

        psi_keys_re = {}
        for party_str, keys in psi_keys.items():
            if party_str != str(label_holder):
                psi_keys_re[party_str] = keys
        
        
        vdf = v_read_csv(
            filepath=psi_input_path,
            # spu=spu,
            keys=psi_keys,
            # drop_keys=psi_keys_re,
            psi_protocl=psi_protocl,
        )

        # vdf = vdf.drop(columns=["y"])
        
        label_holder = sf_config.parties_pyu[label_holder]
        model_loaded = load_model(saving_path_dict, label_holder)
        fed_yhat_loaded = model_loaded.predict(vdf, label_holder)
        
        def save_data(data, index_data, index_name, path):
            import pandas as pd
            
            df_data = pd.DataFrame(data)
            # df_index = pd.DataFrame(index_data)
            df = pd.concat([index_data, df_data], axis=1)
            
            df.set_index(index_name, inplace=True)
            df.columns = ["predict"]
            
            df.to_csv(path, index=True)
        
        predict_partitions = fed_yhat_loaded.partitions  # 获取所有分区
        vdf_index_data = vdf[psi_keys[label_holder]].partitions
        
        path = output_path[label_holder]
        index_data = vdf_index_data[label_holder].data
        index_name = psi_keys[label_holder]
        
        predict_data = predict_partitions[label_holder]
        wait(label_holder(save_data)(predict_data, index_data, index_name, path))
