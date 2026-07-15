---
description: KQL queries for Azure Load Balancer and NAT Gateway: health probes, SNAT, data path, NAT rules.
---

# Load Balancer & NAT Gateway Kusto Queries

> Source: Azure Networking B01 Dashboard (aka.ms/b01)
> Pages: Load Balancer, NAT Gateway

## Load Balancer

### LBs under this subscription(Data delay in few minutes)

```kql
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 1d and timestamp <= endtime
| where type == "microsoft.network/loadbalancers"
| distinct id, SKU=tostring(sku["name"]), Tier=tostring(sku["tier"]), location, ELB=tostring(parse_json(properties)["frontendIPConfigurations"][0]["properties"]["publicIPAddress"]["id"]), ILB=tostring(parse_json(properties)["frontendIPConfigurations"][0]["properties"]["privateIPAddress"]),LoadBalancerArmId=tostring(properties["resourceGuid"])
| extend ELB=case(isnotempty(ELB), "Yes", "No")
| extend  ILB=case(isnotempty(ILB), "Yes", "No")
| distinct ResourceID=id,LoadBalancerArmId, SKU, Tier, location, ELB, ILB
```

### LB Load Balancing Rule Configuration

```kql
let starttime = _startTime;
let endtime = _endTime;
let resourceuri = ResourceURI;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let LBArmId=LoadBalancerArmID;
cluster('Azslb').database('azslbmds').DipEndpointProbeHistoryEvent 
| where TIMESTAMP > starttime - 3h and TIMESTAMP <= endtime
| where NrpLoadBalancerId == LBArmId
| distinct  NrpLoadBalancerId,Vip, VipPort, DipCA, DipPort,ILBVipCA, ProbeType, ProbePort,Region, ContainerId
| join kind=leftouter (cluster('AzureCM').database('AzureCM').LogContainerSnapshot | where PreciseTimeStamp  > starttime - 2h and PreciseTimeStamp <= endtime ) on $left.ContainerId == $right.containerId
| where TIMESTAMP != ""
| extend VMdash=strcat("https://web.kusto.windows.net/dashboards/f9ee36ad-73f0-4ae6-b752-f8be89e9245c?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'),"Z&p-_endTime=",format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime,'HH:mm:ss'),"Z&p-SubIdOrContainerId=v-",subscriptionId,"&&p-VMName=",trim("_",roleInstanceName),"&p-DataPathScan=v-No#8ed1e2a2-d979-401b-9609-7580ad07ccd1")
| extend BackendVMInfo=pack(strcat(trim("_",roleInstanceName), "(", DipCA, ")"),  VMdash)
| summarize BackendVMCA=make_set(strcat(trim("_",roleInstanceName),"(", DipCA, ")")), BackendVMTroubleshooting=make_set(BackendVMInfo) by NrpLoadBalancerId,VipOrILBPA=Vip, VipPort, DipPort,ILBVipCA, ProbeType, ProbePort,Region,subscriptionId
| join kind=leftouter cluster('Azslb').database('azslbmds').VipMetadataSnapshotRecord on $left.VipOrILBPA == $right.Vip
| where env_time > starttime - 3h and env_time <= endtime
| distinct NrpLoadBalancerId,Region, VipOrILBPA=Vip, VipOrILBPASKU=SKU, ILBPrivateFrontendIP=ILBVipCA, VipPort, BackendVMCA=tostring(BackendVMCA),BackendVM=tostring(BackendVMTroubleshooting), DipPort, ProbeType, ProbePort, IsStandardDdosProtectionEnabledOnVnet
| project LoadBalancerArmId=NrpLoadBalancerId,Region, VipOrILBPA, VipOrILBPASKU, ILBPrivateFrontendIP, VipPort, BackendVMCA, DipPort, ProbeType, ProbePort, IsStandardDdosProtectionEnabledOnVnet,BackendVMTroubleshooting=parse_json(BackendVM)
| extend VIPOrILBPATroubleshoot=strcat("https://aka.ms/b01?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'),"Z&p-_endTime=",format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime,'HH:mm:ss'),"Z&p-VIP=v-",VipOrILBPA,"#a172102b-f768-4cc9-982f-0acc07d4765f")
```

### SLB Health Event

