---
description: KQL queries for Software Load Balancer (SLB) ring health and Azure VIP diagnostics.
---

# SLB Ring & Azure VIP Kusto Queries

> Source: Azure Networking B01 Dashboard (aka.ms/b01)
> Pages: SLB Ring, Azure VIP

## ⚠️ Important Schema & Architecture Notes

1. **SLB MUX nodes are managed by Service Fabric, NOT AzureCM.** Do not query `LogNodeSnapshot`/`LogContainerSnapshot` for MUX host-level state — use azslbmds tables instead.
2. **RoleInstance naming varies by table:**
   - AzureCM (`LogContainerSnapshot`): `SlbRingHostRole_IN_N` (e.g., `SlbRingHostRole_IN_3`)
   - azslbmds (`SlbCritical`, `SlbException`, `SlbHealthEvent`): `SlbRingHostRole_N` (e.g., `SlbRingHostRole_3`)
   - azslbmds (`NodeHealthEvent`): `SlbRingHostRole.N` (dot separator)
3. **`NodeHealthEvent` uses `TIMESTAMP`/`Role`/`NodeName`**, NOT `env_time`/`env_cloud_role` — different schema from most azslbmds tables.
4. **`HealthSignalStateHistoryEvent` is for compute hosts only**, NOT for SF-managed MUX nodes.
5. For **deep RCA** (MUX crash, SF health, exceptions), see [slb-deep-rca.md](slb-deep-rca.md).

## SLB Ring

### Tenant Update Event Executed By AutoDri

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
cluster('azslb').database('azslbmds').AutoDriInfrastructureServiceJobInformation
| where env_time >= starttime - 1d and env_time <= endtime + 1d
| where env_cloud_role in (RingN)
| where ImpactAction == "TenantUpdate"
//| summarize arg_max(env_time, *) by Id
//| where JobStatus != "Completed"
| project env_time, Id, env_cloud_role, JobStatus, ImpactAction, AcknowledgementStatus, ActionStatus, CurrentUD
| order by env_time asc 

```

### Service Healing Event

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let SLBRing=strcat("Slb-",RingN);
cluster("azurecm.kusto.windows.net").database('AzureCM').ServiceHealingTriggerEtwTable
| where PreciseTimeStamp >= starttime - 2h and PreciseTimeStamp <= endtime + 2h
| where TenantName in~ (SLBRing)
| project PreciseTimeStamp, Ring=TenantName,RoleInstanceName, FaultInfoFabricOperation,TriggerType,AffectedUpdateDomain, TriggerId, TriggerObjectId 
| order by PreciseTimeStamp asc 



```

