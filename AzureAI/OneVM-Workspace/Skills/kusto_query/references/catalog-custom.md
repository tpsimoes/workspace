# Kusto Catalog — Custom Additions

> **How to add entries**:
> Copy the block template below for the cluster/table you want to add.
> You can add new clusters, new databases within existing clusters, or new tables to existing sections.
> These entries take precedence in agent lookups — if a table is listed here AND in `catalog-AzureIaaSVM.md`, the description here wins.

---

## Entry Template

```
## {cluster-alias} → {Database}
**URI**: `https://{cluster}.kusto.windows.net`
**Access**: {how to get access}
**Purpose**: {what this cluster is for}

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `TableName` | {description} | col1, col2, col3 |
```

---

<!-- Add your entries below this line -->

---

## Cluster Reference

| Cluster Alias | URI | Key Databases | Purpose |
|---------------|-----|---------------|---------|
| `azcrpbifollower` | `https://azcrpbifollower.kusto.windows.net` | `bi_allprod` | CRP BI follower; subscription & AZ metadata |
| `azcore.centralus` | `https://azcore.centralus.kusto.windows.net` | `Fa` | RDOS host telemetry: HyperV, NVMe, Windows events |
| `AzureCM` | `https://Azurecm.kusto.windows.net` | `AzureCM` | Fabric management plane: VM lifecycle, node faults |
| `azcsupfollower` | `https://azcsupfollower.kusto.windows.net` | `AzureCM` | Read-only follower of AzureCM; preferred for CSS queries |
| `moseisley` | `https://moseisley.kusto.windows.net` | `vmadb`, `Air` | VMA RCA engine and VM restart event history |
| `azcrp` | `https://azcrp.kusto.windows.net` | `crp_allprod` | CRP API QoS events and internal context tracing |

---

## Table Reference

| Table | Cluster.Database | Purpose | Key Columns |
|-------|-----------------|---------|-------------|
| `Subscription` | `azcrpbifollower.bi_allprod` | Subscription metadata including physical-to-logical AZ mappings | SubscriptionId, Region, TIMESTAMP, AvailabilityZoneMappings |
| `HyperVStorageStackTable` | `azcore.centralus.Fa` | HyperV storage stack events; NVMe / disk controller errors | PreciseTimeStamp, NodeId, ProviderName, Level, Message |
| `WindowsEventTable` | `azcore.centralus.Fa` | Host node Windows event log; OS-level errors and warnings | PreciseTimeStamp, Cluster, NodeId, Level, ProviderName, EventId, Description, TimeCreated |
| `Atlas_VmStateTransitionEvent` | `vmainsight.Vmadiag` | VM-Host heartbeat state transitions; definitive record of Healthy/Unhealthy/NoSignal/DoNotCare; use to distinguish control-plane from data-plane failures, and to time Redeploy initiation | PreciseTimeStamp, ContainerId, NodeId, HealthState, Reason, osIncarnationId |
| `vfp_restore_fails` | `vmainsight.Vmadiag` | VFP agent process crash/restore failures on a node; if empty during a network outage, VFP process is alive → suspect silent programming failure, not process crash | PreciseTimeStamp, NodeId, ContainerId, FailReason |
| `EventData_SDN_DataPath` | `vmainsight.Vmadiag` | SDN Controller data-path programming events; use when VFP silent failure is suspected and you need control-plane-issued rule programming evidence | PreciseTimeStamp, NodeId, ContainerId, EventType, Message |
| `LogContainerSnapshot` | `AzureCM.AzureCM` | VM container lifecycle state; primary VM identity resolution source | PreciseTimeStamp, roleInstanceName, subscriptionId, virtualMachineUniqueId, containerId, nodeId, tenantName, creationTime, RegionFriendlyName |
| `TMMgmtNodeFaultEtwTable` | `AzureCM.AzureCM` | Node fault codes from Tenant Manager | PreciseTimeStamp, Tenant, BladeID (=NodeId), FaultCode, Reason |
| `LogNodeSnapshot` | `azcsupfollower.AzureCM` | Node state and availability snapshots | PreciseTimeStamp, nodeId, nodeState, nodeAvailabilityState, containerCount, faultInfo |
| `LogContainerHealthSnapshot` | `azcsupfollower.AzureCM` | Container health state snapshots; VM OS/lifecycle state history | PreciseTimeStamp, containerId, roleInstanceName, nodeId, containerLifecycleState, containerState, containerOsState, faultInfo |
| `VMA()` | `moseisley.vmadb` | RCA engine output per container; category, level, duration | PreciseTimeStamp, ContainerId, NodeId, AvailabilityState, RCAEngineCategory, RCALevel1/2/3, StartTime, EndTime |
| `GetVMRestartEvents()` | `moseisley.Air` | Structured VM restart events with FailureSignature and wiki links | Timestamp, ImpactBeginTimeStamp, ImpactEndTimeStamp, VMUniqueId, ContainerId, FailureSignature, CssWikiLink |
| `ApiQosEvent` | `azcrp.crp_allprod` | All CRP API calls including GETs; latency/QoS | PreciseTimeStamp, subscriptionId, resourceName, correlationId, operationId, operationName, httpStatusCode, resultCode, errorDetails, e2EDurationInMilliseconds |
| `ApiQosEvent_nonGet` | `azcrp.crp_allprod` | CRP mutating API calls only (PUT/POST/DELETE) | Same as ApiQosEvent |
| `ContextActivity` | `azcrp.crp_allprod` | CRP internal context traces; maps activityId to workflow steps | PreciseTimeStamp, activityId, message, callerName, sourceFile |

