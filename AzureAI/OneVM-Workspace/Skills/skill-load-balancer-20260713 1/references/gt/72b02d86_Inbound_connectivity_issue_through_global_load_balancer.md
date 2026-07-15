# Inbound connectivity issue through global load balancer

> **Product:** Load Balancer  
> **Solution ID:** 72b02d86-8643-443f-b20e-7728da271423  
> **Trigger words:** balancer, connectivity, connectivity issue, global, inbound, issue, load balancer, through

---

## Overview

This guide provides step-by-step troubleshooting for **Inbound connectivity issue through global load balancer** under **Load Balancer**.
 The original guided troubleshooter contains 18 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Scoping ⭐ (First Step)

### Guidance

This guided troubleshooter is specific to Azure global Load Balancer.

To verify the tier of the load balancer, simply look at the Properties section in ASC for the tier field.

### Question

**Are you facing inbound connectivity issues with a global load balancer?**

### Options

- **Yes** → Go to: *Global Tier or not*
- **No, Its regional inbound issue** → Go to: *454c4292-c3c0-4c42-9ed9-a8e4428b0d21*
- **No** → Go to: *Out of scope*

---

### Step 2: Out of scope

### Support Engineer Solution

Please add another solution set on the ASC to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results.

### Customer Solution

*Content type: MarkdownText*

n/a

---

### Step 3: Global Tier or not

### Content

To verify the tier of the load balancer, simply look at the Properties section in ASC for the tier field.

---

### Step 4: Global Probe Up or Down

### Guidance

Azure global Load Balancer utilizes the health of the backend regional load balancers when deciding where to distribute traffic to. Health checks by cross-region load balancer are done automatically every 5 seconds, given that health probes are set up on your regional load balancer.

**Recommended Steps**

To check health probe status of the global load balancer:

- In ASC, browse to the Diagnostics tab of the relevant load balancer and scroll down to "DIP Availability". Click on the link for the relevant frontend IP and port. This will open a new tab with the DipAvailability_HealthProbeStatus Dashboard with the parameters filled out. If you are looking to root cause a prior issue, adjust the time parameter of the dashboard. Be sure to note time zones to ensure you are look at the right point in time.

- On the top set of charts under "Data Path Availability (VipAvailability)," look to see if there are jumps in FailureCount. If you see an increase in NoFowardingDip, the customer is unable to connect to their load balancer because all members of the backend pool were unhealthy.

### Question

**Is the DIP Availability status indicating that the backend is healthy?**

### Options

- **Yes** → Go to: *VIP availability*
- **No** → Go to: *Regional LB probe UP or Down*

---

### Step 5: Regional LB probe UP or Down

### Guidance

The health status of a global load balancer can be marked as down for various reasons. One possible cause is when all the regional load balancers in its backend pool are unhealthy due to issues with their backend instances. As a result, the global load balancer's health status will also be marked as down.

To confirm:

- Begin by checking the backend pool of your global load balancer and identifying the regional load balancers associated with it.

- In ASC, go to the Diagnostics tab of the regional load balancer.

- Scroll down to "DIP Availability" and click the link for the relevant frontend IP and port.

- A new tab will open with the DipAvailability_HealthProbeStatus Dashboard filled out with parameters.

- Adjust the time parameter of the dashboard if you are trying to find the root cause of a prior issue, ensuring the correct time zones are noted.

- On the top charts under "Data Path Availability (VipAvailability)", check for any jumps in FailureCount.

- If there is an increase in NoFowardingDip, it means the customer is unable to connect to their load balancer because all members of the backend pool were unhealthy.

### Question

**For your regional load balancer(s), are the backend instances healthy and responding to health probes?**

### Options

- **Yes** → Go to: *Incorrect Rule Settings*
- **No** → Go to: *Addressing Probe Failures*

---

### Step 6: Incorrect Rule Settings

### Support Engineer Solution

Global load balancer's health status may be reported as down even when the regional load balancer's health probe status is up if there's a misconfiguration in the load balancing rule. Ensure that the **backend port** of your load balancing rule on the **global load balancer** matches the **frontend port** of the load balancing rule or inbound NAT rule on the **regional standard load balancer**.

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

I wanted to bring to your attention an important detail regarding the global load balancer's health status. It may be reported as down even when the regional load balancer's health probe status is up, which can occur due to a misconfiguration in the load balancing rule.

Please ensure that the backend port of your load balancing rule on the global load balancer matches the frontend port of the load balancing rule or inbound NAT rule on the regional standard load balancer.

Best regards, 

---

### Step 7: Addressing Probe Failures

### Guidance

When VIP availability drops because of NoFowardingDip, go to Health Probe Status (Dip Availability). Check the section Aggregated by Frontend-IP-Address : Frontend-Port -> Backend-IP-Address : Backend-Port. The middle graph will show the reason for the failure. If it indicates ProbeTimeout, HttpEndpointUnreachable, or ConnectionTerminated, select timeout error.

### Question

**What is the failure reason ?**

### Options

- **Timeout error** → Go to: *NSG blocking LB probe check*
- **Http status code error** → Go to: *Http error solution*

