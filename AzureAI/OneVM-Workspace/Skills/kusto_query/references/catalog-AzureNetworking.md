# Kusto Catalog — AzureNetworking Wiki

Source: AzureNetworking ADO Wiki (`/Tooling/Kusto/Kusto Clusters and Requirements`, `/Tooling/Kusto/Kusto Examples`, `/Tooling/Kusto/How to Determine Kusto Table Latency`, plus per-service log-source pages)
Last synced: 2025-08-02

> Use `scripts/kusto_catalog_builder.py --wiki-project AzureNetworking` to refresh this file.

---

## Natural Language Semantic Glossary (for Agent Routing)

| User natural language cues | Cluster.DB | Typical interpretation |
|----------------------------|------------|------------------------|
| ARM操作失败、资源创建失败、CRUD失败、PUT/DELETE报错 | `Armprodgbl.eastus → ARMProd` | Control plane: HttpIncomingRequests, EventServiceEntries |
| NRP错误、网络资源操作失败、VNet/NSG/PIP/UDR操作 | `Nrp.mdsnrp` | QosEtwEvent (mirrors ASC Operations), FrontendOperationEtwEvent |
| VPN断连、隧道断开、IKE协商失败、隧道抖动 | `Hybridnetworking.aznwmds` | TunnelEventsTable |
| VPN Gateway事件、GatewayId相关事件 | `Hybridnetworking.aznwmds` | GatewayTenantEventsTable |
| ExpressRoute电路、ExR连接、BGP对等、授权密钥 | `Hybridnetworking.aznwmds` | CircuitTable, GatewayManagerLogsTable, GatewayTenantLogsTable |
| ExR陈旧连接、ExR关联的VNet | `Hybridnetworking.aznwmds` | VnetConfigTable |
| ExR监控告警 | `Hybridnetworking.aznwmds` | ExpressRouteMonitoringLogsTable |
| Application Gateway操作变更、AppGW配置差异、AppGW故障状态 | `Hybridnetworking.aznwmds` | AppGwOperationHistoryLogsTable, AsyncWorkerLogsTable |
| Application Gateway AGIC、AKS Ingress Controller | `Aznw.aznwcosmos` | ApplicationGatewaysExtendedLatest |
| vWAN、Virtual Hub、vHub路由、Hub信息 | `Hybridnetworking.aznwmds` | VirtualHubTable, VirtualWanTable |
| vWAN Route Service、BGP路由传播、路由通告 | `Hybridnetworking.aznwmds` | RouteServiceTable, RouteServiceBgpLogsTable, RouteServiceRoutingLog |
| vWAN VPN Gateway子网关 | `Hybridnetworking.aznwmds` | VpnGatewayTable, VpnGatewayChildGatewayTable |
| vWAN ExR Gateway | `Hybridnetworking.aznwmds` | ExpressRouteGateway |
| 负载均衡器操作、SLB、ILB | `Azslb.azslbmds` | BasicILB (及其他) |
| DDoS攻击、流量丢弃、DDoS PCAP | `Aznwddos.centralus.cnsgeneva` | DDoSPcapFlowLogs |
| Private Link、Private Endpoint CRUD失败 | `Nrp.mdsnrp` | QosEtwEvent |
| AFD、Azure Front Door、CDN操作 | `Azurecdn.azurecdnmds` | AfdCustomDomainSnapshot, ApiAnalytics, OperationSnapshot |
| DNS流量管理、Traffic Manager | `Aztmmon` | (DNS monitoring tables) |
| DNS Private Resolver、Managed Resolver | `Managedresolver.westus2` | (Private DNS Resolver tables) |
| 自动扩缩容、Insights监控、Autoscale | `Azureinsights.Insights` | TelemetryV2 |
| VNet加密、Sirius、SmartNIC、服务节点 | `Sirius.eastus.siriusLogs` | SiriusServicingInfoTable, SiriusCriticalFailureTable |
| 计算资源、CRP、VM API | `Azcrp.crp_allprod` | ApiQosEvent, VMApiQosEvent |
| vWAN资源图谱、网络拓扑 | `Argwus2nrpone.westus2.AzureResourceGraph` | Resources |

### Interpretation Priority

