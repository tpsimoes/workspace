---
name: kusto_query
description: "Azure infrastructure investigation via Kusto (KQL) queries across internal clusters (AzureCM, Disks RP, VMInsight, AzCore, AzureDCM, Sparkle, Hawkeye, ICM, Watson, AzPE, AzureAllocator). Use when the user mentions: Kusto, KQL, VM restart/reboot investigation, disk lifecycle, node fault, service healing, live migration, hardware failure, host update, datapath version, NmAgent, or any query against Azure internal telemetry clusters. Also use when the user asks to investigate a VM availability issue, generate an RCA report, run infrastructure diagnostics, or look up cluster/table schema. Always prefer Kusto MCP (microsoft-fabric-rti-mcp) for query execution; fall back to Python scripts only when MCP is unavailable or batch automation is required."
context: fork 
compatibility: Requires Kusto MCP (microsoft-fabric-rti-mcp) + ADO MCP
---
# Creator: Jack DONG
# Kusto Query Skill — Azure Infrastructure Investigation

## Knowledge Sources

| File | Purpose |
|------|---------|、



| `references/kql-language.md` | KQL operators, patterns, best practices |
| `references/catalog-AzureIaaSVM.md` | Cluster/database/table schema reference + ready-to-use KQL query templates for all scenarios (§Query Templates) |
| `references/catalog-custom.md` | User-defined additions, overrides, and scenario-specific query samples |
| `scripts/kusto_runner.py` | General-purpose single-query runner (--cluster --database --query) |
| `scripts/kusto_vm_investigate.py` | Automated 9-step VM investigation (--subscription-id --vm-name) |
| `scripts/kusto_disk_investigate.py` | Automated 4-step disk investigation (--subscription-id --disk-name) |
| `scripts/kusto_catalog_builder.py` | Rebuild catalog from ADO wiki |

---

## Natural Language Routing (Cluster/DB Semantics)

Use this mapping when the user gives intent in natural language instead of explicit table names.

| User wording / intent | Route to Cluster.DB first | Why this route | First table(s) to check |
|-----------------------|---------------------------|----------------|-------------------------|
| "VM 重启/掉线/不可用/SSH-RDP failed" | `Azcsupfollower.AzureCM` | Fabric-side lifecycle and downtime ground truth | `LogContainerSnapshot`, `LogContainerHealthSnapshot`, `TMMgmtRoleInstanceDowntimeEventEtwTable` |
| "同一时段是否平台操作"、"平台重启" | `Azcsupfollower.AzureCM` | Platform action/fault/recovery timeline | `KronoxVmOperationEvent`, `TMMgmtNodeFaultEtwTable`, `FaultHandlingRecoveryEventEtwTable` |
| "RCA 分类/过去30天是否反复" | `vmainsight.vmadb` | RCA engine output and historical impact | `VMA`, `VMALENS` |
| "宿主机更新/NmAgent/维护引发" | `vmainsight.Air` then `azpe.azpe` | Air gives update/outage timeline; AzPE gives OM workflow | `AirMaintenanceEvents`, `AirManagedEvents`, `AzPEWorkflowEvent` |
| "HyperV/宿主机Windows事件/性能" | `azcore.centralus.Fa` | RDOS host telemetry and HyperV logs | `HyperVAnalyticEvents`, `WindowsEventTable`, `VmCounterFiveMinuteRoleInstanceCentralBondTable` |
| "硬件故障/内存ECC/WHEA/SEL" | `azuredcm.AzureDCMDb` then `sparkle.eastus.defaultdb` | DCM for inventory+repair, Sparkle for hardware error evidence | `ResourceSnapshotHistoryV2`, `FaultCodeTeamMapping`, `SparkleSELByNodeId(...)` |
| "磁盘 I/O 层故障/XStore outage/IaaSxStoreOutage/云盘失联重启" | `Azcsupfollower.AzureCM` → `vmainsight.vmadb` | I/O 层存储故障的证据在 faultInfo (AzureCM) 和 VMA RCA 引擎中；**不要**先查 disks.Disks | `LogContainerHealthSnapshot` (faultInfo), `VMA`, `VMALENS` |
| "磁盘资源生命周期/attach detach/盘是否存在/磁盘资源删除" | `disks.Disks` | Disk RP 资源级别生命周期和后端存在性 | `DiskRPResourceLifecycleEvent`, `DiskManagerApiQoSEvent` |
| "管控面正常但SSH/Ping断连/heartbeat正常但外部不可达/VM看似alive但网络不通" | `vmainsight.Vmadiag` → `Azcsupfollower.AzureCM` | VFP 静默失败会使 heartbeat 保持 Healthy 而数据面断连；需区分管控面与数据面 | `Atlas_VmStateTransitionEvent`, `vfp_restore_fails`, `EventData_SDN_DataPath` |
| "维护通知/客户是否收到通知" | `icmcluster.ACM.Publisher/Backend` | Communication source of truth | `GetCommunicationsForSupport(...)`, `PublishRequest` |

