import secretflow as sf
from secretflow.ml.boost.ss_xgb_v import Xgb
from utils.sf_init import SecretFlowConfigurator
from utils.path_util import modify_path
from secretflow.data.vertical import read_csv as v_read_csv

__all__ = ["ss_xgb"]

def ss_xgb(sf_cluster_desc, sf_node_eval_param, **kwargs):
    
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        psi_input_path = sf_config.replace_keys(modify_path(sf_node_eval_param.pop("input_path", None)))
        psi_keys = sf_config.replace_keys(modify_path(sf_node_eval_param.pop("key", None)))
        psi_protocl = sf_config.replace_keys(sf_node_eval_param.pop("psi_protocl", None))
        
        if psi_input_path and psi_keys and psi_protocl:
            # 抛出错误
            raise ValueError("psi_input_path, psi_keys, psi_protocl must be set")
        
        vdf = v_read_csv(
            filepath=psi_input_path,
            spu=spu,
            keys=psi_keys,
            drop_keys=psi_keys,
            psi_protocl=psi_protocl,
        )
        
        train_x = vdf.drop(columns=['y'])
        train_y = vdf['y']
        xgb = Xgb(spu)
        
        xgb_params = sf_config.replace_keys(sf_node_eval_param.pop("xgb_param", None))
        
        if not xgb_params:
            xgb_params = {
                'num_boost_round': 3,
                'max_depth': 5,
                'sketch_eps': 0.25,
                'objective': 'logistic',
                'reg_lambda': 0.2,
                'subsample': 1,
                'colsample_by_tree': 1,
                'base_score': 0.5,
            }
            
        # xgb_model = xgb.train(params=xgb_params, dtrain=train_x, label=train_y)
        sf.wait(xgb.train(params=xgb_params, dtrain=train_x, label=train_y))