```kql
let starttime = _startTime;
let endtime = _endTime;
let resourceuri = ResourceURI;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let LBArmId=LoadBalancerArmID;
cluster('Azslb').database('azslbmds').SlbHealthEvent
| where env_time >= starttime and env_time <= endtime
| where LoadBalancerArmId == LBArmId
| project env_time,VipOrIlbCA, env_cloud_role, HealthEventType, IsCustomerFacing, CustomerFacingHealthEventType, Description

```

### LB Dashboard

```kql
let starttime = _startTime;
let endtime = _endTime;
let resourceuri = ResourceURI;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let LBArmId=LoadBalancerArmID;
cluster('Azslb').database('azslbmds').VipHealthProbe 
| where env_time > starttime - 1h and env_time <= endtime
| where LoadBalancerArmId == LBArmId
| distinct VipAddress, VipOrIlbPA, Region, LoadBalancerArmId
//| extend VIPInformation=strcat("https://portal.microsoftgeneva.com/s/109DD7E9?overrides=[{%22query%22:%22//*[id='Vip']%22,%22key%22:%22value%22,%22replacement%22:%22",VipAddress,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend BandwithUsage=strcat("https://portal.microsoftgeneva.com/s/3CA61B31?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbhp", Region,"%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", LoadBalancerArmId,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VIPAvailability=strcat("https://portal.microsoftgeneva.com/s/2438DA2C?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbv2",Region, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22",LoadBalancerArmId,"%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DipAvailability=strcat("https://portal.microsoftgeneva.com/s/4FFD22D2?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbv2",Region, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22",LoadBalancerArmId,"%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| distinct BandwithUsage, VIPAvailability, DipAvailability
| evaluate narrow()
| project Key=Column, Value

```

### LB Metadata

```kql
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let LBArmId=LoadBalancerArmID;
cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 1d and timestamp <= endtime
| where type == "microsoft.network/loadbalancers"
| distinct id, SKU=tostring(sku["name"]), Tier=tostring(sku["tier"]), location, ELB=tostring(parse_json(properties)["frontendIPConfigurations"][0]["properties"]["publicIPAddress"]["id"]), ILB=tostring(parse_json(properties)["frontendIPConfigurations"][0]["properties"]["privateIPAddress"]),LoadBalancerArmId=tostring(properties["resourceGuid"])
| extend ELB=case(isnotempty(ELB), "Yes", "No")
| extend  ILB=case(isnotempty(ILB), "Yes", "No")
| where LoadBalancerArmId == LBArmId
| extend ResourceGroup=tostring(split(id, "/")[4]),Name=tostring(split(id, "/")[8])
| distinct Name,ResourceGroup,LoadBalancerArmId, SKU, Tier, location, ELB, ILB,ResourceId=id
| evaluate narrow()
| project Key=Column, Value
```

### Health Probe History from SLBv2 perspective
```kql
let starttime = _startTime;
let endtime = _endTime;
cluster('azslb.kusto.windows.net').database('azslbmds').SlbV2DipHealthProbeHistoryEvent
| where env_time between (starttime .. endtime)
| where LoadBalancerArmId == LBArmId or VipAddress == Vip
| project env_time, env_cloud_role, env_cloud_roleInstance, HostAddress, VipAddress, Protocol, VipPort, DipAddress, DipPort, VnetId, VnetVip, PublicIpArmId, LoadBalancerArmId, ArmResourceRegion, ProbeState, ProbeReason, EffectiveState, EffectiveReason, DipCA, ProbeId, SourceMoniker
```

### SLB Host Plugin Critical Event
```kql
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
cluster('azslb.kusto.windows.net').database('azslbmds').SlbHpCriticalEvent
| where TIMESTAMP  between (starttime .. endtime)
| where NodeId == NodeID
| project TIMESTAMP, DC, Cluster, NodeId, Level, Component, Category, Name, ContextId, Function, Message, SourceMoniker
```

