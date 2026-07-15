---
description: KQL queries for Azure Application Gateway diagnostics: health probes, backend status, WAF, access logs, config changes.
---

# Application Gateway Kusto Queries

> Source: Azure Networking B01 Dashboard (aka.ms/b01)
> Pages: App Gateway

## App Gateway

### History - AppGw-Instance-VFP-Dashboard  ---- Instance List between <starttime - 1d> and <endtime + 1d>

```kql
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let appgwname = AppGwName;
let ShoeBoxMdm=materialize(cluster('AzureCM').database('AzureCM').LogClusterSnapshot 
| distinct Region, shoeboxMdmAccountName);
let GatewayID=materialize(cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd 
//| where SnapshotTime >= starttime and SnapshotTime <= endtime
| where CustomerSubscriptionId == SubscriptionID
| where GatewayName == appgwname
| distinct  GatewayName, GatewaySubscriptionId, GatewayVersion, VmssNrpSubnetUri, InstanceCount,Instances, GatewayId
| distinct GatewayId);
let GatewayNameMapID=materialize(cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedProdHistory
| where SnapshotTime >= starttime - 1d and SnapshotTime <= endtime + 1d
| where CustomerSubscriptionId == SubscriptionID
| where GatewayName == appgwname
| project GatewayName, GatewayId, parse_json(Instances)
| mv-expand Instances
| evaluate bag_unpack(Instances)
| project GatewayName, GatewayId,  InstanceName=strcat("_",Name), IpAddress, LoadBalancerSshPort, LoadBalancerWebApiPort
);
cluster('hybridnetworking').database('aznwmds').AppGwToContainerId
| where PreciseTimeStamp >= starttime - 2h and PreciseTimeStamp <= endtime
| where GatewayId in (GatewayID)
| join kind=leftouter GatewayNameMapID on $left.RoleInstanceName == $right.InstanceName
| distinct GatewayName, GatewayId, Region, Tenant=Cluster, RoleInstanceName, nodeId=toupper(NodeId), containerId=ContainerId, IpAddress, LoadBalancerSshPort, LoadBalancerWebApiPort, VMSize
| join kind=leftouter(cluster('aznwcc').database('aznwmds').Servers) on $left.nodeId == $right.NodeId
| join kind=leftouter(cluster('aznwcc').database('aznwmds').DeviceInterfaceLinks) on $left.DeviceName == $right.StartDevice
//| join kind=inner cluster('aznwsdn').database("aznwmds").MdmVfpVnetAccountMaps on $left.Tenant == $right.Cluster
| join kind=inner cluster("azurehn.kusto.windows.net").database("Azurehn").MdmVfpVnetAccountMaps() on $left.Tenant == $right.Cluster
| extend VFPDashBoard=strcat("https://portal.microsoftgeneva.com/dashboard/VfpMDM/dpop/SupportDashboard?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VFPDropDashBoard=strcat("https://portal.microsoftgeneva.com/dashboard/VfpMDM/dpop/dropsDashboard?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend SupportDashBoard=strcat("https://portal.microsoftgeneva.com/s/9FDB0A67?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DropDashBoard=strcat("https://portal.microsoftgeneva.com/s/FCAB8E6B?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend FPGADashboard=strcat("https://portal.microsoftgeneva.com/s/24C5D63C?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend InvestigateNode=strcat("https://dataexplorer.azure.com/dashboards/bea4ccac-baf1-45f3-b160-533232cbfdaa?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH-mm-ss'),"Z&p-_endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH-mm-ss'), "Z&p-_NodeId=v-", nodeId, "&p-_ContainerId=v-", containerId, "&p-_ICMId=all#2f4843e6-c1e5-4564-ad27-cde71cebc7c7")
| extend ASIHostNode=strcat("https://azureserviceinsights.trafficmanager.net/view/services/Azure%20Host/pages/Azure%20Host%20Node?nodeId=",tolower(nodeId),"&globalFrom=",format_datetime(starttime, 'yyyy-MM-dd'),"T",format_datetime(starttime, 'HH'), "%3A",format_datetime(starttime, 'mm'), "%3A51.000Z&globalTo=",format_datetime(endtime, 'yyyy-MM-dd'),"T",format_datetime(endtime, 'HH'), "%3A",format_datetime(endtime, 'mm'),"%3A51.000Z")
| extend NetVMA=strcat("https://aka.ms/netvma/?destValue=&pathQuery=false&sdnPath=false&showPingMesh=false&startTime=", format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'), "&endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH:mm:ss'), "&value=", containerId)
| extend PerVMAvailability=strcat("https://portal.microsoftgeneva.com/s/A03537E6?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VNETAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend PerProcessorPNICDashboard=strcat("https://portal.microsoftgeneva.com/s/CAC1AF05?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VFPFullRule=strcat("https://portal.microsoftgeneva.com/?page=actions&acisEndpoint=Public&managementOpen=false&automatedTestsReportOpen=false&tab=Extensions&acisRolloutEndpoint=Public&selectedNodeType=3&extension=SupportabilityFabric&group=Fabric%20Operations&operationId=GetVfpFiltersForContainer&operationName=Get%20VFP%20Filters%20(ACL%20and%20VNET)%20programmed%20on%20containers&inputMode=single&params={%22smefabrichostparam%22:%22", Cluster, "%22,%22smenodeidparam%22:%22", nodeId, "%22,%22smecontaineridparam%22:%22", containerId,"%22,%22smemacaddressparam%22:%22%22,%22smelayerparam%22:%22%22,%22smegroupparam%22:%22%22,%22smeruleparam%22:%22%22,%22smenatpoolparam%22:%22%22,%22smenatrangeparam%22:%22%22,%22smespaceparam%22:%22%22,%22smemappingparam%22:%22%22,%22smevfpfiltercommandparam%22:%22list-rule%22,%22smevfpfilteroptionsparam%22:%22%22}&actionEndpoint=Production&genevatraceguid=9964f627-a5ca-435a-a749-e60f4a56c7f0")
| extend ListUnifiedFlow=strcat("https://portal.microsoftgeneva.com/?page=actions&acisEndpoint=Public&managementOpen=false&automatedTestsReportOpen=false&tab=Extensions&acisRolloutEndpoint=Public&selectedNodeType=3&extension=SupportabilityFabric&group=Fabric%20Operations&operationId=GetVfpFiltersForContainer&operationName=Get%20VFP%20Filters%20(ACL%20and%20VNET)%20programmed%20on%20containers&inputMode=single&params={%22smefabrichostparam%22:%22", Cluster, "%22,%22smenodeidparam%22:%22", nodeId, "%22,%22smecontaineridparam%22:%22", containerId,"%22,%22smemacaddressparam%22:%22%22,%22smelayerparam%22:%22%22,%22smegroupparam%22:%22%22,%22smeruleparam%22:%22%22,%22smenatpoolparam%22:%22%22,%22smenatrangeparam%22:%22%22,%22smespaceparam%22:%22%22,%22smemappingparam%22:%22%22,%22smevfpfiltercommandparam%22:%22list-unified-flow%22,%22smevfpfilteroptionsparam%22:%22%22}&actionEndpoint=Production&genevatraceguid=9964f627-a5ca-435a-a749-e60f4a56c7f0")
| where GatewayName != ""
| extend nodeId=tolower(nodeId)
| join kind=leftouter (cluster('AzureCM').database('AzureCM').LogNodeSnapshot | where PreciseTimeStamp >= starttime - 1d and PreciseTimeStamp <= endtime) on nodeId
| distinct GatewayName, RoleInstanceName,IpAddress, SshPort=LoadBalancerSshPort, WebApiPort=LoadBalancerWebApiPort, Tenant, EndDevice, T0Port=EndPort, nodeId=tolower(nodeId), nodeIP=ipAddress, containerId,VMSize, VFPDashBoard,SupportDashBoard, DropDashBoard, FPGADashboard, InvestigateNode, ASIHostNode, NetVMA, PerVMAvailability, PerProcessorPNICDashboard,VFPFullRule,ListUnifiedFlow
| where T0Port != "N"
| summarize T0=make_list(EndDevice) by GatewayName, RoleInstanceName,IpAddress, SshPort, WebApiPort, Tenant, nodeId, nodeIP, containerId,VMSize, VFPDashBoard,SupportDashBoard, DropDashBoard, FPGADashboard, InvestigateNode, ASIHostNode, NetVMA, PerVMAvailability, PerProcessorPNICDashboard,VFPFullRule,ListUnifiedFlow
| extend VMdash=strcat("https://web.kusto.windows.net/dashboards/f9ee36ad-73f0-4ae6-b752-f8be89e9245c?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'),"Z&p-_endTime=",format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime,'HH:mm:ss'),"Z&p-SubIdOrContainerId=v-",containerId,"&&p-VMName=v-ContaizerId&p-DataPathScan=v-No#8ed1e2a2-d979-401b-9609-7580ad07ccd1")
| distinct GatewayName, RoleInstanceName,IpAddress, SshPort, WebApiPort, Tenant, T0=tostring(T0), nodeId, nodeIP, containerId,VMSize, VMdash,VFPDashBoard,SupportDashBoard, DropDashBoard, FPGADashboard, Dridash=InvestigateNode, ASIHostNode, NetVMA, PerVMAvailability, PerProcessorPNICDashboard,VFPFullRule,ListUnifiedFlow

```