---

## Query Samples

---

### Query: Physical Zone ↔ Logical Zone Mapping
**Scenario**: Resolve the correspondence between logical availability zones (1/2/3) and physical zone names for a given subscription and region
**Tables**: `azcrpbifollower.bi_allprod.Subscription`
**Params**: `{subscriptionId}`, `{region}`

```kql
let _SubscriptionID = '{subscriptionId}';
let _Region = '{region}';
cluster('azcrpbifollower.kusto.windows.net').database('bi_allprod').Subscription
| where SubscriptionId == _SubscriptionID
| where Region contains _Region
| where TIMESTAMP > ago(1d)
| limit 1
| extend AvZones = todynamic(AvailabilityZoneMappings)
| project SubscriptionId, Region,
    Zone1 = AvZones[0].PhysicalZone,
    Zone2 = AvZones[1].PhysicalZone,
    Zone3 = AvZones[2].PhysicalZone
```

> Output shape: `SubscriptionId | Region | Zone1 | Zone2 | Zone3`

---

### Query: Native NVMe Disk Errors on Host Node
**Scenario**: Investigate NVMe controller failures on a host node; filter for critical error codes `c000050a` (I/O error) and `c0000184` (failed to start controller)
**Tables**: `azcore.centralus.Fa.HyperVStorageStackTable`
**Params**: `{_StartTime}`, `{_EndTime}`, `{nodeId}`

```kql
let queryFrom = {_StartTime};
let queryTo   = {_EndTime};
let nodeId    = '{nodeId}';
cluster('azcore.centralus.kusto.windows.net').database('Fa').HyperVStorageStackTable
| where PreciseTimeStamp between(queryFrom .. queryTo)
| where NodeId =~ nodeId
| where ProviderName contains "nvme"
| where Level <= 2
| where Message has 'c000050a' or Message has 'c0000184'
| project PreciseTimeStamp, NodeId, Message
```

---

### Query: Host Node Windows Event Log
**Scenario**: Review OS-level errors and warnings on a host node; Level maps to: 1=fatal, 2=error, 3=warning, else info
**Tables**: `azcore.centralus.Fa.WindowsEventTable`
**Params**: `{nodeId}`, `{Start}`, `{End}`

