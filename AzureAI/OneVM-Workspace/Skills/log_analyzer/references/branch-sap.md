# SAP Log Analysis Branch

> 本文件由 `log_analyzer` Step 1 在识别到 SAP（HANA / NetWeaver / Pacemaker HA）问题时加载。  
> 加载后继续执行通用 Step 2-5，本文件提供 SAP 专属错误模式、日志位置和分析指南。

---

## 日志文件速查

| 层级 | 日志类型 | 关键路径 |
|---|---|---|
| NetWeaver | Work Process trace | `/usr/sap/<SID>/D<nr>/work/dev_w*` |
| NetWeaver | System Log | SM21 事务码导出 |
| NetWeaver | ABAP Dump | ST22 事务码（`dev_w*` 中的 short dump ID） |
| NetWeaver | Gateway log | `dev_rd`（RFC / 远程调用） |
| HANA | Name Server trace | `/usr/sap/<SID>/HDB<nr>/<hostname>/trace/nameserver_*.trc` |
| HANA | Index Server trace | `/usr/sap/<SID>/HDB<nr>/<hostname>/trace/indexserver_*.trc` |
| HANA | Backup log | `backint*.log`、`hdbbackint.log` |
| HANA HA | HSR 状态 | `hdbnsutil -sr_state`（运行时查询） |
| OS | syslog | `/var/log/messages` 或 `journalctl` |
| 集群 | Pacemaker / Corosync | `/var/log/pacemaker.log`、`/var/log/corosync.log` |

---

## 错误模式 — SAP NetWeaver

### Work Process 崩溃 (dev_w\* trace)

```
***LOG Q0I=> ThIErrHandle, <code> [thxxhead.c  <line>]
ABAP Runtime Error: <error_code>
Short dump written to <dump_id>
```

- **含义**：ABAP work process 崩溃，生成 short dump
- **对照**：SM21 系统日志 + ST22 ABAP dump（通过 dump_id 关联）
- **常见原因**：内存不足、程序 bug、数据库连接断开

### 数据库连接中断 (dev_w\*)

```
Database connection broken
Reconnect failed
DBSL error: <code>
```

- **关联**：对照 HANA trace 中同时间段的 indexserver/nameserver 错误

### RFC / 远程调用失败 (dev_rd)

```
Error in RFC connection
CALL_FUNCTION_REMOTE_ERROR
```

---

## 错误模式 — SAP HANA

### HANA 内存不足

```
[SYSTEM] out of memory - current usage: <n>
System ran out of memory
```

- **含义**：HANA 内存耗尽，可能触发服务重启
- **对照**：OS syslog OOM Killer 是否同时触发（见 branch-linux.md）

### HANA 服务重启

```
emergency shutdown
[indexserver] service stopped
nameserver: emergency shutdown
```

- **关联影响**：SAP 应用层报 "Database connection broken"（见 correlation-rules.md 规则 7）

### HANA System Replication 中断（HA 场景）

```
[HA DR] Replication channel .* disconnected
[HA DR] LogReplication: error while receiving
```

- **含义**：HSR 复制断开，影响 HA 切换能力
- **立即检查**：`hdbnsutil -sr_state` 确认主从状态

### HANA Backup 失败

```
BACKUP CATALOG error
backup failed
```

---

## 分析决策树

```
SAP 问题
├── 应用层业务中断（用户报 ABAP Runtime Error / 连接超时）
│   ├── dev_w* → 确认 work process crash 时间 + dump ID
│   ├── SM21 / ST22 → 获取 ABAP error class 和 short dump 详情
│   ├── 判断根因方向：
│   │   ├── ABAP 程序 bug → 开发团队 fix
│   │   ├── 数据库连接中断 → 继续查 HANA 层
│   │   └── 内存不足 → 查 OS OOM + HANA 内存配置
│   └── 对照时间线与 OS syslog（是否有 OOM / 磁盘 I/O 错误）
│
├── HANA 服务不可用
│   ├── nameserver_*.trc + indexserver_*.trc → 查 emergency shutdown 或 OOM
│   ├── OS syslog → 是否有 OOM Killer 终止 HANA 进程
│   ├── 检查 HANA 内存分配（current_mem_used / peak_mem_used）
│   └── 确认 HANA 服务是否已自动重启：
│       hdbnsutil -sr_state / HDB info
│
├── HANA HA 切换 / HSR 断开
│   ├── HSR trace → 复制断开时间 + 原因
│   ├── Pacemaker log → 是否触发 HA 自动切换（fencing + 资源切换）
│   ├── 网络检查 → HSR 复制网络是否中断（见 branch-linux.md Corosync）
│   └── 确认切换后主从角色：hdbnsutil -sr_state
│
├── SAP 备份失败
│   ├── hdbbackint.log → 错误码 + backint 报错
│   ├── HANA Backup Catalog → 确认备份失败时间和类型
│   └── 检查存储空间：df -h / SAP HANA backup volume
│
└── 性能问题（响应慢 / 对话超时）
    ├── HANA trace → expensive SQL statements
    ├── dev_w* → dialog work process 等待时间
    ├── OS → CPU / memory / disk I/O 是否有瓶颈
    └── 触发 knowledge_search 查 SAP Note（SAP HANA performance troubleshooting）
```

---

## SAP HANA 常用诊断命令

```bash
# HANA 服务状态
HDB info
HDB version

# HSR 状态
hdbnsutil -sr_state

# HANA 内存使用（在 hdbsql 中执行）
SELECT * FROM M_HOST_RESOURCE_UTILIZATION;
SELECT TOP 20 * FROM M_EXPENSIVE_STATEMENTS ORDER BY DURATION_MICROSEC DESC;

# Backup Catalog
SELECT * FROM M_BACKUP_CATALOG ORDER BY UTC_START_TIME DESC LIMIT 10;
```

---

## 关联规则参考

本 branch 适用的 `correlation-rules.md` 规则：
- **规则 2**：磁盘 I/O 错误 → 数据库写入失败
- **规则 7**：HANA 服务重启 → SAP 应用层报 "Database connection broken"
- **规则 1**：OS OOM → HANA 进程终止（若 HANA 被 OOM Killer 终止）
