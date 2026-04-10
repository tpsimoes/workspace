# Kusto Catalog — AzureIaaSVM Wiki

Source: AzureIaaSVM ADO Wiki (`/Tools/Kusto/Kusto Tables_Tool`, `/Tools/Kusto/Kusto Endpoints_Tool`, `/Tools/Kusto/Kusto Tables Control Plane_Tool`)
Last synced: 2026-03-03

> Use `scripts/kusto_catalog_builder.py --wiki-project AzureIaaSVM` to refresh this file.

---

## Natural Language Semantic Glossary (for Agent Routing)

Use this section as a quick dictionary from user language to cluster/database.

| User natural language cues | Cluster.DB | Typical interpretation |
|----------------------------|------------|------------------------|
| VM 重启、宕机、不可达、连接失败、掉线 | `Azcsupfollower.AzureCM` | Fabric lifecycle/health/downtime truth |
| 服务愈合、自动恢复、平台修复、故障恢复 | `Azcsupfollower.AzureCM` + `aplat.westcentralus.APlat` | FaultHandling + ServiceHealing + Anvil actions |
| Live Migration、迁移抖动、平台迁移 | `Azcsupfollower.AzureCM` | LM session and migration timeline |
| RCA 等级、过去30天是否复发、可用性趋势 | `vmainsight.vmadb` | VMA/VMALENS RCA classification |
| 主机更新、NMAgent、HostNetworking、brownout | `vmainsight.Air` + `azpe.azpe` | Update events + OM workflow |
| HyperV、宿主机事件、性能抖动、内存压力 | `azcore.centralus.Fa` | RDOS host telemetry |
| 硬件告警、WHEA、SEL、ECC、BMC | `azuredcm.AzureDCMDb` + `sparkle.eastus.defaultdb` | Hardware inventory/repair + raw hardware errors |
| 磁盘生命周期、盘不存在、attach/detach失败 | `disks.Disks` | Disk RP lifecycle + backend existence |
| 维护通知、客户通知、communication | `icmcluster.ACM.Publisher/Backend` + `Azdeployer.AzDeployerKusto` | Planned maintenance communications |
| bugcheck、蓝屏、watson | `Azurewatsoncustomer.AzureWatsonCustomer` | Crash evidence and dump analysis |

### Interpretation Priority

1. If both VM-level and node-level cues appear, prioritize **VM-level truth first** (`containerId`, `RoleInstanceName`).
2. If user says "平台" without details, start with `Azcsupfollower.AzureCM`, then branch to `vmainsight`/`azcore` by evidence.
3. If user asks customer impact, prioritize downtime/health tables before deep hardware internals.

---

## azurecm / Azcsupfollower → AzureCM
**URI**: `https://azurecm.kusto.windows.net` (prod) / `https://Azcsupfollower.kusto.windows.net` (follower, prefer this)  
**Access**: Core Identity - FC Log Read-Only Access (12894)  
**Purpose**: Azure Compute Manager — VM/container/node lifecycle, faults, service healing, live migration

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `LogContainerSnapshot` | VM host placement: nodeId, containerId, tenantName, subscriptionId, VM size, cluster | subscriptionId, roleInstanceName, nodeId, containerId, virtualMachineUniqueId, tenantName |
| `LogContainerHealthSnapshot` | Container health & OS state transitions | roleInstanceName, containerId, nodeId, containerState, containerOsState, faultInfo, vmExpectedHealthState |
| `LogNodeSnapshot` | Node state: unallocatable, OFR, availability | nodeId, nodeState, nodeAvailabilityState, faultInfo |
| `LogDedicatedHostSnapshot` | Dedicated host fabric details | Cluster, nodeId |
| `TMMgmtNodeStateChangedEtwTable` | Node state changes / reboots (Booting, Ready, etc.) | BladeID, OldState, NewState |
| `TMMgmtNodeEventsEtwTable` | Events on node for containers (create, delete, redeploy) | NodeId, ContainerId, EventName |
| `TMMgmtNodeFaultEtwTable` | Fault code & reason per node | NodeId, FaultCode, FaultDescription |
| `TMMgmtTenantEventsEtwTable` | Tenant events: ServiceHealing, LiveMigration, Allocation, OOM | ContainerId, NodeId, TenantName, EventName |
| `TMMgmtRoleInstanceDowntimeEventEtwTable` | Downtime events for role instances | ContainerId, DowntimeType, StartTime, EndTime |
| `TMMgmtSlaMeasurementEventEtwTable` | Tenant lifecycle / all roleinstances status | ContainerId, TenantId, SLAState |
| `TMClusterFabricAuditEtwTable` | Tenant deployment, allocation, CRP-to-Fabric API calls | TenantId, ContainerId, OperationName |
| `FaultHandlingRecoveryEventEtwTable` | Recovery actions and results on host node | NodeId, RecoveryAction, RecoveryResult |
| `FaultHandlingContainerFaultEventEtwTable` | Container-level fault events | ContainerId, NodeId, FaultCode |
| `ServiceHealingTenantStatusEtwTable` | Fabric Service Healing status for tenant | TenantId, SHState, ContainerId |
| `ServiceHealingTriggerEtwTable` | Service healing triggers | ContainerId, NodeId, TriggerReason |
| `KronoxVmOperationEvent` | Platform VM operations | ContainerId, OperationType |
| `DCMLMResourceUnexpectedRebootEtwTable` | Unexpected reboots tracked by DCM/LM | NodeId, RebootTime |
| `RootHEGandalfInformationalEventEtwTable` | RootHE update events from Gandalf | NodeId, OldVersion, NewVersion |
| `ServiceManagerInstrumentation` | Service versions on nodes (NmAgent, datapath, etc.) | NodeId, ServiceName, ServiceVersion |

---