### AppGw-Latest-Information

```kql
let starttime = _startTime;
let endtime = _endTime;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| extend config = parse_json(Config)
| extend listeners = config["HttpListeners"]
| extend rules = config["HttpLoadBalancingRules"]
| extend rulesCount = array_length(rules)
| extend listenerCount = array_length(listeners)
| extend l4Listeners = config["L4Listeners"]
| extend l4Rules = config["L4LoadBalancingRules"]
| extend l4RulesCount = array_length(l4Rules)
| extend l4ListenerCount = array_length(l4Listeners)
| extend isAzwaf = binary_and(ApplicationGatewayFeatureFlag, 128) == 128
| extend isModsec = binary_and(ApplicationGatewayFeatureFlag, 1) == 1
| extend isHybrid = binary_and(ApplicationGatewayFeatureFlag, 1024) == 1024
| extend hasMemoryWatcher = binary_and(ApplicationGatewayFeatureFlag, 32768) == 32768
| extend slbAccount =  strcat("slbv2", strcat_array(split(tolower(LocationConstraint)," "),""))
| extend ELBIpAddress = parse_json(VirtualIPs)[0]
| extend ILBIpAddress = parse_json(VirtualIPs)[1]
| extend AppGwVMSS=strcat("/subscriptions/", GatewaySubscriptionId, "/resourceGroups/armrg-", GatewayId, "/providers/Microsoft.Compute/virtualMachineScaleSets/appgw")
| extend AppGwELB=strcat("/subscriptions/", GatewaySubscriptionId, "/resourceGroups/armrg-", GatewayId, "/providers/Microsoft.Network/loadBalancers/appgwLoadBalancer")
| extend AppGwILB=case(isnotempty(parse_json(VirtualIPs)[1]), strcat("/subscriptions/", GatewaySubscriptionId, "/resourceGroups/armrg-", GatewayId, "/providers/Microsoft.Network/loadBalancers/appgwILB"), "")
| extend SupportedFeatureFlag = strcat("https://msazure.visualstudio.com/One/_git/Networking-AppGW?path=/src/Tenant/Contracts/ObjectModel/ApplicationGatewayFlagFeatures.cs&version=GBdevelop")
| project SnapshotTime, GatewayId,ResourceUri, AppGwSubnet=VmssNrpSubnetUri,AppGwVMSS,AppGwELB,AppGwILB, AppGwvNetID= VnetId, CloudCustomerName, LocationConstraint, GatewayVersion, SkuType, listenerCount, rulesCount, l4ListenerCount, l4RulesCount, InstanceCount, AutoscaleConfiguration, RegisteredFeatures,SupportedFeatureFlag, ApplicationGatewayFeatureFlag, GatewaySubscriptionId, VirtualIPs, isAzwaf, isModsec , isHybrid, hasMemoryWatcher

| evaluate narrow()
| project Column, Value
```

