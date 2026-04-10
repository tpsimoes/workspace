# pcap 分析指南

网络抓包文件（`.pcap` / `.pcapng`）分析规范，支持 tshark 和 pyshark 两种方式（自动检测可用工具）。

---

## 工具检测逻辑

```python
import shutil

def detect_tool():
    if shutil.which("tshark"):
        return "tshark"
    try:
        import pyshark
        return "pyshark"
    except ImportError:
        return None
```

若两者均不可用，提示用户安装：
- `tshark`：`sudo apt install tshark` 或随 Wireshark 安装
- `pyshark`：`pip install pyshark`（依赖本机 tshark）

---

## 常用 tshark 命令

### 文件基本信息
```bash
tshark -r <file.pcap> -q -z io,stat,0
capinfos <file.pcap>
```

### 提取 TCP 错误（RST / 重传）
```bash
# TCP RST
tshark -r <file.pcap> -Y "tcp.flags.reset==1" -T fields \
  -e frame.time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport

# TCP 重传
tshark -r <file.pcap> -Y "tcp.analysis.retransmission" -T fields \
  -e frame.time -e ip.src -e ip.dst -e tcp.stream
```

### TLS 握手失败
```bash
tshark -r <file.pcap> -Y "tls.alert_message" -T fields \
  -e frame.time -e ip.src -e ip.dst -e tls.alert_message.desc
```

### DNS 查询与响应
```bash
# 所有 DNS
tshark -r <file.pcap> -Y "dns" -T fields \
  -e frame.time -e ip.src -e dns.qry.name -e dns.resp.name -e dns.flags.rcode

# DNS 失败（NXDOMAIN / SERVFAIL）
tshark -r <file.pcap> -Y "dns.flags.rcode > 0" -T fields \
  -e frame.time -e ip.src -e dns.qry.name -e dns.flags.rcode
```

### HTTP 错误
```bash
tshark -r <file.pcap> -Y "http.response.code >= 400" -T fields \
  -e frame.time -e ip.src -e ip.dst -e http.request.uri -e http.response.code
```

### TCP 连接延迟（握手 RTT）
```bash
tshark -r <file.pcap> -Y "tcp.analysis.ack_rtt" -T fields \
  -e frame.time -e ip.src -e ip.dst -e tcp.analysis.ack_rtt \
  | sort -k4 -n | tail -20
```

### 按 IP 对话统计
```bash
tshark -r <file.pcap> -q -z conv,tcp
```

---

## 关键分析项速查

| 分析项 | tshark 过滤器 | 问题信号 |
|---|---|---|
| TCP RST | `tcp.flags.reset==1` | 连接被强制关闭，端口不可达 |
| 重传率高 | `tcp.analysis.retransmission` | 网络丢包或拥塞 |
| TLS 告警 | `tls.alert_message` | 证书错误、协议不匹配 |
| DNS 失败 | `dns.flags.rcode > 0` | 域名解析故障 |
| 高延迟 ACK | `tcp.analysis.ack_rtt > 0.1` | RTT > 100ms 需关注 |
| 窗口满 | `tcp.analysis.window_full` | 接收端处理慢，发送方被阻塞 |
| 连接拒绝 | `icmp.type==3 && icmp.code==3` | 端口未监听（UDP port unreachable） |
| 零窗口 | `tcp.analysis.zero_window` | 接收端缓冲区满，流控触发 |

---

## pyshark 脚本示例（见 scripts/pcap_analyzer.py）

使用 `scripts/pcap_analyzer.py` 可自动完成：
1. 工具检测（tshark / pyshark）
2. 基本统计（总包数、协议分布、时间范围）
3. 异常提取（RST、重传、DNS 失败、TLS 告警）
4. Top N 会话（按包数/字节数）

```bash
python scripts/pcap_analyzer.py <file.pcap>
```

---

## 常见场景与分析方向

### 场景：应用间歇性连接超时
1. 检查 TCP 重传率和 RTT 分布
2. 过滤目标 IP/Port 的会话
3. 查看是否有 RST 或零窗口

### 场景：TLS 连接失败
1. 过滤 `tls.alert_message`，查看告警类型
2. 常见：`certificate_unknown`（证书不信任）/ `handshake_failure`（协议/密码套件不匹配）
3. 检查 ClientHello 中的 SNI 与服务器证书 CN 是否匹配

### 场景：DNS 解析问题
1. 过滤 DNS 请求 + 响应，检查 rcode
2. 对比请求时间和响应时间，计算解析延迟
3. `NXDOMAIN` = 域名不存在；`SERVFAIL` = DNS 服务器故障

### 场景：Azure VM 与 NVA/LB 通信异常
1. 确认源/目 IP（注意 SNAT 地址转换）
2. 检查 TCP 握手是否完成（SYN → SYN-ACK → ACK）
3. 结合 Azure NSG 流日志对照是否被拦截