```kql
cluster('azcore.centralus.kusto.windows.net').database('Fa').WindowsEventTable
| where NodeId == '{nodeId}'
| where PreciseTimeStamp between(datetime('{Start}') .. datetime('{End}'))
| extend level = case(Level == 1, "fatal", Level == 2, "error", Level == 3, "warning", "info")
| project todatetime(TimeCreated), Cluster, NodeId, level, ProviderName, EventId, Description
```

---

### Query: VM Container Snapshot (resolve VM identity)
**Scenario**: Resolve VM identity and get latest container state — use to obtain `containerId`, `nodeId`, `tenantName` from `virtualMachineUniqueId`, `containerId`, or `roleInstanceName`; first step in any VM restart investigation
**Tables**: `AzureCM.AzureCM.LogContainerSnapshot`
**Params**: `{Start}`, `{End}`, one of `{virtualMachineUniqueId}` / `{containerId}` / `{roleInstanceName}`

```kql
let queryFrom = datetime('{Start}');
let queryTo   = datetime('{End}');
cluster('Azurecm.kusto.windows.net').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp between (queryFrom .. queryTo)
| where case(
    isnotempty('{virtualMachineUniqueId}'), virtualMachineUniqueId =~ '{virtualMachineUniqueId}',
    isnotempty('{containerId}'),            containerId =~ '{containerId}',
    isnotempty('{roleInstanceName}'),       roleInstanceName =~ '{roleInstanceName}',
    false)
| summarize arg_max(PreciseTimeStamp, *) by tenantName, virtualMachineUniqueId, containerId, roleInstanceName
| project-reorder creationTime, PreciseTimeStamp, roleInstanceName, subscriptionId, containerType,
    virtualMachineUniqueId, containerId, nodeId, Tenant, tenantName,
    availabilitySetName, billingType, roleType, RegionFriendlyName
```

---

### Query: Host Node Fault Events
**Scenario**: Determine whether a platform-initiated node fault event occurred on the host during the VM impact window; use `FaultCode` and `Reason` to classify the fault type
**Tables**: `AzureCM.AzureCM.TMMgmtNodeFaultEtwTable`
**Params**: `{Start}`, `{End}`, `{nodeId}`

```kql
let queryFrom = datetime('{Start}');
let queryTo   = datetime('{End}');
cluster("AzureCM.kusto.windows.net").database("AzureCM").TMMgmtNodeFaultEtwTable
| where PreciseTimeStamp between (queryFrom .. queryTo)
| where BladeID == '{nodeId}'
| summarize arg_max(PreciseTimeStamp, *) by Tenant, NodeId=BladeID, FaultCode, Reason
| project-reorder PreciseTimeStamp, Tenant, NodeId, FaultCode, Reason
```

---

### Query: Host Node State Snapshot
**Scenario**: Trace host node availability state and fault info over time; use to establish node health timeline alongside VM impact
**Tables**: `azcsupfollower.AzureCM.LogNodeSnapshot`
**Params**: `{Start}`, `{End}`, `{nodeId}`

```kql
cluster('azcsupfollower').database('AzureCM').LogNodeSnapshot
| where PreciseTimeStamp between(datetime('{Start}') .. datetime('{End}'))
| where nodeId == '{nodeId}'
| order by PreciseTimeStamp asc
| project StartTime = PreciseTimeStamp, Content = nodeState, nodeId, nodeAvailabilityState, containerCount, faultInfo
```

---

### Query: VM Container Health Snapshot
**Scenario**: Trace VM health state history over time — shows `containerLifecycleState`, `containerOsState` transitions; use to confirm VM was impacted and determine recovery time
**Tables**: `azcsupfollower.AzureCM.LogContainerHealthSnapshot`
**Params**: `{Start}`, `{End}`, `{containerId}`

```kql
cluster("azcsupfollower").database("AzureCM").LogContainerHealthSnapshot
| where PreciseTimeStamp between(datetime('{Start}') .. datetime('{End}'))
| where containerId == '{containerId}'
| order by PreciseTimeStamp asc
| project PreciseTimeStamp, containerLifecycleState, containerState, containerOsState,
    roleInstanceName, nodeId, containerId, faultInfo
```

---

