from itertools import count
from utils.sf_init import SecretFlowConfigurator
from utils.path_util import modify_path
from secretflow.data.vertical import read_csv as v_read_csv
import pandas as pd
import secretflow as sf
from secretflow.device import PYU
from typing import Callable, Dict, List, Union
from secretflow.device.driver import wait


def concat_X_y(X_df, y_df):
    return pd.concat([X_df, y_df], axis=1)


def psi_csv(sf_cluster_desc, sf_node_eval_param, **kwargs):
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        sf_node_eval_param["input_path"] = modify_path(sf_node_eval_param["input_path"])
        sf_node_eval_param["output_path"] = modify_path(
            sf_node_eval_param["output_path"]
        )
        psi_csv_param = sf_config.replace_keys(sf_node_eval_param)
        sf.wait(spu.psi_csv(**psi_csv_param))


def replace_data(sf_cluster_desc, sf_node_eval_param, **kwargs):
    import numpy as np

    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)

        replace_dict = sf_node_eval_param.pop("replace_dict", None)
        replace_out = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("replace_out", None))
        )

        # for _, pyu in sf_config.parties_pyu.items():
        #     print(sf.reveal(vdf.partitions[pyu].data))
        #     # return

        for col, replace_value in replace_dict.items():
            for key, value in replace_value.items():
                if value == "np.NaN":
                    replace_value[key] = np.NaN
            vdf[col] = vdf[col].replace(replace_value)

        wait(vdf.to_csv(replace_out, index=False))


def fillna_data(sf_cluster_desc, sf_node_eval_param, **kwargs):
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)

        fillna_dict = sf_node_eval_param.pop("fillna_dict", None)
        fillna_out = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("fillna_out", None))
        )

        for col, fillna_value in fillna_dict.items():
            if fillna_value == "mode":
                vdf[col] = vdf[col].fillna(vdf[col].mode())
            elif fillna_value == "mean":
                vdf[col] = vdf[col].fillna(vdf[col].mean())
            else:
                vdf[col] = vdf[col].fillna(fillna_value)

        wait(vdf.to_csv(fillna_out, index=False))


def woe_binning(sf_cluster_desc, sf_node_eval_param, **kwargs):
    from secretflow.preprocessing.binning.vert_woe_binning import VertWoeBinning
    from secretflow.preprocessing.binning.vert_bin_substitution import (
        VertBinSubstitution,
    )
    from secretflow.data.vertical.dataframe import VDataFrame
    from secretflow.component.core import (
        CompVDataFrame,
        VTableField,
        VTableFieldKind,
        VTableSchema,
    )
    from secretflow.component.core.dist_data.vtable_utils import VTableUtils

    def _build_schema(df: VDataFrame, labels: set = {"y"}) -> dict[str, VTableSchema]:
        res = {}
        for pyu, p in df.partitions.items():
            fields = []
            for name, dtype in p.dtypes.items():
                dt = VTableUtils.from_dtype(dtype)
                kind = (
                    VTableFieldKind.LABEL if name in labels else VTableFieldKind.FEATURE
                )
                fields.append(VTableField(name, dt, kind))

            res[pyu.party] = VTableSchema(fields)

        return res

    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)

        binning_method = sf_node_eval_param.pop("binning_method", None)
        bin_num = sf_node_eval_param.pop("bin_num", None)
        bin_names = sf_config.replace_keys(sf_node_eval_param.pop("bin_names", None))
        label_name = sf_node_eval_param.pop("label_name", None)
        woe_binning_out = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("woe_binning_out", None))
        )

        woe_binning = VertWoeBinning(spu)
        vdf = CompVDataFrame.from_pandas(vdf, schemas=_build_schema(vdf))
        bin_rules = woe_binning.binning(
            vdf,
            binning_method=binning_method,
            bin_num=bin_num,
            bin_names=bin_names,
            label_name=label_name,
        )
        woe_sub = VertBinSubstitution()
        vdf = woe_sub.substitution(vdf, bin_rules)
        vdf = CompVDataFrame.to_pandas(vdf)
        wait(vdf.to_csv(woe_binning_out, index=False))


def one_hot_encoder(sf_cluster_desc, sf_node_eval_param, **kwargs):
    from secretflow.preprocessing.encoder import OneHotEncoder

    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)

        columns_list: List[str] = sf_node_eval_param.pop("column_list", None)
        one_hot_encoder_out: Dict[PYU, str] = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("one_hot_encoder_out", None))
        )

        encoder = OneHotEncoder()

        for col in columns_list:
            tranformed_df = encoder.fit_transform(vdf[col])
            vdf[tranformed_df.columns] = tranformed_df

        vdf = vdf.drop(columns=columns_list)
        wait(vdf.to_csv(one_hot_encoder_out, index=False))


def standard_scaler(sf_cluster_desc, sf_node_eval_param, **kwargs):
    # 导入wait函数到函数内部，避免在进程池初始化时被序列化
    from secretflow.preprocessing import StandardScaler

    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        psi_input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        vdf = v_read_csv(filepath=psi_input_path)

        yes_x_columns = sf_node_eval_param.pop("yes_x_columns", None)
        no_x_columns = sf_node_eval_param.pop("no_x_columns", None)

        assert (yes_x_columns is None and no_x_columns is not None) or (
            yes_x_columns is not None and no_x_columns is None
        ), "yes_x_columns 和 no_x_columns 有且只能有一个值！"

        standard_scaler_out = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("standard_scaler_out", None))
        )

        scaler = StandardScaler()
        if yes_x_columns:
            X = vdf[yes_x_columns]
            X = scaler.fit_transform(X)
            vdf[yes_x_columns] = X
        elif no_x_columns:
            X = vdf.drop(columns=no_x_columns)
            X = scaler.fit_transform(X)
            vdf[X.columns] = X

        wait(vdf.to_csv(standard_scaler_out, index=False))


def split(sf_cluster_desc, sf_node_eval_param, **kwargs):
    from secretflow.data.horizontal import read_csv as h_read_csv
    from secretflow.security.aggregation import SecureAggregator

    # from secretflow.security import SecureAggregator
    from secretflow.security.compare import SPUComparator
    from secretflow.data.split import train_test_split

    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu

        data_type = sf_node_eval_param.pop("data_type", "vdf")
        input_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("input_path", None))
        )
        train_output_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("train_output_path"))
        )
        test_output_path = sf_config.replace_keys(
            modify_path(sf_node_eval_param.pop("test_output_path"))
        )

        if data_type == "vdf":
            sf_node_eval_param.pop("SecureAggregatorDevice", None)
            sf_node_eval_param.pop("participants", None)

            vdf = v_read_csv(filepath=input_path)
            train_vdf, test_vdf = train_test_split(vdf, **sf_node_eval_param)

            wait(train_vdf.to_csv(train_output_path, index=False))
            wait(test_vdf.to_csv(test_output_path, index=False))
        else:
            aggr = SecureAggregator(
                device=sf_node_eval_param.pop("SecureAggregatorDevice"),
                participants=sf_config.parties_pyu.values(),
            )
            comp = SPUComparator(spu)
            hdf = h_read_csv(
                input_path,
                aggregator=aggr,
                comparator=comp,
            )
            train_hdf, test_hdf = train_test_split(hdf, **sf_node_eval_param)
            wait(train_hdf.to_csv(train_output_path))
            wait(test_hdf.to_csv(test_output_path))