## vmainsight → vmadb / Air
**URI**: `https://vmainsight.kusto.windows.net`  
**Access**: IDWeb SG - VMS KustoDB Cluster (wait ~24h after request)  
**Purpose**: VMA RCA, host CPU, node health, Windows events, Air maintenance events

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `VMAs` (vmadb) | Availability events, 3-level RCA (RCALevel1/2/3), support article link | NodeId, ContainerId, Subscription, RCAEngineCategory, RCALevel1, RCALevel2 |
| `VMALENS` (vmadb) | 30-day availability impact history per VM | NodeId, RoleInstanceName, StartTime, EndTime, RCALevel2 |
| `VMA` (vmadb) | RCA category lookup | NodeId, Subscription, RCAEngineCategory, RCALevel1, RCALevel2, Cluster |
| `RootHENodeGoalVersionChange` (vmadb) | NmAgent/Host plugin updates on node | NodeId, OldValue, NewValue |
| `HighCpuCounterNodeTable` (vmadb) | High CPU events on physical node | NodeId, CounterValue, PreciseTimeStamp |
| `Unhealthynode` (vmadb) | Deep root cause for unhealthy nodes | NodeId, RCALevel1, RCALevel2 |
| `WindowsEventTable` (vmadb) | General Windows activities on node | NodeId, EventId, ProviderName, Description |
| `AirMaintenanceEvents` (Air) | Air maintenance events (NMAgent updates, outage type) | NodeId, EventTime, OutageType, EventCategoryLevel2, Diagnostics |
| `AirHostNetworkingUpdateEvents` (Air) | NMAgent updates and networking details | NodeId, EventTime, EventCategoryLevel3, RCALevel1, OutageType |
| `AirManagedEventsBrownouts` (Air) | Host networking update pauses and duration | NodeId, EventTime, EventType, Duration, RCALevel1 |
| `AirManagedEvents` (Air) | Host node update investigation | NodeId, EventTime, EventType, EventCategoryLevel1/2/3 |
| `AirDiskIOBlipEvents` (Air) | Disk IO blip events | NodeId, EventTime |
| `GetVMPhuEventsBySubId` (Air) | VMPHU events at subscription level (function) | SubscriptionId, StartTime, EndTime |
| `GetArticleIdByFailureSignature` (Air) | RCA article lookup (function) | FailureSignature |

---

## azcore.centralus → Fa (RDOS / HyperV)
**URI**: `https://azcore.centralus.kusto.windows.net`  
**Access**: IDWeb SG - AzCore Kusto Viewers  
**Purpose**: RDOS host-level: HyperV, VM health, OS events, performance counters

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `WindowsEventTable` | Host node Windows events (HyperV, memory, updates) | NodeId, EventId, ProviderName, Channel, Description, Level |
| `HyperVAnalyticEvents` | HyperV errors & warnings (Level < 4) | NodeId, Level, ProviderName, TaskName, EventMessage |
| `HyperVWorkerTable` | HyperV worker events (container-level) | NodeId, ContainerId, EventId, TaskName, Message, Level |
| `HyperVHypervisorTable` | Hypervisor version and config | NodeId, TaskName, Message |
| `VmCounterFiveMinuteRoleInstanceCentralBondTable` | Container performance counters (5-min) | VmId, NodeId, CounterName, AverageCounterValue |
| `VmShoeboxCounterTable` | Shoebox performance source data | VmId, MDMCounterName, AverageValue |
| `GuestAgentExtensionEvents` | VM extension usage | NodeId, ExtensionName |
| `GuestOSDetailEtwTable` | Guest OS details | NodeId |
| `MycroftContainerSnapshot_Latest` (AzureCP) | Latest container snapshot from Mycroft | NodeId, SubscriptionId, ContainerId |

---

## azuredcm → AzureDCMDb (Hardware)
**URI**: `https://azuredcm.kusto.windows.net`  
**Access**: IDWeb SG - Azure DCM Kusto Users  
**Purpose**: Hardware inventory, repair history, node lifecycle, fault codes

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `ResourceSnapshotV1` | Identify hostname, IP, SKU, model from NodeId | ResourceId, IPAddress, HostName, Tenant, Sku, Model |
| `ResourceSnapshotHistoryV1` | Node lifecycle & fault codes history | ResourceId, LifecycleState, FaultCode, FaultDescription |
| `ResourceSnapshotHistoryV2` | Node unexpected restart history with repair codes | ResourceId, PowerCycleTime, UnexpectedRebootTime, RepairCode |
| `RmaDetailsV1` | RMA repair actions | ResourceId, TIMESTAMP, RmaDescription |
| `RepairDetailsV1` | Full repair history | ResourceId |
| `FaultCodeTeamMapping` | Fault code to team mapping | FaultCode, TeamName |
| `dcmInventoryComponentDIMM` | Memory inventory | NodeId, DimmSizeInMB, NumberOfPopulatedDimms |
| `dcmInventoryComponentCPUV2` | CPU inventory | NodeId, Name, CurrentClockSpeed, NumberOfCores |
| `dcmInventoryComponentNIC` | NIC/Mellanox firmware versions | NodeId, MellanoxNic_FirmwareVersion |
| `dcmInventoryAPComponentDisk` | Disk inventory | MachineName, MediaType, Size |
| `RhwBmcSelItemEtwTableV1` | BMC SEL hardware events | NodeId, PreciseTimeStamp |
| `RhwChassisSelItemEtwTable` | Chassis SEL hardware events | NodeId |
| `RhLiteDiagBmcSel` | Lite BMC diagnostics SEL | NodeId |
| `RhLiteDiagSel` | Lite diagnostics SEL | NodeId |

---

## sparkle.eastus → defaultdb (Hardware WHEA/SEL)
**URI**: `https://sparkle.eastus.kusto.windows.net`  
**Access**: IDWeb SG - SparkleUsers  
**Purpose**: WHEA/SEL hardware error logs, IERR events

| Table/Function | Purpose | Key Columns |
|----------------|---------|-------------|
| `SparkleSELByNodeId(nodeId, startTime, endTime)` | SEL logs for node (function) | NodeId, BMCSelTimestamp, ParsedLog, EventDataDetails1 |
| `SparkleWHEAByNodeId(nodeId, startTime, endTime)` | WHEA error events (function) | NodeId |

---

## hawkeyedataexplorer.westus2 → HawkeyeLogs
**URI**: `https://hawkeyedataexplorer.westus2.kusto.windows.net`  
**Access**: (available to EEE teams)  
**Web UI**: `aka.ms/WhyUnhealthy?startTime={Start}Z&endTime={End}Z&nodeId={NodeId}`  
**Purpose**: Automated unhealthy node RCA

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `GetLatestHawkeyeRCAEvents` | Automated RCA for unhealthy node | NodeId, RCATimestamp, RCALevel1, RCALevel2, EscalateToOrg, EscalateToTeam |

---

## icmcluster → ACM.Publisher / ACM.Backend
**URI**: `https://icmcluster.kusto.windows.net`  
**Access**: Core Identity - IcM-Kusto-Access + IDWeb SG AzureCommsReader  
**Purpose**: Customer maintenance notifications, planned maintenance

| Table/Function | Purpose | Key Columns |
|----------------|---------|-------------|
| `GetCommunicationsForSupport(Cloud, Subid, StartTime, EndTime)` | Planned maintenance notifications by subscription | Status, Type, TrackingId, MaintenanceStartDate, NotificationContent |
| `AlbnTargets` | Targets for maintenance communications | Subscriptions, CommunicationId |
| `PublishRequest` (ACM.Backend) | Specific incident/maintenance details | IncidentId, CommunicationDateTime, Title, RichTextMessage |