### Query: VMA RCA Classification
**Scenario**: Get the RCA engine's root cause classification for a VM impact event — provides `RCAEngineCategory`, `RCALevel1/2/3`, impact duration, and availability state; excludes customer-initiated events；For example:bytedance VM RCA
**Tables**: `moseisley.vmadb.VMA()`
**Params**: `{Start}`, `{End}`, `{containerId}`

```kql
let queryFrom = datetime('{Start}');
let queryTo   = datetime('{End}');
cluster('moseisley.kusto.windows.net').database('vmadb').VMA()
| where PreciseTimeStamp between(queryFrom .. queryTo)
| where ContainerId == '{containerId}'
| where RCAEngineCategory != 'CustomerInitiated'
| extend DurationSec = datetime_diff("Second", EndTime, StartTime)
| extend DurationInMin = DurationSec / 60.0
| extend StartTime = format_datetime(StartTime, 'yyyy-MM-dd HH:mm:ss.fffffff'),
         EndTime   = format_datetime(EndTime,   'yyyy-MM-dd HH:mm:ss.fffffff')
| summarize arg_max(PreciseTimeStamp, *) by Cluster, StartTime, EndTime, AvailabilityState,
    TenantName, RoleInstanceName, VmUniqueId, ContainerId, NodeId, ResourceId,
    RCAEngineCategory, RCALevel1, RCALevel2, RCALevel3
| project-reorder PreciseTimeStamp, Cluster, StartTime, EndTime, DurationInMin, AvailabilityState,
    TenantName, RoleInstanceName, VmUniqueId, ContainerId, NodeId, ResourceId,
    RCAEngineCategory, RCALevel1, RCALevel2, RCALevel3, DurationSec
| order by PreciseTimeStamp asc
| take 1
```

---

### Query: VM Restart Events
**Scenario**: Get structured VM restart event timeline with `FailureSignature` and CSS wiki link for investigation guidance; use after VMA RCA to get actionable failure details
**Tables**: `moseisley.Air.GetVMRestartEvents()`
**Params**: `{Start}`, `{End}`, `{virtualMachineUniqueId}`

```kql
let queryFrom = datetime('{Start}');
let queryTo   = datetime('{End}');
cluster("moseisley.kusto.windows.net").database("Air").GetVMRestartEvents('{virtualMachineUniqueId}', queryFrom, queryTo)
| extend DurationSec   = datetime_diff("Second", ImpactEndTimeStamp, ImpactBeginTimeStamp)
| extend DurationInMin = DurationSec / 60.0
| project-reorder Timestamp, ImpactBeginTimeStamp, ImpactEndTimeStamp, ImpactDurationTimeSpan,
    DurationInMin, RoleInstanceName, SubscriptionId, VMUniqueId, ContainerId,
    ObjectIds, Cluster, TenantName, FailureSignature, AdditionalInfo, CssWikiLink
```

---

### Query: CRP API Operations (including GETs)
**Scenario**: Get full CRP API call history for a VM resource including read operations; use to correlate customer-side API calls with platform-side events; `StartTime` is back-calculated from e2e duration
**Tables**: `azcrp.crp_allprod.ApiQosEvent`
**Params**: `{Start}`, `{End}`, `{subscriptionId}`, `{resourceName}`

```kql
cluster('azcrp.kusto.windows.net').database('crp_allprod').ApiQosEvent
| where PreciseTimeStamp between(datetime('{Start}') .. datetime('{End}'))
| where subscriptionId == '{subscriptionId}'
| where resourceName == '{resourceName}'
| extend StartTime = datetime_add('Millisecond', -e2EDurationInMilliseconds, PreciseTimeStamp)
| project StartTime, EndTime = PreciseTimeStamp, resourceName, correlationId, operationId,
    operationName, httpStatusCode, resultCode, resultType, errorDetails,
    e2EDurationInMilliseconds, durationInMin = round(e2EDurationInMilliseconds / 60000.0, 2),
    requestEntity
```

---

