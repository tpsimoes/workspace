---
description: Deep-dive KQL queries for SLB/MUX node RCA — crash analysis, Service Fabric health, SLB exceptions, and repair tasks. Use when standard B01 SLB queries don't reveal root cause.
---

# SLB / MUX Deep RCA Kusto Queries

> **Source:** Field-validated queries from NAT Gateway / SLB MUX incident investigations  
> **Cluster:** `cluster('Azslb').database('azslbmds')`  
> **Last Updated:** 2026-02-26

## ⚠️ Critical Architecture Notes

### SLB MUX Nodes Are NOT in AzureCM
SLB MUX nodes are managed by **Service Fabric**, not standard Azure Compute Manager.
- ❌ `LogNodeSnapshot` / `LogContainerSnapshot` in AzureCM — will return **0 results** for MUX NodeIds
- ✅ Use `NodeHealthEvent` in **azslbmds** for SF-level health
- ✅ Use `SlbCritical` / `SlbException` in **azslbmds** for MUX process-level events

### Table Schema Differences in azslbmds
| Table | Timestamp Column | Role/Ring Column | Instance Column |
|-------|-----------------|------------------|-----------------|
| `SlbCritical` | `env_time` | `env_cloud_role` | `env_cloud_roleInstance` |
| `SlbException` | `env_time` | `env_cloud_role` | `env_cloud_roleInstance` |
| `SlbHealthEvent` | `env_time` | `env_cloud_role` | `env_cloud_roleInstance` |
| `NodeHealthEvent` | `TIMESTAMP` | `Role` | `NodeName` |
| `HealthSignalStateHistoryEvent` | `TIMESTAMP` | `Cluster` | `NodeId` / `Ip` |
| `HostActionHistoryEvent` | `TIMESTAMP` | `Cluster` | `Ip` |
| `BgpPeerStateSnapshotEvent` | `env_time` | `Ring` | `Node` / `NodeNumber` |
| `RepairTaskRecord` | `env_time` | `Ring` | — |

### RoleInstance Naming Convention
The same MUX node has **different names** across different tables:
| Context | Name Format | Example |
|---------|------------|---------|
| `LogContainerSnapshot` (AzureCM) | `SlbRingHostRole_IN_N` | `SlbRingHostRole_IN_3` |
| `SlbCritical` / `SlbException` | `SlbRingHostRole_N` | `SlbRingHostRole_3` |
| `SlbHealthEvent` | `SlbRingHostRole_N` | `SlbRingHostRole_2` |
| `NodeHealthEvent` | `SlbRingHostRole.N` | `SlbRingHostRole.3` |

### HealthSignalStateHistoryEvent — NOT for MUX Nodes
This table tracks **compute hosts** (standard VMs), not SF-managed SLB MUX nodes. Querying by MUX NodeId will return 0 results.

---

## MUX Process Crash Detection — SlbCritical

The **most important table** for MUX crash RCA. Records critical MUX service events including unexpected shutdowns.

```kql
// MUX Critical Events — detect crashes, unexpected shutdowns
let RingN = "{RingName}"; // e.g., "r296-bl-az"
let starttime = datetime({StartTime});
let endtime = datetime({EndTime});
cluster('Azslb').database('azslbmds').SlbCritical
| where env_time >= starttime and env_time <= endtime
| where env_cloud_role == RingN
| project env_time, env_cloud_roleInstance, ServiceType, Critical, Message, CallerFilePath, CallerLine
| order by env_time asc
```

**Key `Critical` values to look for:**
| Critical Value | Meaning |
|---------------|---------|
| `MuxShutdownUnexpected` | 🔴 MUX process crashed — **SMOKING GUN** for crash RCA |
| `LogDropped` | Telemetry loss during crash/recovery |
| `MuxUnifiedLwfDeviceControl` | VFP LWF driver reinitialization (recovery) |

**Typical crash evidence pattern:**
1. Last normal log entry → then **complete silence** (process dead)
2. After recovery: `MuxUnifiedLwfDeviceControl` reinit events
3. `MuxShutdownUnexpected` logged by Worker.cs:544 on restart

---

## MUX Exception Analysis — SlbException

Records MUX service exceptions including SDN Gateway reconnection failures after crash recovery.

```kql
// MUX Exceptions — bootstrap failures, reconnection issues
let RingN = "{RingName}";
let starttime = datetime({StartTime});
let endtime = datetime({EndTime});
cluster('Azslb').database('azslbmds').SlbException
| where env_time >= starttime and env_time <= endtime
| where env_cloud_role == RingN
| project env_time, env_cloud_roleInstance, ServiceType, Exception, Message, CallerFilePath, CallerLine
| order by env_time asc
```