---

## Azurewatsoncustomer → AzureWatsonCustomer
**URI**: `https://Azurewatsoncustomer.kusto.windows.net`  
**Purpose**: Host node bugcheck / Watson crash analysis

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `CustomerCrashOccurredV2` | Bugcheck events with crash mode | nodeIdentity, crashMode, EventMessage, PreciseTimeStamp |
| `CustomerDumpAnalysisResultV2` | Bugcheck faulting module analysis | dumpUid, faultingModule1, bucketString, bugLink |

---

## azpe → azpe (AzPE / Policy Engine)
**URI**: `https://azpe.kusto.windows.net`  
**Access**: Core Identity - AzPE Kusto Viewer - New  
**Purpose**: Host update workflow orchestration (Orchestrate Manager)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `AzPEWorkflowEvent` | Host update workflow events | NodeId, WorkflowId, EventType, PreciseTimeStamp |

---

## disks → Disks (Managed Disk)
**URI**: `https://disks.kusto.windows.net`  
**Purpose**: Managed disk lifecycle, storage layer

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `DiskRPResourceLifecycleEvent` | Disk lifecycle: create, attach, detach, delete | subscriptionId, resourceName, diskEvent, stage, state, storageAccountType |
| `DiskManagerApiQoSEvent` | Backend existence check, API QoS | resourceName, operationName, httpStatusCode |
| `Disk` | Disk snapshot (current state) | DisksName, OwnershipState, AccountType, CrpDiskId |
| `AssociatedXStoreEntityResourceLifecycleEvent` | Storage layer lifecycle for disk blobs | parentDiskId, entityName, lifecycleEventType |

---

## azcsupfollower2.centralus → crp_allprod (CRP / Control Plane)
**URI**: `https://azcsupfollower2.centralus.kusto.windows.net`  
**Access**: Core Identity - WA CTS-14817  
**Purpose**: Compute Resource Provider (CRP) API operations

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `ApiQosEvents` | CRP API QoS events | subscriptionId, operationName, resultCode |
| `ApiQosEvent_nonGet` | Non-GET CRP API events | subscriptionId, operationName |
| `ContextActivity` | CRP request execution details through provisioning pipelines | subscriptionId, correlationId, vmName |
| `VMApiQosEvent` | All CRP activity for a customer | subscriptionId, vmName, operationType |

---

## Azdeployer → AzDeployerKusto (Planned Maintenance)
**URI**: `https://Azdeployer.kusto.windows.net`  
**Purpose**: Planned maintenance status and history

| Function | Purpose | Parameters |
|----------|---------|------------|
| `GetCurrentMaintenanceStatusBySubscription_PlannedMaintenance` | Current maintenance status by subscription | ParamSubscriptionId |
| `GetCurrentMaintenanceStatus_PlannedMaintenance` | Planned Maintenance events on VM | ParamSubscriptionId, ParamVmName, ParamDepId |
| `GetMaintenanceHistory_PlannedMaintenance` | History of Planned Maintenance on VM | ParamSubscriptionId, ParamVmName, ParamDepId, StartTime, EndTime |

---

## aplat.westcentralus → APlat (Anvil/Tardigrade Service Healing)
**URI**: `https://aplat.westcentralus.kusto.windows.net`  
**Purpose**: Anvil/Tardigrade service healing orchestration

---

## gandalf → gandalf (Unallocatable Nodes)
**URI**: `https://gandalf.kusto.windows.net`  
**Access**: IDWeb SG - Gandalf (Albus) Kusto Viewers  
**Purpose**: Detect unallocatable nodes

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `GandalfUnallocableNodesHistorical` | Historical unallocatable node records | NodeId, State, FoundTimestamp |

---

## azureallocator.westcentralus → AzureAllocator (VM Allocation)
**URI**: `https://azureallocator.westcentralus.kusto.windows.net`  
**Purpose**: VM allocation capacity and limits

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `AllocatorMonitoringLogAllocableVMCount` | Available VM count per cluster/size | partitionName, vmType, priority, deploymentType, vmCount |

---

## azsh → azshmds (Resource Health)
**URI**: `https://azsh.kusto.windows.net`  
**Access**: Core Identity - AzMon Essentials Logs  
**Purpose**: Azure Service Health / Resource Health telemetry

| Function | Purpose |
|----------|---------|
| `RHCRPAvailabilityStatusHistorical(resourceUri, startTime, endTime)` | Resource health availability history |

---

## Query Templates

> Ready-to-use KQL patterns organized by cluster. Use the Natural Language Routing table above to identify the right section, then copy-adapt the query. Parameters in `{braces}` must be replaced before execution.

---

### AzureCM — Container State & Identity

Cluster: `Azcsupfollower.kusto.windows.net` (preferred) · Database: `AzureCM`

#### LogContainerSnapshot — VM host placement history

```kusto
let sid="{SubscriptionId}";
let vmname="{VMName}";
cluster("Azcsupfollower").database("AzureCM").LogContainerSnapshot
| where subscriptionId == sid and roleInstanceName has vmname
| summarize min(PreciseTimeStamp), max(PreciseTimeStamp)
    by roleInstanceName, creationTime, virtualMachineUniqueId, Tenant,
       containerId, nodeId, tenantName, containerType, updateDomain,
       availabilitySetName, subscriptionId
| project VMName=roleInstanceName, VirtualMachineUniqueId=virtualMachineUniqueId,
    Cluster=Tenant, NodeId=nodeId, ContainerId=containerId,
    ContainerCreationTime=todatetime(creationTime),
    StartTimeStamp=min_PreciseTimeStamp, EndTimeStamp=max_PreciseTimeStamp,
    tenantName, containerType, updateDomain, availabilitySetName, subscriptionId
| order by ContainerCreationTime asc
```

#### LogContainerSnapshot — VMs on a specific node (last 3 days)

```kusto
cluster("Azcsupfollower").database("AzureCM").LogContainerSnapshot
| where nodeId == "{NodeId}"
| where PreciseTimeStamp > ago(3d)
| distinct creationTime, roleInstanceName, subscriptionId, containerType,
           virtualMachineUniqueId, nodeId, containerId
```

#### LogContainerHealthSnapshot — Container health & OS state

```kusto
cluster("Azcsupfollower").database("AzureCM").LogContainerHealthSnapshot
| where PreciseTimeStamp between (datetime({BeginTime}) .. datetime({EndTime}))
| where roleInstanceName contains "{VMName}"
| project PreciseTimeStamp, Tenant, roleInstanceName, tenantName, containerId, nodeId,
    containerState, actualOperationalState, containerLifecycleState, containerOsState,
    faultInfo, vmExpectedHealthState, virtualMachineUniqueId,
    containerIsolationState, AvailabilityZone, Region
```