### Query: CRP API Operations (excluding GETs / mutating only)
**Scenario**: Get only mutating CRP operations (PUT/POST/DELETE) for a VM resource; fewer rows and cleaner signal for change tracking and causation analysis
**Tables**: `azcrp.crp_allprod.ApiQosEvent_nonGet`
**Params**: `{Start}`, `{End}`, `{subscriptionId}`, `{resourceName}`

```kql
cluster('azcrp.kusto.windows.net').database('crp_allprod').ApiQosEvent_nonGet
| where PreciseTimeStamp between(datetime('{Start}') .. datetime('{End}'))
| where subscriptionId == '{subscriptionId}'
| where resourceName == '{resourceName}'
| extend StartTime = datetime_add('Millisecond', -e2EDurationInMilliseconds, PreciseTimeStamp)
| project StartTime, EndTime = PreciseTimeStamp, resourceName, correlationId, operationId,
    operationName, httpStatusCode, resultCode, resultType, errorDetails,
    e2EDurationInMilliseconds, durationInMin = round(e2EDurationInMilliseconds / 60000.0, 2),
    requestEntity
```

---

### Query: CRP Context Activity Trace
**Scenario**: Deep-dive trace of a CRP internal workflow by `activityId`; maps an operation to internal CRP caller chain and source files; use when API call succeeded but downstream behavior is unexpected
**Tables**: `azcrp.crp_allprod.ContextActivity`
**Params**: `{Start}`, `{End}`, `{activityId}`

```kql
cluster('azcrp').database('crp_allprod').ContextActivity
| where PreciseTimeStamp between(datetime('{Start}') .. datetime('{End}'))
| where activityId == '{activityId}'
| project PreciseTimeStamp, message, callerName, sourceFile
```

---

### Query: ASW Agent Case Volume (Last 90 Days)
**Scenario**: Calculate case volume by ASW engineer alias for incidents created in the last 90 days, scoped to ASW customer TPIDs and ASW queues; append a total row and sort by descending case volume
**Tables**: `bedrock.CSI.ASWQueue`, `bedrock.CSI.ASWCustomer`, `bedrock.CSI.ASWStakeholder`, `supportrptwus3prod.KPISupportData.AllCloudsSupportIncidentWithReferenceModelVNext`
**Params**: Optional `{StartTime}`, `{EndTime}` placeholders are declared but the filter currently uses `ago(90d)`

```kql
let ASWQueues = cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWQueue | project Queue;
let ASWCXTPID = cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWCustomer | project TPID;
let ASWAgentAlias = cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWStakeholder | where Role == "Engineer" | where BusinessUnit == "CSS-ASW" | project AgentAlias;
let StartTime = datetime(2025-01-01);
let EndTime = now();
let AgentData =
    cluster('supportrptwus3prod.westus3.kusto.windows.net').database('KPISupportData').AllCloudsSupportIncidentWithReferenceModelVNext
    | where CreatedDateTime >= ago(90d)
    | where Customer_TPID in (ASWCXTPID)
    | where CurrentQueueName in (ASWQueues)
    | where AgentAlias in (ASWAgentAlias | project AgentAlias)
    | summarize CaseVolume = count() by AgentAlias
    | join kind=leftouter (cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWStakeholder
        | project AgentAlias, AgentName) on AgentAlias
    | project AgentAlias, AgentName, CaseVolume;
let AggregatedTotals =
    AgentData
    | summarize TotalCaseVolume = sum(CaseVolume),
                 AgentCount = count()
    | extend AvgCaseVolume = TotalCaseVolume * 1.0 / AgentCount;
let TotalsRow =
    AggregatedTotals
    | extend AgentAlias = "Total", AgentName = "All Agents"
    | project AgentAlias, AgentName, TotalCaseVolume, AvgCaseVolume;
AgentData
| project AgentAlias, AgentName, CaseVolume
| union (
    TotalsRow
    | project AgentAlias, AgentName, CaseVolume = TotalCaseVolume
)
| order by CaseVolume desc
```

---

