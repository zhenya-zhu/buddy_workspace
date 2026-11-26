#!/usr/bin/python3
"""设备端服务注册代理：在固定端口上报本机正在运行的 Web 服务。

每台开发机各跑一份，导航页的 Mac 只需探测这一台机器的 9700 端口。
仅使用 Python 标准库；本机监听端口自动检测，services.json 可选用于改名/分类。
"""

import html
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG_FILE = BASE / "services.json"
PORT = int(os.environ.get("AGENT_PORT", "9700"))
TITLE_RE = re.compile(rb"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
CACHE_SECONDS = 3
_cache = {"time": 0.0, "services": []}


def lan_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


def _lan_bind(address, ip):
    """只上报局域网能连到的端口，排除 127.0.0.1 / ::1 这类本机监听。"""
    address = address.strip()
    return address in ("*", "0.0.0.0", "[::]", ip) or address.startswith(ip + ":")


def listening_ports(ip):
    ports = set()
    if sys.platform == "darwin":
        output = subprocess.check_output(
            ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
            text=True, stderr=subprocess.DEVNULL, timeout=4,
        )
        for match in re.finditer(r"TCP\s+(\S+):(\d+)\s+\(LISTEN\)", output):
            if _lan_bind(match.group(1), ip):
                ports.add(int(match.group(2)))
    elif sys.platform.startswith("win"):
        output = subprocess.check_output(
            ["netstat", "-ano", "-p", "TCP"],
            text=True, stderr=subprocess.DEVNULL, timeout=5,
        )
        for line in output.splitlines():
            match = re.search(r"^\s*TCP\s+(\S+):(\d+)\s+\S+\s+LISTENING", line, re.IGNORECASE)
            if match and _lan_bind(match.group(1), ip):
                ports.add(int(match.group(2)))
    else:
        try:
            output = subprocess.check_output(
                ["ss", "-ltn"], text=True, stderr=subprocess.DEVNULL, timeout=4,
            )
            for line in output.splitlines()[1:]:
                parts = line.split()
                if len(parts) > 3 and ":" in parts[3]:
                    address, port = parts[3].rsplit(":", 1)
                    if _lan_bind(address, ip):
                        ports.add(int(port))
        except Exception:
            pass
    return ports


def probe(port):
    """探测本机端口是否说 HTTP，并抓取页面标题。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.4)
    try:
        if sock.connect_ex(("127.0.0.1", port)) != 0:
            return None
    except Exception:
        sock.close()
        return None

    try:
        sock.settimeout(1.0)
        request = (
            "GET / HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n"
            "User-Agent: LAN-Nav-Agent/1.0\r\nAccept: text/html,*/*\r\n"
            "Connection: close\r\n\r\n" % port
        ).encode("ascii")
        sock.sendall(request)
        chunks, total = [], 0
        while total < 65536:
            chunk = sock.recv(8192)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
    except Exception:
        sock.close()
        return None
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        sock.close()

    raw = b"".join(chunks)
    head, _, body = raw.partition(b"\r\n\r\n")
    first_line = head.split(b"\r\n", 1)[0].decode("latin-1", "ignore")
    if "HTTP/" not in first_line:
        return None
    if " 403 " in first_line and not TITLE_RE.search(body):
        return None  # macOS AirPlay 之类的系统服务

    title = ""
    match = TITLE_RE.search(body)
    if match:
        for encoding in ("utf-8", "gbk", "latin-1"):
            try:
                title = match.group(1).decode(encoding)
                break
            except Exception:
                continue
        title = html.unescape(re.sub(r"\s+", " ", title)).strip()[:80]
    return title, first_line.strip()


def load_config():
    try:
        with open(str(CONFIG_FILE), encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def collect_services():
    now = time.time()
    if now - _cache["time"] < CACHE_SECONDS:
        return _cache["services"]

    ip = lan_ip()
    config = load_config()
    overrides, ignored, extras = {}, {PORT}, []
    for item in config:
        if not isinstance(item, dict):
            continue
        if item.get("port"):
            port = int(item["port"])
            if item.get("enabled") is False:
                ignored.add(port)
            else:
                overrides[port] = item
        elif item.get("url") and item.get("enabled") is not False:
            extras.append(item)

    services, seen = [], set()
    for port in sorted(listening_ports(ip)):
        if port in ignored or port in seen:
            continue
        # 5 万段通常是编辑器/工具的内部服务，不是开发项目；需要时可用环境变量放开。
        if 50000 <= port <= 59999 and os.environ.get("AGENT_ALLOW_HIGH_PORTS") != "1":
            continue
        result = probe(port)
        if not result:
            continue
        title, status = result
        override = overrides.get(port, {})
        url = override.get("url") or ("http://%s:%d" % (ip, port))
        services.append({
            "name": override.get("name") or title or "%s:%d" % (ip, port),
            "url": url,
            "desc": override.get("desc") or (("%s:%d" % (ip, port)) if title else status),
            "tag": override.get("tag") or "",
            "port": port,
            "title": title,
        })
        seen.add(port)

    for item in extras:
        services.append({
            "name": item.get("name") or item["url"],
            "url": item["url"],
            "desc": item.get("desc") or "",
            "tag": item.get("tag") or "",
            "port": item.get("port"),
            "title": "",
        })

    _cache["time"] = now
    _cache["services"] = services
    return services


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path not in ("/", "/services"):
            self.send_error(404, "Not Found")
            return
        payload = {
            "device": socket.gethostname(),
            "ip": lan_ip(),
            "registryPort": PORT,
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
            "services": collect_services(),
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("服务注册代理已启动：http://%s:%d/services" % (lan_ip(), PORT), flush=True)
    print("本机监听端口自动上报；可选配置文件：%s" % CONFIG_FILE, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
