#!/usr/bin/env bash

set -euo pipefail

echo "📦 关闭旧容器..."
docker compose -f ../docker/test/docker-compose.yaml down
echo "🐘 启动 PostgreSQL test-db 数据库..."
docker compose -f ../docker/test/docker-compose.yaml up test_mysql_beng003 test_redis_beng003 --build -d

# 回到根目录
cd ..
# 如果没有传参，则直接跑 pytest
if [ $# -eq 0 ]; then
  echo "🧪 运行所有测试 (默认)..."
  pytest
else
  echo "🧪 运行 pytest with args: $*"
  pytest "$@"
fi