### SLB Mux (Ring Node) Info
```kql
let _pip = "<Azure PIP or ILB PA>";
let _region = "<Region Name>";      // e.g.) useast2, europewest, japaneast, etc.
let _dataSlice = materialize (
cluster('aznwsdn.kusto.windows.net').database('aznwmds').SlbVipRangeInfo
| where ipv4_is_in_any_range(_pip, Prefix )
| top 1 by DataIngestionTime
| project DataRingSlice
);
cluster('aznwsdn.kusto.windows.net').database('aznwmds').SlbSliceInfo
| where SliceName == toscalar(_dataSlice) and RegionId == _region
| top 1 by DataIngestionTime
| extend _rings = split(Rings,",")
| mv-expand _rings
| extend _ringName = strcat("Slb-", replace_regex(tostring(_rings), "^\\w+\\.", ""))
| project SliceName, _ringName
| join kind=leftouter (
    cluster('azurecm.kusto.windows.net').database('AzureCM').LogContainerSnapshot
    | where TIMESTAMP > ago(3d)
    | join kind=leftouter (
        cluster('azurecm.kusto.windows.net').database('AzureCM').LogNodeSnapshot
        | where TIMESTAMP > ago(3d)
        | project nodeId, _nodePA=ipAddress
    ) on $left.nodeId == $right.nodeId
    | summarize latest=max(TIMESTAMP) by Tenant, nodeId, containerId, tenantName, roleInstanceName, _nodePA
) on $left._ringName == $right.tenantName
```

### PV

```kql
let pv=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('kusto').adxpageview| where page contains "b01/loadbalancers";
let pvcount=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('microsoft').adxpageview | where page contains "b01/loadbalancers" | summarize count();
union pv, pvcount
```

## NAT Gateway

### NAT Gateway under this subscription(Data delay in few minutes)

```kql
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| project timestamp, name, location,tostring(sku), properties, id
| distinct name, id,location, sku, ResourceGUID=tostring(parse_json(properties)["resourceGuid"])
```

### NAT Gateway Information(Data delay in about 10~15 minutes)

```kql
let starttime = _startTime;
let endtime = _endTime;
let NATGN = NATGatewayName;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let NatGwId=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| where name == NATGN
| project timestamp, name, location,tostring(sku), properties, id
| distinct ResourceGUID=tostring(parse_json(properties)["resourceGuid"])
| extend NatGatewayId=strcat("NGW_", ResourceGUID)
| distinct NatGatewayId);
let location=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| where name == NATGN
| distinct location);
cluster('Azslb').database('azslbmds').NatGatewayAllocation
| where env_time >= starttime - 1d and env_time <= endtime
| where NatGatewayId in (NatGwId)
| extend NatGatewayIds=tostring(split(tostring(NatGatewayId), "NGW_")[1])
| extend Region=location
| distinct SdnId, NatGatewayId=NatGatewayIds, SnatIpAddresses, Protocols, Subnets, IdleTimeoutInSeconds, EnableTcpReset, VnetId, NetworkKey, NatSlice, SliceVip,Region
| join kind=leftouter cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord on $left.SliceVip == $right.Vip
| distinct SdnId, NatGatewayId, SnatIpAddresses, Protocols, Subnets, IdleTimeoutInSeconds, EnableTcpReset, VnetId, NetworkKey, NatSlice, SliceVip,Region, NATRing = strcat("Slb-",extract(@"Slice_(.+?)""", 1, VmLocs))
| join kind=leftouter (cluster('AzureCM').database('AzureCM').LogContainerSnapshot | where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime) on $left.NATRing == $right.tenantName
| distinct SdnId, NatGatewayId, SnatIpAddresses, Protocols, Subnets, IdleTimeoutInSeconds, EnableTcpReset, VnetId, NetworkKey, NatSlice, SliceVip, NATRing=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region,Region1
| join kind=leftouter MDMAccount on $left.Region1 == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2")
| extend NATGatewayDataPathAvailability=strcat("https://portal.microsoftgeneva.com/s/70F5B074?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbv2", Region, "%22},{%22query%22:%22//*[id='NATGatewayId']%22,%22key%22:%22value%22,%22replacement%22:%22" , NatGatewayId, "%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend NATGatewayDataPathAvailabilityPerNATRing=strcat("https://portal.microsoftgeneva.com/s/41F5B804?overrides=[{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22", NATRing, "%22},{%22query%22:%22//*[id='ClusterName']%22,%22key%22:%22value%22,%22replacement%22:%22", NATRing, "%22},{%22query%22:%22//dataSources[namespace='BandwidthUsage'%20or%20namespace='VipStats'%20or%20namespace='NatService'%20or%20namespace='Health'%20or%20namespace='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountName, "%22},{%22query%22:%22//dataSources[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountNameInternal, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend NATGatewayThroughputMetrics=strcat("https://portal.microsoftgeneva.com/s/F372A89F?overrides=[{%22query%22:%22//*[id='NatGatewayId']%22,%22key%22:%22value%22,%22replacement%22:%22", NatGatewayId, "%22},{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbv2", Region, "%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true") 
| extend NATRingHealth=strcat("https://portal.microsoftgeneva.com/s/47A96AB9?overrides=[{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22", NATRing, "%22},{%22query%22:%22//*[id='ClusterName']%22,%22key%22:%22value%22,%22replacement%22:%22", NATRing, "%22},{%22query%22:%22//*[id='NodeId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//dataSources[namespace='BandwidthUsage'%20or%20namespace='VipStats'%20or%20namespace='NatService'%20or%20namespace='Health'%20or%20namespace='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountName, "%22},{%22query%22:%22//dataSources[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountNameInternal, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend NATRingVipProber=strcat("https://portal.microsoftgeneva.com/s/D9A6A883?overrides=[{%22query%22:%22//dataSources[namespace='BandwidthUsage'%20or%20namespace='VipStats'%20or%20namespace='NatService'%20or%20namespace='Health'%20or%20namespace='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountName, "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22",MdmAccountNameInternal, "%22},{%22query%22:%22//dataSources[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id='NodeId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22",NATRing, "%22},{%22query%22:%22//*[id='ServiceId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='RegionShortId']%22,%22key%22:%22value%22,%22replacement%22:%22ustsc%22},{%22query%22:%22//*[id='ServiceInstance']%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend NATRingMuxProber = strcat("https://jarvis-west.dc.ad.msft.net/dashboard/slbv2stage/Mux/MuxProber?overrides=[%7B%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id=%27Ring%27]%22,%22key%22:%22value%22,%22replacement%22:%22", NATRing, "%22},{%22query%22:%22//*[id=%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend NATRingMuxStatsV2 = strcat("https://jarvis-west.dc.ad.msft.net/dashboard/slbv2stage/Mux/MuxStatsV2?overrides=[%7B%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id=%27Ring%27]%22,%22key%22:%22value%22,%22replacement%22:%22", NATRing, "%22},{%22query%22:%22//*[id=%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend NATWorkerStats=strcat("https://portal.microsoftgeneva.com/s/22AB849B?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountName,"%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22", NATRing,"%22},{%22query%22:%22//*[id='NodeId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//dataSource[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal,"%22},{%22query%22:%22//dataSources[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| evaluate narrow()
| project Key=Column, Value

```

