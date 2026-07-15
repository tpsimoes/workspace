# Application Gateway — 常用 Kusto 快查表 (Cheat-Sheet)

> 所有查询均为 **完整可 copy-run** 格式（带 `cluster().database().表` 前缀）。
> 使用前替换顶部 `let` 参数。时间用 UTC。
> 完整查询包见 [application-gateway.md](application-gateway.md)。

## 参数约定

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `_sub` | 客户订阅 ID | `"00000000-0000-0000-0000-000000000000"` |
| `_appgw` | Application Gateway 名称 | `"myAppGw"` |
| `_start` / `_end` | 调查时间窗 (UTC) | `datetime(2026-07-13 00:00:00)` |

---

## 1. 列出订阅下所有 App Gateway（含 SKU / VIP / State）

```kusto
let _sub = "<SubscriptionId>";
cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == _sub
| project SnapshotTime, GatewayName, SkuType, LocationConstraint, State, VirtualIPs, ResourceUri
```

## 2. 单个 App Gateway 最新配置摘要（listener / rule / WAF 模式）

```kusto
let _sub = "<SubscriptionId>";
let _appgw = "<AppGwName>";
cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == _sub and GatewayName == _appgw
| extend config = parse_json(Config)
| extend listenerCount = array_length(config["HttpListeners"]),
         rulesCount    = array_length(config["HttpLoadBalancingRules"]),
         isAzwaf  = binary_and(ApplicationGatewayFeatureFlag, 128) == 128,
         isModsec = binary_and(ApplicationGatewayFeatureFlag, 1)   == 1
| project SnapshotTime, GatewayName, SkuType, GatewayVersion, LocationConstraint,
          InstanceCount, listenerCount, rulesCount, isAzwaf, isModsec,
          VirtualIPs, State, ResourceUri
```

## 3. 配置变更历史（排查“什么时候变了”）

```kusto
let _sub = "<SubscriptionId>";
let _appgw = "<AppGwName>";
let _start = datetime(2026-07-12 00:00:00);
let _end   = datetime(2026-07-13 00:00:00);
cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedProdHistory
| where SnapshotTime between (_start .. _end)
| where CustomerSubscriptionId == _sub and GatewayName == _appgw
| extend config = parse_json(Config)
| project SnapshotTime, SkuType, GatewayVersion, InstanceCount,
          listenerCount = array_length(config["HttpListeners"]),
          rulesCount    = array_length(config["HttpLoadBalancingRules"]),
          AutoscaleConfiguration, State
| sort by SnapshotTime asc
```

## 4. 实例 → 容器/节点映射（定位到 host 做数据面排查）

```kusto
let _sub = "<SubscriptionId>";
let _appgw = "<AppGwName>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
let _gwId = toscalar(
    cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
    | where CustomerSubscriptionId == _sub and GatewayName == _appgw
    | distinct GatewayId);
cluster('hybridnetworking').database('aznwmds').AppGwToContainerId
| where PreciseTimeStamp between (_start - 2h .. _end)
| where GatewayId == _gwId
| distinct GatewayName, GatewayId, Region, Tenant=Cluster, RoleInstanceName,
           NodeId=toupper(NodeId), ContainerId, IpAddress, VMSize
```

## 5. 控制面操作（客户发起的 CRUD / 部署，含状态）

```kusto
let _sub = "<SubscriptionId>";
let _appgw = "<AppGwName>";
let _start = datetime(2026-07-12 00:00:00);
let _end   = datetime(2026-07-13 00:00:00);
union
    cluster('armprodsea.southeastasia').database('Requests').EventServiceEntries,
    cluster('armprodeus.eastus').database('Requests').EventServiceEntries,
    cluster('armprodweu.westeurope').database('Requests').EventServiceEntries
| where PreciseTimeStamp between (_start .. _end)
| where subscriptionId == _sub and resourceUri contains _appgw
| where operationName !contains "Authorization"
| project PreciseTimeStamp, operationName, status,
          AppGwName = tostring(split(resourceUri, "applicationGateways/")[1]),
          Operator  = tostring(parse_json(claims)["name"]), correlationId
| sort by PreciseTimeStamp asc
```

