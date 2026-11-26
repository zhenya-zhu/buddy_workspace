#!/usr/bin/python3
"""局域网导航页服务：静态文件 + 保存条目的 API + 自动发现。

仅使用 Python 标准库。手工条目存 sites.json，扫描结果存 discovered.json。
如需给编辑页加密码：NAV_EDIT_TOKEN=your-token ./server.py
"""

import json
import os
import socket
import sys
import tempfile
import threading
import time
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from discover import scan_lan

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "sites.json"
DISCOVERED_FILE = BASE / "discovered.json"
TOKEN = os.environ.get("NAV_EDIT_TOKEN", "")
ALLOWED_GROUPS = {"basics", "production", "testing", "lab"}
SCAN_INTERVAL = 120


def read_json(path, fallback):
    try:
        with open(str(path), encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return fallback


def write_json(path, data):
    fd, tmp_path = tempfile.mkstemp(prefix=".nav-", suffix=".json", dir=str(BASE))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, str(path))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def normalize_url(url):
    """把 http://host:80/ 和 http://host 视为同一地址，便于去重。"""
    try:
        parts = urlsplit(str(url).strip())
        port = parts.port
        if parts.scheme == "http" and port == 80:
            port = None
        if parts.scheme == "https" and port == 443:
            port = None
        host = (parts.hostname or "").lower()
        netloc = host + ((":" + str(port)) if port else "")
        return urlunsplit((parts.scheme.lower(), netloc, parts.path.rstrip("/"), "", ""))
    except Exception:
        return str(url).strip().lower().rstrip("/")


def prune_discovered():
    """手工条目新增后，把它从自动发现列表里去掉。"""
    data = read_json(DISCOVERED_FILE, {})
    if not isinstance(data, dict) or not isinstance(data.get("services"), list):
        return
    manual = {normalize_url(item.get("url", "")) for item in read_json(DATA_FILE, [])
              if isinstance(item, dict)}
    kept = [item for item in data["services"]
            if normalize_url(item.get("url", "")) not in manual]
    if len(kept) != len(data["services"]):
        data["services"] = kept
        write_json(DISCOVERED_FILE, data)


def refresh_discovery():
    previous = read_json(DISCOVERED_FILE, {})
    if isinstance(previous, dict):
        pending = dict(previous)
        pending["scanning"] = True
        write_json(DISCOVERED_FILE, pending)

    result = scan_lan()
    manual = {normalize_url(item.get("url", "")) for item in read_json(DATA_FILE, [])
              if isinstance(item, dict)}
    result["services"] = [item for item in result["services"]
                          if normalize_url(item["url"]) not in manual]
    result["scanning"] = False
    write_json(DISCOVERED_FILE, result)
    return result


def discovery_loop():
    while True:
        try:
            refresh_discovery()
        except Exception:
            traceback.print_exc()
        time.sleep(SCAN_INTERVAL)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE), **kwargs)

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self):
        return not TOKEN or self.headers.get("X-Token", "") == TOKEN

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/config":
            self._json(200, {"auth": bool(TOKEN)})
            return
        super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/scan":
            if not self._authorized():
                self._json(401, {"ok": False, "error": "编辑口令不正确"})
                return
            try:
                result = refresh_discovery()
                self._json(200, {"ok": True, "scannedAt": result["scannedAt"],
                                 "count": len(result["services"])})
            except Exception as exc:
                self._json(500, {"ok": False, "error": str(exc)})
            return
        if path != "/api/sites":
            self.send_error(404, "Not Found")
            return
        if not self._authorized():
            self._json(401, {"ok": False, "error": "编辑口令不正确"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"ok": False, "error": "Content-Length 无效"})
            return
        if length <= 0 or length > 1024 * 1024:
            self._json(400, {"ok": False, "error": "数据为空或超过 1 MB"})
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, list):
                raise ValueError("数据必须是数组")
            cleaned = []
            for item in payload:
                if not isinstance(item, dict):
                    raise ValueError("每条记录必须是对象")
                group = str(item.get("group", "")).strip()
                name = str(item.get("name", "")).strip()
                url = str(item.get("url", "")).strip()
                if group not in ALLOWED_GROUPS:
                    raise ValueError("未知分组：" + group)
                if not name or not url:
                    raise ValueError("名称和地址不能为空")
                if not url.startswith(("http://", "https://")):
                    raise ValueError("地址必须以 http:// 或 https:// 开头：" + url)
                cleaned.append({
                    "group": group,
                    "name": name,
                    "url": url,
                    "desc": str(item.get("desc", "")).strip(),
                    "tag": str(item.get("tag", "")).strip(),
                })

            # 先写临时文件再替换，避免写入中途被读取到半截数据。
            fd, tmp_path = tempfile.mkstemp(prefix=".sites-", suffix=".json", dir=str(BASE))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(cleaned, fh, ensure_ascii=False, indent=2)
                    fh.write("\n")
                os.chmod(tmp_path, 0o644)
                os.replace(tmp_path, str(DATA_FILE))
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
        except Exception as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return

        prune_discovered()
        self._json(200, {"ok": True, "count": len(cleaned)})


def lan_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    ip = lan_ip()
    print("导航页服务已启动，数据文件：" + str(DATA_FILE), flush=True)
    print("本机访问：  http://localhost:%d" % port, flush=True)
    print("局域网访问：http://%s:%d" % (ip, port), flush=True)
    print("编辑条目：  http://%s:%d/edit.html" % (ip, port), flush=True)
    print("自动发现：  每 %d 秒扫描一次局域网 Web 服务" % SCAN_INTERVAL, flush=True)
    if TOKEN:
        print("编辑页已启用口令保护", flush=True)
    threading.Thread(target=discovery_loop, daemon=True, name="discovery").start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