### Ring MUX Instance Information

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MuxInstance=cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 6h  and PreciseTimeStamp <= endtime
| where tenantName in~ (SLBRing)
| join kind=leftouter(cluster('aznwcc').database('aznwmds').Servers) on NodeId
| join kind=leftouter (cluster('AzureCM').database('AzureCM').LogNodeSnapshot | where PreciseTimeStamp >= starttime - 2h  and PreciseTimeStamp <= endtime) on $left.nodeId == $right.nodeId
| distinct CreationTime=creationTime, roleInstanceName,machinePoolName, Tenant, nodeId, NodeIp=ipAddress, containerId, Region,AvailabilityZone, DataCenterName;
let MuxNode = MuxInstance | distinct nodeId;
let t1t2info=cluster("Azcore.centralus").database("Fc").LogNodeNetworkSpineLevelInformation 
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where nodeId in (MuxNode)
| distinct nodeId, t1NetworkSpine, t2NetworkSpine;
MuxInstance | join t1t2info on nodeId
| distinct CreationTime, roleInstanceName,machinePoolName, Tenant, NodeId=nodeId,t1NetworkSpine,t2NetworkSpine,  NodeIp, containerId, Region,AvailabilityZone, DataCenterName
| extend NodeDash=strcat("https://aka.ms/b01?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH-mm-ss'),"Z&p-_endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH-mm-ss'), "Z&p-nodeid=v-", NodeId, "#805057f2-367d-4cb7-9986-89fbd2533f94")
| distinct CreationTime, roleInstanceName,machinePoolName, Tenant, NodeId,NodeDash, t1NetworkSpine,t2NetworkSpine,  NodeIp, containerId, Region,AvailabilityZone, DataCenterName

```

### Node Service Version Change Status

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MuxNodeId=cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 6h  and PreciseTimeStamp <= endtime
| where tenantName in~ (SLBRing)
| distinct nodeId;
let MUXNodeMapping=cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 6h  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct roleInstanceName, nodeId;
cluster('azcsupfollower').database('AzureCM').ServiceVersionSwitch
| where PreciseTimeStamp >= starttime - 2h  and PreciseTimeStamp <= endtime
| where NodeId in~ (MuxNodeId)
| join kind=leftouter  MUXNodeMapping on $left.NodeId == $right.nodeId
| where isnotempty(CurrentVersion)
| project PreciseTimeStamp,MUXInstanceName=roleInstanceName, NodeId, ServiceName, CurrentVersion, NewVersion, SourceOfService
```

### Ring Metrics Dashboard

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct Ring=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region
| join kind=leftouter MDMAccount on $left.Region == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2") 
| extend RingHealth=strcat("https://portal.microsoftgeneva.com/s/47A96AB9?overrides=[{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22", Ring, "%22},{%22query%22:%22//*[id='ClusterName']%22,%22key%22:%22value%22,%22replacement%22:%22", Ring, "%22},{%22query%22:%22//*[id='NodeId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//dataSources[namespace='BandwidthUsage'%20or%20namespace='VipStats'%20or%20namespace='NatService'%20or%20namespace='Health'%20or%20namespace='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountName, "%22},{%22query%22:%22//dataSources[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountNameInternal, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VipProber=strcat("https://portal.microsoftgeneva.com/s/D9A6A883?overrides=[{%22query%22:%22//dataSources[namespace='BandwidthUsage'%20or%20namespace='VipStats'%20or%20namespace='NatService'%20or%20namespace='Health'%20or%20namespace='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountName, "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22",MdmAccountNameInternal, "%22},{%22query%22:%22//dataSources[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id='NodeId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22",Ring, "%22},{%22query%22:%22//*[id='ServiceId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='RegionShortId']%22,%22key%22:%22value%22,%22replacement%22:%22ustsc%22},{%22query%22:%22//*[id='ServiceInstance']%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend MuxProber = strcat("https://jarvis-west.dc.ad.msft.net/dashboard/slbv2stage/Mux/MuxProber?overrides=[%7B%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id=%27Ring%27]%22,%22key%22:%22value%22,%22replacement%22:%22", Ring, "%22},{%22query%22:%22//*[id=%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend MuxStatsV2 = strcat("https://jarvis-west.dc.ad.msft.net/dashboard/slbv2stage/Mux/MuxStatsV2?overrides=[%7B%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id=%27Ring%27]%22,%22key%22:%22value%22,%22replacement%22:%22", Ring, "%22},{%22query%22:%22//*[id=%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| project Ring, RingHealth, VipProber, MuxProber, MuxStatsV2
| evaluate narrow()
| project Key=Column, Value
```

### MuxProber V4 Availability in % - Per Node

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let MdmAccountNameInternal = toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct Ring=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region
| join kind=leftouter MDMAccount on $left.Region == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2") 
| distinct MdmAccountNameInternal);
let FailedAttempts = strcat("metricNamespace('MuxHealth').metric('MuxProberFailedAttempts').dimensions('Ring','NodeId').samplingTypes('Sum') | where Ring == '",RingName, "'");
let SuccessAttempts = strcat("metricNamespace('MuxHealth').metric('MuxProberSuccessAttempts').dimensions('Ring','NodeId').samplingTypes('Sum') | where Ring == '",RingName, "'");
let MuxProbeFailedAttempts=evaluate geneva_metrics_request(MdmAccountNameInternal, FailedAttempts, starttime, endtime)
| project TimestampUtc, NodeId, FailedAttempts=Sum;
let MuxProbeSuccessAttempts=evaluate geneva_metrics_request(MdmAccountNameInternal, SuccessAttempts, starttime, endtime)
| project TimestampUtc, NodeId, MuxProbeSuccessAttempts=Sum;
MuxProbeFailedAttempts | join  MuxProbeSuccessAttempts on NodeId and TimestampUtc
| project TimestampUtc, NodeId, FailedAttempts, MuxProbeSuccessAttempts
| extend MuxProberV4Availability=round(toreal(MuxProbeSuccessAttempts*100/(FailedAttempts + MuxProbeSuccessAttempts)), 2)
| extend Availability=iff(isnan(MuxProberV4Availability),0.0, MuxProberV4Availability)
| project TimestampUtc, NodeId, Availability
| render timechart
```

### MuxProber V6 Availability in % - Per Node

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let MdmAccountNameInternal = toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct Ring=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region
| join kind=leftouter MDMAccount on $left.Region == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2") 
| distinct MdmAccountNameInternal);
let FailedAttempts = strcat("metricNamespace('MuxHealth').metric('MuxProberV6FailedAttempts').dimensions('Ring','NodeId').samplingTypes('Sum') | where Ring == '",RingName, "'");
let SuccessAttempts = strcat("metricNamespace('MuxHealth').metric('MuxProberV6SuccessAttempts').dimensions('Ring','NodeId').samplingTypes('Sum') | where Ring == '",RingName, "'");
let MuxProbeFailedAttempts=evaluate geneva_metrics_request(MdmAccountNameInternal, FailedAttempts, starttime, endtime)
| project TimestampUtc, NodeId, FailedAttempts=Sum;
let MuxProbeSuccessAttempts=evaluate geneva_metrics_request(MdmAccountNameInternal, SuccessAttempts, starttime, endtime)
| project TimestampUtc, NodeId, MuxProbeSuccessAttempts=Sum;
MuxProbeFailedAttempts | join  MuxProbeSuccessAttempts on NodeId and TimestampUtc
| project TimestampUtc, NodeId, FailedAttempts, MuxProbeSuccessAttempts
| extend MuxProberV4Availability=round(toreal(MuxProbeSuccessAttempts*100/(FailedAttempts + MuxProbeSuccessAttempts)), 2)
| extend Availability=iff(isnan(MuxProberV4Availability),0.0, MuxProberV4Availability)
| project TimestampUtc, NodeId, Availability
| render timechart
```

### MuxProber V4 Running State: 1 is running, 0 or lack of data means prober is not running

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let MdmAccountNameInternal = toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct Ring=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region
| join kind=leftouter MDMAccount on $left.Region == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2") 
| distinct MdmAccountNameInternal);
let SuccessAttempts = strcat("metricNamespace('MuxHealth').metric('MuxProberSuccessAttempts').dimensions('Ring','NodeId').samplingTypes('Count') | where Ring == '",RingName, "'");
let MuxProbeSuccessAttempts=evaluate geneva_metrics_request(MdmAccountNameInternal, SuccessAttempts, starttime, endtime)
| project TimestampUtc, NodeId, Count;
MuxProbeSuccessAttempts
| render timechart 

```

### MuxProber V6 Running State: 1 is running, 0 or lack of data means prober is not running

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let MdmAccountNameInternal = toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct Ring=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region
| join kind=leftouter MDMAccount on $left.Region == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2") 
| distinct MdmAccountNameInternal);
let SuccessAttempts = strcat("metricNamespace('MuxHealth').metric('MuxProberV6SuccessAttempts').dimensions('Ring','NodeId').samplingTypes('Count') | where Ring == '",RingName, "'");
let MuxProbeSuccessAttempts=evaluate geneva_metrics_request(MdmAccountNameInternal, SuccessAttempts, starttime, endtime)
| project TimestampUtc, NodeId, Count;
MuxProbeSuccessAttempts
| render timechart
```

### MUX Node - TOR Pingmesh

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let SLBMUXNodeId = cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct nodeId;
let MUXNodeMapping=cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct roleInstanceName, nodeId;
cluster('aznwsdn').database('aznwmds').TorPingSendAggreEvent
| where TIMESTAMP between (starttime .. endtime)
| where NodeId in~ (SLBMUXNodeId)
| summarize SendCount = max(SendCount) by TIMESTAMP, NodeId, TorName
| join kind = leftouter
(
cluster('aznwsdn').database('aznwmds').TorPingRecvAggreEvent
| where TIMESTAMP between (starttime .. endtime)
| where NodeId in~ (SLBMUXNodeId)
| summarize RecvCount = max(RecvCount) by TIMESTAMP, NodeId
)
on TIMESTAMP, NodeId
| extend RecvCount = iff(isnull(RecvCount), 0, RecvCount)
| project TIMESTAMP, NodeId, Availability = todouble(RecvCount) / todouble(SendCount) * 100
| join kind=leftouter  MUXNodeMapping on $left.NodeId == $right.nodeId
| project TIMESTAMP, MUX=strcat(roleInstanceName, " ->NodeId: ", nodeId), Availability
| render timechart
```