## 6. GWM 控制面活动摘要（后端配置下发结果 / 失败）

```kusto
let _sub = "<SubscriptionId>";
let _appgw = "<AppGwName>";
let _start = datetime(2026-07-12 00:00:00);
let _end   = datetime(2026-07-13 00:00:00);
let _uri = toscalar(
    cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
    | where CustomerSubscriptionId == _sub and GatewayName == _appgw
    | distinct ResourceUri);
cluster('Hybridnetworking').database('aznwmds').AppGwOperationHistorySummary(_uri, _start, _end)
| project GwmOperationStartTime, OperationCategory, GatewayManagerActivityId,
          SdkOperationStatus, AsyncOperationStatus, Diff
| sort by GwmOperationStartTime asc
```

## 7. ELB / 前端 VIP 健康与 SKU（502 时确认前端可用性）

```kusto
let _sub = "<SubscriptionId>";
let _appgw = "<AppGwName>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
let _vip0 = toscalar(
    cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
    | where CustomerSubscriptionId == _sub and GatewayName contains _appgw
    | project VIP = parse_json(VirtualIPs)[0]);
cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord
| where env_time between (_start - 6h .. _end + 1h)
| where Vip == _vip0
| summarize by Vip, VipUri, Type, SKU, CountHosts, Region, env_cloud_role
```

## 8. App Gateway NSG 规则（子网 NSG 是否挡了 65200-65535 探针端口）

```kusto
let _sub = "<SubscriptionId>";
let _appgw = "<AppGwName>";
let _start = datetime(2026-07-13 00:00:00);
let _end   = datetime(2026-07-13 06:00:00);
let _uri = toscalar(
    cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedProdHistory
    | where SnapshotTime between (_start - 1d .. _end)
    | where CustomerSubscriptionId == _sub and GatewayName == _appgw
    | distinct ResourceUri);
let _nsg = toscalar(
    cluster('Hybridnetworking').database('GatewayManager').GetAppGwNsg(_uri)
    | project nsgId);
cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where timestamp between (_start - 2d .. _end)
| where id in~ (_nsg)
| mv-expand rule = parse_json(properties)["securityRules"]
| project Name=rule["name"], Direction=rule["properties"]["direction"],
          Priority=toint(rule["properties"]["priority"]), Access=rule["properties"]["access"],
          Protocol=rule["properties"]["protocol"],
          SrcPrefix=rule["properties"]["sourceAddressPrefix"],
          DstPortRange=rule["properties"]["destinationPortRange"]
| sort by Priority asc
```

---

## 关键表速查

| 用途 | 集群 / 数据库 / 表 |
|------|---------------------|
| 最新配置/清单 | `cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd` |
| 配置历史 | `cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedProdHistory` |
| 实例→容器映射 | `cluster('hybridnetworking').database('aznwmds').AppGwToContainerId` |
| GWM 控制面日志 | `cluster('hybridnetworking').database('aznwmds').GatewayManagerLogsTable` |
| GWM 操作摘要(函数) | `cluster('Hybridnetworking').database('aznwmds').AppGwOperationHistorySummary(uri,start,end)` |
| ARM 控制面请求 | `cluster('armprod<region>').database('Requests').EventServiceEntries` |
| 前端 VIP 元数据 | `cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord` |
| VIP/DIP 健康探针 | `cluster('Azslb').database('azslbmds').VipHealthProbe` |

> **诊断日志（客户侧）：** 若 App Gateway 已开诊断，Access log / Firewall(WAF) log / Performance log 可在客户 Log Analytics 工作区用 `AzureDiagnostics | where ResourceType == "APPLICATIONGATEWAYS"` 查询（此为客户资源，非内部集群）。