1. 对于大多数网络CRUD问题：先查 `Nrp.mdsnrp.QosEtwEvent`（最接近ASC Operations视图），再用 `correlationId` 深入 `FrontendOperationEtwEvent`，最后追溯到 `Armprodgbl/ARM` 层。
2. VPN/ExR/AppGW 问题均在 `Hybridnetworking.aznwmds` 内，通过 `GatewayId` 或 `ServiceKey` 定位。
3. Fairfax (Government) 等效集群：`Aznwff.kusto.usgovcloudapi.net`（database: `aznwmds`）覆盖 NRP、VPN、ExR、AppGW 所有表；`Armff.kusto.usgovcloudapi.net`（database: `armff`）覆盖 ARM。

---

## ARM (Azure Resource Manager) → ARMProd / Requests

**URI (Global)**: `https://Armprodgbl.eastus.kusto.windows.net` → database: `ARMProd` (use `Unionizer` function to fan out)  
**URI (Regional)**:
- East US: `https://Armprodeus.eastus.kusto.windows.net` → database: `Requests`
- West Europe: `https://Armprodweu.westeurope.kusto.windows.net` → database: `Requests`
- Southeast Asia: `https://Armprodsea.southeastasia.kusto.windows.net` → database: `Requests`

**Access**: CoreIdentity SG `WA CTS-14817` (FTE) or `ARM Logs` (non-FTE)  
**Retention**: 45 days. **Latency**: ~5–7 min.  
**Purpose**: Azure Resource Manager control plane — all CRUD API requests, audit events, outgoing calls for any ARM-managed resource.  
**Tip**: Use the global `Armprodgbl` cluster with `Unionizer` or `macro-expand ARMProdEG` to discover which regional cluster holds the data, then re-query regionally for full detail.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `HttpIncomingRequests` | Incoming ARM API requests (all CRUD) | TIMESTAMP, subscriptionId, operationName, httpMethod, httpStatusCode, targetUri, correlationId, userAgent, durationInMilliseconds |
| `EventServiceEntries` | ARM audit log / event service entries | TIMESTAMP, subscriptionId, operationName, resourceUri, status, correlationId, claims |
| `HttpOutgoingRequests` | Outgoing ARM requests to downstream RP | TIMESTAMP, subscriptionId, operationName, httpStatusCode, correlationId, errorCode |

### Key KQL: ARM CRUD Lookup (Two-step: global → regional)

```kusto
// Step 1 — Find which regional cluster via global Unionizer
cluster('Armprodgbl.eastus').database('ARMProd').Unionizer('Requests', 'HttpIncomingRequests')
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where subscriptionId == '{SubscriptionId}'
| where httpMethod != "GET"
| project TIMESTAMP, TaskName, operationName, httpMethod, httpStatusCode,
    targetUri, correlationId, $cluster
| order by TIMESTAMP asc

// Step 2 — Query regional cluster directly (replace with $cluster value from above)
cluster('Armprodeus.eastus').database('Requests').HttpIncomingRequests
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where subscriptionId == '{SubscriptionId}'
| where httpMethod != "GET"
| project TIMESTAMP, operationName, httpMethod, httpStatusCode, correlationId,
    targetUri, durationInMilliseconds
```

### Key KQL: ARM via macro-expand (all-in-one)

```kusto
// Run from: armprodgbl.eastus.kusto.windows.net / database: ARMProd
macro-expand isfuzzy=true ARMProdEG as X
(
    X.database('Requests').HttpIncomingRequests
    | extend $cluster = X.$current_cluster_endpoint
    | union (X.database('Requests').HttpOutgoingRequests)
    | where subscriptionId == '{SubscriptionId}'
    | where PreciseTimeStamp >= datetime({Start})
    | where httpMethod != "GET"
    | order by PreciseTimeStamp asc
    | project PreciseTimeStamp, TaskName, correlationId, operationName, httpMethod,
        httpStatusCode, targetResourceType, targetUri, userAgent, durationInMilliseconds
)
```

**Fairfax**: `https://Armff.kusto.usgovcloudapi.net` → database: `armff`

---

## NRP (Network Resource Provider) → mdsnrp