### AppGw-History-Information

```kql
let starttime = _startTime;
let endtime = _endTime;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedProdHistory
| where SnapshotTime >= starttime - 1d and SnapshotTime <= _endTime
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| extend config = parse_json(Config)
| extend listeners = config["HttpListeners"]
| extend rules = config["HttpLoadBalancingRules"]
| extend rulesCount = array_length(rules)
| extend listenerCount = array_length(listeners)
| extend l4Listeners = config["L4Listeners"]
| extend l4Rules = config["L4LoadBalancingRules"]
| extend l4RulesCount = array_length(l4Rules)
| extend l4ListenerCount = array_length(l4Listeners)
| extend isAzwaf = binary_and(ApplicationGatewayFeatureFlag, 128) == 128
| extend isModsec = binary_and(ApplicationGatewayFeatureFlag, 1) == 1
| extend isHybrid = binary_and(ApplicationGatewayFeatureFlag, 1024) == 1024
| extend hasMemoryWatcher = binary_and(ApplicationGatewayFeatureFlag, 32768) == 32768
| extend slbAccount =  strcat("slbv2", strcat_array(split(tolower(LocationConstraint)," "),""))
| extend vipAddress = parse_json(VirtualIPs)[0]
| project SnapshotTime, GwId = GatewayId, CloudCustomerName, LocationConstraint, GatewayVersion, SkuType, listenerCount, rulesCount, l4ListenerCount, l4RulesCount, InstanceCount, Instances, AutoscaleConfiguration, RegisteredFeatures, ResourceUri, ApplicationGatewayFeatureFlag, GatewaySubscriptionId, VirtualIPs, isAzwaf, isModsec , isHybrid, hasMemoryWatcher
| sort by SnapshotTime
```

### AppGw - Data Path Dashboard

```kql
let starttime = _startTime;
let endtime = _endTime;
let min = datetime_diff('minute',endtime,starttime);
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| project GatewayName, GatewayId, LocationConstraint, ResourceUri
| extend  BackendServerDiagnosticHistory=strcat("https://portal.microsoftgeneva.com/logs/dgrep?be=DGrep&time=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'), "Z&offset=", min, "&offsetUnit=Minutes&UTC=true&ep=Diagnostics%20PROD&ns=AppGWT&en=BackendServerDiagnosticHistory&scopingConditions=[[%22Tenant%22,%22", GatewayId, "%22],[%22__Region__%22,%22", LocationConstraint,"%22]]&conditions=[]&clientQuery=orderby%20preciseTimeStamp%20asc&chartEditorVisible=true&chartType=line&chartLayers=[[%22New%20Layer%22,%22%22]]%20")
| extend ReqResLog=strcat("https://portal.microsoftgeneva.com/logs/dgrep?be=DGrep&time=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'), "Z&offset=", min, "&offsetUnit=Minutes&UTC=true&ep=Diagnostics%20PROD&ns=AppGWT&en=ReqRespLog&scopingConditions=[[%22Tenant%22,%22", GatewayId, "%22],[%22__Region__%22,%22", LocationConstraint,"%22]]&serverQuery=source%0A|%20extend%20json%3Dparse_json(properties)%0A|%20extend%20clientIP%20%3D%20trim('%22',json.clientIP)%0A|%20extend%20clientPort%20%3D%20tolong(trim('%22',json.clientPort))%0A|%20extend%20httpMethod%20%3D%20trim('%22',json.httpMethod)%0A|%20extend%20originalRequestUriWithArgs%20%3D%20trim('%22',json.originalRequestUriWithArgs)%0A|%20extend%20requestUri%20%3D%20trim('%22',json.requestUri)%0A|%20extend%20requestQuery%20%3D%20trim('%22',json.requestQuery)%0A|%20extend%20userAgent%20%3D%20trim('%22',json.userAgent)%0A|%20extend%20httpStatus%20%3D%20tolong(trim('%22',json.httpStatus))%0A|%20extend%20httpVersion%20%3D%20trim('%22',json.httpVersion)%0A|%20extend%20receivedBytes%20%3D%20tolong(trim('%22',json.receivedBytes))%0A|%20extend%20sentBytes%20%3D%20tolong(trim('%22',json.sentBytes))%0A|%20extend%20timeTaken%20%3D%20todouble(trim('%22',json.timeTaken))%0A|%20extend%20transactionId%20%3D%20trim('%22',json.transactionId)%0A|%20extend%20sslEnabled%20%3D%20trim('%22',json.sslEnabled)%0A|%20extend%20sslCipher%20%3D%20trim('%22',json.sslCipher)%0A|%20extend%20sslProtocol%20%3D%20trim('%22',json.sslProtocol)%0A|%20extend%20sslClientVerify%20%3D%20trim('%22',json.sslClientVerify)%0A|%20extend%20sslClientCertificateFingerprint%20%3D%20trim('%22',json.sslClientCertificateFingerprint)%0A|%20extend%20serverRouted%20%3D%20trim('%22',json.serverRouted)%0A|%20extend%20serverStatus%20%3D%20toint(trim('%22',json.serverStatus))%0A|%20extend%20serverResponseLatency%20%3D%20todouble(trim('%22',json.serverResponseLatency))%0A|%20project-away%20json,%20properties&serverQueryType=kql&kqlClientQuery=source%0A|%20order%20by%20PreciseTimeStamp%20asc&chartEditorVisible=true&chartType=line&chartLayers=[[%22New%20Layer%22,%22%22]]%20")
| extend ReqresErrorLog=strcat("https://portal.microsoftgeneva.com/logs/dgrep?be=DGrep&time=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'), "Z&offset=", min, "&offsetUnit=Minutes&UTC=true&ep=Diagnostics%20PROD&ns=AppGWT&en=ReqRespErrorLog&scopingConditions=[[%22Tenant%22,%22", GatewayId, "%22],[%22__Region__%22,%22", LocationConstraint,"%22]]&conditions=[]&clientQuery=orderby%20preciseTimeStamp%20asc&chartEditorVisible=true&chartType=line&chartLayers=[[%22New%20Layer%22,%22%22]]%20")
| extend  AppGwWAFLog=strcat("https://portal.microsoftgeneva.com/logs/dgrep?be=DGrep&time=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'), "Z&offset=", min, "&offsetUnit=Minutes&UTC=true&ep=Diagnostics%20PROD&ns=AppGWT&en=ApplicationGatewayFirewallLog&scopingConditions=[[%22Tenant%22,%22", GatewayId, "%22],[%22__Region__%22,%22", LocationConstraint,"%22]]&conditions=[]&clientQuery=orderby%20preciseTimeStamp%20asc&chartEditorVisible=true&chartType=line&chartLayers=[[%22New%20Layer%22,%22%22]]%20")
| extend AppGwTenantLog=strcat("https://portal.microsoftgeneva.com/logs/dgrep?be=DGrep&time=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'), "Z&offset=", min, "&offsetUnit=Minutes&UTC=true&ep=Diagnostics%20PROD&ns=AppGWT&en=ApplicationGatewayTenant,ErrorLogEvent,InformationLogEvent&scopingConditions=[[%22Tenant%22,%22", GatewayId,"%22],[%22__Region__%22,%22", LocationConstraint,"%22]]&conditions=[]&clientQuery=orderby%20preciseTimeStamp%20asc&chartEditorVisible=true&chartType=line&chartLayers=[[%22New%20Layer%22,%22%22]]%20")
| extend PlatformMetrics_V1SKU=strcat("https://portal.microsoftgeneva.com/s/1EE704C6?overrides=[{%22query%22:%22//*[id='applicationGatewayId']%22,%22key%22:%22value%22,%22replacement%22:%22", GatewayId, "%22},{%22query%22:%22//*[id='roleInstance']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='servicePrefix']%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend Overview_V2SKU=strcat("https://portal.microsoftgeneva.com/s/5444025C?overrides=[{%22query%22:%22//*[id='applicationGatewayId']%22,%22key%22:%22value%22,%22replacement%22:%22",GatewayId,"%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend AppGwV2_RequestMetrics=strcat("https://portal.microsoftgeneva.com/s/C32DF4E7?overrides=[{%22query%22:%22//*[id='ResourceId']%22,%22key%22:%22value%22,%22replacement%22:%22",ResourceUri,"%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VMSSPlatformMetrics_V2SKU=strcat("https://portal.microsoftgeneva.com/s/177F7E8A?overrides=[{%22query%22:%22//*[id='applicationGatewayId']%22,%22key%22:%22value%22,%22replacement%22:%22",GatewayId,"%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| project ReqResLog,ReqresErrorLog,AppGwWAFLog,BackendServerDiagnosticHistory, Overview_V2SKU,AppGwV2_RequestMetrics,PlatformMetrics_V1SKU,VMSSPlatformMetrics_V2SKU,AppGwTenantLog
| evaluate narrow()
| project Key=Column, Value



```

