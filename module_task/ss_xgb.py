import secretflow as sf
from secretflow.ml.boost import SSXGB
from secretflow.data import partition
from secretflow.security.aggregation import SecureAggregator
from utils.yaml_util import read_yaml
from utils.sf_init import SecretFlowConfigurator
import pandas as pd
import numpy as np
import os
import logging

__all__ = ["ss_xgb_train", "ss_xgb_predict"]

def ss_xgb_train(sf_cluster_desc, sf_node_eval_param, **kwargs):
    """
    两方SS-XGB模型训练函数
    
    Args:
        sf_cluster_desc: SecretFlow集群配置
        sf_node_eval_param: 节点评估参数
        **kwargs: 其他参数
    
    Returns:
        训练好的模型
    """
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        
        alice = sf_config.alice
        bob = sf_config.bob
        
        # 替换参数中的键
        ss_xgb_param = sf_config.replace_keys(sf_node_eval_param)
        
        alice_data_path = ss_xgb_param.get('alice_data_path', '')
        bob_data_path = ss_xgb_param.get('bob_data_path', '')
        
        if not os.path.exists(alice_data_path) or not os.path.exists(bob_data_path):
            raise FileNotFoundError(f"数据文件不存在: {alice_data_path} 或 {bob_data_path}")
        
        alice_data = pd.read_csv(alice_data_path)
        bob_data = pd.read_csv(bob_data_path)
        
        # 数据分区
        alice_data = partition(alice_data, alice)
        bob_data = partition(bob_data, bob)
        
        label_col = ss_xgb_param.get('label_col', '')
        
        # 创建SS-XGB模型
        ss_xgb = SSXGB(
            spu=spu,
            label_col=label_col,
            num_boost_round=ss_xgb_param.get('num_boost_round', 10),
            max_depth=ss_xgb_param.get('max_depth', 3),
            learning_rate=ss_xgb_param.get('learning_rate', 0.1),
            subsample=ss_xgb_param.get('subsample', 0.8),
            colsample_bytree=ss_xgb_param.get('colsample_bytree', 0.8),
            reg_alpha=ss_xgb_param.get('reg_alpha', 0.1),
            reg_lambda=ss_xgb_param.get('reg_lambda', 1.0),
            random_state=ss_xgb_param.get('random_state', 42),
            aggregator=SecureAggregator(spu)
        )
        
        logging.info("开始训练SS-XGB模型...")
        model = ss_xgb.fit(
            train_data=[alice_data, bob_data],
            eval_data=None
        )
        logging.info("SS-XGB模型训练完成")
        
        model_path = ss_xgb_param.get('model_path', '')
        if model_path:
            model.save_model(model_path)
            logging.info(f"模型已保存到: {model_path}")
        
        return model

def ss_xgb_predict(sf_cluster_desc, sf_node_eval_param, **kwargs):
    """
    两方SS-XGB模型预测函数
    
    Args:
        sf_cluster_desc: SecretFlow集群配置
        sf_node_eval_param: 节点评估参数
        **kwargs: 其他参数
    
    Returns:
        预测结果
    """
    with SecretFlowConfigurator(**sf_cluster_desc) as sf_config:
        spu = sf_config.spu
        alice = sf_config.alice
        bob = sf_config.bob
        
        # 替换参数中的键
        ss_xgb_param = sf_config.replace_keys(sf_node_eval_param)
        
        alice_data_path = ss_xgb_param.get('alice_data_path', '')
        bob_data_path = ss_xgb_param.get('bob_data_path', '')
        
        if not os.path.exists(alice_data_path) or not os.path.exists(bob_data_path):
            raise FileNotFoundError(f"数据文件不存在: {alice_data_path} 或 {bob_data_path}")
        alice_data = pd.read_csv(alice_data_path)
        bob_data = pd.read_csv(bob_data_path)
        
        # 数据分区
        alice_data = partition(alice_data, alice)
        bob_data = partition(bob_data, bob)
        
        model_path = ss_xgb_param.get('model_path', '')
        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        # 创建SS-XGB模型实例
        ss_xgb = SSXGB(
            spu=spu,
            label_col=ss_xgb_param.get('label_col', ''),
            aggregator=SecureAggregator(spu)
        )
        
        model = ss_xgb.load_model(model_path)
        
        logging.info("开始SS-XGB模型预测...")
        predictions = model.predict([alice_data, bob_data])
        logging.info("SS-XGB模型预测完成")
        
        output_path = ss_xgb_param.get('output_path', '')
        if output_path:
            pred_df = pd.DataFrame({'predictions': predictions})
            pred_df.to_csv(output_path, index=False)
            logging.info(f"预测结果已保存到: {output_path}")
        
        return predictions 