**URI**: `https://Nrp.kusto.windows.net` → database: `mdsnrp`  
**Access**: Included in `WA CTS-14817`  
**Retention**: ~185 days. **Latency**: ~1–3 min.  
**Purpose**: Network Resource Provider internal operations — most detailed view of NRP-layer success/failure, error codes, and operation traces for all networking resources (VNet, NSG, PIP, LB, NIC, Private Endpoint, AppGW, etc.).

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `QosEtwEvent` | NRP operation QoS — mirrors ASC Operations view; success/fail, error codes per request | TIMESTAMP, SubscriptionId, OperationName, HttpMethod, Success, StatusCode, ErrorCode, InternalErrorCode, ResourceName, Region, DurationInMilliseconds, CorrelationRequestId, ClientOperationId, UserError, AsynchronousDurationInMilliseconds |
| `FrontendOperationEtwEvent` | Detailed NRP frontend operation trace; use for root cause deep-dive after locating correlationId in QosEtwEvent | TIMESTAMP, SubscriptionId, Region, HttpMethod, OperationId, CorrelationRequestId, Message, EventCode, ResourceGroup, ResourceType, ResourceName, ClientOperationId, Sequence |

### Key KQL: NRP Failure Investigation

```kusto
// QoS view — failure summary (mirrors ASC Operations tab)
cluster('Nrp').database('mdsnrp').QosEtwEvent
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where SubscriptionId == "{SubscriptionId}"
| where Success == false
| project TIMESTAMP, HttpMethod, OperationName, Success, StatusCode, UserError,
    ResourceName, InternalErrorCode, ErrorCode, ErrorDetails,
    DurationInMilliseconds, Region, CorrelationRequestId, OperationId
| order by TIMESTAMP asc
```

```kusto
// Non-GET operations for a resource by name
cluster('Nrp').database("mdsnrp").QosEtwEvent
| where PreciseTimeStamp between (datetime({Start}) .. datetime({End}))
| where SubscriptionId == "{SubscriptionId}"
| where ResourceName == "{ResourceName}"
| where HttpMethod != "GET"
| project PreciseTimeStamp, OperationName, UserError, Success, ErrorDetails,
    OperationId, CorrelationRequestId, StartTime, AsynchronousDurationInMilliseconds
```

```kusto
// Detailed trace using correlationId from ARM or ASC
cluster('nrp.kusto.windows.net').database('mdsnrp').FrontendOperationEtwEvent
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where Region == "{Region}"
| where SubscriptionId == "{SubscriptionId}"
| where CorrelationRequestId == "{CorrelationId}"
| order by PreciseTimeStamp asc
| project PreciseTimeStamp, CorrelationRequestId, EventCode, Message, Sequence
```

**Fairfax**: `https://Aznwff.kusto.usgovcloudapi.net` → database: `aznwmds` (QosEtwEvent + FrontendOperationEtwEvent)

---

## Hybridnetworking → aznwmds (VPN / ExpressRoute / AppGW / vWAN / Gateway Manager)

**URI**: `https://Hybridnetworking.kusto.windows.net` → database: `aznwmds`  
**Access**: Included in `WA CTS-14817`  
**Retention**: ~90 days (most tables). **Latency**: 4–20 min depending on table.  
**Purpose**: Gateway Manager, VPN Gateway, ExpressRoute, Application Gateway, vWAN (Virtual Hub, Route Service), BGP routing — operations and configuration history.

### VPN / Gateway Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `TunnelEventsTable` | VPN tunnel state changes: connect/disconnect, planned failover, DPD timeout, host maintenance | TIMESTAMP, GatewayId, RoleInstance, Message, DownTimeInMilliSeconds, IsPlannedFailover, TunnelName, TunnelStateChangeReason, NegotiatedSAs |
| `GatewayTenantEventsTable` | Generic gateway tenant events | TIMESTAMP, GatewayId, RoleInstance, Message |
| `GatewayTenantLogsTable` | BGP route ingress/egress logs for VPN/ExR child gateways | TIMESTAMP, GatewayId, Message (contains route CIDR) |
| `GatewayManagerLogsTable` | Gateway Manager internal logs; used to look up ExR authorization key and correlate NRP OperationId | TIMESTAMP, NrpUri, Message, ActivityId, CustomerSubscriptionId, ServicePrefix |

**TunnelStateChangeReason decode**:
| Value | Meaning |
|-------|---------|
| `GlobalStandby` | Planned failover / active-passive switch |
| `RemotelyTriggered` | Customer side (on-prem) triggered reset |
| `DPD timed out` | Dead Peer Detection failure — actual connectivity loss |
| `Standby changed` | Host maintenance (active-active gateway) |

### Key KQL: VPN Tunnel Disconnect Investigation

