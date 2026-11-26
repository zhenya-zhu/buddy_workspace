#!/bin/bash
# 在本机启动服务注册代理（端口 9700）。
cd "$(dirname "$0")" || exit 1

if [ -x /usr/bin/python3 ]; then
  PYTHON=/usr/bin/python3
else
  PYTHON=$(command -v python3)
fi

echo "启动服务注册代理，端口 9700。停止服务按 Control + C。"
exec "$PYTHON" agent.py
