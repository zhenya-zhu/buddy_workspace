#!/usr/bin/python3
"""每台设备自己的导航页：静态页面 + 本机服务探测 + 手工入口保存。

不扫描网段，不读取其他设备；默认监听 0.0.0.0:8000。
仅使用 Python 标准库。
"""

import json
import os
import socket
import sys
import tempfile
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from detect import collect_services, lan_ip

BASE = Path(__file__).resolve().parent
SITES_FILE = BASE / "sites.json"
SERVICES_FILE = BASE / "services.json"
PORT = int(os.environ.get("PORT", "8000"))
TOKEN = os.environ.get("NAV_EDIT_TOKEN", "")
ALLOWED_GROUPS = {"basics", "production", "testing", "lab"}
MAX_BODY = 1024 * 1024


def read_json(path, fallback):
    try:
        with open(str(path), encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return fallback


def write_json(path, data):
    fd, tmp_path = tempfile.mkstemp(prefix=".device-nav-", suffix=".json", dir=str(BASE))
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


def clean_sites(payload):
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
    return cleaned


class DeviceHTTPServer(ThreadingHTTPServer):
    # Windows 的 SO_REUSEADDR 允许同一端口重复绑定；关掉它，端口冲突才能被检测到。
    allow_reuse_address = sys.platform != "win32"


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
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/api/config":
            self._json(200, {
                "auth": bool(TOKEN),
                "device": socket.gethostname(),
                "ip": lan_ip(),
                "port": PORT,
            })
            return
        if path == "/api/services":
            refresh = parse_qs(parsed.query).get("refresh", ["0"])[0] == "1"
            services = collect_services(
                SERVICES_FILE,
                exclude_ports={PORT, 9700},
                allow_high_ports=os.environ.get("DEVICE_NAV_ALLOW_HIGH_PORTS") == "1",
                force=refresh,
            )
            self._json(200, {
                "device": socket.gethostname(),
                "ip": lan_ip(),
                "port": PORT,
                "updatedAt": datetime.now().isoformat(timespec="seconds"),
                "services": services,
            })
            return
        if path == "/api/sites":
            self._json(200, read_json(SITES_FILE, []))
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/api/refresh":
            services = collect_services(
                SERVICES_FILE,
                exclude_ports={PORT, 9700},
                allow_high_ports=os.environ.get("DEVICE_NAV_ALLOW_HIGH_PORTS") == "1",
                force=True,
            )
            self._json(200, {
                "ok": True,
                "count": len(services),
                "updatedAt": datetime.now().isoformat(timespec="seconds"),
            })
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
        if length <= 0 or length > MAX_BODY:
            self._json(400, {"ok": False, "error": "数据为空或超过 1 MB"})
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            cleaned = clean_sites(payload)
            write_json(SITES_FILE, cleaned)
        except Exception as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return

        self._json(200, {"ok": True, "count": len(cleaned)})

    def log_message(self, fmt, *args):
        if os.environ.get("DEVICE_NAV_DEBUG") == "1":
            sys.stderr.write("[%s] %s\n" % (self.client_address[0], fmt % args))
            sys.stderr.flush()


def main():
    global PORT
    requested = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = None
    for port in range(requested, requested + 20):
        try:
            server = DeviceHTTPServer(("0.0.0.0", port), Handler)
            if port != requested:
                print("端口 %d 被占用，已改用 %d。" % (requested, port), flush=True)
            PORT = port
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit("端口 %d–%d 都被占用，请用 PORT=其他端口 启动。" % (requested, requested + 19))

    ip = lan_ip()
    print("本机导航页已启动，只探测本机服务，不扫描网段。", flush=True)
    print("本机访问：  http://127.0.0.1:%d/" % PORT, flush=True)
    print("局域网访问：http://%s:%d/" % (ip, PORT), flush=True)
    print("编辑入口：  http://%s:%d/edit.html" % (ip, PORT), flush=True)
    if TOKEN:
        print("编辑页已启用口令保护。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