### Mux Health in % - Per Node

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let MdmAccountNameInternal = toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct Ring=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region
| join kind=leftouter MDMAccount on $left.Region == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2") 
| distinct MdmAccountNameInternal);
let MUXHealth = strcat("metricNamespace('MpmHealth').metric('MuxHealth').dimensions('Ring','MuxId').samplingTypes('Average') | where Ring == '",RingName, "'");
evaluate geneva_metrics_request(MdmAccountNameInternal, MUXHealth, starttime, endtime)
| project TimestampUtc, MuxId, Average
| render timechart 


```

### Routes Per MUX

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let SLBRing=strcat("Slb-",RingN);
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let MdmAccountNameInternal = toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (SLBRing)
| distinct Ring=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region
| join kind=leftouter MDMAccount on $left.Region == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2") 
| distinct MdmAccountNameInternal);
let RoutesPerMUX = strcat("metricNamespace('MuxHealth').metric('MuxRouteCount').dimensions('Ring','ServiceId').samplingTypes('Average') | where Ring == '",RingName, "'");
evaluate geneva_metrics_request(MdmAccountNameInternal, RoutesPerMUX, starttime, endtime)
| project TimestampUtc, ServiceId, Average
| render timechart 


```

### MUX OS Version State

```kql
let RingN = iff(isempty(RingName), "abcdefg", tolower(RingName));
let starttime = _startTime;
let endtime = _endTime;
cluster('azslb.kusto.windows.net').database('azslbmds').SlbOsVersionRecord
| where env_time >= starttime - 12h and env_time  < endtime + 2h
| where Ring in (RingN)
| project env_time, Ring, NodeName, StrippedVersion, NsmReservedIp
| extend NodeOSVersion=strcat(NodeName, "->", StrippedVersion)
| summarize count() by bin(env_time, 5m), NodeOSVersion
| render columnchart    
```

## Azure VIP

