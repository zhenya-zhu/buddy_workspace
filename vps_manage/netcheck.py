#!/usr/bin/env python3
"""Client-side VPS network diagnostics; Python 3.9+ standard library only.

No credentials, no root, no persistent traffic or network configuration changes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import ipaddress
import math
import os
import platform
import re
import shutil
import socket
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_TARGETS = [
    {"name": "V.PS Tokyo SoftBank", "host": "103.201.131.7", "port": 5202, "role": "candidate"},
    {"name": "Singapore reference", "host": "sgp.lg.vebble.com", "port": 5201, "role": "reference"},
    {"name": "Cloudflare reference", "host": "1.1.1.1", "port": 443, "role": "reference"},
]
API_ENDPOINTS = [
    ("OpenAI API", "https://api.openai.com/v1/models"),
    ("DeepSeek API", "https://api.deepseek.com/models"),
    ("GitHub", "https://github.com/"),
]
PING_TIME = re.compile(r"(?:time|时间)\s*(=|<)\s*([\d.,]+)\s*ms", re.I)
PING_TTL = re.compile(r"\bttl\s*=\s*(\d+)", re.I)


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    v = sorted(values)
    index = (len(v) - 1) * fraction
    low, high = math.floor(index), math.ceil(index)
    return v[low] + (v[high] - v[low]) * (index - low)


def parse_target(spec: str) -> dict[str, Any]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("Use NAME=HOST:PORT (example: Tokyo=1.2.3.4:22)")
    name, addr = spec.split("=", 1)
    name, addr = name.strip(), addr.strip()
    if not name or not addr or ":" not in addr:
        raise argparse.ArgumentTypeError("Use NAME=HOST:PORT")
    host, port_text = addr.rsplit(":", 1)
    if not host or not re.fullmatch(r"[A-Za-z0-9._-]+", host):
        raise argparse.ArgumentTypeError("HOST must be an IPv4 address or DNS name")
    try:
        port = int(port_text)
        if port < 1 or port > 65535:
            raise ValueError
    except ValueError as e:
        raise argparse.ArgumentTypeError("PORT must be 1..65535") from e
    return {"name": name, "host": host, "port": port, "role": "candidate"}


def tcp_probe(host: str, port: int, timeout: float) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        # getaddrinfo is excluded from TCP timing for IP literals (the default targets).
        with socket.create_connection((host, port), timeout=timeout):
            return {"ms": round((time.perf_counter() - t0) * 1000, 3), "error": None}
    except OSError as e:
        msg = e.strerror or str(e)
        return {"ms": None, "error": msg[:100]}


def run_tcp(target: dict[str, Any], samples: int, interval: float, timeout: float) -> dict[str, Any]:
    results = []
    for i in range(samples):
        results.append(tcp_probe(target["host"], target["port"], timeout))
        if i + 1 < samples:
            time.sleep(interval)
    success = [r["ms"] for r in results if r["ms"] is not None]
    n = len(success)
    return {
        "attempts": samples,
        "successful": n,
        "failures": samples - n,
        "connect_success_pct": round(100 * n / samples, 1),
        "p50_ms": round(statistics.median(success), 2) if n else None,
        "p95_ms": round(percentile(success, 0.95), 2) if n else None,
        "min_ms": round(min(success), 2) if n else None,
        "max_ms": round(max(success), 2) if n else None,
        "spread_ms": round((percentile(success, .95) or 0) - (percentile(success, .5) or 0), 2) if n else None,
        "errors": sorted(set(r["error"] for r in results if r["error"])),
        "samples_ms": success,
    }


def run_dns(host: str, timeout: float) -> dict[str, Any]:
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        t0 = time.perf_counter()
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        ips = sorted({item[4][0] for item in infos})
        return {"ok": True, "duration_ms": round((time.perf_counter() - t0) * 1000, 2), "addresses": ips[:8]}
    except OSError as e:
        return {"ok": False, "error": str(e)[:150]}
    finally:
        socket.setdefaulttimeout(old_timeout)


def run_ping(host: str, count: int) -> dict[str, Any]:
    exe = shutil.which("ping")
    if not exe:
        return {"available": False, "note": "ping command not installed"}
    is_windows = platform.system().lower() == "windows"
    is_macos = platform.system().lower() == "darwin"
    if is_windows:
        command = [exe, "-n", str(count), "-w", "2000", host]
    elif is_macos:
        command = [exe, "-n", "-c", str(count), "-W", "2000", host]
    else:
        command = [exe, "-n", "-c", str(count), "-W", "2", host]
    try:
        p = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=count * 3 + 5)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"available": False, "note": str(e)[:150]}
    times = []
    ttls = []
    for line in p.stdout.splitlines():
        m = PING_TIME.search(line)
        if m:
            number = float(m.group(2).replace(",", "."))
            times.append(number if m.group(1) == "=" else number / 2)
            t = PING_TTL.search(line)
            if t:
                ttls.append(int(t.group(1)))
    return {
        "available": True,
        "sent": count,
        "received": len(times),
        "loss_pct": round(100 * (count - len(times)) / count, 1),
        "avg_ms": round(statistics.mean(times), 3) if times else None,
        "min_ms": round(min(times), 3) if times else None,
        "max_ms": round(max(times), 3) if times else None,
        "ttl_values": sorted(set(ttls)),
        "exit_code": p.returncode,
        "note": "ICMP may be filtered or locally answered; see anomaly warnings",
    }


def detect_icmp_anomaly(tgt: dict[str, Any]) -> str | None:
    icmp = tgt.get("icmp", {})
    tcp = tgt.get("tcp", {})
    v = icmp.get("avg_ms")
    if v is None:
        return None
    p50 = tcp.get("p50_ms")
    if p50 is not None and v < 3 and p50 > 10:
        return "ICMP RTT extremely low vs TCP connect time; suspect local interception/virtual reply. Do NOT use ICMP RTT for ranking."
    if v < 1 and "Tokyo" in tgt["name"]:
        return "Sub-millisecond ICMP to a Tokyo-labeled endpoint is implausible from Shanghai; check network/proxy/ICMP handling."
    return None


def heuristic(tcp: dict[str, Any]) -> dict[str, Any]:
    """Conservative human-facing grading, NOT packet-loss measurement or SLA."""
    n = tcp["successful"]
    total = tcp["attempts"]
    if n == 0:
        return {"label": "unreachable on tested TCP port", "score": 0, "note": "This does not prove the host is offline; the port may be blocked/closed."}
    med, p95 = tcp["p50_ms"], tcp["p95_ms"]
    good = n == total and med <= 100 and p95 <= 180
    usable = n >= max(1, math.ceil(total * .9)) and med <= 180 and p95 <= 350
    if good:
        label = "good for SSH/CLI (short test)"
    elif usable:
        label = "likely usable; verify peak hours"
    else:
        label = "unstable/slow; retest before purchase"
    score_latency = max(0, 50 - max(0, med - 30) * .35)
    score_reliability = 35 * n / total
    score_variability = max(0, 15 - max(0, (p95 - med) - 10) * .15)
    score = round(score_latency + score_reliability + score_variability)
    return {"label": label, "score": score, "note": "Heuristic only; short TCP connect tests do not measure sustained SSH stability or packet loss."}


def run_iperf(rate: str, seconds: int) -> dict[str, Any]:
    exe = shutil.which("iperf3")
    if not exe:
        return {"available": False, "note": "iperf3 missing; install it to use --iperf"}
    result = {"available": True, "bitrate_cap": rate, "duration_per_direction_s": seconds}
    for direction, extra in (("upload", []), ("download", ["-R"])):
        cmd = [exe, "-4", "-c", "tok-sb-ipv4.lg.xtom.com", "-p", "5202", "-t", str(seconds), "-b", rate, "-J", *extra]
        try:
            run = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=seconds + 20)
            data = json.loads(run.stdout)
            if run.returncode or data.get("error"):
                result[direction] = {"ok": False, "error": str(data.get("error") or run.stderr or "iperf3 failed")[:180]}
                continue
            sums = data.get("end", {})
            stat = sums.get("sum_received") or sums.get("sum_sent") or {}
            result[direction] = {"ok": True, "mbps": round(stat.get("bits_per_second", 0) / 1e6, 2),
                                 "bytes": stat.get("bytes"),
                                 "retransmits": sums.get("sum_sent", {}).get("retransmits")}
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            result[direction] = {"ok": False, "error": str(e)[:180]}
    return result


def run_https(title: str, url: str, timeout: float) -> dict[str, Any]:
    # urllib respects HTTP(S)_PROXY; this is marked in the report.
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "vps-netcheck/1.0"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"name": title, "url": url, "http_status": r.status, "tls_http_reachable": True,
                    "elapsed_ms": round((time.perf_counter() - t0)*1000, 2)}
    except urllib.error.HTTPError as e:
        # 401/403 etc prove an HTTP server answered but not that API access is authorized.
        return {"name": title, "url": url, "http_status": e.code, "tls_http_reachable": True,
                "elapsed_ms": round((time.perf_counter() - t0)*1000, 2)}
    except Exception as e:
        return {"name": title, "url": url, "tls_http_reachable": False, "error": str(e)[:160]}


def redact_private_hops(text: str) -> str:
    """Mask private/CGNAT intermediate IPv4 addresses before report storage."""
    def replacement(match: re.Match[str]) -> str:
        value = match.group(0)
        try:
            ip = ipaddress.ip_address(value)
            return value if ip.is_global else "[private-hop]"
        except ValueError:
            return value
    return re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", replacement, text)


def run_route(host: str) -> dict[str, Any]:
    system = platform.system().lower()
    if system == "windows":
        exe = shutil.which("tracert")
        args = ["-d", "-h", "15", "-w", "1000", host]
    else:
        exe = shutil.which("traceroute")
        args = ["-n", "-m", "15", "-w", "1", "-q", "1", host]
    if not exe:
        return {"available": False, "note": "traceroute/tracert not installed"}
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True, errors="replace", timeout=25)
        lines = redact_private_hops(r.stdout).splitlines()[:18]
        return {"available": True, "exit_code": r.returncode, "hops": lines,
                "note": "Private/CGNAT hops redacted. Public hops could still reveal network details; review before sharing."}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"available": False, "note": str(e)[:140]}


def fmt(ms: float | None) -> str:
    return "N/A" if ms is None else f"{ms:.1f}"


def build_markdown(data: dict[str, Any]) -> str:
    lines = ["# VPS 网络测试报告", "", f"- 时间：{data['timestamp']}",
             f"- 环境：{data['environment']}（测试机所在地请自行确认）",
             f"- TCP 每目标采样：{data['settings']['samples']} 次；TCP 失败率 ≠ IP 丢包率",
             "- 结论为经验性短时判断；不构成线路 SLA 或晚高峰稳定性保证", "",
             "## 汇总（主要参考 TCP）", "",
             "| 目标 | TCP 成功 | p50 / p95 (ms) | ICMP 丢包 | 判断 |", "|---|---:|---:|---:|---|"]
    for t in data["targets"]:
        c, p = t["tcp"], t.get("icmp", {})
        icmp_loss = f"{p['loss_pct']:.0f}%" if p.get("available") else "未测"
        if t.get("icmp_warning"):
            icmp_loss += "（ICMP 异常）"
        lines.append(f"| {t['name']} (`{t['host']}:{t['port']}`) | {c['successful']}/{c['attempts']} | {fmt(c['p50_ms'])} / {fmt(c['p95_ms'])} | {icmp_loss} | {t['grade']['label']} |")
    lines += ["", "## 详细诊断", ""]
    for t in data["targets"]:
        c = t["tcp"]
        lines += [f"### {t['name']}", "", f"- 目标：`{t['host']}:{t['port']}`；类别：{t['role']}",
                  f"- TCP：成功 {c['successful']}/{c['attempts']}，中位数 {fmt(c['p50_ms'])} ms，P95 {fmt(c['p95_ms'])} ms，P95-P50 {fmt(c['spread_ms'])} ms",
                  f"- TCP 连接错误：{'; '.join(c['errors']) if c['errors'] else '无'}"]
        p = t.get("icmp", {})
        if p.get("available"):
            lines.append(f"- ICMP：{p['received']}/{p['sent']} 回复，丢包 {p['loss_pct']}%，平均 {fmt(p['avg_ms'])} ms；TTL {p.get('ttl_values')}")
        else:
            lines.append("- ICMP：未获得可用结果（可能缺少命令、无权限或被过滤）")
        if t.get("icmp_warning"):
            lines.append(f"- **警告**：{t['icmp_warning']}")
        lines += [f"- 判断：{t['grade']['label']}（参考分 {t['grade']['score']}/100，不应跨网络视为基准分）", ""]
    if "dns" in data:
        lines += ["## DNS", "", f"- `{data['dns']['hostname']}`：" +
                  (f"成功，{data['dns']['duration_ms']} ms，地址 {', '.join(data['dns']['addresses'])}" if data['dns'].get('ok') else f"失败：{data['dns'].get('error')}") , ""]
    if "iperf3" in data:
        i = data["iperf3"]
        lines += ["## 可选带宽测试", ""]
        if i.get("available"):
            lines += [f"- 方向限速设为 {i['bitrate_cap']}；这是限速样本，不代表线路最大带宽。"]
            for k in ("upload", "download"):
                s = i.get(k, {})
                lines.append(f"- {k}：" + (f"{s['mbps']} Mbps，TCP 重传 {s.get('retransmits', '未知')}" if s.get('ok') else f"失败：{s.get('error', '未知')}"))
        else:
            lines.append(f"- 未测：{i.get('note')}")
        lines.append("")
    if "route" in data:
        route = data["route"]
        lines += ["## 路由（可选）", "", route.get("note", ""), ""]
        if route.get("hops"):
            lines += ["```text", *route["hops"], "```", ""]
    if "https" in data:
        lines += ["## API HTTPS 连通性（无凭证）", "",
                  "注意：401 表示鉴权不足，403 表示服务返回拒绝，均不代表账号可用；本测试不会发送 API Key。", ""]
        if data.get("proxy_configured"):
            lines.append("**检测到系统代理配置**：HTTPS 结果可能走代理，不能当作直连证明。")
        for item in data["https"]:
            lines.append(f"- {item['name']}：" + (f"HTTP {item['http_status']}，{item['elapsed_ms']} ms" if item['tls_http_reachable'] else f"失败：{item.get('error')}"))
        lines.append("")
    lines += ["## 如何解读", "",
              "- **TCP**：`connect()` 用时包含本机/网络栈开销；DNS 名称还可能包含解析时间。SSH 真实交互体验更需要关注高峰期与长连接。",
              "- **ICMP**：可能被屏蔽、限速、拦截/代答；异常低延迟不能用来推断跨境光纤性能。",
              "- **成功率**：此处是特定 TCP 端口建立连接的成功比例，不是网络层丢包率；端口关闭会造成全部失败。",
              "- **P95**：按本次少量样本估计，不能替代长时间监控；建议不同时间、不同接入网络至少测三轮。",
              "- **企业网络**：请仅在允许的网络测试策略下运行，分享路由输出前删除内部地址。", ""]
    return "\n".join(lines)


def print_report(data: dict[str, Any], md_path: Path, json_path: Path) -> None:
    print("\n" + "=" * 80)
    print("VPS NETWORK CHECK | SHORT-TERM SUMMARY")
    print("=" * 80)
    print(f"{'Target':<25} {'TCP ok':>8} {'p50':>8} {'p95':>8} {'ICMP loss':>12}  Assessment")
    for t in data["targets"]:
        c, p = t["tcp"], t.get("icmp", {})
        loss = f"{p['loss_pct']:.0f}%" if p.get("available") else "N/A"
        if t.get("icmp_warning"):
            loss += "!"
        ratio = f"{c['successful']}/{c['attempts']}"
        print(f"{t['name'][:25]:<25} {ratio:>8} {fmt(c['p50_ms']):>8} {fmt(c['p95_ms']):>8} {loss:>12}  {t['grade']['label']}")
        if t.get("icmp_warning"):
            print("  ! " + t["icmp_warning"])
        if c['errors']:
            print("  ! TCP error: " + "; ".join(c['errors'])[:160])
    print("-" * 80)
    print("Note: TCP failure != packet loss. ICMP is not trusted when flagged (!).")
    if "iperf3" in data:
        i = data['iperf3']
        if i.get('available'):
            for d in ('upload','download'):
                r=i.get(d,{})
                print(f"iperf3 {d}: {r.get('mbps','failed')} Mbps (rate capped at {i['bitrate_cap']})")
        else:
            print("iperf3:", i.get("note"))
    if "https" in data:
        for i in data['https']:
            print(f"HTTPS {i['name']}: HTTP {i.get('http_status')}" if i['tls_http_reachable'] else f"HTTPS {i['name']}: failed ({i.get('error')})")
        if data.get('proxy_configured'):
            print("! HTTPS may use an environment/system proxy; not evidence of direct connectivity.")
    print(f"Markdown: {md_path}")
    print(f"JSON:     {json_path}")
    print("Run again during Shanghai evening peak (20:00-23:00).\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="One-command VPS network diagnostics (Python stdlib, no root required).")
    p.add_argument("--target", action="append", type=parse_target, default=[], metavar="NAME=HOST:PORT", help="Add a provider or your VPS IP and an OPEN TCP port; repeatable")
    p.add_argument("--only-custom", action="store_true", help="Skip built-in V.PS, Singapore and Cloudflare targets")
    p.add_argument("--compare-tokyo", action="store_true", help="Also compare a second Tokyo provider (SpeedyPage Looking Glass)")
    p.add_argument("--samples", type=int, default=10, help="TCP samples per target (default: 10)")
    p.add_argument("--interval", type=float, default=0.4, help="Seconds between TCP probes (default: 0.4)")
    p.add_argument("--timeout", type=float, default=3.0, help="TCP connect timeout in seconds (default: 3)")
    p.add_argument("--no-ping", action="store_true", help="Skip ICMP ping attempts")
    p.add_argument("--iperf", action="store_true", help="Optional rate-limited 5 s up + 5 s down test to V.PS Tokyo (uses mobile data)")
    p.add_argument("--iperf-rate", default="10M", help="iperf TCP bitrate cap (default: 10M; suffix K/M/G)")
    p.add_argument("--api-check", action="store_true", help="Optional HTTPS checks to OpenAI, DeepSeek and GitHub, useful when run ON a VPS")
    p.add_argument("--route", action="store_true", help="Optional traceroute summary; full private network hops are not saved")
    p.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "reports", help="Where to save Markdown/JSON reports")
    args = p.parse_args(argv)
    if not 1 <= args.samples <= 100 or not 0 <= args.interval <= 10 or not .1 <= args.timeout <= 30:
        p.error("--samples must be 1..100, --interval 0..10, --timeout 0.1..30")
    if not re.fullmatch(r"[1-9]\d*(?:\.\d+)?[KMG]", args.iperf_rate, re.I):
        p.error("--iperf-rate must be e.g. 5M, 10M, 50M")
    targets = ([] if args.only_custom else [dict(t) for t in DEFAULT_TARGETS]) + args.target
    if args.compare_tokyo:
        targets.append({"name": "Tokyo reference (SpeedyPage)", "host": "tyo.lg.speedypage.com", "port": 5201, "role": "reference"})
    if not targets:
        p.error("No targets: add --target NAME=HOST:PORT or omit --only-custom")
    now = dt.datetime.now().astimezone()
    data = {"timestamp": now.isoformat(timespec="seconds"),
            "environment": f"{platform.system()} {platform.release()} / Python {platform.python_version()}",
            "settings": {"samples": args.samples, "interval_s": args.interval, "timeout_s": args.timeout,
                         "icmp_enabled": not args.no_ping, "iperf_enabled": args.iperf}, "targets": []}
    print("Starting network checks. No credentials, no admin privileges, no external Python libraries.", flush=True)
    print("IMPORTANT: Test from EACH actual network (phone 4G, office Wi-Fi, home broadband).", flush=True)
    for t in targets:
        print(f"  TCP {t['name']} ({t['host']}:{t['port']}) ...", flush=True)
        entry = dict(t)
        entry["tcp"] = run_tcp(t, args.samples, args.interval, args.timeout)
        entry["icmp"] = {"available": False, "note": "disabled"} if args.no_ping else run_ping(t["host"], min(args.samples, 5))
        entry["icmp_warning"] = detect_icmp_anomaly(entry)
        entry["grade"] = heuristic(entry["tcp"])
        data["targets"].append(entry)
    print("  DNS tok-sb-ipv4.lg.xtom.com ...", flush=True)
    data["dns"] = dict(hostname="tok-sb-ipv4.lg.xtom.com", **run_dns("tok-sb-ipv4.lg.xtom.com", args.timeout))
    if args.route:
        print("  Optional traceroute ...", flush=True)
        data["route"] = run_route(targets[0]["host"])
    if args.iperf:
        print("  Optional, rate-limited iperf3 (10 seconds total) ...", flush=True)
        data["iperf3"] = run_iperf(args.iperf_rate, 5)
    if args.api_check:
        data["proxy_configured"] = bool(urllib.request.getproxies())
        print("  Optional HTTPS API checks (no authentication) ...", flush=True)
        data["https"] = [run_https(name, url, min(8, args.timeout * 2)) for name, url in API_ENDPOINTS]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    md_path = args.output_dir / f"netcheck_{stamp}.md"
    json_path = args.output_dir / f"netcheck_{stamp}.json"
    md_path.write_text(build_markdown(data), encoding="utf-8")
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print_report(data, md_path, json_path)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user; no network settings changed.", file=sys.stderr)
        sys.exit(130)