```kusto
cluster("hybridnetworking").database("aznwmds").TunnelEventsTable
| where GatewayId == "{GatewayId}"
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| project TIMESTAMP, RoleInstance, Message, DownTimeInMilliSeconds,
    IsPlannedFailover, TunnelName, TunnelStateChangeReason, NegotiatedSAs
```

```kusto
// GatewayManagerLogs — trace NRP OperationId through Gateway Manager
cluster('HybridNetworking').database('aznwmds').GatewayManagerLogsTable
| where * contains "{OperationIdFromNRP}"
| where PreciseTimeStamp >= datetime("{Start}") and PreciseTimeStamp <= datetime("{End}")
| project PreciseTimeStamp, Message, ActivityId, CustomerSubscriptionId
```

### ExpressRoute Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `CircuitTable` | ExR circuit details, service provider, port info | TIMESTAMP, AzureServiceKey, AzureSubscriptionId, Location, ServiceProviderName, PortPairId |
| `VnetConfigTable` | VNet config linked to ExR circuit — used to find stale connections or identify GatewayId | TIMESTAMP, ServiceKey, VNetId, VNetName, GatewayId |
| `ExpressRouteMonitoringLogsTable` | ExR monitoring events | TIMESTAMP, PreciseTimeStamp |
| `ExpressRouteGateway` | ExR Gateway in vWAN hub (ExR GW ARM ID, child gateway ID) | TIMESTAMP, ExpressRouteGatewayArmId, ExpressRouteGatewayName, ExRGWID |

### Key KQL: ExpressRoute Stale Connection Lookup

```kusto
cluster('hybridnetworking').database('aznwmds').VnetConfigTable
| where ServiceKey == "{ExRServiceKey}"
| where PreciseTimeStamp >= datetime("{Start}") and PreciseTimeStamp <= datetime("{End}")
| project VNetId, VNetName, GatewayId
```

```kusto
// ExR authorization key lookup via GatewayManagerLogsTable
cluster('HybridNetworking').database('aznwmds').GatewayManagerLogsTable
| where Message contains "{AuthorizationKey}"
| where PreciseTimeStamp >= datetime("{Start}") and PreciseTimeStamp <= datetime("{End}")
| project PreciseTimeStamp, Message, ActivityId, CustomerSubscriptionId
```

### Application Gateway Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `AppGwOperationHistoryLogsTable` | AppGW configuration change history — shows exactly what was added/removed (diff format) per operation; covers v1/v2/WAF. Latency ~4 min | PreciseTimeStamp, GatewayId, GatewayName, OperationType, OperationName, ActivityId, OperationId, CorrelationRequestId, ConfigDiff, ResourceDiff, NewConfig, OldConfig, Status, DurationInSecond, SequenceNumber, IsNewGateway, UpdateOperationType, FastUpdateResult |
| `AsyncWorkerLogsTable` | AppGW async worker logs — internal processing details for AppGW operations | TIMESTAMP, OperationId, OperationName, Message, CustomerSubscriptionId |

### Key KQL: Application Gateway Config Change Diff

```kusto
// What changed on an AppGW? (ConfigDiff shows +/- for added/removed config)
cluster("Hybridnetworking").database("aznwmds").AppGwOperationHistoryLogsTable
| where PreciseTimeStamp > ago(1d)
| where GatewayId =~ "{GatewayId}"
| where isnotempty(ConfigDiff)
| extend OrderNr = toint(substring(SequenceNumber, 0, indexof(SequenceNumber, "/")))
| order by StartTimeUtc asc, OrderNr asc
| project StartTimeUtc, OrderNr, ConfigDiff, CorrelationRequestId, ActivityId,
    NewConfig, OldConfig, Status
```

```kusto
// Track when a specific listener/rule was added or deleted (large time window)
let AutoscaleInstanceRefreshOp = toscalar(
    cluster("Hybridnetworking").database("aznwmds").AsyncWorkerLogsTable
    | where PreciseTimeStamp between (datetime({Start}) .. datetime({End}))
    | where OperationName == "PutVMSSApplicationGatewayWorkItem"
    | where Message contains "Updating Instance List"
    | where Message contains "{ListenerName}"
    | project "AutoscaleRefreshInstanceDetails"
);
cluster("Hybridnetworking").database("aznwmds").AppGwOperationHistoryLogsTable
| where PreciseTimeStamp between (datetime({Start}) .. datetime({End}))
| where GatewayName == "{GatewayName}"
| where OperationName == "PutVMSSApplicationGatewayWorkItem"
| where ResourceDiff contains "{ListenerName}"
| summarize ConfigDiff=make_list(ConfigDiff), ResourceDiff=make_list(ResourceDiff)
    by StartTimeUtc, Tenant, OperationType, OperationName, ActivityId, OperationId,
    Status, DurationInSecond, IsNewGateway, GatewayName, UpdateOperationType,
    FastUpdateResult, FastUpdateDurationInSecond
| project StartTimeUtc, OperationName,
    UpdateOperationType=coalesce(AutoscaleInstanceRefreshOp, UpdateOperationType),
    GatewayName, Status, DurationInSecond, ResourceDiff=strcat_array(ResourceDiff, ""),
    ConfigDiff=strcat_array(ConfigDiff, "")
```

