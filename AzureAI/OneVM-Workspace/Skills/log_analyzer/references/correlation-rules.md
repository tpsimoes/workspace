# 跨层关联规则

多文件分析时，用于识别跨层因果链的规则库。

---

## 关联规则格式

```
触发事件（来源层）→ 预期影响（目标层）
匹配条件 + 时间窗口
```

---

## OS 层 → 中间件层

### 规则 1：OOM → 进程终止
- **触发**：syslog 中出现 `Out of memory: Kill process`
- **预期影响**：同时间窗口内，中间件/数据库日志出现 `connection refused` / `connection reset` / 服务重启记录
- **时间窗口**：±30 秒
- **关联说明**：内核 OOM killer 终止进程后，依赖该进程的服务会立即感知连接断开

### 规则 2：磁盘 I/O 错误 → 数据库写入失败
- **触发**：`kern.log` / `dmesg` 出现 `I/O error, dev` / `Buffer I/O error`
- **预期影响**：数据库 errorlog 出现 `write error` / `disk full` / `tablespace` 错误
- **时间窗口**：±60 秒
- **关联说明**：底层磁盘故障会直接传导至数据库 I/O 层

### 规则 3：系统时钟跳变 → 集群脑裂
- **触发**：syslog 出现 `time jump` / `ntpd: time stepped`
- **预期影响**：Pacemaker/Corosync 出现节点超时、资源切换
- **时间窗口**：±120 秒
- **关联说明**：集群心跳超时阈值通常基于系统时间，NTP 跳变可误触发 fencing

---

## OS 层 → 网络层

### 规则 4：网络接口 Down → 连接超时
- **触发**：syslog/dmesg 出现 `link down` / `NIC link is Down` / `eth0: renamed`
- **预期影响**：同时间窗口内，pcap 中出现大量 TCP 重传、RST，或 DNS 解析失败
- **时间窗口**：±10 秒
- **关联说明**：NIC 状态变化直接导致 TCP 会话中断

### 规则 5：防火墙规则变更 → 连接被拒
- **触发**：auth.log/syslog 出现 `iptables` / `firewalld` 规则变更
- **预期影响**：pcap 中出现 TCP RST 或 ICMP type 3（port unreachable）
- **时间窗口**：±30 秒

---

## 中间件层 → 应用层

### 规则 6：数据库连接池耗尽 → 应用 500 错误
- **触发**：数据库日志出现 `max_connections reached` / `too many connections`
- **预期影响**：Nginx/Apache error.log 出现 `upstream timed out` / HTTP 502/503
- **时间窗口**：±30 秒

### 规则 7：SAP HANA 服务重启 → SAP 应用层报错
- **触发**：HANA trace 出现 `System stopped` / `emergency shutdown`
- **预期影响**：SAP SM21 系统日志出现 `Database connection broken` / dev_w* 出现 `reconnect`
- **时间窗口**：±120 秒

---

## 集群层关联规则

### 规则 8：Fencing 触发 → 资源切换
- **触发**：Pacemaker 出现 `will be fenced` / `stonith` 操作
- **预期影响**：另一节点接管资源，日志中出现资源 `start` 操作，应用短暂中断
- **时间窗口**：fencing 后 0~300 秒

### 规则 9：集群脑裂（Split-brain）
- **触发**：Corosync 出现两个分区同时认为自己是 DC
- **特征**：两个节点的 Pacemaker 日志均出现 `I am the DC` 且时间重叠
- **影响**：最严重的集群故障，数据一致性风险

---

## 时间关联算法说明

多文件分析时，`scripts/correlator.py` 执行以下逻辑：

1. **时间戳标准化**：所有文件事件转换为 UTC，精确到秒
2. **滑动窗口匹配**：对每个触发事件，在目标文件中查找时间窗口内的相关事件
3. **置信度评分**：
   - 时间窗口内命中 + 关键词匹配 → 高置信（明确因果）
   - 时间窗口内命中但无关键词 → 中置信（疑似关联）
   - 仅时间接近 → 低置信（时间巧合，需人工判断）
4. **因果链输出**：按置信度排序，高置信链条优先展示
