# Inbound connectivity issue through global load balancer

> **Product:** Load Balancer  
> **Solution ID:** ccaeb9da-acc8-408f-abe1-afbfabd72f98  
> **Trigger words:** balancer, connectivity, connectivity issue, global, inbound, issue, load balancer, through

---

## Overview

This guide provides step-by-step troubleshooting for **Inbound connectivity issue through global load balancer** under **Load Balancer**.
 The original guided troubleshooter contains 17 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Scoping ⭐ (First Step)

### Guidance

This guided troubleshooter is specific to Azure global Load Balancer.

Determine whether this is a global or regional load balancer:

1. Open the load balancer resource in the Azure portal.

2. Check the **Overview** page.

### Question

**Are you facing inbound connectivity issues with a global load balancer?**

### Options

- **Yes** → Go to: *Global Tier or not*
- **No, Its regional inbound issue** → Go to: *e3c6812c-4c20-4903-b542-08a19a17aa49*
- **No** → Go to: *Out of TSG scope*

---

### Step 2: Out of TSG scope

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

**Note:**

If your issue is not related to inbound connectivity through Azure global Load Balancer, go to the **Support + Troubleshooting** option in the **Help** section on Azure portal to look for new insights and troubleshooters.

---

### Step 3: Global Tier or not

### Content

Determine whether this is a global or regional load balancer:

1. Open the load balancer resource in the Azure portal.

2. Check the **Overview** page.

---

### Step 4: Global Probe Up or Down

### Guidance

Azure global Load Balancer utilizes the health of the backend regional load balancers when deciding where to distribute traffic to. Health checks by cross-region load balancer are done automatically every 5 seconds, given that health probes are set up on your regional load balancer.

To check health probe status of the global load balancer:

- In the Azure portal, on the **load balancer** page, select the **Metrics** tab.

- Select the **Health Probe Status** metric.

- Select **Avg** for the aggregation type.

- Apply splitting by **Backend IP Address**.

