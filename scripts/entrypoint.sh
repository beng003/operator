ray start --head \
    --node-ip-address="${RAY_NODE_DOMAIN}" \
    --port="6379" \
    --include-dashboard=False \
    --disable-usage-stats

ray start --address="${RAY_NODE_DOMAIN}:6379"

exec python3 app.py