### Disambiguation Rules (Important)

1. **Always identify VM identity first** via `LogContainerSnapshot` to get `containerId`, `nodeId`, `tenantName`.
2. **Do not treat same-node events as same-VM events** unless `ContainerId` or `RoleInstanceName` matches target VM.
3. If user says **"节点异常"** but asks impact to one VM, query node-level tables and VM-level tables in parallel, then intersect by time + VM identity.
4. If user asks **"是否客户可感知"**, prioritize downtime/health state tables before deep RCA tables.
5. If user gives only **resourceId**, first parse `{SubscriptionId}/{ResourceGroupName}/{VMName}` then map to internal IDs.
6. **管控面 vs 数据面判断**：若 VM heartbeat/WireServer 正常（LogContainerHealthSnapshot 不含 faultInfo，VMA 无 RCA 事件）但 SSH/Ping/RDP 断连，优先考虑 VFP/SDN 数据平面故障，转向 `vmainsight.Vmadiag.Atlas_VmStateTransitionEvent` 和 `vfp_restore_fails`，而非继续深挖 AzureCM。
7. **磁盘故障二义性**："磁盘相关" 问题需先判断是 I/O 层故障（XStore/IaaSxStoreOutage，证据在 AzureCM）还是资源层问题（attach/detach/盘不存在，证据在 disks.Disks），两者使用完全不同的表。

### Natural Language Input Templates (for stable auto-routing)

Use or adapt these sentence patterns when requesting investigations.

1. **VM可用性 / 重启类**
    - "帮我查 VM `{VMName}` 在 UTC `{Start}` 到 `{End}` 是否有重启/掉线，给出平台侧证据。"
    - Expected route: `Azcsupfollower.AzureCM` → `vmainsight.vmadb` (if RCA needed)

2. **平台操作归因类**
    - "看 VM `{VMName}` 在 `{Start}~{End}` 是否存在平台触发操作（reboot/redeploy/live migration）。"
    - Expected route: `Azcsupfollower.AzureCM`

3. **宿主机更新 / NmAgent 类**
    - "分析节点 `{NodeId}` 在 `{Start}~{End}` 的 NMAgent/HostNetworking 更新是否影响 VM `{VMName}`。"
    - Expected route: `vmainsight.Air` + `azpe.azpe`

4. **硬件根因类（WHEA/SEL）**
    - "排查节点 `{NodeId}` 在 `{Start}~{End}` 的硬件故障，重点看 WHEA/SEL/ECC。"
    - Expected route: `azuredcm.AzureDCMDb` + `sparkle.eastus.defaultdb`

5. **磁盘生命周期类**
    - "检查磁盘 `{DiskName}` 在订阅 `{SubscriptionId}` 的生命周期和当前是否存在。"
    - Expected route: `disks.Disks`

6. **维护通知 / 客户影响类**
    - "查订阅 `{SubscriptionId}` 在 `{Start}~{End}` 是否收到维护或故障通知，是否客户可感知。"
    - Expected route: `icmcluster.ACM.Publisher/Backend` (optionally `Azdeployer.AzDeployerKusto`)

7. **最稳妥通用模板（建议优先）**
    - "目标对象: `{VMName|NodeId|DiskName}`；时间: `{Start}~{End}` UTC；问题类型: `{availability|platform action|hardware|disk|maintenance}`；
        输出要求: `{是否客户可感知 + 证据表名 + 时间线 + 结论}`。"

---

## Workflow

### Step 1 — Identify Scenario