See more about [health probe monitoring](https://learn.microsoft.com/azure/load-balancer/load-balancer-standard-diagnostics#are-the-backend-instances-for-my-load-balancer-responding-to-probes).

### Question

**Is the health probe status indicating that the backend is healthy?**

### Options

- **Yes** → Go to: *Global Datapath availability*
- **No** → Go to: *Regional LB probe UP or Down*

---

### Step 5: Regional LB probe UP or Down

### Guidance

A global load balancer's health status metric can be down for several reasons. One potential cause is when all regional load balancers in the backend pool of the global load balancer are unhealthy due to their backend instances. This will result in the global load balancer's health status to also be marked as down. 

To confirm:

- Begin by checking the backend pool of your global load balancer and identifying the regional load balancers associated with it.

- In the Azure portal, on the **regional load balancer** page, select the **Metrics** tab.

- Select the **Health Probe Status** metric.

- Select **Avg** for the aggregation type.

- Apply splitting by **Backend IP Address**.

See more about [health probe monitoring](https://learn.microsoft.com/azure/load-balancer/load-balancer-standard-diagnostics#are-the-backend-instances-for-my-load-balancer-responding-to-probes).

### Question

**For your regional load balancer(s), are the backend instances healthy and responding to health probes?**

### Options

- **Yes** → Go to: *Incorrect Rule Settings*
- **No** → Go to: *Addressing Probe Failures*

---

### Step 6: Incorrect Rule Settings

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

Global load balancer's health status may be reported as down even when the regional load balancer's health probe status is up if there's a misconfiguration in the load balancing rule. Ensure that the **backend port** of your load balancing rule on the **global load balancer** matches the **frontend port** of the load balancing rule or inbound NAT rule on the **regional standard load balancer**.

---

### Step 7: Addressing Probe Failures

### Guidance

For the load balancer's health probe to mark up your instance, you must allow the IP address 168.63.129.16 in any Azure network security groups and local firewall policies. The AzureLoadBalancer service tag identifies this source IP address in your network security groups and permits health probe traffic by default. 

Review the Network Security Group (NSG) settings applied at the subnet or interface level for the regional load balancer's backend pool and confirm that they are correctly configured.

To learn more, see [What is IP address 168.63.129.16?](https://learn.microsoft.com/azure/virtual-network/what-is-ip-address-168-63-129-16)

### Question

**Is the network security group for the backend pool configured appropriately to allow the load balancer's health probe IP?**

### Options

- **Yes** → Go to: *Addressing Health Probe with Application Responses*
- **No** → Go to: *Fixing NSG Misconfiguration for down health Probe*

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

In order for load balancer health probes to succeed, the IP address 168.63.129.16 which is also denoted by the AzureLoadBalancer service tag must be allowed through all network security group rules.

If network security group rule are configured correctly to allow health probe, but connectivity issues still exist, we recommend that you check whether your application is responding to the configured health probe (protocol, port, and path) within the configured interval.

To do so:

- On Windows, use this command: `netstat -ano | findstr LISTENING | findstr 80`.

- On Linux, use this command: `netstat -ano | grep LISTEN | grep tcp | grep 80`.

Make sure that the operating system firewall is allowing the health probe port. On Windows use `wf.msc`, and on Linux use `iptables`.

---

### Step 9: Fixing NSG Misconfiguration for down health Probe

### Support Engineer Solution

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

### Customer Solution

*Content type: MarkdownText*

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

---

### Step 10: Global Datapath availability

### Guidance

- In the Azure portal, on the **load balancer** page, select the **Metrics** tab.

- Select the **Data path availability** metric.

- Select **Avg** for the aggregation type.

### Question

**Is the global load balancer's Data Path Availability metric reporting 100%?**

### Options

- **Yes** → Go to: *Global has floating ip*
- **No** → Go to: *Platform Issue*

---

### Step 11: Platform Issue

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

 Based on the information you've provided, it appears that the issue may be related to the platform itself. To ensure a thorough investigation and timely resolution, I kindly recommend that you open a support ticket with our technical support team.

---

### Step 12: Global has floating ip

### Content

Check the global load balancer rule to see if the floating IP option is enabled or disabled.

- **Floating IP enabled:** Azure changes the IP address mapping to the frontend IP address of the **global** load balancer.

- **Floating IP disabled:**	Azure exposes the VM instance's IP address.

---

### Step 13: No Load Balancing Rule

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

No load balancer rule configured.

There were no rules found in the load balancer that can handle the traffic with the parameters provided. 

Rerun this solution and verify that you provided the correct parameters.

If you continue experiencing this issue, review your load balancer configuration and verify that you have a rule to process the traffic.

[Manage rules for Azure Load Balancer using the Azure portal](https://learn.microsoft.com/azure/load-balancer/manage-rules-how-to)

---

### Step 14: Resolving NSG and UDR Issues

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

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

**Note:** If this doesn't help, open a service request to help with resolving your issue.

---

### Step 15: Global up floating ip config

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

- **Yes** → Go to: *NSG and UDR solution*
- **No** → Go to: *Floating IP Misconfiguration*

---

### Step 16: NSG and UDR solution

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

Standard Load Balancer is secure-by-default, hence it requires an explicit NSG rule allowing traffic from original client IP's. More information at: [Load Balancer overview](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-overview#securebydefault)

**Resolution:** Confirm there is a NSG in the backend VM Subnet or NIC that explicitly allows traffic from the Cient IP. 

Remedy this by adding a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP Flow Verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in Azure Portal.

**Cause - UDR Misconfiguration**

**Resolution:** 

Confirm if the effective routes of the backend network interface have the right route for Source Client IP:

1. For internet users, check if the next hop is internet, otherwise you need to confirm there is no asymetrric routing and firewalls in between are allowing the traffic.

2. For Azure users, please check if the next hop is the correct one and there is no asymmetric routing as well.

**Note:** If this doesn't help, open a service request to help with resolving your issue.

---

### Step 17: Floating IP Misconfiguration

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

**Issue:** Backend is not configured correctly for the Floating IP feature.

**Resolution:** Configure the Guest OS for the virtual machine to receive all traffic bound for the frontend IP and port of the **global load balancer**. Configuring the VM requires:

- Adding a loopback network interface

- Configuring the loopback with the frontend IP address of the load balancer

- Ensuring the system can send/receive packets on interfaces that don't have the IP address assigned to that interface.Windows systems require setting interfaces to use the "weak host" model. For Linux systems, this model is normally used by default.

- Configuring the host firewall to allow traffic on the frontend IP port.

Steps for [Windows:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#windows-server)

Steps for [Linux Ubuntu:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#ubuntu)

---