### NAT Gateway SNAT VIP Troubleshooting(Customer's VIP)

```kql
let starttime = _startTime;
let endtime = _endTime;
let NATGN = NATGatewayName;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let NatGwId=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| where name == NATGN
| project timestamp, name, location,tostring(sku), properties, id
| distinct ResourceGUID=tostring(parse_json(properties)["resourceGuid"])
| extend NatGatewayId=strcat("NGW_", ResourceGUID)
| distinct NatGatewayId);
let location=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| where name == NATGN
| distinct location);
cluster('Azslb').database('azslbmds').NatGatewayAllocation
| where env_time >= starttime - 1d and env_time <= endtime
| where NatGatewayId in (NatGwId)
| project env_time, env_cloud_role, env_cloud_roleInstance,SdnId, NatGatewayId, SnatIpAddresses, Protocols, Subnets, IdleTimeoutInSeconds, EnableTcpReset, VnetId, NetworkKey, NatSlice, SliceVip
| extend NatGatewayIds=tostring(split(tostring(NatGatewayId), "NGW_")[1])
| extend Region=location
| distinct  SnatIpAddresses
| extend SnatIP = split(SnatIpAddresses, ",")
| mv-expand SnatIP
| project SnatIP
| extend VIPTroubleshoot=strcat("https://aka.ms/b01?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'),"Z&p-_endTime=",format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime,'HH:mm:ss'),"Z&p-VIP=v-",SnatIP,"#a172102b-f768-4cc9-982f-0acc07d4765f")



```

### NAT Gateway Slice VIP Troubleshooting(Internal VIP)