Filter tips:
- `containerOsState == "ContainerOsStateUnresponsive"` — guest OS unresponsive
- `containerOsState == "GuestOsStateProvisioningRecovery"` — provisioning recovery
- `faultInfo <> ""` — CreateContainer failures

#### LogContainerSnapshot + Gandalf — Unallocatable node check

```kusto
let dateTime_StartTime = datetime_add('day', -8, datetime({BeginTime}));
let dateTime_EndTime = datetime_add('hour', +1, datetime({BeginTime}));
cluster('Azcsupfollower').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp between(dateTime_StartTime..dateTime_EndTime)
| where subscriptionId =~ "{SubscriptionId}" and roleInstanceName has "{VMName}"
| project-rename ContainerId = containerId
| distinct nodeId, ContainerId
| join kind=inner (
    cluster('Gandalf').database('gandalf').GandalfUnallocableNodesHistorical
    | project-rename FoundTimestamp = PreciseTimeStamp
    | where State == "Unallocatable"
  ) on $left.nodeId == $right.NodeId
| join kind=inner (
    cluster('Azcsupfollower').database('AzureCM').LogContainerHealthSnapshot
    | where PreciseTimeStamp >= datetime({BeginTime}) and containerState has "ContainerStateDestroyed"
    | project-rename IssueTimestamp = PreciseTimeStamp
  ) on $left.nodeId == $right.nodeId
| where containerId == ContainerId
| where (IssueTimestamp - datetime_add('day', +7, FoundTimestamp)) between (0min .. 10min)
| distinct FoundTimestamp, State, nodeId, IssueTimestamp, ContainerId, containerState
```

---

### AzureCM — Node Events

#### TMMgmtNodeStateChangedEtwTable — Node state changes / reboots

```kusto
cluster("AzureCM").database("AzureCM").TMMgmtNodeStateChangedEtwTable
| where BladeID == "{NodeId}"
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| project PreciseTimeStamp, BladeID, OldState, NewState
```

#### LogNodeSnapshot — Unallocatable, OFR, node state

```kusto
cluster('Azcsupfollower').database('AzureCM').LogNodeSnapshot
| where nodeId =~ "{NodeId}"
  and PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| project PreciseTimeStamp, nodeState, nodeAvailabilityState, containerCount,
          diskConfiguration, faultInfo, rootUpdateAllocationType, RoleInstance
```

Filter tips: `nodeState == "PoweringOn"` · `nodeAvailabilityState == "Unallocatable"` · `diskConfiguration == "AllDisksInStripe"`

#### TMMgmtNodeEventsEtwTable — Detailed node operations

```kusto
cluster("AzureCM").database("AzureCM").TMMgmtNodeEventsEtwTable
| where NodeId == "{NodeId}"
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| project PreciseTimeStamp = tostring(PreciseTimeStamp), Message
| sort by PreciseTimeStamp asc
```

Message filter tips: `"Node reboot event: EventType:"` · `"->"` state transitions · `"Marking container"` · `"Fault Code: 10005"` · `"Not enough memory"`

#### TMMgmtNodeEventsEtwTable — Dirty shutdown confirmation

```kusto
let timeSpan = 7d;
cluster("AzureCM").database("AzureCM").TMMgmtNodeEventsEtwTable
| where NodeId == "{NodeId}" and PreciseTimeStamp >= ago(timeSpan)
  and Message contains "Node reboot event: EventType: "
| parse Message with "Node reboot event: EventType: " eventType "," * "EventTimeStamp: " eventTimeStamp:datetime "," *
| project PreciseTimeStamp, eventTimeStamp, RoleInstance, Tenant, NodeId, eventType, Message
| where eventType in ("DirtyShutdown", "BugCheck", "PXEEvent")
```

#### TMMgmtTenantEventsEtwTable — Fabric-triggered operations (LM, SH, OOM)

```kusto
cluster("AzureCM").database("AzureCM").TMMgmtTenantEventsEtwTable
| where TenantName == "{TenantName}"
| where PreciseTimeStamp > datetime({BeginTime}) and PreciseTimeStamp < datetime({EndTime})
| project PreciseTimeStamp, TaskName, TenantName, Message
```

Message filter tips: `"unhealthy"` · `"LiveMigration"` · `"Not enough memory in the system to start"`

#### TMMgmtContainerTraceEtwTable — Container event trace

```kusto
cluster("AzureCM").database("AzureCM").TMMgmtContainerTraceEtwTable
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp < datetime({EndTime})
| where ContainerID == "{ContainerId}"
| project PreciseTimeStamp, ContainerID, Message
```

#### TMMgmtSlaMeasurementEventEtwTable — Container & tenant state details

```kusto
cluster("AzureCM").database("AzureCM").TMMgmtSlaMeasurementEventEtwTable
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp < datetime({EndTime})
| where ContainerID == "{ContainerId}"
| project PreciseTimeStamp, Context, EntityState, Detail0, Tenant, TenantName,
          RoleInstanceName, NodeID, ContainerID, Region
```

Filter: `EntityState == "GuestOsStateHardPowerOff"`

---

### AzureCM — Node Fault & Recovery

#### TMMgmtNodeFaultEtwTable — Node-level faults

```kusto
cluster("AzureCM").database("AzureCM").TMMgmtNodeFaultEtwTable
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| where NodeId has "{NodeId}" or BladeID has "{NodeId}"
| project PreciseTimeStamp, FaultCode, Reason, Time, Details,
          FaultInfoJsonString, CorrelationGuid, BladeID, NodeId
| order by PreciseTimeStamp asc
```

#### FaultHandlingContainerFaultEventEtwTable — Container faults

```kusto
cluster("AzureCM").database("AzureCM").FaultHandlingContainerFaultEventEtwTable
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| where ContainerId == "{ContainerId}" or NodeId has "{NodeId}"
| project PreciseTimeStamp, NodeId, ContainerId, FaultTime, FaultCode,
          FaultType, FabricOperation, NodeState, FaultScope, Reason, Details
| order by PreciseTimeStamp asc
```

#### FaultHandlingRecoveryEventEtwTable — Node recovery actions

```kusto
cluster("AzureCM").database("AzureCM").FaultHandlingRecoveryEventEtwTable
| where NodeId == "{NodeId}"
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| project PreciseTimeStamp, NodeId, Reason, RecoveryAction, RecoveryResult
```

RecoveryAction values: `PowerCycle` · `RestartNodeService` · `HumanInvestigate` · `ResetNodeHealth` · `RebootNode` · `MarkNodeAsUnallocatable`