### VIP Ring Information

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let RingLists=materialize(cluster('azslb.kusto.windows.net').database('azslbmds').VipRangesSnapshotEvent
| where env_time >= starttime - 1d and env_time < endtime
| where ipv4_is_in_range(IP,VipRange) or ipv6_is_in_range(IP,VipRange)
| distinct strcat("Slb-",RingName));
cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (RingLists)
| distinct Ring=tostring(split(tenantName, "Slb-")[1]), Region, AvailabilityZone, DC=DataCenterName
```

### MUX Instance Information

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
let RingList=materialize(cluster('azslb.kusto.windows.net').database('azslbmds').VipRangesSnapshotEvent
| where env_time >= starttime - 1d and env_time < endtime
| where ipv4_is_in_range(IP,VipRange) or ipv6_is_in_range(IP,VipRange)  
| distinct RingNames=strcat("Slb-",RingName));
cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (RingList)
| distinct Ring=tenantName, roleInstanceName, Tenant, NodeId=toupper(nodeId),nodeId, containerId, AvailabilityZone, Region,creationTime, DataCenterName
| join kind=leftouter(cluster('aznwcc').database('aznwmds').Servers) on NodeId
| join kind=leftouter cluster('AzureCM').database('AzureCM').LogNodeSnapshot on $left.nodeId == $right.nodeId
| join kind=leftouter(cluster('aznwcc').database('aznwmds').DeviceInterfaceLinks) on $left.DeviceName == $right.StartDevice
| distinct Ring, roleInstanceName, EndDevice,Tenant, NodeId,ipAddress, containerId, AvailabilityZone, Region,creationTime, DataCenterName, EndPort
| summarize T0=strcat_array(make_list(EndDevice), ", ") by Ring, roleInstanceName, Tenant, NodeId,ipAddress, containerId, AvailabilityZone, Region,creationTime, DataCenterName, EndPort
| project Ring=tostring(split(Ring, "Slb-")[1]), RoleInstanceName=roleInstanceName, Region,  AvailabilityZone, DataCenterName, Tenant,T0, TORInterface=EndPort, NodeId=tolower(NodeId),NodeIP=ipAddress, containerId
| extend NodeDash=strcat("https://aka.ms/b01?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH-mm-ss'),"Z&p-_endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH-mm-ss'), "Z&p-nodeid=v-", NodeId, "#805057f2-367d-4cb7-9986-89fbd2533f94")
| extend TORTroubleshoot=strcat("https://aka.ms/b01?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH-mm-ss'),"Z&p-_endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH-mm-ss'), "Z&p-_DeviceName=v-",T0,"&p-SyslogFilter=all#ecac89d5-b4b2-4960-9c5d-6166c2aa3b23")
```

### VIP Dashboard

```kql
let starttime= _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord
| where env_time > starttime - 6h and env_time < endtime + 1h
| where Vip == VIP
| summarize by Vip, VipUri, Type, SKU, AltAddress, VmLocs, CountHosts, env_cloud_role, Region
| join (cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time > starttime - 1h and env_time < endtime + 1h
|summarize by Region, MdmAccountName, ArmRegion
| extend HPAccountName = strcat("slbhp", substring(MdmAccountName, 5))) on $left.Region == $right.Region
| extend BandwithUsage=strcat("https://portal.microsoftgeneva.com/s/3CA61B31?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbhp", ArmRegion,"%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VIPAvailability=strcat("https://portal.microsoftgeneva.com/s/2438DA2C?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountName, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip, "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22""%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DipAvailability=strcat("https://portal.microsoftgeneva.com/s/4FFD22D2?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountName, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip, "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend SNATDashboard=strcat("https://portal.microsoftgeneva.com/s/FB2F30A4?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountName, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip, "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend Sflowdashboard=strcat("https://portal.microsoftgeneva.com/s/B40A24AB?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend Netflowdashboard=strcat("https://portal.microsoftgeneva.com/s/A5CECCEE?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DDOSStandardPlanCRIDashboard=strcat("https://portal.microsoftgeneva.com/s/BA074862?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| distinct Vip, Region=ArmRegion, VipUri, SKU, AltAddress, VmLocs, CountHosts, env_cloud_role, BandwithUsage,VIPAvailability,DipAvailability,SNATDashboard,Netflowdashboard,DDOSBasicPlanSflowDashbard=Sflowdashboard,DDOSStandardPlanCRIDashboard
| evaluate narrow()
| project Key=Column, Value
```

### MUX Dashboard

```kql
let starttime= _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
cluster('azslb').database('azslbmds').DSMulticastGroupEvent
| where env_time > starttime - 1h and env_time < endtime + 1h
| where SegmentName != "0.0.0.0_0" and SegmentName != "::_0"
| where Uri has "MuxPoolManager"
| summarize arg_max(env_time, *) by SegmentName, Uri
| project env_cloud_name, SegmentName, GroupIncarnationId, MulticastGroup
| extend CidrString = replace_string(SegmentName, "_", "/")
| extend Ipv4Cidr = iff(CidrString has ":", "", CidrString), Ipv6Cidr = iff(CidrString has ":", CidrString, "")
| where ipv6_is_in_range(VIP, Ipv6Cidr) or ipv4_is_in_range(VIP, Ipv4Cidr)
| extend groupIncarnationIdStr = replace_string(GroupIncarnationId, "-azr", "-az,r")
| join (
cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time > starttime - 1h and env_time < endtime + 1h
| summarize by Region, MdmAccountName, ArmRegion) on $left.env_cloud_name == $right.Region
| extend MuxProber = strcat("https://jarvis-west.dc.ad.msft.net/dashboard/slbv2stage/Mux/MuxProber?overrides=[%7B%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbintv2", ArmRegion, "%22},{%22query%22:%22//*[id=%27Ring%27]%22,%22key%22:%22value%22,%22replacement%22:%22", groupIncarnationIdStr, "%22},{%22query%22:%22//*[id=%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend MuxStatsV2 = strcat("https://jarvis-west.dc.ad.msft.net/dashboard/slbv2stage/Mux/MuxStatsV2?overrides=[%7B%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbintv2", ArmRegion, "%22},{%22query%22:%22//*[id=%27Ring%27]%22,%22key%22:%22value%22,%22replacement%22:%22", groupIncarnationIdStr, "%22},{%22query%22:%22//*[id=%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| project CidrString, MulticastGroup, MuxProber, MuxStatsV2
| evaluate narrow()
| project Key=Column, Value
```

