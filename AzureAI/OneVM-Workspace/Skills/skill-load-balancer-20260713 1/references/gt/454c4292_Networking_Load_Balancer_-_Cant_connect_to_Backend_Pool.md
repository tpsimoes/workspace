# Networking] Load Balancer - Can't connect to Backend Pool

> **Product:** Load Balancer  
> **Solution ID:** 454c4292-c3c0-4c42-9ed9-a8e4428b0d21  
> **Trigger words:** backend, balancer, can't, connect, connectivity issue, load balancer, networking]

---

## Overview

This guide provides step-by-step troubleshooting for **Networking] Load Balancer - Can't connect to Backend Pool** under **Load Balancer**.
 The original guided troubleshooter contains 29 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Check Scope ⭐ (First Step)

### Guidance

Verify the customer issue is a match for this troubleshooting checklist and guide. This is a load balancer connectivity troubleshooting guide, not an operation failure troubleshooting guide (such as unable to delete load balancer). If you need assistance with troubleshooting failed load balancer operations, consult your TA (an interactive troubleshooting checklist and guide has not yet been developed for this scenario).

Note: this TSG is also NOT for configuring AKS. Do not submit feedback asking for AKS control plane troubleshooting.

### Question

**Check if the customer issue within the scope of this TSG**

### Options

- **Yes** → Go to: *Clarify problem statement*
- **No** → Go to: *This issue is outside the scope for this TSG*

---

### Step 2: Some scenarios not supported

### Support Engineer Solution

## Basic load balancer support

* Resources in one virtual network cannot communicate with the front-end IP address of a Basic SKU internal load balancer in a globally peered virtual network
* To connect to internal load balancers from globally peered VNets, the customer must upgrade to Standard Load Balancer SKU. Currently, the customer must delete their existing load balancer and redeploy it as standard SKU as directly upgrading is not possible. The product team makes a script available to automate this available here: https://docs.microsoft.com/azure/load-balancer/upgrade-basic-standard

### Recommended Documents

* https://docs.microsoft.com/azure/virtual-network/virtual-networks-faq#what-are-the-constraints-related-to-global-vnet-peering-and-load-balancers

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reviewed your configuration and determined your issue is due to the use of a basic SKU load balancer. Resources in one virtual network cannot communicate with the front-end IP address of a basic internal load balancer in a globally peered vnet. Please see our documentation here for more details: https://docs.microsoft.com/azure/virtual-network/virtual-networks-faq#what-are-the-constraints-related-to-global-vnet-peering-and-load-balancers.

Our suggestion is to migrate your basic load balancer to a standard SKU load balancer where this is a supported scenario. Here are the instructions of how to do it: https://docs.microsoft.com/azure/load-balancer/upgrade-basic-standard  

Best regards,

---

### Step 3: Solution for All DIPs down during prior incident

### Support Engineer Solution

If all DIPs were down during the time of the incident, the load balancer frontend IP will not respond. It will also not respond to ping (this is always the case regardless of backend health). Customers sometimes think that their load balancer was "down" when in fact the issue is that all their backend pool members were probed down at the time so the load balancer would have no healthy pool member to send the traffic to. Use the DIP Availability Dashboard leveraged in the prior step to determine the reason the DIPs were probed down.

## Recommended Steps

Scroll down to Health Probe Status (Dip Availability): Aggregated by Frontend-IP-Address : Frontend-Port -> Backend-IP-Address : Backend-Port. The middle graph will show the failure count reason. If you see the failure reason as ProbeTimeout, ConnectionTerminated, HttpStatusCodeError, or HttpEndpointUnreachable, these are indications of customer backend application/VM configuration failures.

If you see ProbeTimeout or [HttpEndpointUnreachable](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/735012/How-to-Troubleshoot-probe-error-codes-for-HttpEndpointUnreachable), it is likely there was likely an issue with the customer's application at the time. This is even more likely if it is currently working and the customer reports making no changes.
 

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer connectivity issue on [insert date and time]. We have noticed that all members of the backend pool are detected as down by the load balancer probes. Please review any application logs and metrics you may have for more information.

To view metrics on your load balancer probe status, please browse to the load balancer object in the Azure Portal, click on the Metrics tab below Monitoring and select the Health Probe Status metric. We recommend using the Min aggregation and splitting on backend IP address and potentially port to see any changes in probe status over time. For more information, please see: https://docs.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview

Thank you,

---

