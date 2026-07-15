# Troubleshoot connection issues between load balancer and backend pool

> **Product:** Load Balancer  
> **Solution ID:** e3c6812c-4c20-4903-b542-08a19a17aa49  
> **Trigger words:** backend, balancer, between, connection, connectivity issue, load balancer, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot connection issues between load balancer and backend pool** under **Load Balancer**.
 The original guided troubleshooter contains 31 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Inbound or outbound ⭐ (First Step)

### Guidance

Inbound traffic: Traffic originates from external clients (internet or other Azure resources) and targets the load balancer’s frontend public IP.

Outbound traffic: Traffic originates from backend pool virtual machines and goes out to the internet or public IPs using the load balancer’s frontend public IP via SNAT (Source Network Address Translation).

### Question

**Is the connectivity issue inbound to the load balancer or outbound through the load balancer’s public IP?**

### Options

- **Inbound** → Go to: *Load Balancer tier*
- **Outbound** → Go to: *544906a8-a2db-4da3-8788-db27a954dd6d*

---

### Step 2: Standard LB internal or external

### Content

Check to see what type of load balancing it is:

1. Open the load balancer resource in the Azure portal.

2. Select the **Properties** tab.

---

### Step 3: Standard LB INT floating IP check

### Content

Check the load balancer or NAT rule to see if the floating IP option is enabled or disabled.

- **Floating IP enabled:** Azure changes the IP address mapping to the frontend IP address of the load balancer.

- **Floating IP disabled:**	Azure exposes the virtual machine instance's IP address.

---

### Step 4: Standard INT LB floating IP configuration check

### Guidance

We've identified that your load balancing or NAT rule for this traffic has the floating IP setting enabled.

 

