# Windows VM Log Analysis Branch

> 本文件由 `log_analyzer` Step 1 在识别到 Windows VM 问题时加载。  
> 执行下方三步工作流，**替代**通用 Step 2-5。

---

## 公用信息

### 日志包类型速查

| 包类型 | 来源 | 典型内容 |
|---|---|---|
| **IID**（Inspect IaaS Disk） | Azure Support Center → VM → Diagnose and Solve → Inspect IaaS Disk | 事件日志、CBS.log、WU ETL、Netlogon.log、注册表导出、setupapi、SystemInfo |
| **TSS**（TroubleShooting Script） | 在 VM 内运行 TSS.ps1，按场景指定参数 | 场景专属日志（RDP/WU/AD 等）+ 网络信息 |
| **xray** | TSS 内嵌或独立运行 | 预分析结果（ISSUES-FOUND 文件），优先阅读 |

### 知识检索触发规则

| 情况 | 触发动作 |
|---|---|
| 遇到未识别的错误码 | 触发 `knowledge_search` → ADO Wiki + Microsoft Learn |
| 需要查找内部已知 Bug | 调用 `OSBugs` MCP（ADO Microsoft 项目，search work-items） |
| 需要查找内部 KB / 已解决案例 | 调用 `internalkb` MCP（ADO ContentIdea 项目，search） |

> `knowledge_search` 处理通用知识层；`OSBugs` 和 `internalkb` 是 Windows OS 专属，在本 branch 中直接调用。

---

## W-Step 1 — 分类路由

根据问题描述和截图，分类到以下场景之一，再跳转到对应 H3 章节：