### Query: VM-Host Heartbeat State Transitions
**Scenario**: Trace VM-to-Host heartbeat state over time — use to determine if the platform considered the VM healthy during a customer-reported outage; `NoSignal` = heartbeat lost; `DoNotCare` = platform is performing a Redeploy/Migration; confirms control-plane vs data-plane split when VM is Healthy but SSH/Ping fails; also use to time-stamp exactly when Redeploy was initiated (`DoNotCare` transition = Redeploy start)
**Tables**: `vmainsight.Vmadiag.Atlas_VmStateTransitionEvent`
**Params**: `{Start}`, `{End}`, `{containerId}`

```kql
let queryFrom = datetime('{Start}');
let queryTo   = datetime('{End}');
cluster('vmainsight.kusto.windows.net').database('Vmadiag').Atlas_VmStateTransitionEvent
| where PreciseTimeStamp between(queryFrom .. queryTo)
| where ContainerId =~ '{containerId}'
| order by PreciseTimeStamp asc
| project PreciseTimeStamp, ContainerId, NodeId, HealthState, Reason, osIncarnationId
```

> **Key interpretation**:
> - `Healthy` → platform sees heartbeat — control-plane OK
> - `Unhealthy` → heartbeat lost briefly (often recovers in <2 min for transient faults)
> - `DoNotCare` → Redeploy/Migration initiated; VM identity will change after this
> - `NoSignal` → VM on new node, heartbeat not yet established
> - `osIncarnationId = 00000000-...` throughout → OS never rebooted (cold reboot excluded)

---

### Query: VFP Restore Failures on Node
**Scenario**: Check whether the VFP agent process crashed and failed to restore rules on a host node; if this table returns **no rows** during a network outage, the VFP process is alive — the failure is a **silent rule programming failure** (NMAgent partial programming), not a VFP process crash; combine with `Atlas_VmStateTransitionEvent` to confirm control-plane vs data-plane split
**Tables**: `vmainsight.Vmadiag.vfp_restore_fails`
**Params**: `{Start}`, `{End}`, `{nodeId}`

```kql
let queryFrom = datetime('{Start}');
let queryTo   = datetime('{End}');
cluster('vmainsight.kusto.windows.net').database('Vmadiag').vfp_restore_fails
| where PreciseTimeStamp between(queryFrom .. queryTo)
| where NodeId =~ '{nodeId}'
| order by PreciseTimeStamp asc
| project PreciseTimeStamp, NodeId, ContainerId, FailReason
```

> **If no rows**: VFP process did not crash → suspect silent NMAgent VFP programming failure; escalate to network team with `Atlas_VmStateTransitionEvent` evidence.

---

### Query: VM Identity Change History
**Scenario**: Detect whether a VM was Redeployed or Live Migrated over a time window by tracking `containerId` and `nodeId` changes in `LogContainerSnapshot`; each unique (containerId, nodeId) pair = one placement history entry; use to confirm number of Redeployments, map before/after identity, and determine exact transition time; note: **`ToBeDestroyedOnNode` timestamp = Redeploy initiation**, not the customer-visible recovery time
**Tables**: `azcsupfollower.AzureCM.LogContainerSnapshot`
**Params**: `{Start}`, `{End}`, `{subscriptionId}`, `{roleInstanceName}`

```kql
let queryFrom = datetime('{Start}');
let queryTo   = datetime('{End}');
cluster('azcsupfollower.kusto.windows.net').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp between(queryFrom .. queryTo)
| where subscriptionId =~ '{subscriptionId}'
| where roleInstanceName =~ '{roleInstanceName}'
| summarize
    FirstSeen = min(PreciseTimeStamp),
    LastSeen  = max(PreciseTimeStamp)
    by containerId, nodeId, roleInstanceName, subscriptionId
| order by FirstSeen asc
| extend IdentityChange = row_number() - 1
| project FirstSeen, LastSeen, containerId, nodeId, roleInstanceName, IdentityChange
```

> **Output interpretation**: Each row is one "life" of the VM on a given node. `IdentityChange = 0` = original placement; each increment = one Redeploy or Migration.