```kql
let starttime = _startTime;
let endtime = _endTime;
let NATGN = NATGatewayName;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let NatGwId=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| where name == NATGN
| project timestamp, name, location,tostring(sku), properties, id
| distinct ResourceGUID=tostring(parse_json(properties)["resourceGuid"])
| extend NatGatewayId=strcat("NGW_", ResourceGUID)
| distinct NatGatewayId);
let location=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| where name == NATGN
| distinct location);
cluster('Azslb').database('azslbmds').NatGatewayAllocation
| where env_time >= starttime - 1d and env_time <= endtime
| where NatGatewayId in (NatGwId)
| project env_time, env_cloud_role, env_cloud_roleInstance,SdnId, NatGatewayId, SnatIpAddresses, Protocols, Subnets, IdleTimeoutInSeconds, EnableTcpReset, VnetId, NetworkKey, NatSlice, SliceVip
| extend NatGatewayIds=tostring(split(tostring(NatGatewayId), "NGW_")[1])
| extend Region=location
| distinct SliceVip
| extend VIPTroubleshoot=strcat("https://aka.ms/b01?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'),"Z&p-_endTime=",format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime,'HH:mm:ss'),"Z&p-VIP=v-",SliceVip,"#a172102b-f768-4cc9-982f-0acc07d4765f")

```

### NAT Ring Infra Host Information

```kql
let starttime = _startTime;
let endtime = _endTime;
let NATGN = NATGatewayName;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let NatGwId=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| where name == NATGN
| project timestamp, name, location,tostring(sku), properties, id
| distinct ResourceGUID=tostring(parse_json(properties)["resourceGuid"])
| extend NatGatewayId=strcat("NGW_", ResourceGUID)
| distinct NatGatewayId);
let location=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where subscriptionId == SubscriptionID
| where timestamp >= starttime - 2d and timestamp <= endtime
| where type == "microsoft.network/natgateways"
| where name == NATGN
| distinct location);
let NATRing=cluster('Azslb').database('azslbmds').NatGatewayAllocation
| where env_time >= starttime - 1d and env_time <= endtime
| where NatGatewayId in (NatGwId)
| extend NatGatewayIds=tostring(split(tostring(NatGatewayId), "NGW_")[1])
| extend Region=location
| distinct SdnId, NatGatewayId=NatGatewayIds, SnatIpAddresses, Protocols, Subnets, IdleTimeoutInSeconds, EnableTcpReset, VnetId, NetworkKey, NatSlice, SliceVip,Region
| join kind=leftouter cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord on $left.SliceVip == $right.Vip
| distinct NATRing = strcat("Slb-",extract(@"Slice_(.+?)""", 1, VmLocs));
cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (NATRing)
| distinct Ring=tenantName, roleInstanceName, Tenant, NodeId=toupper(nodeId),nodeId, containerId, AvailabilityZone, Region,creationTime, DataCenterName
| join kind=leftouter(cluster('aznwcc').database('aznwmds').Servers) on NodeId
| join kind=leftouter cluster('AzureCM').database('AzureCM').LogNodeSnapshot on $left.nodeId == $right.nodeId
| join kind=leftouter(cluster('aznwcc').database('aznwmds').DeviceInterfaceLinks) on $left.DeviceName == $right.StartDevice
| distinct Ring, roleInstanceName, EndDevice,Tenant, NodeId,ipAddress, containerId, AvailabilityZone, Region,creationTime, DataCenterName, EndPort
| summarize T0=strcat_array(make_list(EndDevice), ", ") by Ring, roleInstanceName, Tenant, NodeId,ipAddress, containerId, AvailabilityZone, Region,creationTime, DataCenterName, EndPort
| project Ring=tostring(split(Ring, "Slb-")[1]), RoleInstanceName=roleInstanceName, DataCenterName, AvailabilityZone, Tenant,T0, TORInterface=EndPort, NodeId=tolower(NodeId),NodeIP=ipAddress, containerId
| extend NodeDash=strcat("https://aka.ms/b01?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH-mm-ss'),"Z&p-_endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH-mm-ss'), "Z&p-nodeid=v-", NodeId, "#805057f2-367d-4cb7-9986-89fbd2533f94")
| extend TORTroubleshoot=strcat("https://aka.ms/b01?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH-mm-ss'),"Z&p-_endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH-mm-ss'), "Z&p-_DeviceName=v-",T0,"&p-SyslogFilter=all#ecac89d5-b4b2-4960-9c5d-6166c2aa3b23")
```

### PV

```kql
let pv=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('kusto').adxpageview| where page contains "b01/natgateways";
let pvcount=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('microsoft').adxpageview | where page contains "b01/natgateways" | summarize count();
union pv, pvcount
```