#### FaultHandlingContainerRecoveryEventEtwTable — Container recovery

```kusto
cluster("AzureCM").database("AzureCM").FaultHandlingContainerRecoveryEventEtwTable
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| where ContainerId == "{ContainerId}" or NodeId has "{NodeId}"
| project PreciseTimeStamp, NodeId, ContainerId, AttemptResult, FaultDetails,
          RecoveryAction, FaultTime, RecoveryTime, ImpactedContainers
| order by PreciseTimeStamp asc
```

#### ServiceHealingTriggerEtwTable — Service healing confirmation

```kusto
cluster("AzureCM").database("AzureCM").ServiceHealingTriggerEtwTable
| where NodeId == "{NodeId}" and TenantName == "{TenantName}"
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp < datetime({EndTime})
| project PreciseTimeStamp, TriggerId, TriggerType, FaultCode, FaultReason,
          FaultInfoFabricOperation, TenantName, RoleInstanceName, AffectedUpdateDomain, NodeId
```

#### AnvilRepairServiceForgeEvents — Anvil/Tardigrade recovery

```kusto
cluster('aplat.westcentralus.kusto.windows.net').database('APlat').AnvilRepairServiceForgeEvents
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| where ResourceDependencies has_any ("{NodeId}")
| where TreeNodeKey !in ('Root', 'Node')
| summarize arg_max(PreciseTimeStamp, *) by RequestIdentifier, TreeNodeKey
| project PreciseTimeStamp, AnvilOperation=TreeNodeKey,
    NodeId=tostring(parse_json(ResourceDependencies).NodeId),
    AnvilRequestIdentifier=RequestIdentifier, ResourceId, ResourceType
| sort by PreciseTimeStamp asc
```

#### KronoxVmOperationEvent — Platform VM operations (reboot/restart/redeploy)

```kusto
cluster("AzureCM").database("AzureCM").KronoxVmOperationEvent
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| where SubscriptionId =~ "{SubscriptionId}" or VmId == "{VMId}"
| project PreciseTimeStamp, OperationType, OperationId, CurrentOperationStatus,
          NewOperationStatus, VmId, SubscriptionId, ActivationTime, CompletionTime,
          DeadlineUtc, ErrorCode, ErrorDetails
| order by PreciseTimeStamp asc
```

#### DCMLMResourceUnexpectedRebootEtwTable — Unexpected node reboots

```kusto
cluster("AzureCM").database("AzureCM").DCMLMResourceUnexpectedRebootEtwTable
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| where ResourceId has "{NodeId}" or SourceNodeId has "{NodeId}"
| project PreciseTimeStamp, ResourceId, PowerCycleTime, PxeRequestTime,
          TimeBetweenPowerAndPxe, CloudName, Region, DataCenterName
| order by PreciseTimeStamp asc
```

---

### AzureCM — Live Migration

#### LiveMigrationContainerDetailsEventLog — Identify LM session ID

```kusto
cluster("AzureCM").database("AzureCM").LiveMigrationContainerDetailsEventLog
| where destinationContainerId == "{ContainerId}" or sourceContainerId == "{ContainerId}"
| where PreciseTimeStamp > datetime({BeginTime}) and PreciseTimeStamp < datetime({EndTime})
| project triggerType, migrationConstraint, sessionId
```

#### LiveMigrationSessionCompleteLog — LM completion

```kusto
cluster("AzureCM").database("AzureCM").LiveMigrationSessionCompleteLog
| where destinationContainerId == "{ContainerId}" or sourceContainerId == "{ContainerId}"
| where sessionId == "{LMSessionId}"
```

#### LiveMigrationSessionStatusEventLog — LM errors

```kusto
cluster("AzureCM").database("AzureCM").LiveMigrationSessionStatusEventLog
| where sessionId == "{LMSessionId}"
| where ['type'] == "Error"
| project ['state'], message
```

#### LiveMigrationSessionCriticalLog — Critical LM errors

```kusto
cluster("AzureCM").database("AzureCM").LiveMigrationSessionCriticalLog
| where sessionId == "{LMSessionId}"
| project exceptionType, exception, lmContext
```

---

### vmainsight — VMA RCA & Air Events

Cluster: `vmainsight.kusto.windows.net` · Databases: `vmadb`, `Air`

#### VMA — Fault info + RCA category + support article

```kusto
let myTable = cluster("Vmainsight").database("vmadb").VMA
| where PreciseTimeStamp >= datetime({StartTime}) and PreciseTimeStamp <= datetime({EndTime})
| where NodeId == "{NodeId}" and RoleInstanceName has "{VMName}"
| distinct PreciseTimeStamp, NodeId, RoleInstanceName, RCAEngineCategory,
           RCALevel1, RCALevel2, RCA_CSS, Cluster, ContainerId;
myTable
| extend StartTime = now(), EndTime = now(), RCAEngineCategory = ""
| invoke cluster("Vmainsight").database('Air').AddVmRestartSupportArticle()
| project-away StartTime, EndTime, RCAEngineCategory, InternalArticleId
```

#### VMALENS — 30-day VM availability impact

```kusto
cluster("vmainsight").database("vmadb").VMALENS()
| where StartTime >= ago(30d)
| where Subscription == "{SubscriptionId}"
| project StartTime, RoleInstanceName, PreciseTimeStamp, LastKnownSubscriptionId,
          Cluster, NodeId, RCA, RCALevel1, RCALevel2, RCALevel3,
          SEL_RCA, EscalateToBucket, RCAEngineCategory,
          LastEvents, EG_Followup, EG_Url
| order by StartTime asc nulls last
```

#### AirManagedEvents — Host node update impact timeline

```kusto
cluster('vmainsight.kusto.windows.net').database('Air').AirManagedEvents
| where EventTime between (datetime({StartTime}) .. datetime({EndTime})) and NodeId == "{NodeId}"
| project EventTime, EventType, EventSource, ObjectType, ObjectId, Duration,
          EventCategoryLevel1, EventCategoryLevel2, EventCategoryLevel3, RCALevel1
```

#### AirHostNetworkingUpdateEvents — NMAgent updates

```kusto
cluster('vmainsight.kusto.windows.net').database('Air').AirHostNetworkingUpdateEvents
| where EventTime > datetime({StartTime}) and EventTime < datetime({EndTime})
| where NodeId =~ "{NodeId}"
| distinct EventTime, EventCategoryLevel3, EventSource, RCALevel1, OutageType, NodeId
```

#### AirManagedEventsBrownouts — HostNetworking update pauses

