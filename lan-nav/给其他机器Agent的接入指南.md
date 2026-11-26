# 局域网导航页 · 设备端 Agent 接入指南

> 阅读对象：**在其他机器（Windows PC / Mac / Linux）上运行的 AI Agent**。
> 目标：让本机正在开发的 Web 服务自动出现在常驻 Mac 的导航页 `http://192.168.31.94:8000` 的「自动发现」分组中，**不需要手工登记**。
> 编写时间：2026-11-26。若与 `agent.py` 实际行为不一致，以代码为准。

---

## 0. 一句话原理

每台开发机运行一个**服务注册代理** `agent.py`，它在本机固定端口 **9700** 上以 JSON 形式报告「我有哪些 Web 服务」。常驻 Mac 上的扫描器每 120 秒只访问各设备的 9700 端口，把结果汇总到导航页。

```
[Windows PC]                    [常驻 Mac 192.168.31.94]
 agent.py  :9700  ──HTTP JSON──▶  discover.py ──▶ 导航页 :8000
 services.json（可选）             每 120 秒扫一次
```

你（其他机器上的 Agent）**只需要负责自己这一台机器**：把代理跑起来、保持它运行、按需配置 `services.json`。不要去改 Mac 上的文件。

---

## 1. 前置条件（请先确认）

| 项 | 要求 |
|---|---|
| Python | 3.x，仅用标准库，无需 pip 安装任何包。Windows 用 `py -3` 或 `python`，Mac/Linux 用 `python3`（macOS 建议 `/usr/bin/python3`） |
| 网络 | 与 Mac 在同一局域网 `192.168.31.0/24`，能 ping 通 `192.168.31.94` |
| 端口 | 本机 **9700** 未被其他程序占用 |
| 权限 | 允许 Python 监听 0.0.0.0:9700；Windows 首次运行可能弹出防火墙提示，选「允许访问」（专用网络） |

从常驻 Mac 复制这三个文件到本机**同一个目录**（建议 `C:\Users\<用户>\lan-nav-agent\` 或 `~/lan-nav-agent/`）：

- `agent.py` —— 注册代理本体
- `services.json` —— 可选配置文件（可先用模板）
- `start-agent.bat`（Windows）/ `start-agent.command`（Mac/Linux）—— 一键启动器

---

## 2. 快速开始

### Windows

1. 把上述三个文件放到同一目录。
2. 双击 `start-agent.bat`，保持黑色命令行窗口开着。
3. 浏览器访问 `http://<本机IP>:9700/services`，应看到包含 `"device"`、`"ip"`、`"services"` 的 JSON。

### Mac / Linux

```bash
chmod +x start-agent.command
./start-agent.command          # 停止用 Control + C
curl http://127.0.0.1:9700/services
```

启动器内部等价于 `python3 agent.py`（Mac 用 `/usr/bin/python3`）。也可以直接命令行运行，便于查看输出。

> 代理**不会开机自启**。需要长期使用时，Windows 把 `start-agent.bat` 的快捷方式放进「启动」文件夹；Mac 用 launchd / 登录项。

---

## 3. 它会自动做什么

代理每次收到 `/services` 请求时（结果缓存 3 秒）：

1. 用 `netstat -ano -p TCP`（Windows）/ `lsof -nP -iTCP -sTCP:LISTEN`（macOS）/ `ss -ltn`（Linux）列出本机**正在监听**的 TCP 端口。
2. **只保留局域网可访问的监听**：绑定 `0.0.0.0`、`*`、`[::]` 或本机内网 IP 的端口；**排除只绑 `127.0.0.1` / `::1` 的服务**（手机连不上，不报）。
3. 对每个候选端口发一个 HTTP GET，确认它确实说 HTTP，并抓 `<title>` 作为默认服务名。
4. 用 `services.json` 里的配置覆盖名称/备注/标签，或屏蔽端口。
5. 返回如下 JSON：

```json
{
  "device": "PC-NAME",
  "ip": "192.168.31.22",
  "registryPort": 9700,
  "updatedAt": "2026-11-26T23:10:00",
  "services": [
    {
      "name": "订单系统后台",
      "url": "http://192.168.31.22:3000",
      "desc": "192.168.31.22:3000",
      "tag": "正式",
      "port": 3000,
      "title": "订单系统"
    }
  ]
}
```

字段说明：`name` 首页卡片标题；`url` 点击跳转地址；`desc` 备注；`tag` 角标；`port` 源端口；`title` 抓到的网页标题。`name`/`desc`/`tag` 可被 `services.json` 覆盖。

**默认过滤规则**（重要）：

- 屏蔽 50000–59999 端口（通常是编辑器/工具的内部服务，不是开发项目）。确实需要时以 `AGENT_ALLOW_HIGH_PORTS=1` 启动代理。
- 屏蔽 9700 自身（避免把自己上报成服务）。
- 屏蔽返回 403 且无 `<title>` 的响应（如 macOS AirPlay 等系统服务）。
- 只上报**说 HTTP 的端口**；纯 TCP 服务（数据库、SSH 等）不会被上报。

---

## 4. 配置 `services.json`（可选，但建议看一眼）

文件是**数组**，每项按端口覆盖自动识别结果。留空数组 `[]` 表示全部自动识别。

```json
[
  {
    "port": 3000,
    "name": "订单系统后台",
    "desc": "正式版，主项目",
    "tag": "正式",
    "enabled": true
  },
  {
    "port": 5173,
    "name": "管理前端",
    "tag": "测试"
  },
  {
    "port": 8080,
    "enabled": false
  },
  {
    "url": "http://192.168.31.22:9900/path",
    "name": "外部系统集成",
    "desc": "不在本机监听，手工补充"
  }
]
```

