# Linux / Cluster Log Analysis Branch

> 本文件由 `log_analyzer` Step 1 在识别到 Linux OS / 集群 / 容器 / Web 服务问题时加载。  
> 加载后继续执行通用 Step 2-5，本文件提供错误模式、日志位置和关联规则补充。

---

## 日志文件速查

| 层级 | 日志类型 | 关键路径 |
|---|---|---|
| OS | syslog / messages | `/var/log/syslog`, `/var/log/messages` |
| OS | 内核日志 | `dmesg`, `/var/log/kern.log` |
| OS | systemd journal | `journalctl` 导出 |
| OS | 认证日志 | `/var/log/auth.log`, `/var/log/secure` |
| 集群 | Pacemaker | `/var/log/pacemaker.log`, `/var/log/cluster/corosync.log` |
| 集群 | Corosync | `/var/log/corosync.log` |
| Web | Nginx | `/var/log/nginx/access.log`, `/var/log/nginx/error.log` |
| Web | Apache | `/var/log/apache2/error.log`, `/var/log/httpd/error_log` |
| 容器 | K8s pod logs | `kubectl logs <pod> --previous` |
| 容器 | kubelet | `/var/log/messages` 或 `journalctl -u kubelet` |

---

## 错误模式

### OS — OOM Killer

```
Out of memory: Kill process <pid> (<name>) score <n> or sacrifice child
Killed process <pid> (<name>) total-vm:<n>kB
```

- **含义**：内存耗尽，内核强制终止进程
- **关联影响**：进程终止 → 服务中断、数据库连接断开（见 correlation-rules.md 规则 1）

### OS — Kernel Panic

```
Kernel panic - not syncing: <reason>
BUG: unable to handle kernel NULL pointer dereference
```

- **含义**：内核级致命错误，系统停机
- **关联影响**：VM/宿主机重启、所有服务中断

### OS — 磁盘 I/O 错误

```
blk_update_request: I/O error, dev <sda>, sector <n>
EXT4-fs error (device <sda>): <function>
Buffer I/O error on dev <sda>, logical block <n>
```

- **含义**：磁盘读写故障（物理故障或驱动问题）
- **关联影响**：文件系统损坏、数据库写入失败（见 correlation-rules.md 规则 2）

### OS — Systemd 服务失败

```
<service>.service: Main process exited, code=exited, status=<n>/<sig>
<service>.service: Failed with result 'exit-code'
Failed to start <Service Description>
```

### OS — SSH 认证失败

```
Failed password for <user> from <ip> port <port> ssh2
Invalid user <user> from <ip>
Connection closed by authenticating user <user> <ip> [preauth]
```

- **含义**：暴力破解尝试或认证配置问题

---

## 错误模式 — Pacemaker / Corosync（Linux 集群）

### Fencing 触发

```
stonith: <node> will be fenced
Scheduling Node <node> for STONITH
```

- **含义**：节点被强制隔离，通常是心跳超时或资源失败触发
- **关联影响**：资源切换到另一节点（见 correlation-rules.md 规则 8）

### 资源启动失败

```
<resource>_start_0 on <node> 'unknown error' (1)
<resource>_monitor_0 on <node> 'not running' (7)
```

- **常见原因**：Fencing Agent 配置错误、资源依赖未满足

### Corosync 心跳丢失

```
TOTEM: A processor failed, forming new configuration
corosync[<pid>]: [TOTEM ] A new membership
```

- **含义**：集群节点通信中断，触发重新选主（见 correlation-rules.md 规则 9）

---

## 错误模式 — Nginx / Apache

### 上游连接失败

```
connect() failed (111: Connection refused) while connecting to upstream
upstream timed out (110: Connection timed out) while reading response header
no live upstreams while connecting to upstream
```

- **关联影响**：前端返回 502/503，见 correlation-rules.md 规则 6

### 权限 / 配置错误

```
open() "<path>" failed (13: Permission denied)
directory index of "<path>" is forbidden
```

---

## 错误模式 — Kubernetes / Container

### Pod OOMKilled

```
OOMKilled
Reason: OOMKilled
Exit Code: 137
```

- **含义**：容器内存超限被杀
- **关联影响**：Pod 重启；重启次数超限则 CrashLoopBackOff

### CrashLoopBackOff

```
Back-off restarting failed container
CrashLoopBackOff
```

**诊断**：
```bash
kubectl describe pod <pod-name> -n <namespace>   # 查看 Events 和 Last State
kubectl logs <pod-name> --previous               # 查看上次崩溃日志
```

### 节点 NotReady

```
node/<node> condition: Ready=False
Taint node.kubernetes.io/not-ready
```

- **含义**：节点失联或资源耗尽，上面的 Pod 会被驱逐

---

## 分析决策树

```
Linux 问题
├── VM / 节点重启
│   ├── dmesg / syslog 查 Kernel Panic 或 OOM
│   ├── 查 last reboot / journalctl --since 确认重启时间
│   └── 若有 Azure Diagnostics → 查 platform reboot 事件
│
├── 服务不可用
│   ├── systemctl status <service> + journalctl -u <service>
│   ├── 检查 OOM（服务进程是否被 OOM Killer 终止）
│   └── 检查磁盘 I/O 错误（是否影响服务数据目录）
│
├── 集群切换 / Fencing
│   ├── corosync.log → 心跳是否超时
│   ├── pacemaker.log → fencing 操作确认
│   ├── 检查系统时钟（时间跳变可误触发 fencing，见 correlation-rules.md 规则 3）
│   └── 检查网络（NIC 状态变化，见规则 4）
│
├── Web 服务报错（502/503）
│   ├── nginx error.log → upstream 连接失败
│   ├── 追溯后端进程是否崩溃（OOM / 服务失败）
│   └── 见 correlation-rules.md 规则 6
│
└── 容器 / K8s 问题
    ├── kubectl describe pod → Events 查最近错误
    ├── kubectl logs --previous → 崩溃前最后日志
    └── kubectl top node/pod → 资源使用是否超限
```

---

## Azure Diagnostics 补充

### VM 平台重启

```json
"operationName": "Microsoft.Compute/virtualMachines/restart"
"status": "Succeeded"
"initiatedBy": "platform"
```

### 磁盘挂载失败

```json
"operationName": "Microsoft.Compute/virtualMachines/attachDataDisk"
"status": "Failed"
"error": { "code": "AttachDiskWhileBeingDetached" }
```

### RBAC 权限拒绝

```json
"authorization": { "action": "..." }
"properties": { "statusCode": "Forbidden" }
```