### AppGw-ELB-Dashboard

```kql
let starttime = _startTime;
let endtime = _endTime;
let min = datetime_diff('minute',endtime,starttime);
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
let GatewayVIP0=toscalar(cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName contains appgwname
| project VIP=parse_json(VirtualIPs)[0]);
let GatewayVIP1=toscalar(cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName contains appgwname
| project VIP=parse_json(VirtualIPs)[1]);
cluster('azslb').database('azslbmds').VipMetadataSnapshotRecord
| where env_time > starttime - 6h and env_time < endtime + 1h
| where Vip == GatewayVIP0 or Vip == GatewayVIP1
| summarize by Vip, VipUri, Type, SKU, AltAddress, VmLocs, CountHosts, env_cloud_role, Region
| join (cluster('azslb').database('azslbmds').SlbMetadataVersionRecord
| where env_time > starttime - 1h and env_time < endtime + 1h
|summarize by Region, MdmAccountName, ArmRegion
| extend HPAccountName = strcat("slbhp", substring(MdmAccountName, 5))) on $left.Region == $right.Region
| extend BandwithUsage=strcat("https://portal.microsoftgeneva.com/s/3CA61B31?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbhp", ArmRegion,"%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VIPAvailability=strcat("https://portal.microsoftgeneva.com/s/2438DA2C?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountName, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip, "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22""%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DipAvailability=strcat("https://portal.microsoftgeneva.com/s/4FFD22D2?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",MdmAccountName, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip, "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend Sflowdashboard=strcat("https://portal.microsoftgeneva.com/s/B40A24AB?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend Netflowdashboard=strcat("https://portal.microsoftgeneva.com/s/A5CECCEE?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DDOSStandardPlanCRIDashboard=strcat("https://portal.microsoftgeneva.com/s/BA074862?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",Vip,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| distinct Vip,  SKU, CountHosts, BandwithUsage,VIPAvailability,DipAvailability,Netflowdashboard,DDOSBasicPlanSflowDashbard=Sflowdashboard,DDOSStandardPlanCRIDashboard
| evaluate narrow()
| project Key=Column, Value
```

### Control Plane - By Customer Initiated