### Ingress direction VIP Bandwidth utilization(Mbps)

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
cluster('netcapplan.kusto.windows.net').database('NetCapPlan').RealTimeIpfixWithMetadata
| where TimeStamp >= starttime and TimeStamp < endtime
| where DstIpAddress == IP
//| where RouterName matches regex "ier"
//| where RouterName matches regex "ier" or RouterName matches regex "icr" or RouterName matches regex "rwa"
//| summarize Mbps=sum((NumOfBytes*8 + NumOfPackets*14)*4096/(60*1000000)) by bin(TimeStamp, 1m)
| summarize Mbps=round((sum(NumOfBytes + NumOfPackets*14)*4096*8.0)/(60*1000000),0) by bin(TimeStamp, 1m)
| render timechart
```

### DDoS Mitigation Event

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
cluster('aznwddos.centralus').database('cnsgeneva').DDoSMitigationEvent
| where PreciseTimeStamp >= starttime and PreciseTimeStamp <= endtime
| where destPublicIpAddressString == IP
| project PreciseTimeStamp, TaskName, destPublicIpAddress, mitigationStatus, mitigationDirection, policies, deviceList, routerId, triggerEventType
```

### DDoS Mitigation Report

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
cluster('aznwddos.centralus').database('cnsgeneva').MitigationReports
| where PreciseTimeStamp >= starttime and PreciseTimeStamp <= endtime
| where IPAddress == IP
| extend TrafficOverview=replace_string(TrafficOverview, "\\", ""), Protocols=replace_string(Protocols, "\\", ""), Top10SourceASNs=replace_string(Top10SourceASNs, "\\", ""),Top10SourceCountries=replace_string(Top10SourceCountries, "\\", ""), Top10SourceCountriesDroppedPackets=replace_string(Top10SourceCountriesDroppedPackets, "\\", "")
| project PreciseTimeStamp, Category, MitigationPeriodStart, MitigationPeriodEnd, TrafficOverview, Protocols, Top10SourceASNs, Top10SourceCountries, Top10SourceCountriesDroppedPackets
```

### Ingress direction VIP PPS

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
cluster('netcapplan.kusto.windows.net').database('NetCapPlan').RealTimeIpfixWithMetadata
| where TimeStamp >= starttime and TimeStamp < endtime
| where DstIpAddress == IP
//| where RouterName matches regex "ier"
//| where RouterName matches regex "ier" or RouterName matches regex "icr" or RouterName matches regex "rwa"
| summarize sum(NumOfPackets) by bin(TimeStamp, 1m), IpProtocolIdentifier
| project TimeStamp, Protocol=strcat(" ", IpProtocolIdentifier," "), PPS = sum_NumOfPackets * 4096 / 60
| render timechart
```

### DDoS Pcap Flow Log

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
cluster("aznwddos.centralus").database("cnsgeneva").DDoSPcapFlowLogs
| where destPublicIpAddress == IP
| where TIMESTAMP >= starttime and TIMESTAMP <= endtime
| project TIMESTAMP, sourcePublicIpAddress, sourcePort, destGeoGroup, destPublicIpAddress, destPort, protocol, payloadLength, messageValue, OpcodeName
```

### Egress direction VIP PPS

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
cluster('netcapplan.kusto.windows.net').database('NetCapPlan').RealTimeIpfixWithMetadata
| where TimeStamp >= starttime and TimeStamp < endtime
| where SrcIpAddress == IP
//| where RouterName matches regex "ier"
//| where RouterName matches regex "ier" or RouterName matches regex "icr" or RouterName matches regex "rwa"
| summarize sum(NumOfPackets) by bin(TimeStamp, 1m), IpProtocolIdentifier
| project TimeStamp, Protocol=strcat(" ", IpProtocolIdentifier," "), PPS = sum_NumOfPackets * 4096 / 60
| render timechart
```

### Egress direction VIP Bandwidth utilization(Mbps)

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
cluster('netcapplan.kusto.windows.net').database('NetCapPlan').RealTimeIpfixWithMetadata
| where TimeStamp >= starttime and TimeStamp < endtime
| where SrcIpAddress == IP
//| where RouterName matches regex "ier"
//| where RouterName matches regex "ier" or RouterName matches regex "icr" or RouterName matches regex "rwa"
| summarize Mbps=round((sum(NumOfBytes + NumOfPackets*14)*4096*8.0)/(60*1000000),0) by bin(TimeStamp, 1m)
| render timechart
```

### VFP - Outbound Data(MB) Per minute - Counter from VFP SLB_NAT_LAYER

```kql
let starttime= _startTime;
let endtime = _endTime;
let AzureIP = VIP;
let SLBHPAccount=toscalar(cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord
| where env_time > starttime - 6h and env_time < endtime + 1h
| where Vip == VIP
| summarize by Vip, VipUri, Type, SKU, AltAddress, VmLocs, CountHosts, env_cloud_role, Region
| join (cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time > starttime - 1h and env_time < endtime + 1h
|summarize by Region, MdmAccountName, ArmRegion
| extend HPAccountName = strcat("slbhp", substring(MdmAccountName, 5))) on $left.Region == $right.Region
| distinct HPAccountName);
let query = strcat("metricNamespace('BandwidthUsage').metric('ByteCount').dimensions('VipAddress','Direction').samplingTypes('Sum') | where VipAddress == '",AzureIP, "'");
evaluate geneva_metrics_request(SLBHPAccount, query, starttime, endtime)
| where Direction == "Out"
| project TimestampUtc, Sum
| extend MBPerMin=Sum/1000000
| project TimestampUtc, MBPerMin
| render timechart
 
