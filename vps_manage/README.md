# VPS 网络诊断工具

用于在**实际访问 VPS 的设备/网络**上测试 TCP 连接延迟与可靠性，并生成便于比较的 Markdown + JSON 报告。适合上海的公司网络、家宽，以及 Android Termux 下的 4G/5G 网络。

> [工程] 只用 Python 3.9+ 标准库，无需 `pip install`，无需 root。默认只做短时、小流量测试。测试结果反映**当前网络至测试目标的指定端口**，不代表所有 VPS 实例、整个供应商或不同运营商的服务质量。

## 直接运行（默认一条命令）

在仓库根目录：

```bash
python3 vps_manage/netcheck.py
```

Windows PowerShell：

```powershell
py -3 vps_manage/netcheck.py
```

Android Termux 首次使用：

```bash
pkg install python iputils
# 已下载仓库后在其根目录：
python vps_manage/netcheck.py
```

脚本默认测试：

| 目标 | 测试地址和端口 | 含义 |
|---|---|---|
| V.PS Tokyo SoftBank | `103.201.131.7:5202` | [V.PS 东京 Cloud / Mini KVM 所用线路](https://v.ps/speedtest/)。端口也是用户先前成功测试的 iperf3 端口 |
| Singapore reference | `sgp.lg.vebble.com:5201` | [Vebble 新加坡线路的 Looking Glass](https://sgp.lg.vebble.com/)，**不是腾讯云** |
| Cloudflare reference | `1.1.1.1:443` | 公网参考基线，不代表某个 VPS 供应商 |

可选比较第二个东京商家（SpeedyPage，**不是腾讯云**）：

```bash
python3 vps_manage/netcheck.py --compare-tokyo
```

由于没有验证过腾讯云针对东京/新加坡 Lighthouse 实例的可用官方**同线路 TCP 测试端点**，工具不会虚构一个腾讯云测速地址。购买腾讯云实例后可直接用实例的公网 IP + 开放端口对比（如 SSH 22）：

```bash
python3 vps_manage/netcheck.py --target 'Tencent-Tokyo=实际公网IP:22'
```

若需要**只测自己的 VPS**：

```bash
python3 vps_manage/netcheck.py --only-custom --target 'My-VPS=实际公网IP:22'
```

> [工程] 如果目标 TCP 端口未监听或公司网络屏蔽它，TCP 测试会失败，**不能**直接推论“这家 VPS 网络差”。有条件请尽量使用不同服务器上实际开放的相同服务端口，再进行横向比较。

## 输出报告

脚本在终端输出一张表，包含每个目标的：

- TCP 建连成功次数、p50/p95 毫秒、经验性“适合 SSH/需要复测”判断；
- ICMP Ping 回复与丢包百分比（明确**不等于** TCP 失败率）；
- Ping 真实性检查：例如平均 `0.066ms`，而 TCP 建连明显高于它，则标记 **ICMP 异常**，不采用 Ping 延迟排名；
- DNS 状态、可选 TCP 速率测试、可选 HTTPS API 连通性；
- 评分仅作阅读辅助，不是 SLA/权威质量排名，短时采样无法证明晚高峰长期稳定。

同时在 `vps_manage/reports/` 自动保存带时间戳的 `.md` 和 `.json`，目录通过 `.gitignore` 排除，不会误把公司网络诊断信息提交到 GitHub。分享报告前仍应检查其中的公网 IP 信息。

## 进阶用法

### 对比办公室、4G、家宽

分别从每个实际网络运行默认命令；最佳实践是在白天和 **上海时间 20:00–23:00** 各测一次。使用 `--samples 30` 获取更多样本（执行时间增加）。

```bash
python3 vps_manage/netcheck.py --samples 30
```

### 带宽（必须主动加 `--iperf`）

先安装 `iperf3`，再执行：

```bash
python3 vps_manage/netcheck.py --iperf
```

仅对 V.PS 东京 SoftBank 执行正/反向各 5 秒的 `iperf3` TCP 传输，**默认限速 10Mbit/s** 以控制手机流量（总理论有效载荷约 12.5 MB，实际加协议开销可能更多）。

这测的是**10Mbit/s 限速下能否跑满**，不是最大吞吐测试。需要更高上限可显式写 `--iperf-rate 30M`，注意流量消耗随之上升。第三方测试服务器也可能限制并发或带宽。未安装 iperf3 时自动跳过，不影响报告。

### HTTPS（建议在买到 VPS 后从 VPS 内部运行）

```bash
python3 vps_manage/netcheck.py --api-check
```

对 OpenAI `/v1/models`、DeepSeek `/models`、GitHub 发起**不含任何 API Key 的 HTTPS GET**。HTTP 401 代表服务器正常回应但缺少认证，403 可能是权限/区域策略拒绝；**两者都不意味着 API 可实际调用**。HTTPS 可能遵循系统代理设置，因此也不能单独证明直连。无需发送或输入任何密钥。

### 追踪路由（可选）

```bash
python3 vps_manage/netcheck.py --route
```

如果系统已安装 `traceroute`（Windows 为 `tracert`），执行最多 15 跳的路由测试，报告对私有地址/CGNAT 地址做掩码；**公网跃点仍可能泄露企业网络结构，分享前自行审核**。路由中某一跳不回复不代表最终端到端丢包。

## 如何判断该不该买？

[工程] 对 SSH/Agent CLI，优先关注 **TCP 成功率、P95 延迟，以及多轮/晚高峰的稳定性**。2 秒内 TCP 可连接不代表 8 小时 SSH 会话不中断；选择月付，连续测试多次再决定。不要仅凭 Ping 值挑机房。

[工程] 尤其注意：手机 4G 和公司网络可能由不同运营商、企业 VPN/代理出口转发；两者结果不具有可替代性。公司网络测试须遵守公司网络与安全政策，不要将生产系统地址、内部跳点或敏感凭证公开。

### 已知限制

- TCP 连接耗时是 `socket.create_connection` 的耗时；对 DNS 主机名包含解析过程，不是纯网络 RTT。要精确比较推荐使用 IP 形式（默认 V.PS 就是 IPv4）。
- ICMP 在 Windows/macOS/Linux/Termux 上解析格式可能略有区别，解析失败会显示无有效 ICMP 结果，而不是虚构 0% 丢包。
- TCP 失败率不是 ICMP 丢包率；TCP 连接拒绝也可能表示端口没开。
- TCP p95 由小样本估计，偏差较大；建议 10–30 次采样，并跨时段复测。
- 原始数据保存在本机，脚本不上传测试报告、不检测或发送本机公网 IP、不请求 API 密钥。

## 参考与验证

- `[原文]` [V.PS Looking Glass 网络对应关系](https://v.ps/speedtest/)
- `[原文]` [V.PS 东京 Cloud / Mini / Performance 线路区别](https://v.ps/locations/tokyo/)
- `[原文]` [Vebble 新加坡 Looking Glass 的 iperf3 测试端口](https://sgp.lg.vebble.com/)
- `[原文]` [SpeedyPage 东京 Looking Glass 的 iperf3 测试端口](https://tyo.lg.speedypage.com/)
- `[工程]` 运行 `python3 vps_manage/netcheck.py --help` 查看全部参数。