```kql
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
union cluster('armprodsea.southeastasia').database('Requests').EventServiceEntries,cluster('armprodeus.eastus').database('Requests').EventServiceEntries,cluster('armprodweu.westeurope').database('Requests').EventServiceEntries
| where PreciseTimeStamp >= starttime and PreciseTimeStamp <= endtime
| where subscriptionId == subscriptionid
| where resourceUri contains appgwname
| where operationName !contains "Authorization"
| distinct PreciseTimeStamp,operationName, status, AppGwName=tostring(split(resourceUri, "applicationGateways/")[1]), correlationId, Operator=tostring(parse_json(claims)["name"]), Status = strcat(PreciseTimeStamp, " -> ", status)
| summarize Status = make_list (Status) by operationName, AppGwName, correlationId, Operator
| join kind=inner cluster('hybridnetworking').database('aznwmds').GatewayManagerLogsTable on $left.correlationId == $right.CorrelationRequestId
| where PreciseTimeStamp >= starttime and PreciseTimeStamp <= endtime
| distinct Operator,AppGwName, OperationStatus=tostring(Status),operationName, correlationId, GWMActivityID=ActivityId
|extend parse_json(OperationStatus)
| extend ControlPlane=strcat("https://portal.microsoftgeneva.com/s/88483F35?overrides=[{%22query%22:%22//*[id='GatewayManagerActivityId']%22,%22key%22:%22value%22,%22replacement%22:%22", GWMActivityID,"%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| project Operator, AppGwName,operationName, OperationStatus, ControlPlane, correlationId, GWMActivityID
```

### AppGw-Resources-Under-Subscription

```kql
//forpageview
let pv=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('kusto').adxpageview| where page contains "b01/appgw";
//forpageview
let starttime = _startTime;
let endtime = _endTime;
let subscriptionid = SubscriptionID;
cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| project SnapshotTime, GatewayName, SkuType,LocationConstraint, ResourceUri,VirtualIPs, State
```

### AppGw-ILB-Dashboard

```kql
let starttime = _startTime;
let endtime = _endTime;
let subscriptionid = SubscriptionID;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let appgwname = AppGwName;
let AppGwILB=cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| extend ILBIpAddress = parse_json(VirtualIPs)[1]
| extend AppGwILB=iff(isnotempty(parse_json(VirtualIPs)[1]), strcat("/subscriptions/", GatewaySubscriptionId, "/resourceGroups/armrg-", GatewayId, "/providers/Microsoft.Network/loadBalancers/appgwILB"), "N/A")
| distinct AppGwILB;
let AppGwILBARMID=cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where timestamp >= starttime - 1d and timestamp <= endtime
| where type == "microsoft.network/loadbalancers"
| where id in~ (AppGwILB)
| distinct LoadBalancerArmId=tostring(properties["resourceGuid"]);
cluster('Azslb').database('azslbmds').VipHealthProbe 
| where env_time > starttime - 1h and env_time <= endtime
| where LoadBalancerArmId in (AppGwILBARMID)
| distinct VipAddress, VipOrIlbPA, Region, LoadBalancerArmId
| extend BandwithUsage=strcat("https://portal.microsoftgeneva.com/s/3CA61B31?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbhp", Region,"%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", LoadBalancerArmId,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VIPAvailability=strcat("https://portal.microsoftgeneva.com/s/2438DA2C?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbv2",Region, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22",LoadBalancerArmId,"%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DipAvailability=strcat("https://portal.microsoftgeneva.com/s/4FFD22D2?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22slbv2",Region, "%22},{%22query%22:%22//*[id='VipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22},{%22query%22:%22//*[id='Slbv2MDMAccount']%22,%22key%22:%22value%22,%22replacement%22:%22slbv2francecentral%22},{%22query%22:%22//*[id='CaAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipPort']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='ProtocolType']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='DipAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='HostAddress']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='Ring']%22,%22key%22:%22value%22,%22replacement%22:%22%22},{%22query%22:%22//*[id='LoadBalancerArmId']%22,%22key%22:%22value%22,%22replacement%22:%22",LoadBalancerArmId,"%22},{%22query%22:%22//*[id='PublicIpArmId']%22,%22key%22:%22value%22,%22replacement%22:%22", "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend Sflowdashboard=strcat("https://portal.microsoftgeneva.com/s/B40A24AB?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",VipAddress,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend Netflowdashboard=strcat("https://portal.microsoftgeneva.com/s/A5CECCEE?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",VipAddress,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DDOSStandardPlanCRIDashboard=strcat("https://portal.microsoftgeneva.com/s/BA074862?overrides=[{%22query%22:%22//*[id='DestinationVIP']%22,%22key%22:%22value%22,%22replacement%22:%22",VipAddress,"%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| distinct  ILBPA=VipOrIlbPA, Region, BandwithUsage, VIPAvailability, DipAvailability,Netflowdashboard, DDOSBasicPlanSflowDashbard=Sflowdashboard,DDOSStandardPlanCRIDashboard
| evaluate narrow()
| project Key=Column, Value
```

### Latest - AppGw-Instance-VFP-Dashboard

