"""局域网服务发现：只探测每台设备的固定注册端口（默认 9700）。

设备端跑 agent.py，在 9700 端口上报自己的 Web 服务清单。
Mac 端只需 ping 找存活主机，再读取该端口的 JSON，不做多端口扫描。
仅使用 Python 标准库。
"""

import ipaddress
import json
import os
import re
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlsplit

REGISTRY_PORT = int(os.environ.get("REGISTRY_PORT", "9700"))
PING_WORKERS = 64
FETCH_WORKERS = 48
CONNECT_TIMEOUT = 0.3
HTTP_TIMEOUT = 8.0


def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


def network():
    ip = local_ip()
    iface = "en0"
    try:
        # 查默认路由的接口；查本机 IP 会返回 lo0（/8），不能用来扫网段。
        route = subprocess.check_output(["route", "-n", "get", "default"], text=True, timeout=2)
        match = re.search(r"interface: (\S+)", route)
        if match:
            iface = match.group(1)
    except Exception:
        pass

    netmask = "255.255.255.0"
    try:
        info = subprocess.check_output(["ifconfig", iface], text=True, timeout=2)
        match = re.search(r"netmask (0x[0-9a-fA-F]+)", info)
        if match:
            netmask = socket.inet_ntoa(int(match.group(1), 16).to_bytes(4, "big"))
    except Exception:
        pass

    try:
        net = ipaddress.IPv4Network("%s/%s" % (ip, netmask), strict=False)
        if net.num_addresses > 1024:
            raise ValueError("网段过大")
        return net
    except Exception:
        return ipaddress.IPv4Network("%s/24" % ip, strict=False)


def _ping(ip):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-t", "1", ip],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2,
        )
        return result.returncode == 0
    except Exception:
        return False


def _arp_hosts():
    try:
        output = subprocess.check_output(["arp", "-a"], text=True, timeout=3)
    except Exception:
        return set()
    return {match.group(0) for match in re.finditer(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", output)}


def live_hosts(net):
    all_hosts = [str(host) for host in net.hosts()]
    found = set()
    with ThreadPoolExecutor(max_workers=PING_WORKERS) as pool:
        futures = {pool.submit(_ping, ip): ip for ip in all_hosts}
        for future in as_completed(futures):
            if future.result():
                found.add(futures[future])

    # 禁 ping 的设备若还在 ARP 表里，也尝试读取注册端口。
    found |= _arp_hosts() & set(all_hosts)
    found.add(str(net.network_address + 1))
    return sorted(found, key=lambda ip: int(ipaddress.IPv4Address(ip)))


def _fetch_registry(ip):
    """读取一台设备的 9700 端口，返回其服务清单 JSON。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)
    try:
        if sock.connect_ex((ip, REGISTRY_PORT)) != 0:
            return None
    except Exception:
        sock.close()
        return None

    try:
        sock.settimeout(HTTP_TIMEOUT)
        request = (
            "GET /services HTTP/1.1\r\n"
            "Host: %s:%d\r\n"
            "User-Agent: LAN-Nav-Discovery/1.0\r\n"
            "Accept: application/json\r\n"
            "Connection: close\r\n\r\n" % (ip, REGISTRY_PORT)
        ).encode("ascii")
        sock.sendall(request)
        chunks, total = [], 0
        while total < 262144:
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
    if "HTTP/" not in first_line or " 200 " not in first_line:
        return None
    try:
        data = json.loads(body.decode("utf-8", "ignore"))
    except Exception:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("services"), list):
        return None
    return data


def scan_lan():
    started = time.time()
    net = network()
    hosts = live_hosts(net)

    registries = []
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {pool.submit(_fetch_registry, ip): ip for ip in hosts}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                data = future.result()
            except Exception:
                data = None
            if data:
                registries.append((ip, data))

    registries.sort(key=lambda pair: int(ipaddress.IPv4Address(pair[0])))
    services, seen = [], set()
    for ip, data in registries:
        for item in data["services"]:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            if not url:
                continue
            key = url.lower().rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            try:
                port = urlsplit(url).port or 80
            except Exception:
                port = 0
            services.append({
                "host": ip,
                "port": port,
                "url": url,
                "name": str(item.get("name") or url),
                "desc": str(item.get("desc") or ""),
                "tag": str(item.get("tag") or ""),
                "title": str(item.get("title") or ""),
                "device": str(data.get("device") or ip),
            })

    services.sort(key=lambda item: (int(ipaddress.IPv4Address(item["host"])), item["port"]))
    return {
        "scannedAt": datetime.now().isoformat(timespec="seconds"),
        "duration": round(time.time() - started, 1),
        "network": str(net),
        "hostsScanned": len(hosts),
        "registryPort": REGISTRY_PORT,
        "devices": len(registries),
        "services": services,
    }


if __name__ == "__main__":
    print(json.dumps(scan_lan(), ensure_ascii=False, indent=2))