---

### Step 8: Addressing Health Probe with Application Responses

### Support Engineer Solution

In order for load balancer health probes to succeed, the IP address 168.63.129.16 which is also denoted by the AzureLoadBalancer service tag must be allowed through all network security group rules.

If network security group rule are configured correctly to allow health probe, but connectivity issues still exist, we recommend that you check whether your application is responding to the configured health probe (protocol, port, and path) within the configured interval.

To do so:

- On Windows, use this command: `netstat -ano | findstr LISTENING | findstr 80`.

- On Linux, use this command: `netstat -ano | grep LISTEN | grep tcp | grep 80`.

Make sure that the operating system firewall is allowing the health probe port. On Windows use `wf.msc`, and on Linux use `iptables`.

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

To ensure the success of load balancer health probes, the IP address 168.63.129.16 (denoted by the AzureLoadBalancer service tag) must be allowed through all network security group rules.

If network security group rules are correctly configured to allow the health probe but connectivity issues still persist, we recommend checking whether your application is responding to the configured health probe (protocol, port, and path) within the specified interval.

To do this:

On Windows, use the command: netstat -ano | findstr LISTENING | findstr 80

On Linux, use the command: netstat -ano | grep LISTEN | grep tcp | grep 80

Additionally, ensure that the operating system firewall is allowing the health probe port. On Windows, use wf.msc, and on Linux, use iptables.

Best regards,

---

### Step 9: NSG blocking LB probe check

### Guidance

The SLB Host Plugin running on all Azure nodes sends the load balancer probes to all VMs that are running on it. Once the probe traffic gets to the guest OS, it appears to be sourced from the IP address 168.63.129.16. NSGs have a default rule to allow this communication (rule priority 65001, rule name AllowAzureLoadBalancerInBound). If the customer has a rule with a lower priority value (meaning it gets evaluated first), the probe traffic will be blocked by the NSG and the health probe will appear down. Check for this condition using the steps below. The probe configuration is up to the customer. It can be a TCP ping or an HTTP GET request. The VM will be probed down if the TCP ping times out or if the HTTP response code is a non-200 series.

To remedy this, the customer must add an inbound rule with higher priority (lower number) to allow traffic from source tag AzureLoadBalancer.

**Recommended Steps**

- On Azure Support Center, review the probe configuration for the load balancing rule in the load balancer properties.

- Navigate to a VM in the backend pool of the load balancing rule in question (this is in the load balancer resource)

- In the VM resource, go to the Diagnostics tab and scroll down to the TestTraffic tool

- Run TestTraffic with the following parameters: Direction: InternetIn Source IP: 168.63.129.16 Source Port: 2345 Destination IP: Destination port: <Port customer configured for their probe or 80/443 for HTTP/HTTPS> Protocol: TCP

In the result, browse to "Stateful Test (NSG Layer)" to see if the traffic is allowed or blocked.

**For additional public documentation, refer to these Microsoft Docs:** 

https://docs.microsoft.com/azure/virtual-network/what-is-ip-address-168-63-129-16 https://docs.microsoft.com/azure/virtual-network/service-tags-overview"

### Question

**Is an inbound NSG blocking load balancer probe traffic?**

### Options

- **Yes** → Go to: *Solution for all DIPs down due to NSG block probe IP*
- **No** → Go to: *Addressing Health Probe with Application Responses*

---

### Step 10: Solution for all DIPs down due to NSG block probe IP

### Support Engineer Solution

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

To resolve this issue, please add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag.

For more information, See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

Best regards,

---

### Step 11: Http error solution

### Support Engineer Solution

If you see HttpStatusCodeError, this is an indication of a customer application failure. Advise customer that they could not connect to their load balancer VIP because all VMs in your regional load balancer backend pool returning an invalid HTTP response and the customer should look at their application logs for additional information.

### Customer Solution

*Content type: MarkdownText*

Dear < Customer >,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reviewed diagnostics and configuration available to us and have determined that your connectivity issue is likely due all VMs in your regional load balancer backend pool returning an invalid HTTP response to the load balancer prober address. The next step is to look in your application logs for connections coming from the load balancer probe IP 168.63.129.16.

If you need additional support on this matter, please let us know.

Best regards,

---

### Step 12: VIP availability

### Guidance

To check the VIP Availability status of the global load balancer:

In ASC, browse to the Diagnostics tab of the relevant load balancer and scroll down to "VIP Availability". Click on the link for the relevant frontend IP and port. This will open a new tab with the VipAvailability_DataPathAvailability Dashboard with the parameters filled out. If you are looking to root cause a prior issue, adjust the time parameter of the dashboard. Be sure to note time zones to ensure you are look at the right point in time.

### Question

**Is the VIP Availability metric reporting 100%?**

### Options

- **Yes** → Go to: *Global has floating ip*
- **No** → Go to: *Platform Issue*

---

### Step 13: Platform Issue

### Support Engineer Solution

Check the corresponding reason you see under the Failure Reasons count graph, the following information will help you understand what exact issue was the customer facing:

**Success:**	The ping was sent out, routed to a host, bounced off VFP, and successfully returned

