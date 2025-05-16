"""
在 SecretFlow 中，sf.shutdown() 会关闭当前进程内的所有 SecretFlow 集群和相关资源。具体行为如下：

## 单进程作用域：

sf.shutdown() 仅作用于当前 Python 进程，会释放该进程内所有 SecretFlow 资源（包括所有 SPU/HEU 设备、通信链接等）。

如果初始化了多个 SPU/HEU 设备，无论它们是否属于不同集群，均会被一次性关闭。

## 多进程场景：

若在不同进程中分别初始化了 SecretFlow 集群，每个进程需要独立调用 sf.shutdown() 关闭自身资源。


sf_cluster_desc:
  devices:
    spu_config:
      cluster_def:
        nodes:
        - address: 127.0.0.1:11666
          listen_address: 0.0.0.0:11666
          party: alice
        - address: 127.0.0.1:11667
          listen_address: 0.0.0.0:11667
          party: bob
        runtime_config:
          field: 3
          protocol: 2
      link_desc:
        brpc_channel_connection_type: pooled
        brpc_channel_protocol: http
        connect_retry_interval_ms: 1000
        connect_retry_times: 60
        http_timeout_ms: 1200000
        recv_timeout_ms: 1200000
  sf_init:
    parties:
    - alice
    - bob
    address: local
"""

import secretflow as sf
from secretflow.device import SPU, HEU
from secretflow.security.aggregation import SecureAggregator
from secretflow.security.compare import PlainComparator


class SecretFlowConfigurator:
    def __init__(self, devices: dict, sf_init: dict):
        """
        SecretFlow 隐私计算设备初始化类
        """
        self.sf_device = devices
        self.sf_init = sf_init
        
        self._init_sf()
        self.spu = self._init_spu()
        self.heu = self._init_heu()
        self.parties_pyu = {it: sf.PYU(it) for it in self.sf_init.get("parties", [])}

    def __enter__(self):
        """进入上下文时返回自身，以便在with块中使用"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时，关闭设备以释放资源"""
        sf.shutdown()

    def _init_sf(self) -> SPU:
        """初始化SPU设备"""
        if not self.sf_init:
            raise ValueError("sf_init not found in sf_cluster_desc")
        sf.init(**self.sf_init)

    def _init_spu(self) -> SPU:
        """初始化SPU设备"""
        spu_config = self.sf_device.get("spu_config", {})
        if not spu_config:
            return None
        return SPU(**spu_config)

    def _init_heu(self) -> HEU:
        """初始化HEU设备"""
        heu_config = self.sf_device.get("heu_config", {})
        if not heu_config:
            return None
        return HEU(**heu_config)

    def get_security_tools(self):
        """获取安全工具"""
        return {
            "aggregator": SecureAggregator(self.heu, self.spu),
            "comparator": PlainComparator(self.spu),
        }
        
    def replace_keys(self, data):
        if isinstance(data, dict):  # 如果是字典，递归处理
            return {self.parties_pyu.get(k, k): self.replace_keys(v) for k, v in data.items()}
        elif isinstance(data, list):  # 如果是列表，递归处理
            return [self.replace_keys(i) for i in data]
        else:
            return data