```kusto
// AsyncWorkerLogs — trace by NRP OperationId
cluster('HybridNetworking').database('aznwmds').AsyncWorkerLogsTable
| where OperationId == "{OperationIdFromNRP}"
| where PreciseTimeStamp >= datetime("{Start}") and PreciseTimeStamp <= datetime("{End}")
| project PreciseTimeStamp, Message, OperationId, OperationName, CustomerSubscriptionId
```

### vWAN Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `VirtualHubTable` | vWAN Virtual Hub info — address space, routing preference, ARM ID | TIMESTAMP, CustomerSubscriptionId, HubName, VnetName, AddressSpace, HubRoutingPreference, ArmId, ArmGuid, VpnGatewayArmId, ExpressRouteGatewayArmId |
| `VirtualWanTable` | vWAN instance info | TIMESTAMP, CustomerSubscriptionId, ArmGuid |
| `VirtualHubVnetConnectionTable` | Spoke VNet connections to vHub | TIMESTAMP, HubArmGuid, ConnectedVnetArmId |
| `VpnGatewayTable` | VPN Gateway within vHub | TIMESTAMP, VpnGatewayArmId, Name |
| `VpnGatewayChildGatewayTable` | Maps ARM VPN GW → child GatewayId (needed to query TunnelEventsTable) | TIMESTAMP, VpnGatewayArmId, GatewayId |
| `RouteServiceTable` | vWAN Route Service configuration: ASN, BGP communities, VIPs | TIMESTAMP, RouteServiceId, EnabledFeatures, ASN, BgpCommunities, NMAgentVIP, RouteServiceVIPs, HubArmId |
| `RouteServiceLogsTable` | Route Service change-history log | TIMESTAMP, RouteServiceId, RoleInstance, Message |
| `RouteServiceBgpLogsTable` | BGP protocol log for Route Service (route advertisements/withdrawals) | TIMESTAMP, DeploymentId, VirtualNetworkId, Message |
| `RouteServiceRoutingLog` | Route updates processed by Route Service | TIMESTAMP, RouteServiceId, RoleInstance, Message |
| `RouteServicePeerConfigTable` | BGP peer configuration for Route Service | TIMESTAMP, RouteServiceId, PeerIp, PeerAsn, PeerType, PeerVipAddress, PeerWeight |

### Key KQL: vWAN Hub Lookup

```kusto
cluster("Hybridnetworking.kusto.windows.net").database("aznwmds").VirtualHubTable
| where CustomerSubscriptionId == "{SubscriptionId}"
| where TIMESTAMP >= ago(15d)
| project TIMESTAMP, CustomerSubscriptionId, HubName, AddressSpace, HubRoutingPreference,
    ArmId, ArmGuid, VpnGatewayArmId, ExpressRouteGatewayArmId
```

```kusto
// Resolve ARM VpnGateway → GatewayId (needed for TunnelEventsTable)
cluster("Hybridnetworking.kusto.windows.net").database("aznwmds").VpnGatewayChildGatewayTable
| where VpnGatewayArmId contains "{VpnGatewayArmId}"
| project TIMESTAMP, VpnGatewayArmId, GatewayId
```

### Key KQL: vWAN BGP Route Tracing

```kusto
// Track route advertisement using Route Service BGP log
cluster('hybridnetworking.kusto.windows.net').database('aznwmds').RouteServiceBgpLogsTable
| where DeploymentId contains "armrg-{RouteServiceId}"
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where Message contains "{RouteCIDR}"
| where Message contains "Processing ingress route"
| parse Message with * 'Processing ingress route ' routeSource:string ':' * ') ' route:string ' ' *

// Route Service change history
cluster('hybridnetworking.kusto.windows.net').database('aznwmds').RouteServiceLogsTable
| where RouteServiceId == "{RouteServiceId}"
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| project TIMESTAMP, RoleInstance, Message
```

