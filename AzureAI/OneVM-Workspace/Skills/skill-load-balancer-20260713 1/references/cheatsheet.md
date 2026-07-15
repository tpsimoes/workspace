# Load Balancer — 常用 Kusto 快查表 (Cheat-Sheet)

> 所有查询均为 **完整可 copy-run** 格式（带 `cluster().database().表` 前缀）。
> 使用前替换顶部 `let` 参数。时间用 UTC。
> 完整查询包见 [load-balancer.md](load-balancer.md)、[slb-vip.md](slb-vip.md)、[slb-deep-rca.md](slb-deep-rca.md)。

## 参数约定

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `_sub` | 客户订阅 ID | `"00000000-0000-0000-0000-000000000000"` |
| `_lbArmId` | LB 的 resourceGuid（见查询 1 输出 `LoadBalancerArmId`） | `"11111111-1111-1111-1111-111111111111"` |
| `_vip` | 前端 VIP / ILB 私网 IP | `"20.1.2.3"` |
| `_start` / `_end` | 调查时间窗 (UTC) | `datetime(2026-07-13 00:00:00)` |

---

## 1. 列出订阅下所有 Load Balancer（SKU / Tier / ELB/ILB）

```kusto
let _sub = "<SubscriptionId>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == _sub
| where timestamp between (_start - 1d .. _end)
| where type == "microsoft.network/loadbalancers"
| extend props = parse_json(properties)
| distinct ResourceId = id,
           LoadBalancerArmId = tostring(props["resourceGuid"]),
           SKU  = tostring(sku["name"]),
           Tier = tostring(sku["tier"]),
           location,
           ELB = iff(isnotempty(tostring(props["frontendIPConfigurations"][0]["properties"]["publicIPAddress"]["id"])), "Yes", "No"),
           ILB = iff(isnotempty(tostring(props["frontendIPConfigurations"][0]["properties"]["privateIPAddress"])), "Yes", "No")
```

## 2. 负载均衡规则 + 后端池 DIP/探针配置

```kusto
let _lbArmId = "<LoadBalancerArmId>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
cluster('Azslb').database('azslbmds').DipEndpointProbeHistoryEvent
| where TIMESTAMP between (_start - 3h .. _end)
| where NrpLoadBalancerId == _lbArmId
| distinct NrpLoadBalancerId, Vip, VipPort, DipCA, DipPort, ILBVipCA,
           ProbeType, ProbePort, Region, ContainerId
```

## 3. 健康探针历史（SLBv2 视角 — 后端为什么被标 Down）

```kusto
let _lbArmId = "<LoadBalancerArmId>";
let _vip = "<VIP>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
cluster('azslb.kusto.windows.net').database('azslbmds').SlbV2DipHealthProbeHistoryEvent
| where env_time between (_start .. _end)
| where LoadBalancerArmId == _lbArmId or VipAddress == _vip
| project env_time, env_cloud_role, HostAddress, VipAddress, Protocol, VipPort,
          DipAddress, DipPort, ProbeState, ProbeReason,
          EffectiveState, EffectiveReason, DipCA, ProbeId
| sort by env_time asc
```

## 4. SLB 健康事件（面向客户的健康状态变更）

```kusto
let _lbArmId = "<LoadBalancerArmId>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
cluster('Azslb').database('azslbmds').SlbHealthEvent
| where env_time between (_start .. _end)
| where LoadBalancerArmId == _lbArmId
| project env_time, VipOrIlbCA, env_cloud_role, HealthEventType,
          IsCustomerFacing, CustomerFacingHealthEventType, Description
| sort by env_time asc
```

## 5. VIP 健康探针 + Region 定位（进一步查 SLB ring）

```kusto
let _lbArmId = "<LoadBalancerArmId>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
cluster('Azslb').database('azslbmds').VipHealthProbe
| where env_time between (_start - 1h .. _end)
| where LoadBalancerArmId == _lbArmId
| distinct VipAddress, VipOrIlbPA, Region, LoadBalancerArmId
```

## 6. SLB Host Plugin 严重事件（宿主机侧 SLB HP 故障）

```kusto
let _nodeId = "<NodeId>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
cluster('azslb.kusto.windows.net').database('azslbmds').SlbHpCriticalEvent
| where TIMESTAMP between (_start .. _end)
| where NodeId == _nodeId
| project TIMESTAMP, DC, Cluster, NodeId, Level, Component, Category, Name, Function, Message
| sort by TIMESTAMP asc
```

## 7. NAT Gateway 清单（SNAT 耗尽排查起点）

```kusto
let _sub = "<SubscriptionId>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == _sub
| where timestamp between (_start - 2d .. _end)
| where type == "microsoft.network/natgateways"
| distinct name, id, location, sku = tostring(sku),
           ResourceGUID = tostring(parse_json(properties)["resourceGuid"])
```

## 8. NAT Gateway SNAT VIP 分配（确认出站公网 IP）

```kusto
let _sub = "<SubscriptionId>";
let _natgw = "<NATGatewayName>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
let _natId = toscalar(
    cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
    | where subscriptionId == _sub
    | where timestamp between (_start - 2d .. _end)
    | where type == "microsoft.network/natgateways" and name == _natgw
    | extend NatGatewayId = strcat("NGW_", tostring(parse_json(properties)["resourceGuid"]))
    | distinct NatGatewayId);
cluster('Azslb').database('azslbmds').NatGatewayAllocation
| where env_time between (_start - 1d .. _end)
| where NatGatewayId == _natId
| distinct SnatIpAddresses, Protocols, Subnets, IdleTimeoutInSeconds, EnableTcpReset, VnetId
```

---

## 关键表速查

| 用途 | 集群 / 数据库 / 表 |
|------|---------------------|
| LB / NAT GW 清单 | `cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources` |
| LB 规则+DIP/探针配置 | `cluster('Azslb').database('azslbmds').DipEndpointProbeHistoryEvent` |
| 探针历史 (SLBv2) | `cluster('azslb.kusto.windows.net').database('azslbmds').SlbV2DipHealthProbeHistoryEvent` |
| SLB 健康事件 | `cluster('Azslb').database('azslbmds').SlbHealthEvent` |
| VIP 健康探针 | `cluster('Azslb').database('azslbmds').VipHealthProbe` |
| SLB HP 严重事件 | `cluster('azslb.kusto.windows.net').database('azslbmds').SlbHpCriticalEvent` |
| VIP 元数据 | `cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord` |
| SLB slice/ring 信息 | `cluster('aznwsdn.kusto.windows.net').database('aznwmds').SlbSliceInfo` |
| NAT GW 分配 | `cluster('Azslb').database('azslbmds').NatGatewayAllocation` |

> **SNAT 端口耗尽提示：** Standard LB 默认无出站 SNAT；出站需显式配置（Outbound rule / NAT Gateway / Public IP on instance）。排查顺序：查询 1（确认 SKU）→ 查询 7/8（NAT GW / SNAT IP）→ 客户侧 `AzureDiagnostics` 的 `SNATConnectionCount` / `UsedSNATPorts` 指标。