**NoForwardingDip:**	All Dips behind this endpoint are probed down. This failure is usually caused by customer side configuration.

**Unreachable NonPlatform:** False	The ping was sent out but didn't return as expected before the timeout. This is a platform failure, often this is caused by vfp, unhealthy nodes/T0-2s.

**Unreachable NonPlatform:** True	The ping was sent out but didn't return as expected before the timeout. This is a non-platform failure and caused by customer configuration.

**NoEndpoint:**	The mux does not have this endpoint (vip+port) configured in the goal state. This is platform failure.

**NoVipGoalState:**	The mux does not have this vip configured in the goal state at all. This is platform failure.

If you're unable to diagnose the issue, please post your case in Ava, including all the troubleshooting steps you've taken. A TA will then review it to determine if an ICM is necessary.

### Customer Solution

*Content type: MarkdownText*

n/a

---

### Step 14: Global has floating ip

### Content

Check the global load balancer rule to see if the floating IP option is enabled or disabled.

- **Floating IP enabled:** Azure changes the IP address mapping to the frontend IP address of the **global** load balancer.

- **Floating IP disabled:**	Azure exposes the VM instance's IP address.

---

### Step 15: No Load balancing rule found

### Support Engineer Solution

No load balancer rule configured.

There were no rules found in the load balancer that can handle the traffic with the parameters provided. 

Rerun this solution and verify that you provided the correct parameters.

If you continue experiencing this issue, review your load balancer configuration and verify that you have a rule to process the traffic.

[Manage rules for Azure Load Balancer using the Azure portal](https://learn.microsoft.com/azure/load-balancer/manage-rules-how-to)

### Customer Solution

*Content type: MarkdownText*

n/a

---

### Step 16: Resolving NSG and UDR Issues

### Support Engineer Solution

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

Standard Load Balancer is secure-by-default, hence it requires an explicit NSG rule allowing traffic from original client IP's. More information at: [Load Balancer overview](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-overview#securebydefault)

**Resolution:** Confirm there is a NSG in the backend VM Subnet or NIC that explicitly allows traffic from the Cient IP. 

Remedy this by adding a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP Flow Verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in Azure Portal.

**Cause - UDR Misconfiguration**

**Resolution:** 

Confirm if the effective routes of the backend network interface have the right route for Source Client IP:

1. For Internet users, please check if the next hop is internet, otherwise you need to confirm there is no asymmetric routing and firewalls in between are allowing the traffic.

2. For Azure users, please check if the next hop is the correct one and there is no asymmetric routing as well.

### Customer Solution

*Content type: MarkdownText*

n/a

---

### Step 17: Global up floating ip config

### Guidance

We have identified that your load lalancing or inbound NAT rule for this traffic has floating IP setting enabled.

 

Backend connectivity may not work if your VM is not configured to accept connections for the frontend IP address of your load balancing rule. Typically, this is done in conjunction with a clustering technology such as Windows clustering or Kubernetes. You can also do this by configuring a loopback interface in your operating system. For more information, see [Azure Load Balancer floating IP configuration](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#floating-ip-guest-os-configuration).

Validate that you've configured your clustering technology correctly or that you have a loopback interface listening on your frontend IP address. If you do not have a clustering technology or loopback interface configured, reconfigure your load balancing rule and disable floating IP.

Configuration instructions:

- [Windows:](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#windows-server)

- [Linux Ubuntu:](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#ubuntu)

### Question

**Have the loopback interfaces been configured to all backend instances?**

### Options

- **Yes** → Go to: *Resolving NSG and UDR Issues*
- **No** → Go to: *Floating IP Misconfiguration*

---

### Step 18: Floating IP Misconfiguration

### Support Engineer Solution

**Issue:** Backend is not configured correctly for the Floating IP feature.

**Resolution:** Configure the Guest OS for the virtual machine to receive all traffic bound for the frontend IP and port of the **global load balancer**. Configuring the VM requires:

- Adding a loopback network interface

- Configuring the loopback with the frontend IP address of the load balancer

- Ensuring the system can send/receive packets on interfaces that don't have the IP address assigned to that interface.Windows systems require setting interfaces to use the "weak host" model. For Linux systems, this model is normally used by default.

- Configuring the host firewall to allow traffic on the frontend IP port.

Steps for [Windows:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#windows-server)

Steps for [Linux Ubuntu:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#ubuntu)

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

**Issue:** Backend is not configured correctly for the Floating IP feature.

**Resolution:** Configure the Guest OS for the virtual machine to receive all traffic bound for the frontend IP and port of the **global load balancer**. Configuring the VM requires:

- Adding a loopback network interface

- Configuring the loopback with the frontend IP address of the load balancer

- Ensuring the system can send/receive packets on interfaces that don't have the IP address assigned to that interface.Windows systems require setting interfaces to use the "weak host" model. For Linux systems, this model is normally used by default.

- Configuring the host firewall to allow traffic on the frontend IP port.

Steps for [Windows:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#windows-server)

Steps for [Linux Ubuntu:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#ubuntu)

Best regards, 

---
