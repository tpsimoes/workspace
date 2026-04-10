# Network / Packet Capture Analysis Branch

> 本文件由 `log_analyzer` Step 1 在识别到网络抓包（pcap/pcapng）或网络层问题时加载。  
> 加载后继续执行通用 Step 2-5，本文件提供抓包工具使用、关键过滤器和常见场景分析。  
> 工具检测和脚本见 `references/pcap-analysis-guide.md`（保留作工具参考）。

---

## 工具检测

```python
import shutil
def detect_tool():
    if shutil.which("tshark"):   return "tshark"
    try:
        import pyshark;          return "pyshark"
    except ImportError:          return None
```

- `tshark`：`sudo apt install tshark` 或随 Wireshark 安装
- `pyshark`：`pip install pyshark`（依赖本机 tshark）
- 批量分析脚本：`python scripts/pcap_analyzer.py <file.pcap>`

---

## 关键分析项速查

| 分析项 | tshark 过滤器 | 问题信号 |
|---|---|---|
| TCP RST | `tcp.flags.reset==1` | 连接被强制关闭，端口不可达 |
| 重传率高 | `tcp.analysis.retransmission` | 网络丢包或拥塞 |
| TLS 告警 | `tls.alert_message` | 证书错误、协议版本不匹配 |
| DNS 失败 | `dns.flags.rcode > 0` | 域名解析故障（NXDOMAIN / SERVFAIL） |
| 高延迟 ACK | `tcp.analysis.ack_rtt > 0.1` | RTT > 100ms 需关注 |
| 窗口满 | `tcp.analysis.window_full` | 接收端处理慢，发送方被阻塞 |
| 零窗口 | `tcp.analysis.zero_window` | 接收端缓冲区满，流控触发 |
| 连接拒绝 | `icmp.type==3 && icmp.code==3` | 端口未监听（UDP port unreachable） |

---

## 常用 tshark 命令

```bash
# 文件基本信息
capinfos <file.pcap>
tshark -r <file.pcap> -q -z io,stat,0

# TCP RST
tshark -r <file.pcap> -Y "tcp.flags.reset==1" -T fields \
  -e frame.time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport

# TCP 重传
tshark -r <file.pcap> -Y "tcp.analysis.retransmission" -T fields \
  -e frame.time -e ip.src -e ip.dst -e tcp.stream

# TLS 握手失败
tshark -r <file.pcap> -Y "tls.alert_message" -T fields \
  -e frame.time -e ip.src -e ip.dst -e tls.alert_message.desc

# DNS 查询与失败
tshark -r <file.pcap> -Y "dns.flags.rcode > 0" -T fields \
  -e frame.time -e ip.src -e dns.qry.name -e dns.flags.rcode

# HTTP 错误
tshark -r <file.pcap> -Y "http.response.code >= 400" -T fields \
  -e frame.time -e ip.src -e ip.dst -e http.request.uri -e http.response.code

# TCP 连接握手 RTT（排序取最高延迟）
tshark -r <file.pcap> -Y "tcp.analysis.ack_rtt" -T fields \
  -e frame.time -e ip.src -e ip.dst -e tcp.analysis.ack_rtt \
  | sort -k4 -n | tail -20

# 按 IP 对话统计
tshark -r <file.pcap> -q -z conv,tcp
```

---

## 常见场景分析

### 场景：应用间歇性连接超时

```
分析路径：
1. tshark -z conv,tcp → 找高重传率对话
2. 过滤目标 IP/Port：-Y "ip.addr==<target> && tcp.port==<port>"
3. 查 TCP RST / 零窗口 → 判断是网络丢包还是接收端处理慢
4. 检查 RTT：tcp.analysis.ack_rtt → 是否存在网络延迟尖峰
```

**关联日志**：对照 OS syslog 是否有 NIC 状态变化（见 branch-linux.md 规则 4）。

### 场景：TLS 连接失败

```
分析路径：
1. tshark -Y "tls" → 查完整握手是否完成
2. tshark -Y "tls.alert_message" → 提取告警类型
   常见 alert: certificate_unknown(46), handshake_failure(40),
               protocol_version(70), bad_certificate(42)
3. 判断方向：
   ├── certificate_unknown → 证书不受信任（CA 链问题）
   ├── protocol_version → 客户端/服务端 TLS 版本不匹配
   └── handshake_failure → 密码套件不兼容
```

### 场景：DNS 解析故障

```
分析路径：
1. tshark -Y "dns" → 确认 DNS 请求是否到达服务器
2. tshark -Y "dns.flags.rcode > 0" → 提取失败响应
   rcode 含义：1=FORMERR, 2=SERVFAIL, 3=NXDOMAIN, 5=REFUSED
3. 若无响应 → UDP 53 被防火墙拦截
4. 若 NXDOMAIN → 域名不存在或 DNS 服务器配置错误
```

### 场景：高丢包 / 网络拥塞

```
分析路径：
1. tshark -q -z io,stat,1 → 按秒统计包量，找流量突刺
2. tcp.analysis.retransmission → 重传帧总数，超过 1% 为异常
3. tcp.analysis.window_full / zero_window → 接收端处理是否跟不上
4. 区分：
   ├── 重传多 + RTT 高 → 网络路径问题（MTU / 带宽 / 路由）
   └── 零窗口多 + RTT 正常 → 接收端应用处理慢
```

### 场景：Azure VM 网络异常

```
额外检查项：
- 检查 NSG 流日志（若可用）确认拦截规则
- 检查 MTU 设置：Azure VM SNAT/VNet 的 MTU 为 1500，
  若有封装（VPN/ExpressRoute）可能需要降低
- ICMP type 3 code 4（Fragmentation Needed）→ MTU 问题信号
```

---

## 分析优先级规则

1. **先看文件基本信息**（时间范围、总包数、协议分布），建立全局印象
2. **优先提取异常帧**（RST / 重传 / TLS Alert / DNS 失败），不全量读取
3. **定位问题时间窗口**，聚焦前后 ±30 秒的会话
4. **跨层关联**：网络异常 → 对照 OS syslog（NIC down / 防火墙变更），见 `correlation-rules.md` 规则 4、5
