## 初始化sf集群，pyu和spu
import secretflow as sf

from secretflow.data.vertical import read_csv as v_read_csv

from secretflow.data.horizontal import read_csv as h_read_csv
from secretflow.security.aggregation import SecureAggregator
from secretflow.security import SecureAggregator
from secretflow.security.compare import SPUComparator

from secretflow.data.split import train_test_split
from utils.sf_init import SecretFlowConfigurator


def split(sf_cluster_desc, sf_node_eval_param):
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu

        data_type = sf_node_eval_param.pop("data_type", "vdf")
        input_path = sf_config.replace_keys(sf_node_eval_param.pop("input_path"))
        train_output_path = sf_config.replace_keys(
            sf_node_eval_param.pop("train_output_path")
        )
        test_output_path = sf_config.replace_keys(
            sf_node_eval_param.pop("test_output_path")
        )
        keys = sf_config.replace_keys(sf_node_eval_param.pop("keys", None))

        import time
        # time.sleep(100)
        time.sleep(20)

        if data_type == "vdf":
            sf_node_eval_param.pop("SecureAggregatorDevice", None)
            sf_node_eval_param.pop("participants", None)

            vdf = v_read_csv(filepath=input_path, keys=keys)
            train_vdf, test_vdf = train_test_split(vdf, **sf_node_eval_param)

            sf.wait(train_vdf.to_csv(train_output_path, index=False))
            sf.wait(test_vdf.to_csv(test_output_path, index=False))

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
            sf.wait(train_hdf.to_csv(train_output_path))
            sf.wait(test_hdf.to_csv(test_output_path))