| 场景 | 触发信号 | 跳转 |
|---|---|---|
| **RDP** | 无法连接 · 黑屏 · CredSSP · NLA · Remote Desktop | [§ RDP](#rdp) |
| **No Boot / BSOD** | VM 无法启动 · 蓝屏 · Stop Code · 0x... · 启动循环 · OS not found | [§ No Boot / BSOD](#no-boot--bsod) |
| **DND**（设备与部署） | Windows Update 失败 · KB 装不上 · CBS 报错 · 激活失败 · 驱动安装 · sysprep | [§ DND](#dnd) |
| **Directory Services** | 无法加域 · Netlogon 报错 · w32tm / 时间同步 · Kerberos 失败 | [§ Directory Services](#directory-services) |

若无法判断，询问用户澄清后再继续。

---

## W-Step 2 — 日志可用性评估

### 已有日志包时

扫描文件夹，识别以下关键文件：

```powershell
Get-ChildItem -Path "<LogPath>" -Recurse |
  Select-Object Name, Length, LastWriteTime |
  Sort-Object LastWriteTime -Descending
```

识别到 `xray_ISSUES-FOUND_*.txt` 时**优先阅读**，获取预分析结论后再深入原始日志。

### 无日志时

**首选**：通过 ASC 收集 IID 包（Inspect IaaS Disk）。  
**备选**（按场景）：

| 场景 | 快速收集命令 |
|---|---|
| DND / WU | `wevtutil epl Microsoft-Windows-WindowsUpdateClient/Operational C:\logs\wu.evtx` |
| DND / CBS | `copy C:\Windows\Logs\CBS\CBS.log C:\logs\` |
| RDP | `wevtutil epl Microsoft-Windows-TerminalServices-LocalSessionManager/Operational C:\logs\rdp.evtx` |
| No Boot | Azure 门户 → VM → Boot Diagnostics（截图） |
| Directory Services | `copy C:\Windows\debug\netlogon.log C:\logs\` && `w32tm /query /status > C:\logs\w32tm.txt` |

---

## W-Step 3 — 分析与报告

### 分析流程

1. **提取查询词**：从问题描述 + 错误截图中提取错误码、Event ID、KB 编号、症状关键词
2. **知识检索**（并发）：
   - `knowledge_search` → ADO Wiki + Microsoft Learn（通用知识层）
   - `OSBugs` → 搜索错误码 / 症状关键词（Windows OS 已知 Bug）
   - `internalkb` → 搜索错误码 / 症状关键词（内部 KB / 已解决案例）
3. **读取日志**：按对应场景章节的"优先读取日志"顺序分析，交叉比对知识检索结果
4. **输出 RCA 报告**

### RCA 报告格式

```
## Diagnosis: [场景] — [一句话根因]

**Confidence:** High / Medium / Low

### Root Cause
[清晰解释故障原因，引用日志证据 + 知识检索结论]

### Key Log Evidence
**[日志文件名，时间戳]**
```
[原始日志片段，保留原文、时间戳、错误码]
```
> 解释：[此条目说明什么，与根因的关联]

### Repair Steps
1. [可直接复制执行的命令]
2. [下一步]
3. [验证命令]

### References
- [mslearn / ADO Wiki] 文档标题 — URL — 与本案关联说明
- [OSBugs] Bug #XXXXX — 描述与状态
- [internalkb] 文章标题 — 描述
```

---

## RDP

### 优先读取日志

| 优先级 | 日志 / 文件 | IID/TSS 包路径 |
|---|---|---|
| 1 | LocalSessionManager 事件日志 | `*_evt_*TerminalServices*.txt/.csv` |
| 2 | System 事件日志 | `*_evt_System.txt` |
| 3 | Security 事件日志 | `*_evt_*Security*.txt` |
| 4 | 注册表：TermServices | `*_reg_TermServices.txt` |
| 5 | 网络 / 代理 | `*_NETWORK_Proxy.txt`, `*_NETWORK_TCPIP_info.txt` |

### 关键 Event ID

| EventID | Source | 含义 |
|---|---|---|
| 1149 | TerminalServices-LocalSessionManager | 用户已认证（RDP 预会话） |
| 21 | TerminalServices-LocalSessionManager | 会话登录成功 |
| 24 | TerminalServices-LocalSessionManager | 会话断开 |
| 40 | TerminalServices-LocalSessionManager | 会话断开 — reason code 是关键 |
| 1158 | TerminalServices-LocalSessionManager | 超出最大连接数 |
| 56 | TermDD | Terminal Device Driver 错误 |
| 4625 | Security | 登录失败 — 查 SubStatus |
| 4771 | Security | Kerberos 预认证失败 |

### 决策树

```
Cannot RDP
├── "Remote Desktop can't connect to the remote computer"
│   ├── RDP 是否启用？reg_TermServices.txt → fDenyTSConnections = 0 表示已启用
│   ├── 3389 端口是否监听？NETWORK_TCPIP_info.txt
│   └── 防火墙是否拦截 3389？（NSG 或 Windows Firewall）
│
├── "CredSSP / NLA / Oracle remediation"
│   ├── 客户端与服务端 CredSSP 补丁版本不匹配
│   └── 修复：客户端设 AllowEncryptionOracle = 2，或两端同时打补丁
│
├── 登录后黑屏
│   ├── Event 1149（认证成功）后紧跟 Event 40（断开）
│   ├── Explorer.exe 未启动（userinit/shell 注册表项损坏）
│   └── 服务端 GPU / 显示驱动问题
│
├── Event 56 / TermDD 错误
│   └── 通常由网络 MTU 不匹配或 NIC 绑定配置引起
│
└── 登录失败：0xC000006D / 0xC0000064
    ├── 凭据错误或账户被锁定
    └── Security 日志 Event 4625 SubStatus 给出精确原因
```

### 常见错误码

| 代码 | 含义 | 修复 |
|---|---|---|
| `0xC000006D` | 用户名/密码错误 | 验证凭据；检查账户锁定 |
| `0xC0000064` | 账户不存在 | 检查 SAM/AD 账户 |
| `0xC000006E` | 账户限制 | 检查登录时间 / 工作站限制 |
| `0x4` | NLA 认证失败 | 打 CredSSP 补丁或设 AllowEncryptionOracle |
| `0x204` | 连接被拒 / 端口关闭 | 启用 RDP，检查防火墙 |

### 关键注册表值

```
HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server
  fDenyTSConnections = 0    (0 = RDP 已启用)

HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp
  PortNumber = 3389

HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services
  (检查是否有 GPO 覆盖禁用了 RDP)
```

### 修复命令

```powershell
# 通过注册表启用 RDP
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name fDenyTSConnections -Value 0

# 通过 Windows 防火墙放行 RDP
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# 修复 CredSSP Oracle Remediation（在连接发起端执行）
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\CredSSP\Parameters" -Name AllowEncryptionOracle -Value 2

# 检查 RDP 服务状态
Get-Service TermService | Select-Object Status, StartType

# 启动 RDP 服务
Start-Service TermService
Set-Service TermService -StartupType Automatic
```

---

## No Boot / BSOD

### 优先读取日志

| 优先级 | 日志 / 文件 | IID/TSS 包路径 |
|---|---|---|
| 1 | System 事件日志 | `*_evt_System.txt` |
| 2 | BCD 输出 | `*_BCDEdit.txt` |
| 3 | CBS.log | `logs\CBS\CBS.log` |
| 4 | Boot Diagnostics 截图 | Azure 门户 → VM → Boot Diagnostics |
| 5 | Memory Dump | `%SystemRoot%\MEMORY.DMP` 或 `Minidump\*.dmp` |

### 截图快速分类

| 截图内容 | 可能的 Stop Code / 问题 |
|---|---|
| "INACCESSIBLE_BOOT_DEVICE" | 0x7B — 存储驱动缺失 |
| "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED" | 0x7E — 第三方驱动故障 |
| "PAGE_FAULT_IN_NONPAGED_AREA" | 0x50 — 内存/驱动损坏 |
| "CRITICAL_PROCESS_DIED" | 0xEF — 关键系统进程崩溃 |
| Winload 错误 / 0xC0000034 / 0xC0000098 | BCD/winload 损坏 |
| 黑屏无文字、旋转圆圈 | 启动卡住 — 检查 Event 41 |
| "Getting Windows ready" 卡住 | WU 安装中途中断 |

### 关键 Event ID

| EventID | Source | 含义 |
|---|---|---|
| 41 | Kernel-Power | 非预期重启 — 查 BugcheckCode 参数 |
| 6008 | EventLog | 上次意外关机 |
| 1001 | BugCheck | BSOD 记录 — 含 Stop Code + 4 个参数 |
| 6 | BugCheck | Dump 文件已写入磁盘 |

### 常见 Stop Code

| Stop Code | 名称 | 常见原因 |
|---|---|---|
| `0x7B` | INACCESSIBLE_BOOT_DEVICE | VM 系列变更后存储驱动缺失 |
| `0x7E` | SYSTEM_THREAD_EXCEPTION | 第三方驱动（参数 2 = 故障模块地址） |
| `0x50` | PAGE_FAULT_IN_NONPAGED_AREA | 驱动或内存损坏 |
| `0x0A` | IRQL_NOT_LESS_OR_EQUAL | 驱动 IRQ 违规 |
| `0xEF` | CRITICAL_PROCESS_DIED | 关键 OS 进程终止 |
| `0xC0000034` | — | BCD 对象未找到 |
| `0xC0000098` | — | winload.efi 缺失或损坏 |
| `0xC000021A` | STATUS_SYSTEM_PROCESS_TERMINATED | Winlogon/CSRSS 崩溃 |

### 决策树

```
VM 无法启动 / BSOD
├── Boot Diagnostics 显示 Stop Code
│   ├── 0x7B INACCESSIBLE_BOOT_DEVICE
│   │   ├── VM 系列变更后存储控制器驱动缺失
│   │   └── 修复：在注册表中启用 storahci/storport（Start = 0）或离线 DISM 注入驱动
│   ├── 0xC0000034 / 0xC0000098（BCD/winload 错误）
│   │   ├── BCD 损坏或设备/路径配置错误
│   │   └── 修复：从 WinRE 重建 BCD（bcdedit /rebuildbcd）
│   ├── 0x7E SYSTEM_THREAD_EXCEPTION_NOT_HANDLED
│   │   └── 第三方驱动故障；参数 2 = 故障模块地址
│   ├── 0x50 PAGE_FAULT_IN_NONPAGED_AREA
│   │   └── 内存损坏或驱动问题；需分析 dump
│   └── 0xC000021A STATUS_SYSTEM_PROCESS_TERMINATED
│       └── Winlogon 或 CSRSS 崩溃 — 检查 CBS.log 是否有失败的更新
│
├── 卡在 "Getting Windows ready" / 旋转圆圈
│   ├── Windows Update 安装中途中断
│   ├── 检查 CBS.log 中未完成的 servicing 事务
│   └── 修复：WinRE → DISM /remove-package 卸载最近的更新
│
├── OS not found / 无可引导设备
│   ├── MBR/VBR 损坏或活动分区设置错误
│   └── 修复：bootrec /fixmbr, /fixboot, /rebuildbcd（从 WinRE）
│
└── 重启循环（立即重启，无报错）
    ├── 检查 Event 41（Kernel-Power）和 Event 6008
    └── 通常需要 dump 分析确定故障模块
```

### 修复命令（WinRE / 恢复 CMD 中执行）

```cmd
REM 重建 BCD
bcdedit /export C:\BCD_Backup
bcdedit /rebuildbcd

REM 修复 MBR/Boot（MBR 磁盘）
bootrec /fixmbr
bootrec /fixboot
bootrec /rebuildbcd

REM 启用关键存储驱动（0x7B 修复 — 对离线 OS 执行）
reg load HKLM\BROKENSYSTEM C:\Windows\System32\config\SYSTEM
reg add "HKLM\BROKENSYSTEM\ControlSet001\Services\storahci" /v Start /t REG_DWORD /d 0 /f
reg add "HKLM\BROKENSYSTEM\ControlSet001\Services\storport" /v Start /t REG_DWORD /d 0 /f
reg add "HKLM\BROKENSYSTEM\ControlSet001\Services\stornvme" /v Start /t REG_DWORD /d 0 /f
reg unload HKLM\BROKENSYSTEM

REM 卸载最近更新（从 WinRE，用于 spinner 卡住）
dism /image:C:\ /get-packages | findstr Package_for_KB
dism /image:C:\ /remove-package /packagename:<PackageName>

REM 对离线镜像修复组件存储
dism /image:C:\ /cleanup-image /restorehealth /source:D:\sources\install.wim
```

---

## DND

> 覆盖：Windows Update 失败、CBS/组件存储损坏、激活失败、驱动安装失败、sysprep 错误

### 优先读取日志

| 优先级 | 日志 / 文件 | 重点查找 |
|---|---|---|
| 1 | Setup 事件日志 | `*_evt_Setup.txt` — WUSA 错误、Servicing Events 1013/1014/1015 |
| 2 | CBS.log | `logs\CBS\CBS.log` — HRESULT 错误、"Failed to" 条目 |
| 3 | WU ETL 转换日志 | `*_WindowsUpdateETL_Converted.log` — 更新标题、错误码、DeploymentAction |
| 4 | WU 报告日志 | `*_WindowsUpdate_ReportingEvents.log` — 每个 KB 的最终安装状态 |
| 5 | DISM 日志 | `logs\DISM\dism.log` |
| 6 | DISM CheckHealth | `*_dism_CheckHealth.txt` |
| 7 | xray ISSUES-FOUND | `xray_ISSUES-FOUND_*.txt` — 优先阅读（预分析结果） |
| 8 | Summary | `*__SUMMARY.TXT` — OS 版本、最近重启、最后安装的更新 |

### 关键 Event ID

| EventID | Source | 含义 |
|---|---|---|
| 1013 | Microsoft-Windows-Servicing | CBS 损坏扫描开始 |
| 1014 | Microsoft-Windows-Servicing | CBS 损坏扫描完成 — 比较 "repaired" vs "found" 数量 |
| 1015 | Microsoft-Windows-Servicing | **警告：损坏未修复** — 阻塞后续 servicing |
| 19 | WindowsUpdateClient | 更新安装成功 |
| 20 | WindowsUpdateClient | 更新安装失败 |

### 常见错误码

| HRESULT | 十六进制 | 含义 |
|---|---|---|
| — | `0x800F0838` | CBS_E_MANIFEST_INVALID — CBS 损坏 |
| — | `0x80070005` | 访问被拒绝（TrustedInstaller） |
| — | `0x80070002` | 文件未找到 |
| — | `0x8024200D` | WU 数据库损坏 |
| — | `0x80072EE2` | 网络超时，无法访问 WU |
| — | `0x800F09DE` | 挂起重启阻塞 servicing |
| — | `0x800F080C` | CBS_E_UNKNOWN_UPDATE — 组件未识别 |

### 决策树

```
DND 问题
├── Windows Update KB 安装失败
│   ├── 0x800F0838 → CBS 损坏（见下方 CBS 分支）
│   ├── 0x80070005 → TrustedInstaller 未运行或权限丢失
│   │   修复：sc config TrustedInstaller start= auto && net start TrustedInstaller
│   ├── 0x8024200D / 0x80242006 → WU 数据库损坏
│   │   修复：重置 SoftwareDistribution 文件夹
│   ├── 0x80072EE2 / 0x8024402C → 网络超时
│   │   检查：代理和防火墙是否阻拦 WU 端点
│   ├── 0x80070002 → 源文件缺失
│   │   修复：先运行 SFC /scannow
│   └── 0x800F09DE / 0x800F0922 → 需要重启
│       修复：重启后重试
│
├── CBS / 组件存储损坏
│   ├── Event 1015（损坏未修复）
│   │   步骤 1：DISM /Online /Cleanup-Image /RestoreHealth
│   │   步骤 2：DISM /Source:WIM /LimitAccess（如步骤 1 失败）
│   │   步骤 3：SFC /scannow
│   │   步骤 4（最后手段）：原地修复升级 Setup.exe /auto upgrade
│   └── CBS.log 中反复出现 0x800F080C
│       → Foundation Package 未识别，需重建组件存储
│
├── 激活失败
│   ├── 0x8007232B → KMS 主机不可达（DNS SRV 记录无法解析）
│   ├── 0xC004F074 → KMS 主机可访问但无法连接（检查 1688 端口）
│   └── 0xC004C008 → MAK 密钥已用尽（联系许可团队）
│
├── 驱动安装失败
│   ├── 检查 setupapi.dev.log 中安装时间戳附近的 "error" 条目
│   ├── Event 219（驱动加载失败）、Event 7026（启动时驱动未启动）
│   └── 修复：DISM 离线注入驱动
│
└── Sysprep 失败
    ├── 检查 %WINDIR%\System32\Sysprep\Panther\setupact.log + setuperr.log
    ├── 常见原因：Store 应用未为通用化准备好
    └── 修复：sysprep 前先移除问题应用包
```

### 修复命令

```powershell
# CBS / 组件存储修复
DISM /Online /Cleanup-Image /RestoreHealth
DISM /Online /Cleanup-Image /RestoreHealth /Source:D:\sources\install.wim /LimitAccess
DISM /Online /Cleanup-Image /ScanHealth
sfc /scannow

# Windows Update 重置
net stop wuauserv; net stop cryptSvc; net stop bits; net stop msiserver
Rename-Item C:\Windows\SoftwareDistribution SoftwareDistribution.old
Rename-Item C:\Windows\System32\catroot2 catroot2.old
net start wuauserv; net start cryptSvc; net start bits; net start msiserver

# 激活诊断与修复
slmgr /dli
slmgr /xpr
slmgr /skms <kmshost>:1688
slmgr /ato
Test-NetConnection -ComputerName <kmshost> -Port 1688

# TrustedInstaller 修复
sc config TrustedInstaller start= auto
net start TrustedInstaller

# 原地修复升级（最后手段，挂载 ISO 为 D:）
D:\setup.exe /auto upgrade /DynamicUpdate disable
```

---

## Directory Services

> 覆盖：AD 域加入失败、Netlogon 安全通道中断、w32tm 时间同步问题

### 优先读取日志

| 优先级 | 日志 / 文件 | IID/TSS 包路径 |
|---|---|---|
| 1 | Netlogon.log | `logs\NetSetup\netlogon.log` 或 `C:\Windows\debug\netlogon.log` |
| 2 | System 事件日志 | `*_evt_System.txt` — EventID 5719, 3210, 1129, 29, 36, 47 |
| 3 | DSRegCmd 输出 | `*_DSregCmd.txt` — 设备/域加入状态 |
| 4 | 网络信息 | `*_NETWORK_TCPIP_info.txt` — DNS 服务器设置（关键） |
| 5 | DNS 客户端缓存 | `*_NETWORK_DnsClient_ipconfig-displaydns.txt` |

### 关键 Event ID

| EventID | Source | 含义 |
|---|---|---|
| 5719 | NETLOGON | 无法建立到 DC 的安全通道 |
| 3210 | NETLOGON | 与 DC 认证失败 |
| 5722 | NETLOGON | DC 端计算机账户密码不匹配 |
| 1129 | GroupPolicy | 组策略处理失败 — DC 不可达 |
| 29 | W32Time | NTP 源不可访问 |
| 36 | W32Time | 时间同步超过 X 秒未成功 |
| 47 | W32Time | 已配置的 NTP Peer 无有效响应 |

### Netlogon.log 关键模式

```
# DC 发现失败（DNS 问题）
[CRITICAL] [domain] DsGetDcName: NO entry found: Status = 0x54B (ERROR_NO_SUCH_DOMAIN)

# 安全通道密码不匹配
[LOGON] [domain] NO_TRUST_SAM_ACCOUNT

# 认证失败
[LOGON] [domain] 0xC000006D  (STATUS_LOGON_FAILURE)

# DC 发现成功（基线参考）
[MISC] DsGetDcName called: flags: 0x40001010 domain: <name> -> found DC: \\<DC-name>
```

### 域加入失败决策树

```
域加入失败
├── "指定域不存在或无法联系"
│   ├── DNS 无法解析域名
│   │   检查：TCPIP_info.txt 中 DNS 服务器必须是 DC IP，不能是 8.8.8.8
│   │   修复：将 DNS 指向域控制器 IP
│   └── 网络无法到达 DC（389/88/445/3268 端口被拦截）
│       修复：更新 NSG / 防火墙规则
│
├── "账户已存在" / NERR_SetupAlreadyJoined (0x8b)
│   ├── AD 中存在密码不匹配的旧计算机账户
│   │   修复 1：在 ADUC 中删除计算机账户后重新加入
│   │   修复 2：netdom resetpwd /server:<DC> /ud:<admin> /pd:*
│   └── 检查 Netlogon.log：NO_TRUST_SAM_ACCOUNT 或 WRONG_PASSWORD
│
├── "访问被拒绝" / 0x5
│   ├── 加入账户缺少 OU 加入权限
│   └── 用户已达到 10 台机器加入限制（域默认策略）
│       修复：委派 OU 的"创建计算机对象"权限，或使用管理员账户
│
└── 加入成功但认证失败
    ├── Event 5719：安全通道中断
    │   修复 1：nltest /sc_reset:<domain>
    │   修复 2：netdom resetpwd /server:<DC> /ud:<domain>\<admin> /pd:*
    └── 时间偏移 > 5 分钟（Kerberos 硬限制）
        → 必须先修复 Windows Time 同步（见下方 §w32tm）
```

### w32tm 时间同步决策树

```
Windows Time 不同步
├── w32tm /query /status 显示 "Last Successful Sync Time: never" 或时间戳过旧
│   ├── W32Time 服务未运行 → net start w32time
│   └── NTP 源不可达（UDP 123 被防火墙阻拦）
│       检查：Test-NetConnection <NTP-server> -Port 123
│
├── Event 29：NTP 源不可访问
│   修复：w32tm /config /manualpeerlist:"time.windows.com,0x8" /syncfromflags:manual /update
│
├── Event 47：配置的 NTP Peer 无响应
│   ├── NTP 服务器地址配置错误
│   └── NSG / 防火墙阻拦 UDP 123
│
├── 时间偏移大（导致 Kerberos 失败，5 分钟硬限制）
│   ├── 强制立即同步：w32tm /resync /force
│   └── 若偏移 > 5 分钟，先手动设时：Set-Date -Date "<UTC 正确时间>"
│
└── 域成员 VM 未从 DC 同步
    ├── 预期层级：域成员 → DC → PDC Emulator → 外部 NTP
    ├── 检查：w32tm /query /source → 应显示 DC 名称，而非 "Local CMOS Clock"
    └── 修复：w32tm /config /syncfromflags:domhier /update && w32tm /resync /rediscover
```

### 修复命令

```powershell
# 诊断
nltest /dsgetdc:<domain.com>
nltest /sc_verify:<domain.com>

# 测试到 DC 的必需端口
Test-NetConnection -ComputerName <DC-IP> -Port 389   # LDAP
Test-NetConnection -ComputerName <DC-IP> -Port 88    # Kerberos
Test-NetConnection -ComputerName <DC-IP> -Port 445   # SMB
Test-NetConnection -ComputerName <DC-IP> -Port 3268  # Global Catalog
Test-NetConnection -ComputerName <DC-IP> -Port 135   # RPC

# 测试 SRV DNS 记录
Resolve-DnsName -Name _ldap._tcp.dc._msdcs.<domain.com> -Type SRV
Resolve-DnsName -Name _kerberos._tcp.dc._msdcs.<domain.com> -Type SRV

# 重置安全通道（无需重启）
nltest /sc_reset:<domain.com>
netdom resetpwd /server:<DC-name> /ud:<domain>\<admin> /pd:*

# 重新加入域（需重启）
$cred = Get-Credential
Remove-Computer -UnjoinDomainCredential $cred -Force
Add-Computer -DomainName <domain.com> -Credential $cred -OUPath "OU=Servers,DC=domain,DC=com" -Force -Restart

# w32tm 诊断与修复
w32tm /query /status
w32tm /query /source
w32tm /resync /force
w32tm /config /manualpeerlist:"time.windows.com,0x8" /syncfromflags:manual /update
w32tm /config /syncfromflags:domhier /update && w32tm /resync /rediscover
```