```

### VFP - In Data(MB) Per minute - Counter from VFP SLB_NAT_LAYER

```kql
let starttime= _startTime;
let endtime = _endTime;
let AzureIP = VIP;
let SLBHPAccount=toscalar(cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord
| where env_time > starttime - 6h and env_time < endtime + 1h
| where Vip == VIP
| summarize by Vip, VipUri, Type, SKU, AltAddress, VmLocs, CountHosts, env_cloud_role, Region
| join (cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time > starttime - 1h and env_time < endtime + 1h
|summarize by Region, MdmAccountName, ArmRegion
| extend HPAccountName = strcat("slbhp", substring(MdmAccountName, 5))) on $left.Region == $right.Region
| distinct HPAccountName);
let query = strcat("metricNamespace('BandwidthUsage').metric('ByteCount').dimensions('VipAddress','Direction').samplingTypes('Sum') | where VipAddress == '",AzureIP, "'");
evaluate geneva_metrics_request(SLBHPAccount, query, starttime, endtime)
| where Direction == "In"
| project TimestampUtc, Sum
| extend MBPerMin=Sum/1000000
| project TimestampUtc, MBPerMin
| render timechart
 
```

### Dashboard Per Ring

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let MDMAccount=cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time >= starttime - 1d and env_time < endtime
| distinct MdmAccountName, RdfeRegion;
let RingLists=materialize(cluster('azslb.kusto.windows.net').database('azslbmds').VipRangesSnapshotEvent
| where env_time >= starttime - 1d and env_time < endtime
| where ipv4_is_in_range(IP,VipRange) or ipv6_is_in_range(IP,VipRange)
| distinct strcat("Slb-",RingName));
cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (RingLists)
| distinct IP, Ring=tostring(split(tenantName, "Slb-")[1]), AvailabilityZone, DataCenterName, Region
| join kind=leftouter MDMAccount on $left.Region == $right.RdfeRegion
| extend MdmAccountNameInternal=replace_string(MdmAccountName, "slbv2", "slbintv2") 
| extend RingHealth=strcat("https://portal.microsoftgeneva.com/s/47A96AB9?overrides=[{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22", Ring, "%22},{%22query%22:%22//*[id='ClusterName']%22,%22key%22:%22value%22,%22replacement%22:%22", Ring, "%22},{%22query%22:%22//*[id='NodeId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//dataSources[namespace='BandwidthUsage'%20or%20namespace='VipStats'%20or%20namespace='NatService'%20or%20namespace='Health'%20or%20namespace='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountName, "%22},{%22query%22:%22//dataSources[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountNameInternal, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VipProber=strcat("https://portal.microsoftgeneva.com/s/D9A6A883?overrides=[{%22query%22:%22//dataSources[namespace='BandwidthUsage'%20or%20namespace='VipStats'%20or%20namespace='NatService'%20or%20namespace='Health'%20or%20namespace='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountName, "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22",MdmAccountNameInternal, "%22},{%22query%22:%22//dataSources[namespace!='BandwidthUsage'%20and%20namespace!='VipStats'%20and%20namespace!='NatService'%20and%20namespace!='Health'%20and%20namespace!='DipHealth']%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id='NodeId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22",Ring, "%22},{%22query%22:%22//*[id='ServiceId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='RegionShortId']%22,%22key%22:%22value%22,%22replacement%22:%22ustsc%22},{%22query%22:%22//*[id='ServiceInstance']%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend MuxProber = strcat("https://jarvis-west.dc.ad.msft.net/dashboard/slbv2stage/Mux/MuxProber?overrides=[%7B%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id=%27Ring%27]%22,%22key%22:%22value%22,%22replacement%22:%22", Ring, "%22},{%22query%22:%22//*[id=%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend MuxStatsV2 = strcat("https://jarvis-west.dc.ad.msft.net/dashboard/slbv2stage/Mux/MuxStatsV2?overrides=[%7B%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22", MdmAccountNameInternal, "%22},{%22query%22:%22//*[id=%27Ring%27]%22,%22key%22:%22value%22,%22replacement%22:%22", Ring, "%22},{%22query%22:%22//*[id=%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| project Ring, RingHealth, VipProber, MuxProber, MuxStatsV2
```

