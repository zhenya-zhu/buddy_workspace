#!/bin/bash
# 双击本文件即可在常驻 Mac 上启动局域网导航页。
# 自定义端口：PORT=8001 ./start-mac.command

set -u
PORT="${PORT:-8000}"
cd "$(dirname "$0")" || exit 1

IFACE=$(route -n get default 2>/dev/null | awk '/interface:/ {print $2}')
LAN_IP=$(ipconfig getifaddr "$IFACE" 2>/dev/null || true)
LAN_IP="${LAN_IP:-127.0.0.1}"

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "端口 $PORT 已被占用，请先关闭占用程序，或换一个端口："
  echo "  PORT=8001 ./start-mac.command"
  exit 1
fi

echo "------------------------------------------------------------"
echo "局域网导航已启动（目录：$(pwd)）"
echo "导航页：    http://$LAN_IP:$PORT"
echo "编辑条目：  http://$LAN_IP:$PORT/edit.html"
echo "Windows 上打开编辑页改完保存，导航页 30 秒内自动更新"
echo "外网访问：  开启 Tailscale，经 Mac 子网路由，地址不变"
echo "停止服务：  按 Control + C"
echo "------------------------------------------------------------"

# 优先使用系统 Python：macOS 应用防火墙通常已放行 /usr/bin/python3 的传入连接；
# 第三方 Python（如 Homebrew / 工具内置版本）可能被防火墙拦截，导致手机无法访问。
if [ -x /usr/bin/python3 ]; then
  PYTHON=/usr/bin/python3
else
  PYTHON=$(command -v python3)
fi

( sleep 1; open "http://localhost:$PORT/edit.html" ) &

exec "$PYTHON" server.py "$PORT"