```kql
let starttime = _startTime;
let endtime = _endTime;
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let appgwname = AppGwName;
let ShoeBoxMdm=materialize(cluster('AzureCM').database('AzureCM').LogClusterSnapshot 
| distinct Region, shoeboxMdmAccountName);
let GatewayID=materialize(cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd 
//| where SnapshotTime >= starttime and SnapshotTime <= endtime
| where CustomerSubscriptionId == SubscriptionID
| where GatewayName == appgwname
| distinct  GatewayName, GatewaySubscriptionId, GatewayVersion, VmssNrpSubnetUri, InstanceCount,Instances, GatewayId
| distinct GatewayId);
let GatewayNameMapID=materialize(cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == SubscriptionID
| where GatewayName == appgwname
| project GatewayName, GatewayId, parse_json(Instances)
| mv-expand Instances
| evaluate bag_unpack(Instances)
| project GatewayName, GatewayId,  InstanceName=strcat("_",Name), IpAddress, LoadBalancerSshPort, LoadBalancerWebApiPort
);
cluster('hybridnetworking').database('aznwmds').AppGwToContainerId
| where PreciseTimeStamp >= starttime - 2h and PreciseTimeStamp <= endtime
| where GatewayId in (GatewayID)
| join kind=leftouter GatewayNameMapID on $left.RoleInstanceName == $right.InstanceName
| distinct GatewayName, GatewayId, Region, Tenant=Cluster, RoleInstanceName, nodeId=toupper(NodeId), containerId=ContainerId, IpAddress, LoadBalancerSshPort, LoadBalancerWebApiPort, VMSize
| join kind=leftouter(cluster('aznwcc').database('aznwmds').Servers) on $left.nodeId == $right.NodeId
| join kind=leftouter(cluster('aznwcc').database('aznwmds').DeviceInterfaceLinks) on $left.DeviceName == $right.StartDevice
//| join kind=inner cluster('aznwsdn').database("aznwmds").MdmVfpVnetAccountMaps on $left.Tenant == $right.Cluster
| join kind=inner cluster("azurehn.kusto.windows.net").database("Azurehn").MdmVfpVnetAccountMaps() on $left.Tenant == $right.Cluster
| extend VFPDashBoard=strcat("https://portal.microsoftgeneva.com/dashboard/VfpMDM/dpop/SupportDashboard?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VFPDropDashBoard=strcat("https://portal.microsoftgeneva.com/dashboard/VfpMDM/dpop/dropsDashboard?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend SupportDashBoard=strcat("https://portal.microsoftgeneva.com/s/9FDB0A67?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend DropDashBoard=strcat("https://portal.microsoftgeneva.com/s/FCAB8E6B?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend FPGADashboard=strcat("https://portal.microsoftgeneva.com/s/24C5D63C?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend InvestigateNode=strcat("https://dataexplorer.azure.com/dashboards/bea4ccac-baf1-45f3-b160-533232cbfdaa?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH-mm-ss'),"Z&p-_endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH-mm-ss'), "Z&p-_NodeId=v-", nodeId, "&p-_ContainerId=v-", containerId, "&p-_ICMId=all#2f4843e6-c1e5-4564-ad27-cde71cebc7c7")
| extend ASIHostNode=strcat("https://azureserviceinsights.trafficmanager.net/view/services/Azure%20Host/pages/Azure%20Host%20Node?nodeId=",tolower(nodeId),"&globalFrom=",format_datetime(starttime, 'yyyy-MM-dd'),"T",format_datetime(starttime, 'HH'), "%3A",format_datetime(starttime, 'mm'), "%3A51.000Z&globalTo=",format_datetime(endtime, 'yyyy-MM-dd'),"T",format_datetime(endtime, 'HH'), "%3A",format_datetime(endtime, 'mm'),"%3A51.000Z")
| extend NetVMA=strcat("https://aka.ms/netvma/?destValue=&pathQuery=false&sdnPath=false&showPingMesh=false&startTime=", format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'), "&endTime=", format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime, 'HH:mm:ss'), "&value=", containerId)
| extend PerVMAvailability=strcat("https://portal.microsoftgeneva.com/s/A03537E6?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VNETAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend PerProcessorPNICDashboard=strcat("https://portal.microsoftgeneva.com/s/CAC1AF05?overrides=[{%22query%22:%22//dataSources%22,%22key%22:%22account%22,%22replacement%22:%22",VfpAccount, "%22},{%22query%22:%22//*[id%3D%27Cluster%27]%22,%22key%22:%22value%22,%22replacement%22:%22",Tenant,"%22},{%22query%22:%22//*[id%3D%27NodeId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",nodeId, "%22},{%22query%22:%22//*[id%3D%27ContainerId%27]%22,%22key%22:%22value%22,%22replacement%22:%22",containerId, "%22}]&globalStartTime=", startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend VFPFullRule=strcat("https://portal.microsoftgeneva.com/?page=actions&acisEndpoint=Public&managementOpen=false&automatedTestsReportOpen=false&tab=Extensions&acisRolloutEndpoint=Public&selectedNodeType=3&extension=SupportabilityFabric&group=Fabric%20Operations&operationId=GetVfpFiltersForContainer&operationName=Get%20VFP%20Filters%20(ACL%20and%20VNET)%20programmed%20on%20containers&inputMode=single&params={%22smefabrichostparam%22:%22", Cluster, "%22,%22smenodeidparam%22:%22", nodeId, "%22,%22smecontaineridparam%22:%22", containerId,"%22,%22smemacaddressparam%22:%22%22,%22smelayerparam%22:%22%22,%22smegroupparam%22:%22%22,%22smeruleparam%22:%22%22,%22smenatpoolparam%22:%22%22,%22smenatrangeparam%22:%22%22,%22smespaceparam%22:%22%22,%22smemappingparam%22:%22%22,%22smevfpfiltercommandparam%22:%22list-rule%22,%22smevfpfilteroptionsparam%22:%22%22}&actionEndpoint=Production&genevatraceguid=9964f627-a5ca-435a-a749-e60f4a56c7f0")
| extend ListUnifiedFlow=strcat("https://portal.microsoftgeneva.com/?page=actions&acisEndpoint=Public&managementOpen=false&automatedTestsReportOpen=false&tab=Extensions&acisRolloutEndpoint=Public&selectedNodeType=3&extension=SupportabilityFabric&group=Fabric%20Operations&operationId=GetVfpFiltersForContainer&operationName=Get%20VFP%20Filters%20(ACL%20and%20VNET)%20programmed%20on%20containers&inputMode=single&params={%22smefabrichostparam%22:%22", Cluster, "%22,%22smenodeidparam%22:%22", nodeId, "%22,%22smecontaineridparam%22:%22", containerId,"%22,%22smemacaddressparam%22:%22%22,%22smelayerparam%22:%22%22,%22smegroupparam%22:%22%22,%22smeruleparam%22:%22%22,%22smenatpoolparam%22:%22%22,%22smenatrangeparam%22:%22%22,%22smespaceparam%22:%22%22,%22smemappingparam%22:%22%22,%22smevfpfiltercommandparam%22:%22list-unified-flow%22,%22smevfpfilteroptionsparam%22:%22%22}&actionEndpoint=Production&genevatraceguid=9964f627-a5ca-435a-a749-e60f4a56c7f0")
| where GatewayName != ""
| extend nodeId=tolower(nodeId)
| join kind=leftouter (cluster('AzureCM').database('AzureCM').LogNodeSnapshot | where PreciseTimeStamp >= starttime - 1d and PreciseTimeStamp <= endtime) on nodeId
| distinct GatewayName, RoleInstanceName,IpAddress, SshPort=LoadBalancerSshPort, WebApiPort=LoadBalancerWebApiPort, Tenant, EndDevice, T0Port=EndPort, nodeId=tolower(nodeId), nodeIP=ipAddress, containerId,VMSize, VFPDashBoard,SupportDashBoard, DropDashBoard, FPGADashboard, InvestigateNode, ASIHostNode, NetVMA, PerVMAvailability, PerProcessorPNICDashboard,VFPFullRule,ListUnifiedFlow
| where T0Port != "N"
| summarize T0=make_list(EndDevice) by GatewayName, RoleInstanceName,IpAddress, SshPort, WebApiPort, Tenant, nodeId, nodeIP, containerId,VMSize, VFPDashBoard,SupportDashBoard, DropDashBoard, FPGADashboard, InvestigateNode, ASIHostNode, NetVMA, PerVMAvailability, PerProcessorPNICDashboard,VFPFullRule,ListUnifiedFlow
| extend VMdash=strcat("https://web.kusto.windows.net/dashboards/f9ee36ad-73f0-4ae6-b752-f8be89e9245c?p-_startTime=",format_datetime(starttime, 'yyyy-MM-dd'), "T", format_datetime(starttime,'HH:mm:ss'),"Z&p-_endTime=",format_datetime(endtime,'yyyy-MM-dd'), "T", format_datetime(endtime,'HH:mm:ss'),"Z&p-SubIdOrContainerId=v-",containerId,"&&p-VMName=v-ContaizerId&p-DataPathScan=v-No#8ed1e2a2-d979-401b-9609-7580ad07ccd1")
| distinct GatewayName, RoleInstanceName,IpAddress, SshPort, WebApiPort, Tenant, T0=tostring(T0), nodeId, nodeIP, containerId,VMSize,VMdash, VFPDashBoard,SupportDashBoard, DropDashBoard, FPGADashboard, InvestigateNode, ASIHostNode, NetVMA, PerVMAvailability, PerProcessorPNICDashboard,VFPFullRule,ListUnifiedFlow


```