### Ring Service Health Event - Critical Level

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let RingLists=cluster('azslb.kusto.windows.net').database('azslbmds').VipRangesSnapshotEvent
| where env_time >= starttime - 1d and env_time < endtime
| where ipv4_is_in_range(IP,VipRange) or ipv6_is_in_range(IP,VipRange)
| distinct RingName;
cluster('azslb.kusto.windows.net').database('azslbmds').AutoDriServiceInformation
| where env_time >  starttime - 1h and env_time < endtime + 1h
| where env_cloud_role in (RingLists)
| where AggregatedHealthState != "Ok"
| where AggregatedHealthState != "Warning"
| project env_time, env_cloud_roleInstance, ServiceTypeName, ServiceName, AggregatedHealthState
//| summarize  count() by bin(env_time, 1m), ServiceName
//| render columnchart  
```

### VIP Properties

```kql
let starttime= _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where timestamp >= starttime - 2d and timestamp < endtime
| where type == "microsoft.network/publicipaddresses"
| extend PublicIP=tostring(properties.ipAddress)
| where PublicIP ==  VIP
| take 1
| project ResourceId=id, Properties=properties
| project Properties
//| evaluate narrow()
//| project Key=Column, Value
```

### Discard and Error packet counter over the T0 of MUX - Group by datacenter of MUX T0 due to massive data

```kql
let starttime= _startTime;
let endtime = _endTime;
let IP = VIP;
let RingList=materialize(cluster('azslb.kusto.windows.net').database('azslbmds').VipRangesSnapshotEvent
| where env_time >= starttime - 1d and env_time < endtime
| where ipv4_is_in_range(IP,VipRange) or ipv6_is_in_range(IP,VipRange)  
| distinct RingNames=strcat("Slb-",RingName));
let T0=cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 1d  and PreciseTimeStamp <= endtime
| where tenantName in (RingList)
| distinct Ring=tenantName, roleInstanceName, Tenant, NodeId=toupper(nodeId),nodeId, containerId, AvailabilityZone, Region,creationTime, DataCenterName
| join kind=leftouter(cluster('aznwcc').database('aznwmds').Servers) on NodeId
| join kind=leftouter cluster('AzureCM').database('AzureCM').LogNodeSnapshot on $left.nodeId == $right.nodeId
| join kind=leftouter(cluster('aznwcc').database('aznwmds').DeviceInterfaceLinks) on $left.DeviceName == $right.StartDevice
| distinct EndDevice;
cluster('Aznwnetmon').database('aznwmds').sXInterfaceTable 
| where PreciseTimeStamp >= starttime and PreciseTimeStamp <= endtime
| where DeviceName in (T0)
| project ReceivedUtc, DeviceName,ifInDiscards_Counter, ifOutDiscards_Counter, ifInErrors_Counter, ifOutErrors_Counter
| summarize InDiscard=sum(ifInDiscards_Counter), OutDiscard=sum(ifOutDiscards_Counter), InError=sum(ifInErrors_Counter), OutError=sum(ifOutErrors_Counter) by bin(ReceivedUtc, 1m), DeviceName
| extend Discard_Errors= InDiscard + OutDiscard + InError + OutError
| project ReceivedUtc, T0Datacenter=tostring(split(DeviceName, "-")[0]), Discard_Errors
| render columnchart  
 