```kusto
cluster('vmainsight.kusto.windows.net').database('Air').AirManagedEventsBrownouts
| where EventTime between (datetime({StartTime}) .. datetime({EndTime})) and NodeId == "{NodeId}"
| project EventTime, NodeId, EventType, EventSource, ObjectType, ObjectId, Duration,
          EventCategoryLevel1, EventCategoryLevel2, EventCategoryLevel3, RCALevel1, RCALevel2, RCALevel3
```

#### Combined host update query (ServiceManager + RootHE + Gandalf + NMAgent)

```kusto
let RootHE = cluster("Vmainsight").database("vmadb").RootHENodeGoalVersionChange
    | extend RootHE_OldValue=OldValue, RootHE_NewValue=NewValue;
let RootHEGandalf = cluster('Azcsupfollower').database('AzureCM').RootHEGandalfInformationalEventEtwTable
    | extend RootHEGandalf_OldValue=OldVersion, RootHE_NewValueGandalf=NewVersion;
let NMAgent = cluster('vmainsight.kusto.windows.net').database('Air').AirMaintenanceEvents
    | extend PreciseTimeStamp = EventTime, Diagnostics=tostring(Diagnostics);
union
  (cluster("AzureCM").database("AzureCM").ServiceManagerInstrumentation),
  RootHE, RootHEGandalf, NMAgent
| where PreciseTimeStamp >= datetime({StartTime}) and PreciseTimeStamp < datetime({EndTime})
| where NodeId == "{NodeId}"
| summarize NodeUpdatedAtApprox=min(PreciseTimeStamp)
    by ServiceVersion, ServiceName, RootHE_OldValue, RootHE_NewValue,
       RootHEGandalf_OldValue, RootHE_NewValueGandalf,
       EventCategoryLevel2, EventCategoryLevel3, Component, OutageType, Diagnostics, NodeId
| project-reorder NodeUpdatedAtApprox, NodeId
| order by NodeUpdatedAtApprox asc
```

#### WindowsEventTable (vmadb) — Windows events on host node

```kusto
cluster("vmainsight").database("vmadb").WindowsEventTable
| where NodeId == "{NodeId}"
| where PreciseTimeStamp >= datetime({StartTime}) and PreciseTimeStamp <= datetime({EndTime})
| where EventId != "0" and EventId != "505" and EventId != "504" and EventId != "3095"
| project TimeCreated, Cluster, EventId, ProviderName, Description
| order by TimeCreated asc nulls last
```

EventId filter tips: `18500-18560` HyperV container events · `2004,3050,3122,12030` low memory · `ProviderName contains "UpdateNotification"` VM-PHU

#### GetVMPhuEventsBySubId — VM-PHU events at subscription level

```kusto
cluster('vmainsight.kusto.windows.net').database('Air').GetVMPhuEventsBySubId(
    '{SubscriptionId}', datetime({StartTime}), datetime({EndTime}))
```

#### GetArticleIdByFailureSignature / GetCssWikiLinkByArticleId — RCA article lookup

```kusto
cluster('vmainsight').database('Air').GetArticleIdByFailureSignature("HardwareFault.DCM FaultCode 60017")
// Then:
cluster('vmainsight').database('Air').GetCssWikiLinkByArticleId("VMA_RCA_Hardware_NodeReboot_Memory_Failure")
```

---

### AzureDCM — Hardware Inventory & Repair History

Cluster: `Azuredcm.kusto.windows.net` · Database: `AzureDCMDb`

#### ResourceSnapshotV1 — Identify hostname, IP, SKU from NodeId

```kusto
cluster("Azuredcm").database("AzureDCMDb").ResourceSnapshotV1
| where ResourceId == "{NodeId}"
| project ResourceId, IPAddress, HostName, Tenant, Sku, Model, Manufacturer,
          AvailabilityZone, CloudName, Region
```

#### ResourceSnapshotV1 + DIMM — Memory inventory

```kusto
cluster("Azuredcm").database("AzureDCMDb").ResourceSnapshotV1
| where ResourceId == "{NodeId}"
| project ResourceId, IPAddress, HostName, Tenant, Sku, Model, Manufacturer
| join kind=leftouter (
    cluster("Azuredcm").database("AzureDCMDb").dcmInventoryComponentDIMM
    | where NodeId == "{NodeId}"
    | project NodeId, DimmSizeInMB, NumberOfPopulatedDimms
  ) on $left.ResourceId == $right.NodeId
| distinct NodeId, IPAddress, HostName, Tenant, Sku, Model, Manufacturer,
           DimmSizeInMB, NumberOfPopulatedDimms
```

#### ResourceSnapshotV1 + NIC — NIC/Mellanox firmware versions

```kusto
cluster("Azuredcm").database("AzureDCMDb").ResourceSnapshotV1
| where ResourceId == "{NodeId}"
| project ResourceId, IPAddress, HostName, Tenant, Sku, Model, Manufacturer
| join kind=leftouter (
    cluster("Azuredcm").database("AzureDCMDb").dcmInventoryComponentNIC
    | project NodeId, MellanoxNic_FirmwareVersion, Mlx4BusDriverVersion,
              Mlx4EthDriverVersion, Mlx5BusDriverVersion, Description
  ) on $left.ResourceId == $right.NodeId
```

#### ResourceSnapshotHistoryV2 — Node unexpected restart history

```kusto
cluster("Azuredcm").database("AzureDCMDb").ResourceSnapshotHistoryV2
| where ResourceId == "{NodeId}"
| where PowerCycleTime >= datetime({StartTime})
| project PowerCycleTime, UnexpectedRebootTime, RepairCode, RepairResolutionDetails,
          RepairRequireHardwareDiscovery, PreciseTimeStamp, Tenant
| distinct PowerCycleTime, RepairResolutionDetails, Tenant
```

#### ResourceSnapshotHistoryV1 — Node lifecycle & fault codes

```kusto
cluster("Azuredcm").database("AzureDCMDb").ResourceSnapshotHistoryV1
| where ResourceId == "{NodeId}"
| where PreciseTimeStamp >= datetime({StartTime})
| project PreciseTimeStamp, LifecycleState, NeedFlags, FaultCode, FaultDescription, Tenant, ResourceId
```

#### RmaDetailsV1 — RMA repair history

```kusto
cluster("Azuredcm").database("AzureDCMDb").RmaDetailsV1
| where ResourceId == "{NodeId}"
| project TIMESTAMP, RmaDescription
```

#### FaultCodeTeamMapping — Fault code → reason lookup

```kusto
cluster("Azuredcm").database("AzureDCMDb").FaultCodeTeamMapping
| where FaultCode == "20028"
| project FaultCode, FaultReason
```

#### DCMLMResourceResultEtwTable — BMC-SEL hardware faults at node restart