**Key exceptions:**
| Exception | Meaning |
|-----------|---------|
| `WebException` | SDN Gateway connection refused — MUX trying to reconnect after crash |
| `SocketException` | Network-level connection failure |
| `TimeoutException` | SDN Gateway not responding |

---

## Service Fabric Health — NodeHealthEvent

Records Service Fabric Failover Manager (FM) health events. **Uses different schema than env_* tables.**

```kql
// Service Fabric FM — node up/down events
// ⚠️ Uses TIMESTAMP, Role, NodeName — NOT env_time, env_cloud_role
let RingN = "{RingName}";
let starttime = datetime({StartTime});
let endtime = datetime({EndTime});
cluster('Azslb').database('azslbmds').NodeHealthEvent
| where TIMESTAMP >= starttime and TIMESTAMP <= endtime
| where Role == RingN
| project TIMESTAMP, Role, NodeName, SourceId, Property, HealthState, Description
| order by TIMESTAMP asc
```

**Key findings to look for:**
| SourceId | Property | HealthState | Meaning |
|----------|----------|-------------|---------|
| `System.FM` | `State` | `Error` | "Fabric node is down" — SF cannot reach the node |
| `System.FM` | `State` | `Ok` | "Fabric node is up" — node recovered |
| `fabric:/System/InfrastructureService` | — | `Warning` | "StoppedVM" — Azure Fabric treats node as stopped |

**NodeName format:** `SlbRingHostRole.N` (dot separator, not underscore)

---

## SLB Data Plane Health — SlbHealthEvent by Ring

Records customer-facing data plane availability events. Use to correlate MUX crashes with VIP impact.

```kql
// SlbHealthEvent — data plane availability per MUX instance
let RingN = "{RingName}";
let starttime = datetime({StartTime});
let endtime = datetime({EndTime});
cluster('Azslb').database('azslbmds').SlbHealthEvent
| where env_time >= starttime and env_time <= endtime
| where env_cloud_role == RingN
| project env_time, env_cloud_roleInstance, HealthEventType, VipAddress, VipPort, 
    DipAddress, IsCustomerFacing, CustomerFacingHealthEventType, Description
| order by env_time asc
```

**Key HealthEventType values:**
| HealthEventType | Meaning |
|----------------|---------|
| `DataPathAvailabilityWarning` | VIP availability < 90% — customer-facing impact |
| `NoForwardingDip` | DIP has no forwarding path — traffic black-holed |

**RoleInstance naming:** `SlbRingHostRole_N` (underscore + number, NOT `IN_N`)

---

## BGP Peer State — BgpPeerStateSnapshotEvent

Check MUX BGP peering status with ToR switches.

```kql
// BGP peer state for MUX nodes
let RingN = "{RingName}";
let starttime = datetime({StartTime});
let endtime = datetime({EndTime});
cluster('Azslb').database('azslbmds').BgpPeerStateSnapshotEvent
| where env_time >= starttime and env_time <= endtime
| where Ring == RingN
| project env_time, Ring, Node, NodeNumber, MuxIP, PeerIP, State, RouteCount
| order by env_time asc
```

---

## Repair Task History — RepairTaskRecord

Check if any automated repair tasks were executed on the SLB ring.

```kql
// Repair tasks for SLB ring
let RingN = "{RingName}";
let starttime = datetime({StartTime});
let endtime = datetime({EndTime});
cluster('Azslb').database('azslbmds').RepairTaskRecord
| where env_time >= starttime - 1d and env_time <= endtime + 1d
| where Ring == RingN
| project env_time, Ring, TaskId, Action, State, Description, Executor, Impact
| order by env_time asc
```

---

## MUX Log Gap Detection — SlbCritical Timeline

Detect process death by finding gaps in MUX log telemetry. A live MUX emits logs every few seconds; a gap of >1 min strongly suggests process crash.

```kql
// Detect MUX log gaps — process death indicator
let RingN = "{RingName}";
let instanceN = "SlbRingHostRole_{N}"; // e.g., "SlbRingHostRole_3"
let starttime = datetime({StartTime});
let endtime = datetime({EndTime});
cluster('Azslb').database('azslbmds').SlbCritical
| where env_time >= starttime - 30m and env_time <= endtime + 30m
| where env_cloud_role == RingN
| where env_cloud_roleInstance == instanceN
| summarize LogCount=count() by bin(env_time, 1m)
| order by env_time asc
| render columnchart
```

---

## azslbmds Complete Table Inventory

All 50 tables available in `cluster('Azslb').database('azslbmds')`:

| Category | Tables |
|----------|--------|
| **SLB Core** | `SlbCritical`, `SlbException`, `SlbHealthEvent`, `SlbAuditEvent`, `SlbManagerEvent`, `SlbManagerAuditEvent` |
| **MUX / Node** | `NodeHealthEvent`, `BgpPeerStateSnapshotEvent`, `SlbOsVersionRecord`, `SlbMetadataVersionRecord` |
| **VIP / DIP** | `VipHealthProbe`, `VipMetadataSnapshotRecord`, `VipRangesSnapshotEvent`, `DipEndpointProbeHistoryEvent`, `SlbV2DipHealthProbeHistoryEvent`, `DipProberMetadata` |
| **NAT** | `MNatBandwidthRecord`, `MNatConnectionRecord`, `SnatServingTimeDistribution` |
| **Health / Repair** | `HealthSignalStateHistoryEvent`*, `HostActionHistoryEvent`*, `RepairTaskRecord`, `ReplicaHealthState` |
| **Goal State** | `GoalStateHistoryEvent`, `AdapterDriveGoalStateOperationEvent`, `HostManagerHostGoalStateMetadata` |
| **Infrastructure** | `AllocatorSnapshotEvent`, `AllocationEvent`, `DSSegmentOwnershipEvent`, `DSSegmentMigrationEvent`, `VmLocationMapMetadata`, `VmManagerAdminMetadata` |
| **SDN** | `SdnGatewayAuditEvent`, `SdnMetadataSnapshotRecord`, `SdnModuleMetadataSnapshotRecord`, `PubSubGatewayAuditEvent` |
| **HP (Health Prober)** | `SlbHpConfigHistoryEvent`, `SlbHpCriticalEvent`, `SlbHpProcessRunningStateEvent`, `SlbHpAdapterHealthIssueReportResultEvent`, `SlbHpDrainConnectionsHistoryEvent` |
| **AutoDri** | (see slb-vip.md — `AutoDriInfrastructureServiceJobInformation`, `AutoDriServiceInformation`) |
| **Other** | `CorrelatedTrace`, `SystemPerfCounterTable`, `ValidationEvent`, `ValidationServiceSnapshot`, `ImdsRequestHistoryEvent`, `OutboundProbeResultHistoryEvent`, `DdosPolicyManagerMetadata`, `MpmPrefixTransitionRecord`, `VipRangeManagerMetadata` |

\* `HealthSignalStateHistoryEvent` and `HostActionHistoryEvent` are for **compute hosts only**, not SF-managed MUX nodes.

### Tables That Do NOT Exist in azslbmds
These are commonly guessed but **do not exist**:
- ❌ `MuxActivityRecord`
- ❌ `MuxProberAvailabilityRecord`
- ❌ `MuxHealthRecord`
- ❌ `LogNodeSnapshot` (AzureCM only)
- ❌ `LogContainerSnapshot` (AzureCM only)

---

## SLB / MUX Node Failure Troubleshooting SOP

When investigating SLB MUX node failures (TOR Pingmesh drop, datapath availability impact):

### Step 1: Identify the Ring and Faulted Node
Use existing B01 queries in `slb-vip.md`:
- **Ring MUX Instance Information** → get all MUX nodes, NodeIds, ToR mapping
- **MUX Node TOR Pingmesh** → identify which node(s) had connectivity drop

### Step 2: Check MUX Process Crash (SlbCritical)
Query `SlbCritical` for `MuxShutdownUnexpected`. Also check for log gaps — a healthy MUX logs every few seconds; silence indicates process death.

### Step 3: Check Service Fabric Health (NodeHealthEvent)
Query `NodeHealthEvent` for "Fabric node is down" (Error) events. Note: uses `TIMESTAMP`/`Role`/`NodeName` schema, NOT `env_time`/`env_cloud_role`.

### Step 4: Check Data Plane Impact (SlbHealthEvent)
Query `SlbHealthEvent` by Ring to see `DataPathAvailabilityWarning` and `NoForwardingDip` events. This shows the blast radius (which VIPs affected).

### Step 5: Check Recovery (SlbException)
After crash recovery, MUX tries to reconnect to SDN Gateway. Query `SlbException` for `WebException` to see if reconnection was delayed.

### Step 6: Exclude Physical Network
Use existing B01 queries:
- **Discard and Error packet counter over T0 of MUX** (slb-vip.md)
- Physical network queries from `physical-network.md`

### Common Pitfalls
1. **Don't search AzureCM for MUX nodes** — they're SF-managed, not in LogNodeSnapshot
2. **roleInstance naming varies by table** — check the naming convention table above
3. **NodeHealthEvent uses TIMESTAMP, not env_time** — different schema from most azslbmds tables
4. **HealthSignalStateHistoryEvent is for compute hosts only** — not for MUX nodes
5. **MUX crash is often the root cause, not the network** — if TOR Pingmesh drops to 0% but ToR/T1 links are UP, suspect MUX process crash first
