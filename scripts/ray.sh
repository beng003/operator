#!/bin/bash

# 用法提示
usage() {
    echo "用法: $0 --ip <IP地址> --port <端口号>"
    echo "示例: $0 --ip 192.168.1.100 --port 6379"
    exit 1
}

# 检查参数
if [ $# -ne 4 ]; then
    usage
fi

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ip)
            IP="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            usage
            ;;
    esac
done

# 检查 IP 和 PORT 是否为空
if [ -z "$IP" ] || [ -z "$PORT" ]; then
    echo "错误: 必须提供 --ip 和 --port 参数！"
    usage
fi

# 执行 ray start 命令
echo "🚀 启动 Ray head 节点: IP=$IP, PORT=$PORT"
ray start --head \
    --node-ip-address="$IP" \
    --port="$PORT" \
    --include-dashboard=False \
    --disable-usage-stats

ray start --address="$IP:$PORT"

# 检查是否成功
if [ $? -eq 0 ]; then
    echo "✅ Ray head 节点启动成功！"
else
    echo "❌ 启动失败！请检查 IP 和端口是否可用。"
    exit 1
fi

ray start --head \
    --node-ip-address="alice_operator" \
    --port="6379" \
    --include-dashboard=False \
    --disable-usage-stats

ray start --address="alice_operator:6379"

ray start --head \
    --node-ip-address="bob_operator" \
    --port="6379" \
    --include-dashboard=False \
    --disable-usage-stats

ray start --address="bob_operator:6379"


ray start --head \
    --node-ip-address="192.168.0.10" \
    --port="6379" \
    --include-dashboard=False \
    --disable-usage-stats

ray start --address="192.168.0.10:6379"

ray start --head \
    --node-ip-address="192.168.0.11" \
    --port="6379" \
    --include-dashboard=False \
    --disable-usage-stats

ray start --address="192.168.0.11:6379"