Backend connectivity may not work if your virtual machine is not configured to accept connections for the frontend IP address of your load balancing rule. Typically, this is done in conjunction with a clustering technology, such as Windows clustering or Kubernetes. You can also do this by configuring a loopback adapter in your operating system. For more information, see [Azure Load Balancer floating IP configuration](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#floating-ip-guest-os-configuration).

Validate that you've configured your clustering technology correctly or that you have a loopback adapter listening on your frontend IP address. If you do not have a clustering technology or loopback adapter configured, reconfigure your load balancing rule and disable Floating IP.

Configuration instructions:

- [Windows](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#windows-server)

- [Linux Ubuntu](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#ubuntu)

### Question

**Is your backend configured correctly for the floating IP feature?**

### Options

- **Yes.** → Go to: *STD UP INT NSG UDR solution*
- **No, it's not configured.** → Go to: *INT misconfigured floating IP solution*

---

### Step 5: INT misconfigured floating IP solution

### Support Engineer Solution

**Issue:** Backend is not configured correctly for the Floating IP feature.

**Resolution:** Configure the Guest OS for the virtual machine to receive all traffic bound for the frontend IP and port of the load balancer. Configuring the VM requires:

- Adding a loopback network interface

- Configuring the loopback with the frontend IP address of the load balancer

- Ensuring the system can send/receive packets on interfaces that don't have the IP address assigned to that interface.Windows systems require setting interfaces to use the "weak host" model. For Linux systems, this model is normally used by default.

- Configuring the host firewall to allow traffic on the frontend IP port.

Steps for [Windows:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#windows-server)

Steps for [Linux Ubuntu:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#ubuntu)

### Customer Solution

*Content type: MarkdownText*

**Issue:** The backend is not configured correctly for the floating IP feature.

**Resolution:** Configure the Guest OS for the virtual machine (VM) to receive all traffic bound for the frontend IP and port of the load balancer. Configuring the VM requires:

- Adding a loopback network interface.

- Configuring the loopback with the frontend IP address of the load balancer.

- Ensuring the system can send/receive packets on interfaces that don't have the IP address assigned to that interface. Windows systems require setting interfaces to use the weak host model. For Linux systems, this model is normally used by default.

- Configuring the host firewall to allow traffic on the frontend IP port.

Steps for [Windows](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#windows-server)

Steps for [Linux Ubuntu](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#ubuntu)

---

### Step 6: STD UP INT NSG UDR solution

### Support Engineer Solution

**Issue:** Data Path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

There are two potential causes: NSB misconfiguration or UDR misconfiguration

### NSG misconfiguration

Standard Load Balancer is secured by default, hence it requires an explicit NSG rule allowing traffic from original client IP's. See [Load Balancer overview](https://learn.microsoft.com/azure/load-balancer/load-balancer-overview#securebydefault)

**Resolution:** Confirm there is a NSG in the backend VM Subnet or NIC that explicitly allows traffic from the Cient IP. 

Add a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP Flow Verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in Azure Portal.

### UDR Misconfiguration

**Resolution:** Confirm that the effective routes of the backend network interface contain the right route for source client. If there is a Network Virtual Appliance, confirm that there is no asymetrric routing and its allowing the traffic.

If you are still having the issue, review the additional information in this article. 

### Customer Solution

*Content type: MarkdownText*

**Issue:** Data path issues may occur due to the path being blocked (NSGs, firewalls) or if it's misrouted.

There are two potential causes: NSB misconfiguration or UDR misconfiguration

### NSG misconfiguration

Standard Load Balancer is secured by default, so it requires an explicit NSG rule that allows traffic from the original client IPs. See [Load Balancer overview](https://learn.microsoft.com/azure/load-balancer/load-balancer-overview#securebydefault).

**Resolution:** Confirm there is an NSG in the backend VM subnet or NIC that explicitly allows traffic from the client IP. 

Add a rule with higher priority (lower number) allowing the traffic. You can test this by using the [Network Watcher IP flow verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in the Azure portal.

### UDR misconfiguration

**Resolution:** Confirm that the effective routes of the backend network interface contain the right route for the source client. If there is a network virtual appliance, confirm that there is no asymmetric routing and it's allowing traffic.

If you're still having the issue, review the additional information in this article. 

---

### Step 7: STD UP EXT NSG UDR solution

### Support Engineer Solution

**Issue:** Data Path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

Standard Load Balancer is secured by default, hence it requires an explicit NSG rule allowing traffic from original client IP's. More information at: [Load Balancer overview](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-overview#securebydefault)

**Resolution:** Confirm there is a NSG in the backend VM Subnet or NIC that explicitly allows traffic from the Cient IP. 

Remedy this by adding a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP Flow Verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in Azure Portal.

**Cause - UDR Misconfiguration**

**Resolution:** 

Confirm if the effective routes of the backend network interface have the right route for Source Client IP:

1. For internet users, please check if the next hop is internet, otherwise you need to confirm there is no asymetrric routing and firewalls in between are allowing the traffic.

2. For Azure users, please check if the next hop is the correct one and there is no asymmetric routing as well.

**Note:** If this doesn't help, open a service request to help with resolving your issue.

### Customer Solution

*Content type: MarkdownText*

Data path issues may occur due to the path being blocked by network security groups (NSG) or firewalls, or if it's misrouted.

There are two potential causes: NSG misconfiguration or UDR misconfiguration.

**NSG misconfiguration**

Standard Load Balancer is secured by default and requires an explicit NSG rule allowing traffic from the original client IPs. See [Load Balancer overview](https://learn.microsoft.com/azure/load-balancer/load-balancer-overview#securebydefault).

Confirm that there is an NSG in the backend VM's subnet or NIC that explicitly allows traffic from the client IP. 

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic. Test this using the [Network Watcher IP flow verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in the Azure portal.

**UDR misconfiguration**

Confirm that the effective routes of the backend network interface have the correct route for the source client IP:

- For internet users, check if the next hop is set to **internet**. Otherwise, you'll need to confirm that there is no asymmetric routing and that firewalls in between are allowing traffic.

- For Azure users, confirm that the next hop is correct and that there is no asymmetric routing.

If you're still having the issue, review the additional information in this article.

---

### Step 8: BSC UP internal or external

### Content

Check if the load balancer is internal (private) or external (public):

1. Open the load balancer resource in the Azure portal.

2. Select the **Properties** tab.

---

### Step 9: BSC UP INT has floating IP

### Content

Check the load balancer or NAT rule to see if the floating IP option is enabled or disabled.

- **Floating IP enabled:** Azure changes the IP address mapping to the frontend IP address of the load balancer.

- **Floating IP disabled:**	Azure exposes the virtual machine instance's IP address.

---

### Step 10: BSC UP INT floating IP configuration

### Guidance

We've identified that your load balancing or NAT rule for this traffic has the floating IP setting enabled.

Backend connectivity may not work if your virtual machine is not configured to accept connections for the frontend IP address of your load balancing rule. Typically, this is done in conjunction with a clustering technology, such as Windows clustering or Kubernetes. You can also do this by configuring a loopback adapter in your operating system. For more information, see [Floating IP Guest OS configuration](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#floating-ip-guest-os-configuration).

Validate that you've configured your clustering technology correctly or that you have a loopback adapter listening on your frontend IP address. If you do not have a clustering technology or loopback adapter configured, reconfigure your load balancing rule and disable Floating IP.

Steps for [Windows](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#windows-server)

Steps for [Linux Ubuntu](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#ubuntu)

### Question

**Is your backend configured correctly for the floating IP feature?**

### Options

- **Yes** → Go to: *BSC UP INT has global VNET*
- **No** → Go to: *INT misconfigured floating IP solution*

---

### Step 11: BSC UP INT has global VNET

### Guidance

An example would be a resource on VNet 1 in West Europe is trying to connect to another resource on VNet 2 in US East by using global VNet peering.

### Question

**Do the client and destination virtual machines belong to different virtual networks (VNet) that are peered across different regions (also known as global VNet peering)?**

### Options

- **Yes** → Go to: *BSC UP INT global VNET unsupported solution*
- **No** → Go to: *BSC UP INT NSG UDR solution*

---

### Step 12: BSC UP INT global VNET unsupported solution

### Support Engineer Solution

**Global VNET Peering is not supported for Basic Load Balancer** 

If the two virtual networks in two regions are peered over global virtual network peering, you can't connect to resources that are behind a basic load balancer through the front-end IP of the load balancer. This restriction doesn't exist for a standard load balancer:

[Load balancer SKU](https://learn.microsoft.com/en-us/azure/load-balancer/skus)

Our suggestion is to migrate your basic load balancer to a standard SKU load balancer where this is a supported scenario. Here are the instructions of how to do it: [Upgrade Load balancer from basic to standard](https://docs.microsoft.com/azure/load-balancer/upgrade-basic-standard)

### Customer Solution

*Content type: MarkdownText*

Global VNet peering is not supported for Basic Load Balancer.

If the two virtual networks in two regions are peered over global virtual network peering, you can't connect to resources that are behind a basic load balancer through the front-end IP of the load balancer. This restriction doesn't exist for a standard load balancer:

[Load balancer SKU](https://learn.microsoft.com/azure/load-balancer/skus).

We recommend that you migrate your basic load balancer to a standard SKU load balancer, which supports this scenario. To do so, see [Upgrade load balancer from basic to standard](https://docs.microsoft.com/azure/load-balancer/upgrade-basic-standard).

---

### Step 13: BSC UP INT NSG UDR solution

### Support Engineer Solution

**Issue:** Data Path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

**Resolution:** For Basic load balancer, If there is a NSG attached to the Backend Subnet or NIC, make sure that there is no deny rule above the default **AllowVnetInBound** rule.

Remedy this by adding a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP Flow Verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in Azure Portal.

**Cause - UDR Misconfiguration** 

**Resolution:** 

Confirm the effective routes of the backend network interface contain the right route for source client. If there is a Network Virtual Appliance, confirm that there is no asymmetric routing and its allowing the traffic.

**Note:** If the above steps do not resolve the issue, open a service request with Microsoft Support.

 

### Customer Solution

*Content type: MarkdownText*

Data path issues may occur due to the path being blocked by, for example, network security groups (NSG) or firewalls, or if it's misrouted.

There are two potential causes: NSG misconfiguration or UDR misconfiguration.

**NSG misconfiguration**

For Basic Load Balancer, if there is an NSG attached to the backend subnet or NIC, make sure that there is no deny rule above the default AllowVnetInBound rule.

To resolve the issue, add a rule with a higher priority (lower number) to allow traffic. Test it using the [Network Watcher IP flow verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in the Azure portal.

**UDR misconfiguration**

Confirm that the effective routes of the backend network interface contain the correct route for the source client IP. If there is a network virtual appliance, confirm that there is no asymmetric routing and that it's allowing traffic.

If you're still having the issue, review the additional information in this article.

---

### Step 14: BSC UP EXT NSG UDR solution

### Support Engineer Solution

**Issue:** Data Path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

 

 

**Cause - NSG misconfiguration:**

 

**Resolution:** For Basic Load Balancer, make sure that there is no NSG rule (associated with the backend VM NIC, or to the backend VM subnet) blocking inbound traffic from the source Client IP to the backend VM.

 

If there is a rule blocking, you can add a rule with higher priority (lower number) allowing the traffic from source Client IP to the backend VM.

 

**Cause - UDR misconfiguration:**

 

**Resolution:**

 

Confirm if the effective routes of the backend network interface have the right route for source client. If there is a network virtual appliance (NVA), confirm that there is no asymmetric routing and its allowing the traffic.

 

 

**Note:** If the above steps do not resolve the issue, please open a service request with Microsoft Support.

### Customer Solution

*Content type: MarkdownText*

Data path issues may occur due to the path being blocked by, for example, network security groups (NSG) or firewalls, or if it's misrouted.

 

There are two potential causes: NSG misconfiguration or UDR misconfiguration.

**NSG misconfiguration**

 

For Basic Load Balancer, make sure that no NSG rule associated with the backend virtual machine's (VM) subnet or NIC is blocking inbound traffic from the source client IP to the backend VM.

 

If there is a rule blocking traffic, add a rule with a higher priority (lower number) to allow traffic from the source client IP to the backend VM.

 

**UDR misconfiguration**

 

Confirm that the effective routes of the backend network interface contain the correct route for the source client IP. If there is a network virtual appliance, confirm that there is no asymmetric routing and that it's allowing traffic.

 

If you're still having the issue, review the additional information in this article.

---

### Step 15: No load balancing rule

### Support Engineer Solution

# No load balancer rule configured

There were no rules found in the load balancer that can handle the traffic with the parameters provided. 

Re-run this solution and validate if you provided the correct parameters.

If you keep getting this issue, review your load balancer configuration and validate that you have a rule to process the traffic.

[Manage rules for Azure Load Balancer using the Azure portal](https://learn.microsoft.com/en-us/azure/load-balancer/manage-rules-how-to)

### Customer Solution

*Content type: MarkdownText*

No load balancer rule configured.

There were no rules found in the load balancer that can handle the traffic with the parameters provided. 

Rerun this solution and verify that you provided the correct parameters.

If you continue experiencing this issue, review your load balancer configuration and verify that you have a rule to process the traffic.

[Manage rules for Azure Load Balancer using the Azure portal](https://learn.microsoft.com/azure/load-balancer/manage-rules-how-to)

---

### Step 16: STD UP EXT has floating IP

### Content

Check the load balancer or NAT rule to see if the floating IP option is enabled or disabled.

- **Floating IP enabled:** Azure changes the IP address mapping to the frontend IP address of the load balancer.

- **Floating IP disabled:**	Azure exposes the virtual machine instance's IP address.

---

### Step 17: STD EXT floating IP configuration

### Guidance

We've identified that your load balancing or NAT rule for this traffic has the floating IP setting enabled.

 

Backend connectivity may not work if your virtual machine is not configured to accept connections for the frontend IP address of your load balancing rule. Typically, this is done in conjunction with a clustering technology, such as Windows clustering or Kubernetes. You can also do this by configuring a loopback adapter in your operating system. For more information, see [Azure Load Balancer floating IP configuration](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#floating-ip-guest-os-configuration).

Validate that you've configured your clustering technology correctly or that you have a loopback adapter listening on your frontend IP address. If you do not have a clustering technology or loopback adapter configured, reconfigure your load balancing rule and disable Floating IP.

Configuration instructions:

- [Windows](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#windows-server)

- [Linux Ubuntu](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#ubuntu)

### Question

**Is your backend configured correctly for the floating IP feature?**

### Options

- **Yes** → Go to: *STD UP EXT NSG UDR solution*
- **No** → Go to: *INT misconfigured floating IP solution*

---

### Step 18: BSC UP EXT has floating IP

### Content

Check the load balancer or NAT rule to see if the floating IP option is enabled or disabled.

- **Floating IP enabled:** Azure changes the IP address mapping to the frontend IP address of the load balancer.

- **Floating IP disabled:**	Azure exposes the VM instance's IP address.

---

### Step 19: BSC UP EXT floating IP configuration

### Guidance

We've identified that your load balancing or NAT rule for this traffic has the floating IP setting enabled.

 

Backend connectivity may not work if your virtual machine is not configured to accept connections for the frontend IP address of your load balancing rule. Typically, this is done in conjunction with a clustering technology, such as Windows clustering or Kubernetes. You can also do this by configuring a loopback adapter in your operating system. For more information, see [Azure Load Balancer floating IP configuration](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#floating-ip-guest-os-configuration).

Validate that you've configured your clustering technology correctly or that you have a loopback adapter listening on your frontend IP address. If you do not have a clustering technology or loopback adapter configured, reconfigure your load balancing rule and disable Floating IP.

Configuration instructions:

- [Windows](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#windows-server)

- [Linux Ubuntu](https://learn.microsoft.com/azure/load-balancer/load-balancer-floating-ip#ubuntu)

### Question

**Is your backend configured correctly for the floating IP feature?**

### Options

- **Yes** → Go to: *BSC UP EXT NSG UDR solution*
- **No** → Go to: *INT misconfigured floating IP solution*

---

### Step 20: Load Balancer tier

### Content

Determine whether this is a global or regional load balancer:

1. Open the load balancer resource in the Azure portal.

2. Check the **Overview** page.

---

### Step 21: Backend health

### Guidance

Health probes are used to check the status of a backend pool instance. If the health probe fails to get a response from a backend instance, then no new connections will be sent to that backend instance until the health probe succeeds again.

To check if the backend pool is responding to the health probes coming from the load balancer: 

- In the Azure portal, on the **load balancer** page, select the **Metrics** tab.

- Select the **Health Probe Status** metric.

- Select **Avg** for the aggregation type.

- Apply splitting by **Backend IP Address**.

See more about [health probe monitoring](https://learn.microsoft.com/azure/load-balancer/load-balancer-standard-diagnostics#are-the-backend-instances-for-my-load-balancer-responding-to-probes).

**Note:** For Basic Load Balancer, Azure metrics are not supported.

To verify health:

- Take packet captures on the backend virtual machine (VM).

- Confirm you see requests from probe IP 168.63.129.16.

- Ensure the backend VM responds to those requests.

### Question

**Is the load balancer backend pool healthy and responding to health probes?**

### Options

- **Yes** → Go to: *Load balancer SKU*
- **No** → Go to: *5822ba65-5b5a-4583-a7fe-c75ed3a3bc0d*

---

### Step 22: Load balancer SKU

### Content

Determine whether this is a Basic, Standard, or Gateway Load Balancer:

1. Open the load balancer resource in the Azure portal.

2. Check the **Overview** page or the **Properties** tab. 

---

### Step 23: Basic SKU is retired

### Guidance

**Make sure to upgrade to Standard Load Balancer as soon as possible.**

On September 30, 2025, Basic Load Balancer was retired. For more information, see the [official announcement](https://azure.microsoft.com/updates?id=azure-basic-load-balancer-will-be-retired-on-30-september-2025-upgrade-to-standard-load-balancer). For guidance on upgrading, see [Upgrading from Basic Load Balancer - Guidance](https://learn.microsoft.com/azure/load-balancer/load-balancer-basic-upgrade-guidance).

### Question

**What would you like to do?**

### Options

- **I'll plan on upgrading later and will keep using Basic for now.** → Go to: *BSC UP internal or external*
- **I'll upgrade and recheck the issue.** → Go to: *Upgrade to standard SKU*

---

### Step 24: Verify port match

### Guidance

Determine whether the health probe port equals the load balancing rule port.

### Question

**Is the health probe port identical to the load balancing rule port?**

### Options

- **Yes** → Go to: *Same port admin state*
- **No** → Go to: *Datapath availability check*

---

### Step 25: Same port admin state

### Guidance

**Steps to confirm the administrative state of the specific backend pool:**

1. Navigate to **Load Balancer** > **Backend Pools**.

2. For the specific backend pool, look out for **Admin State** option toward the far right.

**More information:**

- [About Admin State](https://learn.microsoft.com/azure/load-balancer/admin-state-overview)

### Question

**Is the admin state of the target backend pool set to "Up"?**

### Options

- **Yes** → Go to: *Switch the admin state*
- **No** → Go to: *Datapath availability check*

---

### Step 26: Datapath availability check

### Guidance

- In the Azure portal, on the **Load balancer** page, select the **Metrics** tab.

- Select the **Data Path Availability** metric.

- Select **Avg** for the aggregation type.

### Question

**Is the load balancer's Data Path Availability metric reporting 100%?**

### Options

- **Yes** → Go to: *Standard LB internal or external*
- **No** → Go to: *Check NSG for LB Port*

---

### Step 27: Check NSG for LB Port

### Guidance

This step ensures that the network security group (NSG) linked to the backend pool allows traffic on the port defined in the load balancing rule. 

### Question

**Is the NSG for the backend pool configured to allow the load balancing rule port?**

### Options

- **Yes** → Go to: *Platform issue*
- **No** → Go to: *NSG solution for LB rule port*

---

### Step 28: Platform issue

### Support Engineer Solution

 Based on the information you've provided, it appears that the issue may be related to the platform itself. To ensure a thorough investigation and timely resolution, we recommend opening a service request with our technical support team.

### Customer Solution

*Content type: MarkdownText*

 Based on the information you've provided, it appears that the issue may be related to the platform itself. To ensure a thorough investigation and timely resolution, we recommend opening a service request with our technical support team.

---

### Step 29: NSG solution for LB rule port

### Support Engineer Solution

**Issue:** Data Path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

Standard Load Balancer is secured by default, hence it requires an explicit NSG rule allowing traffic from original client IP's. More information at: [Load Balancer overview](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-overview#securebydefault)

**Resolution:** Confirm there is a NSG in the backend VM Subnet or NIC that explicitly allows traffic from the Cient IP. 

Remedy this by adding a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP Flow Verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in Azure Portal.

### Customer Solution

*Content type: MarkdownText*

**Issue:** Data path issues may occur due to the path being blocked (NSGs, firewalls) or if it's misrouted.

**Cause - NSG misconfiguration:** 

Standard Load Balancer is secured by default; hence, it requires an explicit NSG rule allowing traffic from original client IPs. For more information, see [Load Balancer overview](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-overview#securebydefault).

**Resolution:** Confirm there is an NSG in the backend virtual machine subnet or NIC that explicitly allows traffic from the client IP. 

Remedy this by adding a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP flow verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in the Azure portal.

---

### Step 30: Switch the admin state

### Guidance

Switch the backend pool admin state to **None** and check the health probe status under portal metrics.

To check the health probe status for a Standard SKU Load Balancer:

1. In the portal, go to **Load Balancer** > **Monitoring** > **Metrics**.

1. Select **Add metric**.

1. Select metric as **Health Probe Status** with **Avg** aggregation type.

1. Apply a filter on the required frontend IP address or port (or both). This is not required if you only have one frontend IP address and port.

1. Apply a filter on the backend IP addresses (either all backends or specific).

See [Standard Load Balancer metrics](https://learn.microsoft.com/azure/load-balancer/load-balancer-standard-diagnostics#are-the-backend-instances-for-my-load-balancer-responding-to-probes).

### Question

**Is the health probe showing as unhealthy after setting the admin state to "none"?**

### Options

- **Yes** → Go to: *5822ba65-5b5a-4583-a7fe-c75ed3a3bc0d*
- **No** → Go to: *Datapath availability check*

---

### Step 31: Upgrade to standard SKU

### Support Engineer Solution

On September 30, 2025, Basic Load Balancer was retired. For more information, see the [official announcement](https://azure.microsoft.com/en-us/updates?id=azure-basic-load-balancer-will-be-retired-on-30-september-2025-upgrade-to-standard-load-balancer).Please make sure to upgrade to Standard Load Balancer as soon as possible. For guidance on upgrading, visit [Upgrading from Basic Load Balancer - Guidance](https://docs.azure.cn/en-us/load-balancer/load-balancer-basic-upgrade-guidance).

### Customer Solution

*Content type: MarkdownText*

On September 30, 2025, Basic Load Balancer was retired. For more information, see the [official announcement](https://azure.microsoft.com/updates?id=azure-basic-load-balancer-will-be-retired-on-30-september-2025-upgrade-to-standard-load-balancer). 

Make sure to upgrade to Standard Load Balancer as soon as possible. For guidance on upgrading, see [Upgrading from Basic Load Balancer - guidance](https://learn.microsoft.com/azure/load-balancer/load-balancer-basic-upgrade-guidance).

---