**Fairfax equivalent**: `https://Aznwff.kusto.usgovcloudapi.net` → database: `aznwmds` (all tables above)

---

## Aznw → aznwcosmos (Application Gateway AGIC / AKS Ingress)

**URI**: `https://Aznw.kusto.windows.net` → database: `aznwcosmos`  
**Access**: `WA CTS-14817`  
**Purpose**: Application Gateway Ingress Controller (AGIC) metadata — lists AppGWs managed by Kubernetes ingress within a subscription.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `ApplicationGatewaysExtendedLatest` | Snapshot of all AppGWs in a subscription; filtered by `UserTags` to find AGIC-managed gateways | CustomerSubscriptionId, CloudCustomerName, TenantCountryCode, GatewayName, InstanceCount, GroupName, UserTags, Config |

### Key KQL: List AppGWs Controlled by AGIC

```kusto
cluster('Aznw').database('aznwcosmos').ApplicationGatewaysExtendedLatest
| where UserTags contains "managed-by-k8s-ingress"
| where CustomerSubscriptionId == "{SubscriptionId}"
| project CustomerSubscriptionId, CloudCustomerName, TenantCountryCode,
    GatewayName, UserTags
| order by CloudCustomerName asc
```

```kusto
// Count AGIC-managed AppGWs and associated AKS clusters
cluster('Aznw').database('aznwcosmos').ApplicationGatewaysExtendedLatest
| where UserTags contains "managed-by-k8s-ingress"
    or Config contains "k8s-fp"
    or Config contains "k8s-ag-ingress-fp"
| where CustomerSubscriptionId == "{SubscriptionId}"
| summarize sum(InstanceCount), count(), make_list(GatewayName),
    make_list(GroupName), make_list(UserTags)
```

---

## Azslb → azslbmds (Software Load Balancer)

**URI**: `https://Azslb.kusto.windows.net` → database: `azslbmds`  
**Access**: `WA CTS-14817`  
**Purpose**: Azure Software Load Balancer (Standard LB, Basic ILB) operations and health.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `BasicILB` | Basic Internal Load Balancer operations | (use `.getschema BasicILB` to enumerate) |

> Run `cluster('Azslb').database('azslbmds') | .show tables` to discover all available tables.

**Fairfax**: `https://Azslbff.kusto.usgovcloudapi.net`

---

## Azurecdn → azurecdnmds (Azure Front Door / CDN)

**URI**: `https://Azurecdn.kusto.windows.net` → database: `azurecdnmds`  
**Access**: `WA CTS-14817`  
**Retention**: ~90 days. **Latency**: ~1–6 min.  
**Purpose**: Azure Front Door (AFD) and CDN — domain snapshots, API analytics, operation history.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `AfdCustomDomainSnapshot` | AFD custom domain configuration snapshot | (domain, origin, status) |
| `ApiAnalytics` | API-level analytics for AFD/CDN requests | (endpoint, statusCode, requestCount) |
| `OperationSnapshot` | AFD/CDN operation history | (operationName, status, timestamp) |

> Afdmoi cluster (TA/EEE/PG restricted) contains additional AFD internal data.

---

## Azureinsights → Insights (Monitoring / Autoscale)

**URI**: `https://Azureinsights.kusto.windows.net` → database: `Insights`  
**Access**: IDWeb `Insight Kusto Users`  
**Retention**: ~30 days. **Latency**: ~8 min.  
**Purpose**: Azure Monitor / Autoscale telemetry — used for diagnosing monitor alerts, autoscale scale-in/out events.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `TelemetryV2` | Monitor/Autoscale telemetry events | (subscriptionId, resourceId, operationName, statusCode) |

---

## Aznwddos.centralus → cnsgeneva (DDoS Protection)

**URI**: `https://Aznwddos.centralus.kusto.windows.net` → database: `cnsgeneva`  
**Access**: IDWeb `Ddos Kusto access for Partners` (FTE only)  
**Purpose**: DDoS Protection PCAP flow logs — packet-level evidence of attack traffic and mitigation.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `DDoSPcapFlowLogs` | DDoS mitigation packet flow log — source/dest IP/port, protocol, mitigation action | TIMESTAMP, destPublicIpAddress, srcIpAddress, destPort, srcPort, protocolNumber, action |