| Scenario | Query Templates | Primary Clusters |
|----------|----------------|-----------------|
| VM restart / availability | `catalog-AzureIaaSVM.md` §AzureCM — Container State + §AzureCM — Node Fault | Azcsupfollower, vmainsight |
| Live Migration | `catalog-AzureIaaSVM.md` §AzureCM — Live Migration | Azcsupfollower |
| VMA RCA & 30-day impact | `catalog-AzureIaaSVM.md` §vmainsight — VMA RCA & Air Events | vmainsight |
| **管控面正常但数据面断连（VFP/SDN故障）** | `catalog-custom.md` §Atlas_VmStateTransitionEvent + §vfp_restore_fails | vmainsight.Vmadiag, Azcsupfollower |
| Node hardware failure | `catalog-AzureIaaSVM.md` §AzureDCM + §Sparkle | AzureDCM, sparkle |
| HyperV / RDOS / host OS | `catalog-AzureIaaSVM.md` §AzCore | azcore.centralus |
| Unhealthy node RCA | `catalog-AzureIaaSVM.md` §Hawkeye | hawkeyedataexplorer |
| Host bugcheck | `catalog-AzureIaaSVM.md` §Watson | Azurewatsoncustomer |
| Host update / NMAgent | `catalog-AzureIaaSVM.md` §vmainsight — Combined host update + §AzPE | vmainsight, azpe |
| Maintenance / notifications | `catalog-AzureIaaSVM.md` §Maintenance & Customer Notifications | icmcluster |
| **磁盘 I/O 层存储故障（XStore/IaaSxStoreOutage）** | `catalog-custom.md` §LogContainerHealthSnapshot faultInfo | Azcsupfollower, vmainsight |
| Disk RP 资源生命周期（attach/detach/盘存在性） | `catalog-AzureIaaSVM.md` §Disks RP — Managed Disk Lifecycle | disks |
| VM 身份变化历史（Redeploy/Migration 次数） | `catalog-custom.md` §VM Identity Change History | Azcsupfollower |
| Schema / catalog lookup | `catalog-AzureIaaSVM.md` + `catalog-custom.md` | — |
| Ad-hoc / custom query | `kql-language.md` | user-specified |

### Step 2 — Build Query

1. **Check query templates first** — look up `catalog-AzureIaaSVM.md` §Query Templates for ready-to-use KQL patterns (organized by cluster/scenario)
2. If no template matches, look up table name and key columns in `catalog-AzureIaaSVM.md` §Cluster Reference or `catalog-custom.md`
3. Apply patterns from `references/kql-language.md`:
   - Always filter by `PreciseTimeStamp` first
   - Use `let` blocks for variables and cross-cluster lookups
   - Prefer `has` over `contains` for string searches
   - Put the smaller table on the LEFT side of a `join`

### Step 3 — Execute and Show

**Execute the query immediately via Kusto MCP — do not ask for confirmation before running.** Display the KQL alongside the results so the user can review. Investigation is time-sensitive and results provide context to evaluate the query itself.

**Exception**: Ask for confirmation before any write operation (ICM comment, ADO update, etc.).

Format output as:

```
**Query** (`{cluster}/{database}`):
\```kusto
{KQL}
\```
**Results**: {table or summary}
```

### Step 4 — Execute

Two options — show both and let the user choose:

```bash
# Option A: Kusto MCP (interactive, results in chat)
# [Use kusto_query MCP tool directly]

# Option B: Python script (for saving results or batch runs)
python scripts/kusto_runner.py \
    --cluster https://{cluster}.kusto.windows.net \
    --database {db} \
    --query "{KQL}" \
    --format table
```

For full automated investigation, use the dedicated scripts:

```bash
# Automated 9-step VM investigation
python scripts/kusto_vm_investigate.py \
    --subscription-id {SubscriptionId} \
    --vm-name {VMName} \
    --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# Automated 4-step disk investigation
python scripts/kusto_disk_investigate.py \
    --subscription-id {SubscriptionId} \
    --disk-name {DiskName} \
    [--lookback-days 90]
```

### Step 5 — Summarize / RCA

Present findings using the RCA template. Adapt sections as needed.

---

## RCA Report Template

```
## VM Availability

The Azure monitoring and diagnostics systems identified that the VM **{VMName}**
was impacted at **{StartTime}**. During this time, RDP/SSH connections or other
requests to the VM could have failed.

## Root Cause

{One-paragraph root cause based on query findings. Reference specific evidence:
fault codes, node state transitions, recovery actions, hardware errors, etc.}

## Resolution

{How service was restored — e.g., node reboot, service healing, live migration,
hardware replacement, etc. Include timestamps where available.}

## Timeline

| Time (UTC) | Event |
|------------|-------|
| {timestamp} | {event description} |

## Additional Information

{Relevant context: whether the node was marked for repair, other VMs on same node
affected, platform improvement efforts, etc.}

## Recommended Documents

- [Auto-recovery of Virtual Machines](https://aka.ms/vmrestartfaq)
- [Configure availability of virtual machines](https://aka.ms/vmavailability)
- [Maintenance and updates for virtual machines in Azure](https://aka.ms/vmmaintenance)
```

---

## Variable Convention

All query templates use these standardized placeholders:

| Placeholder | Description |
|-------------|-------------|
| `{NodeId}` | Physical host node GUID |
| `{ContainerId}` | Container (VM fabric) GUID |
| `{VMName}` | Role instance name (e.g. `web_IN_0`) |
| `{VMId}` | Virtual machine unique ID |
| `{TenantName}` | Fabric tenant name |
| `{Cluster}` | Fabric cluster name |
| `{SubscriptionId}` | Azure subscription GUID |
| `{ResourceGroupName}` | Resource group name |
| `{BeginTime}` / `{EndTime}` | Format: `2025-03-01 10:00:00Z` |
| `{LMSessionId}` | Live Migration session ID |

Extract from Resource ID:
```kusto
let MyResourceID = "{Resource_id}";
let SubID       = tostring(split(MyResourceID, "/")[2]);
let ResourceGrp = tostring(split(MyResourceID, "/")[4]);
let VMName      = tostring(split(MyResourceID, "/")[-1]);
```

---

## Catalog Maintenance

### Add a new entry manually

Edit `references/catalog-custom.md` — follow the template at the top of that file.

### Rebuild catalog from ADO wiki

```bash
# Rebuild AzureIaaSVM catalog
python scripts/kusto_catalog_builder.py --wiki-project AzureIaaSVM

# Add a second project
python scripts/kusto_catalog_builder.py --wiki-project <OtherProject>
# → creates references/catalog-<OtherProject>.md
```

### When to rebuild

- New clusters/tables appear in AzureIaaSVM wiki
- Access instructions have changed
- You onboard to a new ADO wiki project

---

## Clusters Quick Reference

| Alias | URI | Database | Purpose |
|-------|-----|----------|---------|
| Azcsupfollower | `Azcsupfollower.kusto.windows.net` | AzureCM | Container/node lifecycle (follower, use this) |
| azurecm | `azurecm.kusto.windows.net` | AzureCM | Same — prod direct |
| vmainsight | `vmainsight.kusto.windows.net` | vmadb, Air | VMA RCA, node health, Air events |
| vmainsight.Vmadiag | `vmainsight.kusto.windows.net` | Vmadiag | VM-Host heartbeat state transitions; VFP/networking data-plane diagnosis |
| azcore | `azcore.centralus.kusto.windows.net` | Fa | RDOS: HyperV, Windows events, perf |
| AzureDCM | `azuredcm.kusto.windows.net` | AzureDCMDb | Hardware inventory, repair |
| sparkle | `sparkle.eastus.kusto.windows.net` | defaultdb | WHEA/SEL hardware errors |
| hawkeye | `hawkeyedataexplorer.westus2.kusto.windows.net` | HawkeyeLogs | Automated unhealthy node RCA |
| icmcluster | `icmcluster.kusto.windows.net` | ACM.Publisher, ACM.Backend | Customer notifications |
| Watson | `Azurewatsoncustomer.kusto.windows.net` | AzureWatsonCustomer | Host bugcheck |
| azpe | `azpe.kusto.windows.net` | azpe | Host update workflow |
| APlat | `aplat.westcentralus.kusto.windows.net` | APlat | Anvil/Tardigrade service healing |
| Gandalf | `gandalf.kusto.windows.net` | gandalf | Unallocatable node detection |
| disks | `disks.kusto.windows.net` | Disks | Managed disk lifecycle |
| azcsupfollower2 | `azcsupfollower2.centralus.kusto.windows.net` | crp_allprod | CRP API operations |
| Azdeployer | `Azdeployer.kusto.windows.net` | AzDeployerKusto | Planned maintenance |
| azureallocator | `azureallocator.westcentralus.kusto.windows.net` | AzureAllocator | VM allocation capacity |
| azsh | `azsh.kusto.windows.net` | azshmds | Resource Health |

All clusters require **Microsoft Corp tenant** (`72f988bf-86f1-41af-91ab-2d7cd011db47`).

---

## VM Restart Investigation Flow

1. `LogContainerSnapshot` → get containerId, nodeId, tenantName
2. `LogContainerHealthSnapshot` → VM health state changes
3. `TMMgmtNodeStateChangedEtwTable` → node reboot confirmation
4. `TMMgmtNodeEventsEtwTable` → dirty shutdown, bugcheck, operations
5. `TMMgmtRoleInstanceDowntimeEventEtwTable` → downtime events
6. `TMMgmtTenantEventsEtwTable` → fabric-triggered operations, OOM, LM
7. `TMMgmtNodeFaultEtwTable` → node-level faults
8. `FaultHandlingContainerFaultEventEtwTable` → container faults
9. `FaultHandlingRecoveryEventEtwTable` → recovery actions (PowerCycle, etc.)
10. `ServiceHealingTriggerEtwTable` → service healing triggers
11. `VMA` / `VMALENS` (vmadb) → RCA category + 30-day impact history
12. For deeper: hardware (§azuredcm), HyperV (§azcore), Hawkeye (§hawkeye), Watson (§Azurewatsoncustomer)