```

### PV

```kql
let pv=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('kusto').adxpageview| where page contains "b01/azurevip";
let pvcount=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('microsoft').adxpageview | where page contains "b01/azurevip" | summarize count();
union pv, pvcount
```

### Azure ELB - DIP Availability Per Frontend Port

```kql
let starttime= _startTime;
let endtime = _endTime;
let AzureIP = VIP;
let SLBHPAccount=toscalar(cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord
| where env_time > starttime - 6h and env_time < endtime + 1h
| where Vip == VIP
| summarize by Vip, VipUri, Type, SKU, AltAddress, VmLocs, CountHosts, env_cloud_role, Region
| join (cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time > starttime - 1h and env_time < endtime + 1h
|summarize by Region, MdmAccountName, ArmRegion
| extend HPAccountName = strcat("slbv2", substring(MdmAccountName, 5))) on $left.Region == $right.Region
| distinct HPAccountName);
let query = strcat("metricNamespace('DipHealth').metric('DipAvailability').dimensions('VipAddress', 'VipPort').samplingTypes('Average') | where VipAddress == '",AzureIP, "'");
evaluate geneva_metrics_request(SLBHPAccount, query, starttime, endtime)
| project TimestampUtc,VipPort, Average
| render timechart
```

### Azure ELB - VIP Availability Per Frontend Port

```kql
let starttime= _startTime;
let endtime = _endTime;
let AzureIP = VIP;
let SLBHPAccount=toscalar(cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord
| where env_time > starttime - 6h and env_time < endtime + 1h
| where Vip == VIP
| summarize by Vip, VipUri, Type, SKU, AltAddress, VmLocs, CountHosts, env_cloud_role, Region
| join (cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time > starttime - 1h and env_time < endtime + 1h
|summarize by Region, MdmAccountName, ArmRegion
| extend HPAccountName = strcat("slbv2", substring(MdmAccountName, 5))) on $left.Region == $right.Region
| distinct HPAccountName);
let query = strcat("metricNamespace('Health').metric('VipAvailability').dimensions('VipAddress', 'VipPort').samplingTypes('Average') | where VipAddress == '",AzureIP, "'");
evaluate geneva_metrics_request(SLBHPAccount, query, starttime, endtime)
| project TimestampUtc,VipPort, Average
| render timechart
```

### VFP - CurrentTotalFlowEntryIn Of LB Backend VM

```kql
let starttime= _startTime;
let endtime = _endTime;
let AzureIP = iff(isnotempty(VIP), VIP, "abcd");
let ContainerList=cluster('Azslb').database('azslbmds').DipEndpointProbeHistoryEvent
| where PreciseTimeStamp >= starttime - 1d and PreciseTimeStamp <= endtime + 1d
| where Vip == AzureIP
| distinct ContainerId;
let vfpaccount=toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 2h  and PreciseTimeStamp <= endtime
| where containerId in (ContainerList)
| distinct Tenantlower=tolower(Tenant)
| join kind=inner (cluster("azurehn.kusto.windows.net").database("Azurehn").MdmVfpVnetAccountMaps() | extend Tenant=tolower(Cluster)) on $left.Tenantlower == $right.Tenant 
| distinct VfpAccount);
let Containerstring=toscalar(ContainerList
| distinct ContainerId
| summarize containerlist=make_list(ContainerId)
| extend ContainerLists=strcat('("', array_strcat(containerlist, '","'), '")')
| distinct ContainerLists);
let CurrentTotalFlowEntryIn = strcat(@"metricNamespace('VfpPortFlowStats').metric('CurrentTotalFlowEntryIn').dimensions('ContainerId').samplingTypes('Sum') | where ContainerId in ", Containerstring);
evaluate geneva_metrics_request(vfpaccount, CurrentTotalFlowEntryIn, starttime, endtime)
| project TimestampUtc, ContainerId, CurrentTotalFlowEntryIn=Sum
| render timechart
```

### VFP - CurrentTotalFlowEntryOut Of LB Backend VM

```kql
let starttime= _startTime;
let endtime = _endTime;
let AzureIP = iff(isnotempty(VIP), VIP, "abcd");
let ContainerList=cluster('Azslb').database('azslbmds').DipEndpointProbeHistoryEvent
| where PreciseTimeStamp >= starttime - 1d and PreciseTimeStamp <= endtime + 1d
| where Vip == AzureIP
| distinct ContainerId;
let vfpaccount=toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 2h  and PreciseTimeStamp <= endtime
| where containerId in (ContainerList)
| distinct Tenantlower=tolower(Tenant)
| join kind=inner (cluster("azurehn.kusto.windows.net").database("Azurehn").MdmVfpVnetAccountMaps() | extend Tenant=tolower(Cluster)) on $left.Tenantlower == $right.Tenant 
| distinct VfpAccount);
let Containerstring=toscalar(ContainerList
| distinct ContainerId
| summarize containerlist=make_list(ContainerId)
| extend ContainerLists=strcat('("', array_strcat(containerlist, '","'), '")')
| distinct ContainerLists);
let CurrentTotalFlowEntryOut = strcat(@"metricNamespace('VfpPortFlowStats').metric('CurrentTotalFlowEntryOut').dimensions('ContainerId').samplingTypes('Sum') | where ContainerId in ", Containerstring);
evaluate geneva_metrics_request(vfpaccount, CurrentTotalFlowEntryOut, starttime, endtime)
| project TimestampUtc, ContainerId, CurrentTotalFlowEntryOut=Sum
| render timechart
```

### VFP - TcpConnectionsResetByInjectedResetInRate Of LB Backend VM

```kql
let starttime= _startTime;
let endtime = _endTime;
let AzureIP = iff(isnotempty(VIP), VIP, "abcd");
let ContainerList=cluster('Azslb').database('azslbmds').DipEndpointProbeHistoryEvent
| where PreciseTimeStamp >= starttime - 1d and PreciseTimeStamp <= endtime + 1d
| where Vip == AzureIP
| distinct ContainerId;
let vfpaccount=toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 2h  and PreciseTimeStamp <= endtime
| where containerId in (ContainerList)
| distinct Tenantlower=tolower(Tenant)
| join kind=inner (cluster("azurehn.kusto.windows.net").database("Azurehn").MdmVfpVnetAccountMaps() | extend Tenant=tolower(Cluster)) on $left.Tenantlower == $right.Tenant 
| distinct VfpAccount);
let Containerstring=toscalar(ContainerList
| distinct ContainerId
| summarize containerlist=make_list(ContainerId)
| extend ContainerLists=strcat('("', array_strcat(containerlist, '","'), '")')
| distinct ContainerLists);
let TcpConnectionsResetByInjectedResetInRate = strcat(@"metricNamespace('VfpPortDropMetrics').metric('TcpConnectionsResetByInjectedResetInRate').dimensions('ContainerId').samplingTypes('Sum') | where ContainerId in ", Containerstring);
evaluate geneva_metrics_request(vfpaccount, TcpConnectionsResetByInjectedResetInRate, starttime, endtime)
| project TimestampUtc, ContainerId, Sum
| render timechart
```

### VFP - TcpConnectionsResetByInjectedResetOutRate Of LB Backend VM

```kql
let starttime= _startTime;
let endtime = _endTime;
let AzureIP = iff(isnotempty(VIP), VIP, "abcd");
let ContainerList=cluster('Azslb').database('azslbmds').DipEndpointProbeHistoryEvent
| where PreciseTimeStamp >= starttime - 1d and PreciseTimeStamp <= endtime + 1d
| where Vip == AzureIP
| distinct ContainerId;
let vfpaccount=toscalar(cluster('AzureCM').database('AzureCM').LogContainerSnapshot
| where PreciseTimeStamp >= starttime - 2h  and PreciseTimeStamp <= endtime
| where containerId in (ContainerList)
| distinct Tenantlower=tolower(Tenant)
| join kind=inner (cluster("azurehn.kusto.windows.net").database("Azurehn").MdmVfpVnetAccountMaps() | extend Tenant=tolower(Cluster)) on $left.Tenantlower == $right.Tenant 
| distinct VfpAccount);
let Containerstring=toscalar(ContainerList
| distinct ContainerId
| summarize containerlist=make_list(ContainerId)
| extend ContainerLists=strcat('("', array_strcat(containerlist, '","'), '")')
| distinct ContainerLists);
let TcpConnectionsResetByInjectedResetOutRate = strcat(@"metricNamespace('VfpPortDropMetrics').metric('TcpConnectionsResetByInjectedResetOutRate').dimensions('ContainerId').samplingTypes('Sum') | where ContainerId in ", Containerstring);
evaluate geneva_metrics_request(vfpaccount, TcpConnectionsResetByInjectedResetOutRate, starttime, endtime)
| project TimestampUtc, ContainerId, Sum
| render timechart
```

