#!/bin/bash
# 在本机启动导航页（默认端口 6996）。停止按 Control + C。
cd "$(dirname "$0")" || exit 1

if [ -n "$DEVICE_NAV_PYTHON" ]; then
  PYTHON="$DEVICE_NAV_PYTHON"
elif [ -x /usr/bin/python3 ]; then
  PYTHON=/usr/bin/python3
else
  PYTHON=$(command -v python3)
fi

exec "$PYTHON" server.py