字段解释：

| 字段 | 作用 |
|---|---|
| `port` | 按端口匹配一条自动发现的监听；也可与 `url` 一起用于兜底条目 |
| `name` / `desc` / `tag` | 覆盖自动抓取的名称、备注、角标。留空则用网页 `<title>` / 地址兜底 |
| `enabled: false` | 屏蔽该端口，不让它出现在导航页 |
| `url` | ① 覆盖该端口的上报地址（如反向代理）；② 无 `port` 时表示**额外补充**一条固定 URL 的服务 |

注意：

- 修改 `services.json` 后**无需重启**代理，下次请求即生效（最多缓存 3 秒）。
- JSON 必须是合法数组；格式错误时代理静默按空配置处理（不会崩，但你的改名/屏蔽会失效）。
- 当前模板里的示例项是 `"enabled": false`，只是示例，不影响使用。

---

## 5. 验证清单（做完请逐项确认）

在本机执行：

```bash
# 1) 代理活着，并返回 JSON
curl http://127.0.0.1:9700/services

# 2) 端口确实在监听
# Windows: netstat -ano -p TCP | findstr 9700
# Mac/Linux: lsof -nP -iTCP:9700 -sTCP:LISTEN

# 3) 从 Mac 能访问到（在 Mac 上执行）
curl http://<本机IP>:9700/services
```

然后到导航页 `http://192.168.31.94:8000` 点右上角「扫描」（或等最多 120 秒），确认「自动发现」分组里出现本机的服务。

**验收标准**：本机某个开发服务（监听 `0.0.0.0` 或本机内网 IP）在 2 分钟内出现在导航页，点击能打开。

---

## 6. 常见问题排查

| 现象 | 原因与处理 |
|---|---|
| `curl http://127.0.0.1:9700/services` 不通 | 代理没启动或端口被占。换端口用 `AGENT_PORT=9701 python3 agent.py`，但**必须同步告知 Mac 端改 `REGISTRY_PORT=9701`**，否则扫不到 |
| Mac 上 curl 本机 9700 不通，本机自己 curl 通 | Windows 防火墙拦了入站；允许 Python 通过专用网络防火墙。或机器不在同一网段 / 连了访客 Wi-Fi |
| 服务没出现在导航页 | 检查服务是否只绑了 `127.0.0.1`（这类被故意排除）；是否是 50000–59999 段；是否被 `services.json` 里 `enabled: false` 屏蔽；是否只是纯 TCP 服务 |
| 名称不对/想改名 | 在 `services.json` 里按 `port` 写 `name`；3 秒后刷新页面即可，不用重启 |
| 端口 8000 打不开 | 那是 Mac 上导航页本身，与本机代理无关；确认 Mac 上 `start-mac.command` 的终端窗口开着 |
| 手机也访问不了导航页 | 手机须连同一主 Wi-Fi；代理/VPN 里把 `192.168.0.0/16` 设为直连 |

---

## 7. 行为边界（不要越界）

1. **不要修改 Mac 上的任何文件**（`discover.py`、`server.py`、`sites.json` 等由常驻 Mac 的 Agent 维护）。你只需要保证本机的 9700 端口可用。
2. **不要从本机扫描整个网段**——扫描是 Mac 的职责，重复扫描会浪费时间并造成网络噪音。
3. **不要把 `127.0.0.1` 绑定的服务强行上报**——手机/iPad 访问不到，会被过滤；需要暴露时请让开发服务器监听 `0.0.0.0`（例如 Vite `--host 0.0.0.0`、Flask `host='0.0.0.0'`）。
4. **不要改注册端口**，除非同时通知 Mac 端同步 `REGISTRY_PORT`。
5. 导航页中「常用入口 / 正式版 / 测试版 / 实验项目」是手工分组，由 Mac 端维护；你上报的服务统一进「自动发现」。需要固定归类时，把项目名和端口发给 Mac 端 Agent。
6. 代理只在内存中缓存 3 秒，不写任何日志、不收集页面内容，仅抓取 `<title>` 用于命名。

---

## 8. 给 AI Agent 的执行摘要（可直接照做）

```text
1. cd 到放有 agent.py / services.json 的目录。
2. 运行 python3 agent.py（Windows 用 py -3 agent.py），保持进程存活。
3. curl http://127.0.0.1:9700/services 验证返回 JSON 且 services 是数组。
4. 若需要改名/屏蔽，编辑 services.json（数组，字段 port/name/desc/tag/enabled/url）。
5. 若服务未出现在 http://192.168.31.94:8000，检查：服务是否监听 0.0.0.0、
   端口是否在 50000-59999、防火墙是否放行、Mac 是否可达本机 9700。
6. 完成后向用户报告：本机 IP、代理端口、上报的服务数量与名称。
```

---

附：局域网信息（截至 2026-11-26）

| 设备 | IP | 角色 |
|---|---|---|
| 常驻 Mac | `192.168.31.94` | 导航页 + 扫描器（8000 / 9700） |
| Windows PC | `192.168.31.22` | 开发机（部署 agent） |
| NAS | `192.168.31.111` | 群晖 EzioNas.local |
| 路由器 | `192.168.31.1` | 小米路由器 |

更完整的架构与部署说明见同目录 `需求与部署备忘.md`。