```kusto
cluster("AzureCM").database("AzureCM").DCMLMResourceResultEtwTable
| where PreciseTimeStamp >= datetime({BeginTime}) and PreciseTimeStamp <= datetime({EndTime})
| where ResourceId == "{NodeId}"
| project PreciseTimeStamp, ResourceId, ResultType, ActivityName, FaultCode, FaultReason, DeviceType
```

---

### Sparkle — WHEA & SEL Hardware Errors

Cluster: `sparkle.eastus.kusto.windows.net` · Database: `defaultdb`

WHEA = Windows Hardware Error Architecture · SEL = BIOS System Event Log

#### WheaXPFMCAFull — WHEA machine check errors

```kusto
cluster("sparkle.eastus").database("defaultdb").WheaXPFMCAFull
| where NodeId == "{NodeId}"
| where PreciseTimeStamp > ago(7d)
| project TIMESTAMP, ProviderName, ErrorRecordSeverity, PhysicalAddress, Status, RetryReadData
```

#### SparkleSELByNodeId — System Event Log

```kusto
cluster("sparkle.eastus").database("defaultdb").SparkleSELByNodeId(
    nodeId="{NodeId}", startTime=ago(2d), endTime=now())
```

#### SparkleSELByNodeIds — SEL filtered for known failure patterns

```kusto
let nodeId = pack_array("{NodeId}");
cluster("sparkle.eastus").database("defaultdb").SparkleSELByNodeIds(nodeId, ago(2d), now())
| where (EventDetail contains "atal") or (EventDetail contains "PCIe")
    or (EventDetail contains "limit") or (EventDetail contains "nterconnect")
    or (EventDetail contains "iERR") or (EventDetail contains "orrect")
| summarize arg_max(BMCSelTimestamp, *) by EventDetail, EventDataDetails1, EventDataDetails2, EventDataDetails3
| project BMCSelTimestamp, RecordId, EventDetail, EventDataDetails1, EventDataDetails2,
          EventDataDetails3, BMCSelItemMessage, SelSource
| sort by BMCSelTimestamp desc
```

---

### AzCore — HyperV, RDOS, Windows Events, VM Performance

Cluster: `azcore.centralus.kusto.windows.net` · Database: `Fa`

#### WindowsEventTable — Host node Windows events

```kusto
cluster('azcore.centralus.kusto.windows.net').database('Fa').WindowsEventTable
| where PreciseTimeStamp between(datetime({StartTime})..datetime({EndTime}))
| where NodeId == '{NodeId}'
| where not (ProviderName == "NETLOGON" and EventId == 3095)
| where not (ProviderName == 'IPMIDRV' and EventId == 1004)
| where not (ProviderName == "VhdDiskPrt" and EventId == 47)
| where ProviderName <> "CMClientLib"
| where EventId <> 7000 and EventId <> 1023
| where EventId !in (505, 504, 146, 145, 142)
| project todatetime(TimeCreated), Cluster, Level, ProviderName, EventId, Channel,
          Description, NodeId
| order by TimeCreated asc
```

#### HyperVAnalyticEvents — HyperV errors & warnings

```kusto
cluster("azcore.centralus.kusto.windows.net").database("Fa").HyperVAnalyticEvents
| where PreciseTimeStamp >= datetime({StartTime}) and PreciseTimeStamp <= datetime({EndTime})
| where NodeId == '{NodeId}' and Level < 4
| extend leveldescription = case(Level <= 2, "error", Level == 3, "warning", "info")
| project PreciseTimeStamp, NodeId, Level, leveldescription, ProviderName,
          TaskName, EventMessage, Message
```

#### HyperVWorkerTable — Memory allocation delays

```kusto
cluster("azcore.centralus.kusto.windows.net").database("Fa").HyperVWorkerTable
| where PreciseTimeStamp between(datetime({StartTime})..datetime({EndTime}))
| where NodeId == "{NodeId}"
| where TaskName == "TimeSpentInMemoryOperation"
    and Message has "ReservingRam" and Message has "CreateRamMemoryBlocks"
| extend Seconds = trim_end("}", substring(Message, indexof(Message, "Seconds")+9))
| where todouble(Seconds) > 120
| project PreciseTimeStamp, Message, Seconds
```

#### VmHealthRawStateEtwTable — VM availability state (logged every 15s)

```kusto
cluster("azcore.centralus.kusto.windows.net").database("Fa").VmHealthRawStateEtwTable
| where ContainerId == "{ContainerId}"
| where PreciseTimeStamp >= datetime({StartTime}) and PreciseTimeStamp <= datetime({EndTime})
```

Note: `IsVscStateOperational` is always `0` on `AllDisksInStripe` nodes.

#### VmHealthTransitionStateEtwTable — VM state changes only

```kusto
cluster("azcore.centralus.kusto.windows.net").database("Fa").VmHealthTransitionStateEtwTable
| where ContainerId == "{ContainerId}"
| where PreciseTimeStamp >= datetime({StartTime}) and PreciseTimeStamp <= datetime({EndTime})
```

#### NodeServiceOperationEtwTable — StartContainer timing

```kusto
cluster("azcore.centralus.kusto.windows.net").database("Fa").NodeServiceOperationEtwTable
| where PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime}))
| where NodeId =~ '{NodeId}' and Identifier contains "{ContainerId}"
| project PreciseTimeStamp, OperationName, Identifier, Result, ResultCode,
          RequestTime, CompleteTime
```

If StartContainer > 5 minutes → indicates node performance issues.

#### VmCounterFiveMinuteRoleInstanceCentralBondTable — Container performance counters

```kusto
cluster('azcore.centralus.kusto.windows.net').database('Fa').VmCounterFiveMinuteRoleInstanceCentralBondTable
| where PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime}))
| where VmId == '{ContainerId}'
| project PreciseTimeStamp, Cluster, TenantId, NodeId, VmId, RoleInstanceId,
          CounterName, SampleCount, AverageCounterValue, MinCounterValue, MaxCounterValue
```

#### OsLoggerTable — OS error logs

```kusto
cluster("azcore.centralus.kusto.windows.net").database("Fa").OsLoggerTable
| where NodeId == "{NodeId}"
| where PreciseTimeStamp >= datetime({StartTime}) and PreciseTimeStamp <= datetime({EndTime})
| where ComponentName != "XDiskSvc" and LogErrorLevel == "Error"
| project PreciseTimeStamp, Cluster, NodeId, ActivityId, ComponentName,
          FunctionName, LogErrorLevel, ResultCode, ErrorDetails
```

---

### Hawkeye — Automated Unhealthy Node RCA

Cluster: `hawkeyedataexplorer.westus2.kusto.windows.net` · Database: `HawkeyeLogs`

