from itertools import count
from utils.sf_init import SecretFlowConfigurator
from utils.path_util import modify_path
from secretflow.data.vertical import read_csv as v_read_csv
import pandas as pd
import secretflow as sf
from secretflow.device import PYU
from typing import Callable, Dict, List, Union
from secretflow.device.driver import wait


def save_plaintext(
    data: pd.DataFrame, out_path: Dict[PYU, str], index, index_label: str = None
):
    for party, path in out_path.items():
        wait(party(data.to_csv)(path, index=index, index_label=index_label))


def table_statistics_data(sf_cluster_desc, sf_node_eval_param, **kwargs):
    from secretflow.stats.table_statistics import table_statistics

    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)

        table_statistics_out: Dict[PYU, str] = modify_path(
            sf_node_eval_param.pop("table_statistics_out", None)
        )
        data_stats = table_statistics(vdf)
        save_plaintext(data_stats, table_statistics_out, index=True, index_label="feature_name")


def pearson_r(sf_cluster_desc, sf_node_eval_param, **kwargs):
    from secretflow.stats.ss_pearsonr_v import PearsonR

    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)

        x_col: List = sf_node_eval_param.pop("x_col", None)
        pearson_r_out: Dict[PYU, str] = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("pearson_r_out", None))
        )

        pearson_r_calculator = PearsonR(spu)
        corr_matrix = pearson_r_calculator.pearsonr(vdf[x_col])
        corr_matrix_df = pd.DataFrame(corr_matrix, index=x_col, columns=x_col)
        save_plaintext(corr_matrix_df, pearson_r_out, index=True)


def ss_vif_v_data(sf_cluster_desc, sf_node_eval_param, **kwargs):
    from secretflow.stats.ss_vif_v import VIF

    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)

        x_col: List = sf_node_eval_param.pop("x_col", None)
        vif_out: Dict[PYU, str] = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("vif_out", None))
        )

        vif_calculator = VIF(spu)
        vdf_hat = vdf[x_col]
        vif_results = vif_calculator.vif(vdf_hat)
        vif_df = pd.DataFrame(vif_results, index=x_col, columns=["vif"])
        save_plaintext(vif_df, vif_out, index=True, index_label="feature_name")

# todo: psi_eval_score 未完成
# https://www.secretflow.org.cn/zh-CN/docs/secretflow/v1.12.0b0/tutorial/risk_control_scenario#woe%E5%88%86%E7%AE%B1
def psi_eval_score(sf_cluster_desc, sf_node_eval_param, **kwargs):
    from secretflow.stats import psi_eval
    from secretflow.stats.core.utils import equal_range
    import jax.numpy as jnp
    
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)
        
        x_col = sf_node_eval_param.pop("x_col", None)
        
        
        min_val, max_val = vdf[x_col].min(), vdf[x_col].max()
        
        split_points = equal_range(jnp.array([min_val, max_val]), 3)
        # balance_psi_score = psi_eval(train_x['balance'], test_x['balance'], split_points)