### Step 4: Check customer application

### Support Engineer Solution

If you see HttpStatusCodeError, this is an indication of a customer application failure. Advise customer that they could not connect to their load balancer VIP because all VMs in their backend pool returned an invalid HTTP response and the customer should look at their application logs for additional information.

### Customer Solution

*Content type: MarkdownText*

Dear < Customer >,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reviewed diagnostics and configuration available to us and have determined that your connectivity issue is likely due all VMs in your backend pool returning an invalid HTTP response to the load balancer prober address. The next step is to look in your application logs for connections coming from the load balancer probe IP 168.63.129.16.

If you need additional support on this matter, please let us know.  

Best regards,

---

### Step 5: Escalate RCA request

### Support Engineer Solution

You have reached the end of this troubleshooter. If you still needed assistance, please engage your TA via [Teams resource engagement recommendations](https://aka.ms/ANPTeamsPostingGuidelines) to reach out to SME resources in the [Load Balancer Teams Channel](https://nam06.safelinks.protection.outlook.com/?url=https%3A%2F%2Fteams.microsoft.com%2Fl%2Fchannel%2F19%253ac5774cb5dd0649f9a68cc88872281084%2540thread.skype%2FLoad%252520Balancer%252520and%252520Public%252520IPs%252520(Public%252520IP%252520Prefix)%3FgroupId%3Dc3e00ac7-3f76-4350-ba3b-e335a6bbbe21%26tenantId%3D72f988bf-86f1-41af-91ab-2d7cd011db47&data=02%7C01%7CMario.Liu%40microsoft.com%7C4ec52986f7d243ddb41708d80c851f92%7C72f988bf86f141af91ab2d7cd011db47%7C1%7C0%7C637273113181617839&sdata=1BAjB1CPuT6iDgsMpgtZIPg65eRtk0COM10CSXp9Xto%3D&reserved=0)

If you find a solution, please use the frown system to provide feedback to improve this troubleshooter.

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 6: Solution for all DIPs down due to NSG block probe IP

### Support Engineer Solution

Inform the customer to alter their NSG to include an allow rule (with a lower number priority) for the 

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reviewed diagnostics and configuration available to us and have determined that your connectivity issue is likely due to a misconfiguration with the NSG applied to your backend VM. Please ensure that traffic from the IP address 168.63.129.16 is allowed inbound to your VM. This can be done by adding an inbound rule with higher priority (lower number) than your block rules to allow traffic from source tag AzureLoadBalancer to the probe port configured. Please see documentation https://docs.microsoft.com/azure/virtual-network/what-is-ip-address-168-63-129-16 and https://docs.microsoft.com/azure/virtual-network/service-tags-overview for more information.

If you need additional support on this matter, please let us know.  

Best regards,

---

### Step 7: Solution for public load balancer invalid routing

### Support Engineer Solution

The customer has invalid routing. Ask them to update their user defined route (RouteTargetNva/RouteTargetVpn) or stop advertising a default route.

### Customer Solution

*Content type: MarkdownText*

**If rule name starts with: RouteTargetNva**

Dear Customer,

Thank you for contacting us about your public load balancer backend pool connectivity issue. We have reviewed the logs and diagnostics available to us and we determined the connectivity issue you are experiencing may be the result of a user defined route to a network virtual appliance. To access your public load balancer from internet clients, it must not be on a Virtual Network subnet with a default route pointing to a network virtual appliance. We recommend you consult with your networking team to determine the appropriate next steps for your deployment and ensure it is consistent with any organizational policies you may have. For more information, see: https://docs.microsoft.com/azure/virtual-network/virtual-networks-udr-overview

Best regards,

**If rule name starts with: RouteTargetVpn**

Dear Customer,

Thank you for contacting us about your public load balancer backend pool connectivity issue. We have reviewed the logs and diagnostics available to us and we determined the connectivity issue you are experiencing may be the result of a user defined route or default route being advertised from on-premises. To access your public load balancer from internet clients, it must not be on a Virtual Network subnet that is subject to a default route back to on-premises. We recommend you consult with your networking team to determine the appropriate next steps for your deployment and ensure it is consistent with any organizational policies you may have. For more information, see: https://docs.microsoft.com/azure/virtual-network/virtual-networks-udr-overview

Best regards,

---

### Step 8: Solution for Floating IP Enabled

### Support Engineer Solution

Confirm with the customer that they intend to have floating IP enabled and insure they understand the implications of enabling it.

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reviewed the logs and diagnostics available to us and we determined the connectivity issue you are experiencing may be the result of specifying floating IP on your load balancing rule. Backend connectivity may not work if your VM is not configured to accept connections for the frontend IP address of your load balancing rule. Typically, this is done in conjunction with a clustering technology such as Windows Clustering or Kubernetes (K8s). You can also do this by configuring a loopback adapter in your OS. For more information, see [this documentation](https://docs.microsoft.com/azure/load-balancer/load-balancer-floating-ip).

Please validate that you have configured your clustering technology correctly or that you have a loopback adapter listening on your front-end IP address. If you do not have a clustering technology or loopback adapter configured, please reconfigure your load balancing rule and disable Floating IP.

Best regards,

---

### Step 9: End of public load balancer troubleshooter

### Support Engineer Solution

Set up DTM for the customer. Ask customer for traceroute from their source VM. Ask customer for a packet capture from both the source and destination backend pool members (all backend pool members) and upload the captures to DTM. Once you get this information, consult your TA if you are not able to determine if the inbound SYN from the client made it to a backend pool member and if the backend pool member responded to it.

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reached a point in the troubleshooting process where we need additional information to further diagnose the connectivity issue. Please perform a traceroute from an allowed source host to the VIP for this load balancer and copy/paste the output. Please gather a packet capture on the source and destination VM simultaneously while reproducing the issue and send both files to us. This will help us determine the appropriate next steps for this case.

Best regards,

---

### Step 10: This issue is outside the scope for this TSG

### Support Engineer Solution

Update the support topic to match the customer issue in ASC 'Edit and Run Again' and check for a related TSG.

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 11: Gather more information on globally peered Vnet

### Support Engineer Solution

Collect more information from the source VM and from the customer. Ask the customer to ensure they have continuous TCP pings running (Windows: psping, Linux: nping) if the load balancing rule is for the TCP protocol  or have continuous UDP attempts going until the resolution of the case. Ask the customer to collect packet captures. Create a DTM link for the customer. Ask the customer for concurrent packet captures from the source and destination VMs (all backend VMs) and upload the captures to DTM.

Once customer has confirmed continuous TCP pings/UDP traffic is flowing, browse to the source VM resource in ASC. Under Diagnostics, use Test Traffic and test from the source VM IP outbound to the load balancer IP and port. Ensure that the traffic is allowed, and the routing layer rule name starts with RouteTargetVnetPeering_VNET. If the routing rule name is RouteTargetNVA, ask customer to verify their NVA configuration. If the traffic is allowed, click "Result File Links" and save the Process Tuples File in the event the case needs to be escalated.

When you get the packet captures, check to determine if the source sent the TCP SYN packet and note the ephemeral port. Then check that one of the destinations got the inbound SYN from the client IP and ephemeral port previously noted. Check that the backend VM responded with a SYN/ACK. Lastly, check that the client VM received the SYN/ACK. If you need assistance, engage your TA via [Teams resource engagement recommendations](https://aka.ms/ANPTeamsPostingGuidelines) to reach out to SME resources in the [Load Balancer Teams Channel](https://nam06.safelinks.protection.outlook.com/?url=https%3A%2F%2Fteams.microsoft.com%2Fl%2Fchannel%2F19%253ac5774cb5dd0649f9a68cc88872281084%2540thread.skype%2FLoad%252520Balancer%252520and%252520Public%252520IPs%252520(Public%252520IP%252520Prefix)%3FgroupId%3Dc3e00ac7-3f76-4350-ba3b-e335a6bbbe21%26tenantId%3D72f988bf-86f1-41af-91ab-2d7cd011db47&data=02%7C01%7CMario.Liu%40microsoft.com%7C4ec52986f7d243ddb41708d80c851f92%7C72f988bf86f141af91ab2d7cd011db47%7C1%7C0%7C637273113181617839&sdata=1BAjB1CPuT6iDgsMpgtZIPg65eRtk0COM10CSXp9Xto%3D&reserved=0)

### Customer Solution

*Content type: MarkdownText*

** If load balancing rule is TCP **

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reached a point in the troubleshooting process where we need additional information to further diagnose the connectivity issue. 

Please start continuous TCP pings (Windows: `psping -t loadBalancerFrontendIp:Port`, Linux: `nping --tcp -p [Port] -c 0 [loadBalancerFrontendIp]`) **until the resolution of the case** to prevent any troubleshooting delays. PSPing is available for download from https://docs.microsoft.com/en-us/sysinternals/downloads/psping. For Linux, consult your distribution documentation for installing the nping utility.

Please gather packet captures from on the source VM and the VMs in your

*(Content truncated — refer to original GT for full details)*

### Step 12: Check customer application for connection rate changes

### Support Engineer Solution

Sudden changes in SYN/FIN rates indicate application issues. It could be that the backend instances of the customer application crashed and as a result caused the customer's clients to re-connect at around the same time. The next step is to look into the backend server logs and telemetry for additional information as to what may have caused the disconnections and/or re-connections.

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reviewed diagnostics and configuration available to us. We observed an increase in the rate of SYN/FIN packets observed on your backend VM instances. This typically indicates that something caused your clients to re-connect to the server. The next step is to look in your application logs and telemetry to determine if there is an indication of what may have happened.

If you need additional support on this matter, please let us know.  

Best regards,

---

### Step 13: Solution for all DIPs down due to probe timeout

### Support Engineer Solution

Help the customer validate that their application is running (netstat -anop), that a guest OS firewall is not blocking the load balancer probe IP, and that the customer's guest OS is properly responding to traffic from the load balancer probe IP 168.63.129.16.

If you have detected that probe down reason is HttpEndpointUnreachable, please use this Wiki: [https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/735012/How-to-Troubleshoot-probe-error-codes-for-HttpEndpointUnreachable](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/735012/How-to-Troubleshoot-probe-error-codes-for-HttpEndpointUnreachable)

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer connectivity issue. We have noticed that all members of the backend pool are detected as down by the load balancer probes. Please remedy this by ensuring:

* The network service is properly running on the backend Virtual Machines and is listening on the port specified by the probe configuration. For example on Windows, use the command to validate your application is listening on port 80:
 `netstat -ano | findstr LISTENING | findstr 80 `.
On Linux, use the command:
`netstat -ano | grep LISTEN | grep tcp | grep 80`
* The guest OS firewall is allowing traffic to the port from the load balancer probe source IP address 168.63.129.16 as well as any other source IP addresses you wish to allow. For more information on the load balancer probe source IP address, please see: https://docs.microsoft.com/en-us/azure/virtual-network/what-is-ip-address-168-63-129-16. On Windows, use wf.msc and on Linux, use iptables or the firewall management tool included with your particular distribution.
* For HTTP/HTTPS Probes, please make sure that backend Virtual Machines are responding with 200 OK.

To view metrics on your load balancer probe status, please browse to the load balancer object in the Azure Portal, click on the Metrics tab below Monitoring and select the Health Probe Status metric. We recommend using the Min aggregation and splitting on backend IP address and potentially port to see any changes in probe status over time. For more information, please see: https://docs.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview

Thank you,

---

### Step 14: Solution for customer VIP under DDoS Mitigation

### Support Engineer Solution

Communicate to the customer that their VIP was under DDoS mitigation at the time to protect their resources in addition to the Azure infrastructure. See the sample customer message.

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reviewed diagnostics and configuration available to us. We observed that at the time of your report of connectivity issues your VIP [VIP] was under DDoS attack mitigation to protect your backend pool as well as the Azure infrastructure.

If you would like DDoS metrics and alerts, mitigation reports, mitigation flow logs, and mitigation policies tuned for your application, please consider enrolling your Azure tenant in a Standard DDoS Protection plan if you have not already done so. For more information, see: https://docs.microsoft.com/en-us/azure/ddos-protection/ddos-protection-overview. Please note that this feature set incurs an additional monthly charge.

If you need additional support on this matter, please let us know.  

Best regards,

---

### Step 15: Solution for NSG blocking access from source IP

### Support Engineer Solution

Help customer update their NSG by configuring an allow rule to permit the traffic from the source IP address the customer specified.

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Thank you for contacting us about your load balancer connectivity issue. We have noticed that NSG rule < rule name > is blocking traffic. Please remedy this by adding a lower rule with a lower number rule priority allowing the traffic. You can test this using the Network Watcher IP Flow Verify tool in the Azure Portal.

For more information, see: https://docs.microsoft.com/azure/virtual-network/diagnose-network-traffic-filter-problem and https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview.

Thank you,

---

### Step 16: Check for changes in SYNFIN rates for backend container

### Guidance

Look at the VfpTcpMetricsDashboard for backend pool member. Look at the VfpTcpMetricsDashboard for backend pool member to see if there is a spike of TCP SYN or FIN packets at the time of the reported incident.

Such spikes in activity can indicate an application failure. If the application fails and restarts, clients will need to re-connect. When TCP based clients connect, they trigger SYN packets as part of the protocol's 3-way handshake. Look for a spike in inbound TcpSyn or TcpFin packets. If so, that points to what is likely a customer application issue.

## Recommended Steps
1. In ASC, browse to a member of the backend pool. In the VM's properties, make note of:
* Region
* Cluster
* NodeId
* ContainerId
2. Browse to URL: https://jarvis-west.dc.ad.msft.net/dashboard/VfpMDM/DatapathDashboards/VfpTcpMetricsDashboard
3. At the top where the parameters are, set the time to on hour before and after the time of the incident. For Account, specify VfpMdm[Region] where region is typically the first two letters of the cluster. VfpMdmSN for SN#PrdApp## clusters (like SN2PrdApp05) in US South Central for example. There are some exceptions however listed below:

Cluster Starts With | Vfp Account Parameter
--- | ---
MNZ | VfpMdmBL
MEL | VfpMdmML
CO | VfpMdmMWH
BZ | VfpMdmBN
AUH | VfpMdmAUHDXB
DXB | VfpMdmAUHDXB
DUB | VfpMdmDB
KW | VfpMdmKWTY
TY | VfpMdmKWTY
SIN | VfpMdmSG
DSM | VfpMdmDM

Then specify the cluster name, node Id, and container Id. Often times, it is easier to construct the URL off-line with the parameters pre-populated: `https://jarvis-west.dc.ad.msft.net/dashboard/VfpMDM/DatapathDashboards/VfpPortMetricsDashboard?overrides=[{"query":"//dataSources","key":"account","replacement":"*VFP Account*"},{"query":"//*[id='Cluster']","key":"value","replacement":"*Cluster Name*"},{"query":"//*[id='NodeId']","key":"value","replacement":"*Node Id*"},{"query":"//*[id='ContainerId']","key":"value","replacement":"*Container Id*"}]%20`

### Question

**Were there any changes in SYN/FIN rates at time of the incident?**

### Options

- **Yes** → Go to: *Check customer application for connection rate changes*
- **No** → Go to: *Check DDoS dashboard*

---

### Step 17: Clarify problem statement

### Guidance

Most customers are asking to help them understand why they are not currently getting responses to requests to their load balancer frontend IP or why they failed in the past. Often, customer's report that their load balancer is "down" but do not check to see if their application is/was healthy or is misconfigured.

## Recommended Steps

1. Review the customer verbatim to understand the customer's ask.
2. Locate the customer's load balancer in ASC. Determine from the verbatim where the customer is connecting from. This should be either a public IP address in the case of external facing load balancers or a VNet IP, resource URI, or on-premises IP for internal load balancers.  From the configuration data is visualized in ASC and what you have read from the customer verbatim, collect the following information to form a concise problem statement:

1. Client IP (source):
2. Load balanced frontend IP, port, and protocol (TCP or UDP - note: other protocols such as ICMP are not supported) client is connecting to (destination): 
3. Load balanced rule the customer configured for the traffic pattern: 
4. Probe configuration associated with the load balanced rule: 
5. Load balancer SKU (standard or basic): 
6. If intermittent/RCA request, date and time in UTC of the incident: 

### Question

**Is this case for troubleshooting an ongoing failure or for a root cause investigation or intermittent issue?**

### Options

- **Ongoing Incident** → Go to: *Check if one or more DIPs are healthy*
- **Root Cause Investigation or Intermittent issue** → Go to: *Check if there was a healthy backend pool member at the time*

---

### Step 18: Check DDoS dashboard

### Guidance

The DDoS system monitors all Microsoft IP space at all network edge sites to prevent attack traffic from saturating the network internally and to protect the load balancer inbound MUX rings from bad actors on the internet. If inbound traffic rates exceed attack thresholds, the DDoS system filters the traffic. By default, all customers are enrolled in DDoS protection basic. Customers can opt into DDoS Protection Standard for an additional charge. DDoS Protection standard offers customers the ability to tune mitigation policies for their application, metrics and alerts, and mitigation reports and flow logs, among other features.

## Recommended Steps for checking if VIP was under mitigation

1. Load the DDoS mitigation dashboard here: https://jarvis-west.dc.ad.msft.net/dashboard/CNS/DDoSSupport/IsIPUnderMitigation
2. In the gray override bar at the top, adjust the time to the time of the incident. Keep in time zones in mind. It is recommended to set Jarvis to use UTC (set this by clicking on the person icon in the upper right-hand corner of Jarvis) and convert the customer's incident time to UTC. Enter the customer's VIP in the DestinationVIP box.

If you do not see the customer's VIP or no data appears, the customer's VIP was not under mitigation and therefore was not under attack.

## Recommended Documents
https://docs.microsoft.com/en-us/azure/ddos-protection/ddos-protection-overview

### Question

**Was the customer's VIP under mitigation?**

### Options

- **Yes** → Go to: *Solution for customer VIP under DDoS Mitigation*
- **No** → Go to: *Escalate RCA request*

---

### Step 19: Check the probe down reason

### Guidance

If you see that VIP availability is down due to NoFowardingDip, scroll down to Health Probe Status (Dip Availability): Aggregated by Frontend-IP-Address : Frontend-Port -> Backend-IP-Address : Backend-Port. The middle graph will show the failure count reason. If you see the failure reason as ProbeTimeout, HttpEndpointUnreachable, or ConnectionTerminated choose timeout.

### Question

**What is the failure reason?**

### Options

- **Timeout** → Go to: *Check if load balancer probe IP is blocked by NSG*
- **Http Status Code Error** → Go to: *Check customer application*

---

### Step 20: Check if one or more DIPs are healthy

### Guidance

Often customers cannot access their load balancer via the load balanced IP because all backend pool members (DIP) are down per the configured probe.

## Recommended Steps
### If Standard SKU
1. In ASC, browse to the Diagnostics tab of the relevant load balancer and scroll down to "DIP Availability". Click on the link for the relevant frontend IP and port. This will open a new tab with the DipAvailability_HealthProbeStatus Dashboard with the parameters filled out. If you are looking to root cause a prior issue, adjust the time parameter of the dashboard. Be sure to note time zones to ensure you are look at the right point in time.
2. On the top set of charts under "Data Path Availability (VipAvailability)," look to see if there are any dips in VipAvailability and if so, see if there are jumps in FailureCount. If you see an increase in NoFowardingDip, the customer is unable to connect to their load balancer because all members of the backend pool were unhealthy."

### If Basic SKU
1. ASC does not show links to DIP Availability for basic SKU, however the data is there. Go to the [SLB DIP Availability](https://jarvis-west.dc.ad.msft.net/dashboard/slbv2prod/AzureMonitor/DipAvailability_HealthProbeStatus) page.
2. Update the time to be current (if on-going) or the relevant time in the past.
3. Update the Slbv2MDMAccount setting to be slbv2< region name > so slbv2westcentralus for West Central US for example. 
4. Update the LoadBalancerArmId value to be the value of "Resource Guid" in the Properties page in ASC.
5. On the top set of charts under "Data Path Availability (VipAvailability)," look to see if there are any dips in VipAvailability and if so, see if there are jumps in FailureCount. If you see an increase in NoFowardingDip, the customer is unable to connect to their load balancer because all members of the backend pool were unhealthy."

### Question

**Are all DIPs currently down?**

### Options

- **Yes** → Go to: *Check the probe down reason*
- **No** → Go to: *Check if an NSG is blocking the customer source IP*

---

### Step 21: Check if load balancer is internal or external

### Content

Next, determine if the load balancer is internal or external facing. This is a property of the load balancer in ASC. It should also be apparent based on the client IP address, a public for external or a private IP (typically) for internal.

---

### Step 22: Check if an NSG is blocking the customer source IP

### Guidance

## Recommended Steps

To validate if a NSG is blocking inbound traffic, use ASC and click on the backend pool member NIC and from there, click on the attached VM link. Click on the Diagnostics tab and then scroll down to Test Traffic. Modify the following parameters:

* **Traffic Direction:** for external load balancers, select InternetIn. For internal load balancers, select TunnelOrLocalIn.
* **Source IP:** Source IP customer is attempting to connect from
* **Destination Port:** The load balanced port
* **Transport Protocol:** The load balanced protocol. This should be TCP or UDP only. Load balancers do not support ICMP and other protocols.

Click Run. Under result, click "Stateful Test (NSG Layer)" and ensure the test result is: Traffic: ALLOWED. If not, advise customer to alter their NSG and create a rule with a higher priority (lower number) to allow the traffic.

### Question

**Is an NSG blocking the source IP?**

### Options

- **Yes** → Go to: *Solution for NSG blocking access from source IP*
- **No** → Go to: *Check if load balance rule has floating IP enabled*

---

### Step 23: Check if outbound next hop type is internet

### Guidance

## Determine outbound next hop type

The next hop type for public load balancers must be internet. If the customer overrides this via a UDR or a default route being advertised via ExpressRoute or VPN, external load balancers will not work for the VM's subnet as return traffic will be sent to the customer's on-premises or a custom NVA. On-premises and NVAs (behind different load balancers) will not be able to source the return traffic from the load balancer public IP as it the IP space owned and advertised to the internet by the Microsoft, not the customer's organization.

## Recommended Steps

* Browse to a backend pool member VM in ASC
* Click the Diagnostics tab and scroll down to Test Traffic
* Specify the following parameters:
* **Traffic Direction:** Out
* **Source IP:** Source IP of the backend pool member IP configuration specified in the load balancer rule name
* **Destination IP:** 1.1.1.1
* **Destination Port:** 443
* **Transport Protocol:** The load balanced protocol. This should be TCP or UDP only.

The port is not super import as we are checking the routing layer and not the NSG layer. Click Run. In the results, click on Stateless Test (Routing Layer). Ensure that the rule name is RouteTargetInternet< Number >.  It  will usually be RouteTargetInternet0.

### Question

**Is the outbound next hop type internet?**

### Options

- **Yes** → Go to: *End of public load balancer troubleshooter*
- **No** → Go to: *Solution for public load balancer invalid routing*

---

### Step 24: Check internal load balancer SKU

### Content

## Recommended Steps

Use ASC to browse to the load balancer object. In the properties pane, look to see if the load balancer SKU is Basic or Standard.

---

### Step 25: Check if load balancer probe IP is blocked by NSG

### Guidance

# How load balancer health probes work
The SLB Host Plugin running on all Azure nodes sends the load balancer probes to all VMs that are running on it. Once the probe traffic gets to the guest OS, it appears to be sourced from the IP address 168.63.129.16. NSGs have a default rule to allow this communication (rule priority 65001, rule name AllowAzureLoadBalancerInBound). If the customer has a rule with a lower priority value (meaning it gets evaluated first), the probe traffic will be blocked by the NSG and the health probe will appear down. Check for this condition using the steps below. The probe configuration is up to the customer. It can be a TCP ping or an HTTP GET request. The VM will be probed down if the TCP ping times out or if the HTTP response code is a non-200 series.

To remedy this, the customer must add an inbound rule with higher priority (lower number) to allow traffic from source tag AzureLoadBalancer.

## Recommended Steps

* Using Resource Explorer in Azure Support Center, review the probe configuration for the load balancing rule in the load balancer properties.
* Navigate to a VM in the backend pool of the load balancing rule in question (this is in the load balancer resource)
* In the VM resource, go to the Diagnostics tab and scroll down to the TestTraffic tool
* Run TestTraffic with the following parameters:
Direction: InternetIn
Source IP: 168.63.129.16
Source Port: 2345
Destination IP: <VM IP>
Destination port: <Port customer configured for their probe or 80/443 for HTTP/HTTPS>
Protocol: TCP

In the result, browse to "Stateful Test (NSG Layer)" to see if the traffic is allowed or blocked.

### For more public documentation, reference these Microsoft Docs:
https://docs.microsoft.com/azure/virtual-network/what-is-ip-address-168-63-129-16
https://docs.microsoft.com/azure/virtual-network/service-tags-overview"

### Question

**Is an inbound NSG blocking load balancer probe traffic?**

### Options

- **Yes** → Go to: *Solution for all DIPs down due to NSG block probe IP*
- **No** → Go to: *Solution for all DIPs down due to probe timeout*

---

### Step 26: Check if there was a healthy backend pool member at the time

### Guidance

If the load balancer heath probe is detected down on all backend pool members, the load balancer will not have any backend pool member to forward the request to. As a result, the load balancer may appear to the customer to be unresponsive. This is especially true if the backend pool members respond to ping or management protocols (but not the application the load balancer probe is configured for). 

## Recommended Steps
### If Standard SKU
1. In ASC, browse to the Diagnostics tab of the relevant load balancer and scroll down to "DIP Availability". Click on the link for the relevant frontend IP and port. This will open a new tab with the DipAvailability_HealthProbeStatus Dashboard with the parameters filled out. Adjust the time parameter of the dashboard. Be sure to note time zones to ensure you are look at the right point in time. 
2. On the top set of charts under "Data Path Availability (VipAvailability)", look to see if there are any dips in VipAvailability and if so, see if there are jumps in FailureCount. If you see an increase in NoFowardingDip, the customer is unable to connect to their load balancer because all members of the backend pool were unhealthy.

### If Basic SKU
1. ASC does not show links to DIP Availability for basic SKU, however the data is there. Go to the [SLB DIP Availability](https://jarvis-west.dc.ad.msft.net/dashboard/slbv2prod/AzureMonitor/DipAvailability_HealthProbeStatus) page.
2. Update the time to be the relevant time in the past.
3. Update the Slbv2MDMAccount setting to be slbv2< region name > so slbv2westcentralus for West Central US for example. 
4. Update the LoadBalancerArmId value to be the value of "Resource Guid" in the Properties page in ASC.
5. On the top set of charts under "Data Path Availability (VipAvailability)," look to see if there are any dips in VipAvailability and if so, see if there are jumps in FailureCount. If you see an increase in NoFowardingDip, the customer is unable to connect to their load balancer because all members of the backend pool were unhealthy."

### Question

**Was there a drop in VIP availability and NoForwardingDip metric greater than 0 at the time of the incident?**

### Options

- **Yes** → Go to: *Solution for All DIPs down during prior incident*
- **No drop in VIP Availability** → Go to: *Check VIP datapath availability*

---

### Step 27: Check VIP datapath availability

### Guidance

If there are no DIP health failures, check the VIP data path availability. This data is generated by the VIP prober which is part of the SLB infrastructure.

## Recommended Steps
1. In ASC, browse to the Diagnostics tab of the relevant load balancer and scroll down to "VIP Availability". Click on the link for the relevant frontend IP and port. This will open a new tab with the VipAvailability_DataPathAvailability with the parameters filled out. Adjust the time parameter of the dashboard. Be sure to note time zones to ensure you are look at the right point in time. 
2. On the top set of charts under "Data Path Availability (VipAvailability)," look to see if there are any dips in VipAvailability and if so, see if there are any increases in FailureCount.

### Question

**Is data path availability 100% at the time of the incident?**

### Options

- **Yes** → Go to: *Check for changes in SYNFIN rates for backend container*
- **No** → Go to: *Check DDoS dashboard*

---

### Step 28: Check if load balance rule has floating IP enabled

### Content

## About Floating IP
Customers can specify floating IP in their load balancer rule configuration. This cases the load balancer to not DNAT their front-end IP address to the Virtual Machine DIP. Frequently, customers enable this when using clustering solutions such as SQL AlwaysOn and Kubernetes (K8s). These technologies configure the guest OS to accept communications to the front-end IP address in addition to the VM DIP. If the customer does not configure their guest OS to accept connections to the front-end IP address, connections will fail. 

Sometimes customers incorrectly enable this option. If you notice that the customer has the option enabled check with the customer to ensure that what they configured is what they intended. Have them validate they have a clustering technology properly configured or a loopback adapter configured with the front-end IP. If the customer does not know what you are talking about, chances are they incorrectly configured floating IP and they should disable it.

## Recommended Steps

1. Find the Load Balancer in Resource Explorer in Azure Support Center
2. Find the load balancing rules used for the customer solution and expand
3. Check the property "Enable Floating IP"

For more information on Floating IPs check this Microsoft Docs Resource below

### Recommended Documents

* [backend port reuse by using Floating IP](https://docs.microsoft.com/azure/load-balancer/load-balancer-multivip-overview#rule-type-2-backend-port-reuse-by-using-floating-ip)

---

### Step 29: No Load Balancing or NAT rule found

### Support Engineer Solution

# No load balancer rule configured

There were no rules found in the load balancer that can handle the traffic with the parameters provided. 

Re-run this solution and validate if you provided the correct parameters. Make sure there are no typos either on the parameters provided or the rule configuration.

If you keep getting this issue, review your load balancer configuration and validate that you have a rule to process the traffic.

[Manage rules for Azure Load Balancer using the Azure portal](https://learn.microsoft.com/en-us/azure/load-balancer/manage-rules-how-to)

### Customer Solution

*Content type: MarkdownText*

N/A

---