### AppGw NSG Rule if has

```kql
let starttime = _startTime;
let endtime = _endTime;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
let AppGwResourceUri=toscalar(cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedProdHistory
| where SnapshotTime >= starttime - 1d and SnapshotTime <= _endTime
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| distinct ResourceUri);
let AppGwNSG=toscalar(cluster('Hybridnetworking').database('GatewayManager').GetAppGwNsg(AppGwResourceUri)
| project nsgId);
let AppGwNSGRulecount=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where timestamp >= starttime - 2d and timestamp <= endtime
| where id in~ (AppGwNSG)
| distinct RemotePeeringCount=array_length((properties["securityRules"]))
);
let end = toint(AppGwNSGRulecount);
let NSGRules=toscalar(cluster('argwus2nrpone.westus2').database('AzureResourceGraph').Resources
| where timestamp >= starttime - 2d and timestamp <= endtime
| where id in~ (AppGwNSG)
| project NSGRules=(properties["securityRules"]));
range i from 0 to end step 1
| project NSGName=NSGRules[i]["name"],Direction=NSGRules[i]["properties"]["direction"], Priority=toint(NSGRules[i]["properties"]["priority"]), Action=NSGRules[i]["properties"]["access"], protocol=NSGRules[i]["properties"]["protocol"], sourceAddressPrefix=NSGRules[i]["properties"]["sourceAddressPrefix"], sourceAddressPrefixes=NSGRules[i]["properties"]["sourceAddressPrefixes"], sourcePortRange=NSGRules[i]["properties"]["sourcePortRange"], sourcePortRanges=NSGRules[i]["properties"]["sourcePortRanges"],destinationAddressPrefix=NSGRules[i]["properties"]["destinationAddressPrefix"],destinationAddressPrefixes=NSGRules[i]["properties"]["destinationAddressPrefixes"],destinationPortRange=NSGRules[i]["properties"]["destinationPortRange"],destinationPortRanges=NSGRules[i]["properties"]["destinationPortRanges"],description=NSGRules[i]["properties"]["description"]
| where NSGName != ""
| order by Priority asc  

```

### AppGw - Control Plane Activity on GWM

```kql
let starttime = _startTime;
let endtime = _endTime;
let min = datetime_diff('minute',endtime,starttime);
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
let appgwresourceuri=toscalar(cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| distinct ResourceUri);
cluster('Hybridnetworking').database('aznwmds').AppGwOperationHistorySummary(appgwresourceuri,starttime,endtime)
| project GwmOperationStartTime, OperationCategory, GatewayManagerActivityId,SdkOperationStatus, AsyncOperationStatus,ConfDiff, ResDiff, Diff
| extend ControlPlaneDetailed=strcat("https://portal.microsoftgeneva.com/s/88483F35?overrides=[{%22query%22:%22//*[id='GatewayManagerActivityId']%22,%22key%22:%22value%22,%22replacement%22:%22", GatewayManagerActivityId,"%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| project OperationStartTime=GwmOperationStartTime, OperationCategory, ControlPlaneDetailed


```

### AppGw - Control Plane Dashboard

```kql
let starttime = _startTime;
let endtime = _endTime;
let min = datetime_diff('minute',endtime,starttime);
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| project GatewayName, GatewayId, LocationConstraint, ResourceUri
| extend ControlPlaneOverView=strcat("https://portal.microsoftgeneva.com/s/5B0DA176?overrides=[{%22query%22:%22//*[id='ResourceUri']%22,%22key%22:%22value%22,%22replacement%22:%22", ResourceUri, "%22},{%22query%22:%22//*[id='ResourceId']%22,%22key%22:%22value%22,%22replacement%22:%22", ResourceUri,"%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| extend AutoscaleMetrics=strcat("https://portal.microsoftgeneva.com/s/34385D01?overrides=[{%22query%22:%22//*[id='GatewayId']%22,%22key%22:%22value%22,%22replacement%22:%22",GatewayId,"%22},{%22query%22:%22//*[id='ResourceUri']%22,%22key%22:%22value%22,%22replacement%22:%22%22}]&globalStartTime=",startunixtime, "&globalEndTime=", endunixtime, "&pinGlobalTimeRange=true")
| project ControlPlaneOverView,AutoscaleMetrics
| evaluate narrow()
| project Key=Column, Value



```