Web UI: `aka.ms/WhyUnhealthy?startTime={StartTime}Z&endTime={EndTime}Z&nodeId={NodeId}`

```kusto
cluster('hawkeyedataexplorer.westus2.kusto.windows.net').database('HawkeyeLogs').GetLatestHawkeyeRCAEvents
| where RCATimestamp >= datetime({StartTime}) and RCATimestamp < datetime({EndTime})
| where NodeId == "{NodeId}"
| distinct RCATimestamp, NodeId, RCALevel1, RCALevel2, EscalateToOrg, EscalateToTeam
```

---

### Watson — Host Node Bugchecks

Cluster: `Azurewatsoncustomer.kusto.windows.net` · Database: `AzureWatsonCustomer`

#### CustomerCrashOccurredV2 + DumpAnalysis — Bugcheck with faulting module

```kusto
cluster('Azurewatsoncustomer').database('AzureWatsonCustomer').CustomerCrashOccurredV2
| where PreciseTimeStamp >= datetime({StartTime}) and PreciseTimeStamp <= datetime({EndTime})
| where nodeIdentity == "{NodeId}" and crashMode == "km"
| join kind=leftouter (
    cluster('Azurewatsoncustomer').database('AzureWatsonCustomer').CustomerDumpAnalysisResultV2
  ) on $left.dumpUid == $right.dumpUid
| project PreciseTimeStamp, nodeIdentity, EventMessage, crashMode,
          faultingModule1, bucketString, dumpType, bugId, bugLink
```

---

### Maintenance & Customer Notifications

Cluster: `icmcluster.kusto.windows.net` · Databases: `ACM.Publisher`, `ACM.Backend`

#### GetCommunicationsForSupport — Planned maintenance notifications

```kusto
cluster('icmcluster').database('ACM.Publisher').GetCommunicationsForSupport(
    Cloud="Public", Subid="{SubscriptionId}", StartTime=ago(60d), EndTime=now())
| extend JSON = parse_json(list_json) | project-away list_json
| mv-expand JSON
| where JSON.Type contains "Maintenance"
| project Status=tostring(JSON.Status), Type=tostring(JSON.Type),
    TrackingId=tostring(JSON.TrackingId), ICMNumber=tostring(JSON.LSIID),
    MaintenanceStartDate=todatetime(JSON.StartTime), MaintenanceEndDate=todatetime(JSON.EndTime),
    NotificationCreationDate=todatetime(JSON.CreateDate),
    NotificationContent=tostring(JSON.CurrentDescription)
| where NotificationContent !contains "Azure SQL"
| order by MaintenanceStartDate desc
```

#### PublishRequest — Specific incident/outage notification details

```kusto
cluster('Icmcluster').database("ACM.Backend").PublishRequest
| where IncidentId == "{IncidentId}"
```

---

### AzPE — Host Update Workflow (OM)

Cluster: `azpe.kusto.windows.net` · Database: `azpe`

```kusto
cluster('azpe.kusto.windows.net').database('azpe').AzPEWorkflowEvent
| where PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime}))
| where WorkflowId contains "{NodeId}"
| where WorkflowType == "OM"
| where EntityId contains "AzPEHostUpdateMonitor"
| project PreciseTimeStamp, WorkflowInstanceGuid, WorkflowId, WorkflowType, WorkflowEventData
| order by PreciseTimeStamp asc
```

---

### Disks RP — Managed Disk Lifecycle

Cluster: `disks.kusto.windows.net` · Database: `Disks`

#### DiskRPResourceLifecycleEvent — Find disk by name & subscription

```kusto
cluster("disks.kusto.windows.net").database("Disks").DiskRPResourceLifecycleEvent
| where subscriptionId == "{SubscriptionId}"
| where resourceName == "{DiskName}"
| where PreciseTimeStamp >= ago(90d)
| project PreciseTimeStamp, resourceName, subscriptionId, resourceGroupName,
          diskEvent, stage, state, storageAccountType, diskSizeBytes, id
| order by PreciseTimeStamp asc
```

diskEvent values: `Create` · `Update` · `Attach` · `Detach` · `Delete` · `SoftDelete`
state values: `Unattached` · `Attached` · `Reserved` · `ActiveSAS`

#### DiskRPResourceLifecycleEvent — Full lifecycle (latest state per disk)

```kusto
cluster("disks.kusto.windows.net").database("Disks").DiskRPResourceLifecycleEvent
| where resourceName == "{DiskName}"
| where subscriptionId == "{SubscriptionId}"
| summarize arg_max(PreciseTimeStamp, *) by resourceName
| project PreciseTimeStamp, resourceName, subscriptionId, resourceGroupName,
          diskEvent, stage, state, storageAccountType, diskOwner, id
```

#### DiskRPResourceLifecycleEvent — By storage account

```kusto
cluster('Disks').database('Disks').DiskRPResourceLifecycleEvent
| where (TIMESTAMP >= datetime({StartTime}) and TIMESTAMP <= datetime({EndTime}))
| where subscriptionId == "{SubscriptionId}"
| where storageAccountName == "{StorageAccountName}"
| project TIMESTAMP, resourceName, diskEvent
```

#### DiskManagerApiQoSEvent — Backend existence check

```kusto
cluster("disks.kusto.windows.net").database("Disks").DiskManagerApiQoSEvent
| where resourceName == "{DiskName}"
| where subscriptionId == "{SubscriptionId}"
| project PreciseTimeStamp, operationName, httpStatusCode, resourceName,
          clientApplicationId, userAgent, region
| order by PreciseTimeStamp desc
| limit 10
```

Interpretation:
- `httpStatusCode == 200` + `clientApplicationId == "Azure Resource Graph"` → Disk **exists**
- `httpStatusCode == 404` → Disk has been **deleted**

#### Disk — Snapshot current state

```kusto
cluster("disks.kusto.windows.net").database("Disks").Disk
| where DisksName has "{DiskName}"
| order by PreciseTimeStamp desc
| limit 5
| project PreciseTimeStamp, DisksId, DisksName, DiskResourceType,
          OwnershipState, AccountType, ResourceGroup, DiskSizeBytes,
          BlobUrl, StorageAccountName, CrpDiskId
```

#### AssociatedXStoreEntityResourceLifecycleEvent — Storage layer

```kusto
cluster("disks.kusto.windows.net").database("Disks").AssociatedXStoreEntityResourceLifecycleEvent
| where parentDiskId == "{DiskRPInternalId}"
    or entityName has "{DiskName}"
| project PreciseTimeStamp, id, parentDiskId, entityName, entityType,
          lifecycleEventType, stage, entityUri, storageAccountName,
          storageAccountType, entitySizeBytes, isHydrated, subscriptionId
| order by PreciseTimeStamp asc
```
