"""本机 Web 服务探测：只列出这台设备上局域网可访问的 HTTP 服务。

不扫描网段，不访问其他设备；每个设备只负责自己的页面。
仅使用 Python 标准库。
"""

import html
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parent
TITLE_RE = re.compile(rb"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
CACHE_SECONDS = 3
PROBE_WORKERS = 24
_cache = {"time": 0.0, "key": None, "services": []}
_lock = threading.Lock()


def lan_ip():
    """返回本机默认路由使用的内网 IP；取不到时回退到主机名解析。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        pass
    finally:
        sock.close()

    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return "127.0.0.1"


def _lan_bind(address, ip):
    """只保留局域网能连到的监听地址，排除 127.0.0.1 / ::1。"""
    address = address.strip()
    return address in ("*", "0.0.0.0", "[::]", ip) or address.startswith(ip + ":")


def listening_ports(ip):
    """列出本机正在监听、且绑定在局域网地址上的 TCP 端口。"""
    ports = set()
    try:
        if sys.platform == "darwin":
            output = subprocess.check_output(
                ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                text=True, errors="replace", stderr=subprocess.DEVNULL, timeout=4,
            )
            for match in re.finditer(r"TCP\s+(\S+):(\d+)\s+\(LISTEN\)", output):
                if _lan_bind(match.group(1), ip):
                    ports.add(int(match.group(2)))
        elif sys.platform.startswith("win"):
            output = subprocess.check_output(
                ["netstat", "-ano", "-p", "TCP"],
                text=True, errors="replace", stderr=subprocess.DEVNULL, timeout=5,
            )
            for line in output.splitlines():
                match = re.search(r"^\s*TCP\s+(\S+):(\d+)\s+\S+\s+LISTENING", line, re.IGNORECASE)
                if match and _lan_bind(match.group(1), ip):
                    ports.add(int(match.group(2)))
        else:
            output = subprocess.check_output(
                ["ss", "-ltn"], text=True, errors="replace", stderr=subprocess.DEVNULL, timeout=4,
            )
            for line in output.splitlines()[1:]:
                parts = line.split()
                if len(parts) > 3 and ":" in parts[3]:
                    address, port = parts[3].rsplit(":", 1)
                    if _lan_bind(address, ip):
                        ports.add(int(port))
    except Exception:
        return ports
    return ports


def probe(port):
    """确认端口说 HTTP，并抓取 <title> 作为默认名称。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.25)
    try:
        if sock.connect_ex(("127.0.0.1", port)) != 0:
            return None
    except Exception:
        sock.close()
        return None

    try:
        sock.settimeout(0.8)
        request = (
            "GET / HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n"
            "User-Agent: Device-Nav/1.0\r\nAccept: text/html,*/*\r\n"
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
        return None  # 系统服务（如 macOS AirPlay）通常 403 且无标题

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

    try:
        code = int(first_line.split()[1])
    except (IndexError, ValueError):
        code = 0
    return title, first_line.strip(), code


def load_config(path):
    try:
        with open(str(path), encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def collect_services(config_path=None, exclude_ports=(), allow_high_ports=False, force=False):
    """返回本机服务清单；结果缓存 3 秒，配置变更会立即失效。

    config_path 可选，默认同目录 services.json。数组每项可按端口覆盖名称/备注/标签，
    或带 url 追加一条固定入口；enabled=false 表示屏蔽。
    """
    config_path = Path(config_path) if config_path else BASE / "services.json"
    exclude = tuple(sorted(set(int(port) for port in exclude_ports)))
    try:
        mtime = config_path.stat().st_mtime
    except Exception:
        mtime = 0
    key = (str(config_path), mtime, exclude, bool(allow_high_ports))

    with _lock:
        now = time.time()
        if not force and _cache["key"] == key and now - _cache["time"] < CACHE_SECONDS:
            return list(_cache["services"])

        ip = lan_ip()
        overrides, ignored, extras = {}, set(exclude), []
        for item in load_config(config_path):
            if not isinstance(item, dict):
                continue
            if item.get("port"):
                try:
                    port = int(item["port"])
                except (TypeError, ValueError):
                    continue
                if item.get("enabled") is False:
                    ignored.add(port)
                else:
                    overrides[port] = item
            elif item.get("url") and item.get("enabled") is not False:
                extras.append(item)

        candidates = []
        for port in sorted(listening_ports(ip)):
            if port in ignored:
                continue
            # 5 万段通常是编辑器/工具的内部服务，不是开发项目。
            if 50000 <= port <= 59999 and not allow_high_ports:
                continue
            candidates.append(port)

        # 并发探测：本机可能有几十个监听端口，串行超时会让页面首屏很慢。
        with ThreadPoolExecutor(max_workers=PROBE_WORKERS) as pool:
            probed = list(pool.map(lambda port: (port, probe(port)), candidates))

        services, seen_urls = [], set()
        for port, result in probed:
            if not result:
                continue
            title, status, code = result
            override = overrides.get(port, {})
            url = override.get("url") or ("http://%s:%d" % (ip, port))
            url_key = url.lower().rstrip("/")
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
            # 4xx/5xx 或没有 <title>，基本是协议错误页 / 报错页，算「打不开」。
            ok = bool(title) and code < 400
            services.append({
                "name": override.get("name") or title or ("%s:%d" % (ip, port)),
                "url": url,
                "desc": override.get("desc") or (("%s:%d" % (ip, port)) if title else status),
                "tag": override.get("tag") or "本机",
                "port": port,
                "title": title,
                "status": code,
                "ok": ok,
            })

        for item in extras:
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            url_key = url.lower().rstrip("/")
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
            services.append({
                "name": item.get("name") or url,
                "url": url,
                "desc": item.get("desc") or "",
                "tag": item.get("tag") or "手工",
                "port": item.get("port"),
                "title": "",
                "status": 0,
                "ok": True,
            })

        # 可用的排前面，打不开的（无标题 / 5xx）排到本组最后。
        services.sort(key=lambda item: (
            not item.get("ok", True),
            item.get("port") is None,
            item.get("port") or 0,
        ))
        _cache.update({"time": now, "key": key, "services": services})
        return list(services)