### PV

```kql
let pv=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('kusto').adxpageview| where page contains "b01/appgw";
let pvcount=cluster('kvcy2wf2t0n1epwsyck1cj.australiaeast').database('microsoft').adxpageview | where page contains "b01/appgw" | summarize count();
union pv, pvcount
```

### ApplicationGatewayTenant _QoS (limit 2000)

```kql
let starttime = _startTime;
let endtime = _endTime;
let min = datetime_diff('minute',endtime,starttime);
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
let GatewayID=cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| distinct GatewayId;
cluster('Hybridnetworking').database('aznwmds').ApplicationGatewayTenant
| where PreciseTimeStamp >= starttime and PreciseTimeStamp <= endtime
| where GatewayId in (GatewayID)
| where not (ActivityName == 'MetricDaemonPeriodicTask' or ActivityName =='SendBillingEventPeriodicTask' or ActivityName =='ScheduledEventsPeriodicTask')
| project PreciseTimeStamp, ActivityId, ActivityName, ComponentName, Tid, Pid, Level, Msg, RoleInstance
| project-reorder PreciseTimeStamp | order by PreciseTimeStamp asc
| take 2000

```

### ApplicationGatewayTenant _ActivitySummary

```kql
let starttime = _startTime;
let endtime = _endTime;
let min = datetime_diff('minute',endtime,starttime);
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
let GatewayID=cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| distinct GatewayId;
cluster('Hybridnetworking').database('aznwmds').ApplicationGatewayTenant
| where PreciseTimeStamp >= starttime and PreciseTimeStamp <= endtime
| where GatewayId in (GatewayID)
| project PreciseTimeStamp, ActivityId, ActivityName, ComponentName, Tid, Pid, Level, Msg, RoleInstance
| summarize count() by ActivityName
| project Sum=count_,ActivityName | order by Sum desc 
```

### ApplicationGatewayTenant _GetBackendHealth

```kql
let starttime = _startTime;
let endtime = _endTime;
let min = datetime_diff('minute',endtime,starttime);
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
let GatewayID=cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| distinct GatewayId;
cluster('Hybridnetworking').database('aznwmds').ApplicationGatewayTenant
| where PreciseTimeStamp >= starttime and PreciseTimeStamp <= endtime
| where GatewayId in (GatewayID)
| where ActivityName == 'GetBackendHealth'
| project PreciseTimeStamp, ActivityId, ActivityName, ComponentName, Tid, Pid, Level, Msg, RoleInstance
```

### AsyncWorkerLogsTable

```kql
let starttime = _startTime;
let endtime = _endTime;
let min = datetime_diff('minute',endtime,starttime);
let startunixtime = tolong(starttime-datetime(1970-01-01)) / 10000;
let endunixtime = tolong(endtime-datetime(1970-01-01)) / 10000;
let subscriptionid = SubscriptionID;
let appgwname = AppGwName;
let GatewayID=cluster('Hybridnetworking').database('GatewayManager').ApplicationGatewaysExtendedLatestProd
| where CustomerSubscriptionId == subscriptionid 
| where GatewayName == appgwname
| distinct GatewayId;
cluster('Hybridnetworking').database('aznwmds').AsyncWorkerLogsTable 
| where TIMESTAMP >starttime and TIMESTAMP <endtime
| where GatewayId in (GatewayID)
| project  PreciseTimeStamp, Role, ActivityId, Id, ErrorLevel, GatewayName, Message
```

## Diagnostic Settings

### Check if Application Gateway has Diagnostic Settings / Log Analytics Configured

Use this query to verify if an Application Gateway resource has diagnostic settings configured (Log Analytics, Storage Account, or Event Hub).

```kql
let resId = "<ResourceID>"; // e.g., /subscriptions/xxxxx/resourceGroups/rg-name/providers/Microsoft.Network/applicationGateways/appgw-name
cluster('Azureinsights.kusto.windows.net').database('Insights').RegistrationTelemetry
| where PreciseTimeStamp > ago(5d)
| where resourceId =~ resId
| summarize arg_max(PreciseTimeStamp, *) by name, serviceIdentity, resourceId, workspaceId, serviceBusInformation, customerStorageAccountId, categories
| project resourceId, dataType, categories, omsWorkspaceResourceId, customerStorageAccountId, eventHubAuthorizationRuleId
```

**Result Interpretation:**

| Field | Description |
|-------|-------------|
| `dataType` | `Logs` or `Metrics` |
| `categories` | Enabled log categories (e.g., `ApplicationGatewayAccessLog\|ApplicationGatewayPerformanceLog\|ApplicationGatewayFirewallLog`) |
| `omsWorkspaceResourceId` | Log Analytics workspace resource ID (if configured) |
| `customerStorageAccountId` | Storage account (if configured for archival) |
| `eventHubAuthorizationRuleId` | Event Hub (if configured for streaming) |

**If no results are returned**, the Application Gateway does not have diagnostic settings configured.

If confirm customer has Log Analytics Workspace or storage account or Application Insight, always reminder user to use Azure Support Center to review the log manually 

> **Tip - Query Customer Log Analytics Workspace Data**:
> 1. Extract the subscription ID from `omsWorkspaceResourceId` in the result below
> 2. Go to **Azure Support Center** → open the case and go to **SubscriptionID** in step one **Log** → **Microsoft.OperationalInsights/Workspaces** → **Query Customer Data** → **Kusto Query Table**
> 3. If that subscription is different from the case scope, **add that subscription to your case** before querying the workspace