### Key KQL: DDoS Flow Log Investigation

```kusto
cluster('aznwddos.centralus.kusto.windows.net').database('cnsgeneva').DDoSPcapFlowLogs
| where TIMESTAMP > ago(60d)
| where destPublicIpAddress in ("{PublicIP}")
| where protocolNumber == 17  // 17=UDP, 6=TCP, 1=ICMP
| project TIMESTAMP, destPublicIpAddress, srcIpAddress, destPort, srcPort, action
```

---

## Aztmmon (DNS Traffic Manager Monitoring)

**URI**: `https://Aztmmon.kusto.windows.net`  
**Access**: `WA CTS-14817`  
**Purpose**: Azure DNS and Traffic Manager monitoring logs.

> Table names not fully enumerated in wiki. Run `.show tables` to discover available tables.

---

## Managedresolver.westus2 (DNS Private Resolver)

**URI**: `https://Managedresolver.westus2.kusto.windows.net`  
**Access**: `WA CTS-14817`  
**Purpose**: Azure DNS Private Resolver / Managed Resolver logs.

> Table names not fully enumerated in wiki. Run `.show tables` to discover available tables.

---

## Argwus2nrpone.westus2 → AzureResourceGraph (Resource Graph)

**URI**: `https://Argwus2nrpone.westus2.kusto.windows.net` → database: `AzureResourceGraph`  
**Access**: CoreIdentity `ARG Networking Stamp Users`  
**Purpose**: Azure Resource Graph — full resource topology. Used in vWAN troubleshooting to look up resource address space and ARM metadata without customer access.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `Resources` | Full ARM resource metadata for all Azure resources | id, type, name, subscriptionId, resourceGroup, location, properties |

### Key KQL: vWAN Address Space Lookup via Resource Graph

```kusto
cluster('Argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where type == "microsoft.network/virtualhubs"
| where subscriptionId == "{SubscriptionId}"
| project name, location, properties.addressPrefix, properties.virtualWan
```

---

## Sirius.eastus → siriusLogs (VNet Encryption / SmartNIC)

**URI**: `https://Sirius.eastus.kusto.windows.net` → database: `siriusLogs`  
**Access**: AME credentials required (TA/EEE restricted)  
**Purpose**: Sirius = Azure VNet Encryption / SmartNIC servicing. Tracks provisioning, goal state, critical failures for encrypted VNET nodes.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `SiriusServicingInfoTable` | Node servicing info for VNet Encryption | (nodeId, servicing state, timestamp) |
| `SiriusCriticalFailureTable` | Critical failures in encryption provisioning | (nodeId, failureReason, timestamp) |
| `SiriusGrpcFailureTable` | gRPC channel failures to Sirius service | (nodeId, error, timestamp) |
| `SiriusMadariNotificationTable` | Madari notification events | (nodeId, event, timestamp) |
| `SiriusMadariSubscriptionTable` | Madari subscription state | (nodeId, subscriptionState) |
| `SiriusGoalStateRecievedTable` | Goal state updates received by Sirius agent | (nodeId, goalState, timestamp) |

---

## Azcrp → crp_allprod (Compute Resource Provider)

**URI**: `https://Azcrp.kusto.windows.net` → database: `crp_allprod`  
**Access**: CoreIdentity `Azc Kusto Log RO – 20100`  
**Retention**: ~365 days. **Latency**: ~1–7 min.  
**Purpose**: Compute Resource Provider — used in networking context for VM NIC attachment, VM creation failures affecting networking.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `ApiQosEvent` | CRP API QoS events | subscriptionId, operationName, httpStatusCode, durationMs, correlationId |
| `ContextActivity` | CRP context activity for complex multi-step operations | subscriptionId, operationName, correlationId |
| `VMApiQosEvent` | VM-specific API QoS events | subscriptionId, vmName, operationName, httpStatusCode |

---

## Additional Clusters (Reference Only)

These clusters are listed in the AzureNetworking Kusto Clusters page but have limited query examples in the wiki:

| Cluster | Database | Access | Purpose |
|---------|----------|--------|---------|
| `Aznwwan.kusto.windows.net` | — | `WA CTS-14817` | WAN internal |
| `Aznwsdn.kusto.windows.net` | — | `WA CTS-14817` | SDN internal |
| `Azphynet.kusto.windows.net` | — | IDWeb `aznwkustoreader` | Physical Network |
| `Ipam.kusto.windows.net` | — | IDWeb `IPAMv2-RO-USER` | IP Address Management |
| `Netcapplan.kusto.windows.net` | — | IDWeb `NetCapPlanKustoViewers` (FTE only) | Network Datapath / capacity |
| `Afdmoi.kusto.windows.net` | — | TA/EEE/PG restricted | Azure Front Door internal |
| `Azlinux.kusto.windows.net` | — | IDWeb `AzLinux Kusto Users` | Linux platform |
| `Aznwautotriage.kusto.windows.net` | — | `WA CTS-14817` | Auto-triage |
| `Azsc.kusto.windows.net` | — | `WA CTS-14817` | Azure Support Center |
| `Vmainsight.kusto.windows.net` | `vmadb` / `Air` | IDWeb `VMA KustoDB User` | VMA RCA (see catalog-AzureIaaSVM.md) |
| `Azurecm.kusto.windows.net` | `AzureCM` | CoreIdentity FC Log Read-Only (12894) | Compute Manager (see catalog-AzureIaaSVM.md) |
| `Icmcluster.kusto.windows.net` | `ACM.Publisher` | — | ICM incident notifications |
| `Xstore.kusto.windows.net` | — | — | Azure Storage |

---

## Fairfax (Azure Government) Cluster Map

| Public Cluster | Government Equivalent | Notes |
|---------------|----------------------|-------|
| `Nrp.kusto.windows.net` (mdsnrp) | `Aznwff.kusto.usgovcloudapi.net` (aznwmds) | Same table names |
| `Hybridnetworking.kusto.windows.net` (aznwmds) | `Aznwff.kusto.usgovcloudapi.net` (aznwmds) | AppGW, VPN, ExR, vWAN all in Aznwff |
| `Armprodgbl/eus/weu/sea` (ARMProd/Requests) | `Armff.kusto.usgovcloudapi.net` (armff) | HttpIncomingRequests, HttpOutgoingRequests |
| `Azslb.kusto.windows.net` (azslbmds) | `Azslbff.kusto.usgovcloudapi.net` | — |
| `Azurecm.kusto.windows.net` (AzureCM) | `Azurecmff.kusto.usgovcloudapi.net` | — |
| `Azportal` | `Azportalff` | Azure Portal |
| Other | `Gcwsbn1ff`, `Rdfeff`, `Rdosff` | Government-only clusters |

---

## Latency / Retention Quick Reference

| Cluster | Typical Latency | Typical Retention |
|---------|----------------|-------------------|
| NRP (`Nrp.mdsnrp`) | 1–3 min | ~185 days |
| ARM (`Armprod*.Requests`) | 5–7 min | ~45 days |
| Hybridnetworking (`aznwmds`) | 4–20 min (table-dependent) | ~90 days |
| Azurecdn (`azurecdnmds`) | 1–6 min | ~90 days |
| Azureinsights (`Insights`) | ~8 min | ~30 days |
| CRP (`Azcrp.crp_allprod`) | 1–7 min | ~365 days |

---

## Access Request Summary

| Access Group | Portal | Covers |
|-------------|--------|--------|
| `WA CTS-14817` | CoreIdentity | ARM (FTE), NRP, Hybridnetworking, Azslb, Azurecdn, Aznwwan, Aznwsdn, Aztmmon, Managedresolver, Aznwautotriage |
| `ARM Logs` | CoreIdentity | ARM (non-FTE only) |
| `Azc Kusto Log RO – 20100` | CoreIdentity | CRP (`Azcrp.crp_allprod`) |
| `ARG Networking Stamp Users` | CoreIdentity | Resource Graph (`Argwus2nrpone`) |
| `Ddos Kusto access for Partners` | IDWeb | DDoS (`Aznwddos.centralus`) — FTE only |
| `IPAMv2-RO-USER` | IDWeb | IPAM |
| `NetCapPlanKustoViewers` | IDWeb | Network Datapath — FTE only |
| `aznwkustoreader` | IDWeb | Physical Network (`Azphynet`) |
| `Insight Kusto Users` | IDWeb | Azure Monitor Insights |
| `VMA KustoDB User` | IDWeb | vMAInsight (shared with IaaSVM) |
| `AzLinux Kusto Users` | IDWeb | Linux platform cluster |
| AME credentials | SAW only | Sirius (`Sirius.eastus`), AKV logs |
