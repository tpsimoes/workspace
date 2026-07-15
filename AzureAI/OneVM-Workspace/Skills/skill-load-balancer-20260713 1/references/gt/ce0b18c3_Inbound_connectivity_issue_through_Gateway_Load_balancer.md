# Inbound connectivity issue through Gateway Load balancer

> **Product:** Load Balancer  
> **Solution ID:** ce0b18c3-025d-4c9a-87ed-137480eac3e2  
> **Trigger words:** balancer, connectivity, connectivity issue, gateway, inbound, issue, load balancer, through

---

## Overview

This guide provides step-by-step troubleshooting for **Inbound connectivity issue through Gateway Load balancer** under **Load Balancer**.
 The original guided troubleshooter contains 30 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Scoping ⭐ (First Step)

### Guidance

This guided troubleshooter is specific to Gateway Load Balancer inbound issues.

Determine whether this is a Gateway Load Balancer:

1. Open the load balancer resource in the Azure portal.

2. Check the **Overview** page.

### Question

**Are you facing inbound issues through a Gateway Load Balancer?**

### Options

- **Yes** → Go to: *LB SKU Automated*
- **No, its inbound issue with another SKU** → Go to: *e3c6812c-4c20-4903-b542-08a19a17aa49*
- **No, Its not an inbound issue** → Go to: *Out of TSG scope*

---

### Step 2: Out of TSG scope

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

**Note:**

 If your issue is not related to inbound connectivity through Gateway Load Balancer, visit the **Support + Troubleshooting** option in the **Help** section on Azure Portal to look for new insights and troubleshooters.

---

### Step 3: LB SKU Automated

### Content

Determine whether this is a Basic, Standard or Gateway Load Balancer:

1. Open the load balancer resource in the Azure portal.

2. Check the **Overview** page or the **Properties** tab. 

---

### Step 4: Gateway Probe UP or Down

### Guidance

Health probes are used to check the status of a backend pool instance. If the health probe fails to get a response from a backend instance then no new connections will be sent to that backend instance until the health probe succeeds again.

To check if the backend pool is responding to the health probes coming from the load balancer: 

- In the Azure portal, on the **load balancer** page, select the **Metrics** tab.

- Select the **Health Probe Status** metric.

- Select **Avg** for the aggregation type.

- Apply splitting by **Backend IP Address**.

See more about [health probe monitoring](https://learn.microsoft.com/azure/load-balancer/load-balancer-standard-diagnostics#are-the-backend-instances-for-my-load-balancer-responding-to-probes).

### Question

**Are the backend instances healthy and responding to health probes?**

### Options

- **Yes** → Go to: *Gateway Datapath availability*
- **No** → Go to: *Gateway Probe Down NSG check*

---

### Step 5: Gateway Datapath availability

### Guidance

- In the Azure portal, on the **load balancer** page, select the **Metrics** tab.

- Select the **Data Path Availability** metric.

- Select **Avg** for the aggregation type.

### Question

**Is the load balancer's Data Path Availability metric reporting 100%?**

### Options

- **Yes** → Go to: *Gateway Chaining can be automated*
- **No** → Go to: *Gateway Platform issue*

---

### Step 6: Gateway Platform issue

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

 Based on the information you've provided, it appears that the issue may be related to the platform itself. To ensure a thorough investigation and timely resolution, we recommend opening a service request with our technical support team.

---

### Step 7: Gateway Chaining can be automated

### Guidance

Gateway Load Balancer chaining refers to the process of referencing a Gateway Load Balancer from a Standard public Load Balancer frontend or a Standard public IP configuration on a virtual machine.

[Chain load balancer frontend to Gateway Load Balancer](https://learn.microsoft.com/en-us/azure/load-balancer/tutorial-gateway-portal#chain-load-balancer-frontend-to-the-gateway-load-balancer)

### Question

**Is the Gateway Load Balancer chained to a consumer resource?**

### Options

- **Yes** → Go to: *Gateway Tunnel interfaces*
- **No** → Go to: *No chaining found*

---

### Step 8: No chaining found

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

To ensure that traffic to and from your application endpoint is directed to your Gateway Load Balancer, a Standard public Load Balancer frontend or a Standard IP configuration on a virtual machine needs to reference the Gateway Load Balancer.

See more about [Load Balancer chaining](https://learn.microsoft.com/en-us/azure/load-balancer/gateway-overview#benefits).

---

### Step 9: Gateway Tunnel interfaces

### Guidance

Gateway Load Balancer backend pools have a component called tunnel interfaces.

The tunnel interface enables the network virtual appliances (NVAs) in the backend to receive and send traffic using VXLAN tunnels. Each backend pool can have up to two tunnel interfaces. Tunnel interfaces can be either internal or external. For traffic going to your backend pool, otherwise known as untrusted traffic, you should use the external tunnel. For traffic going from the NVAs to the application, otherwise known as trusted traffic, you should use the internal tunnel.

Verify that the tunnel interface on the appliance side matches the configuration in the backend pool of the Gateway Load Balancer. See more about [Gateway load balancer configuration guide](https://learn.microsoft.com/en-us/azure/load-balancer/tutorial-gateway-portal#create-gateway-load-balancer).

### Question

**Are the tunnel interfaces on the backend appliance configured correctly?**

### Options

- **Yes** → Go to: *Gateway tunnel interface MTU*
- **No** → Go to: *Gateway Tunnel interface issue*

---

### Step 10: Gateway Tunnel interface issue

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

Refer to the configuration guide provided by your NVA partner [here](https://learn.microsoft.com/en-us/azure/load-balancer/gateway-partners). If you require additional information, it may be necessary to open a support ticket with the third-party vendor.

---

### Step 11: Gateway tunnel interface MTU

### Guidance

Azure Gateway Load Balancer utilizes VXLAN encapsulation to transmit packets, so the provider backend must support an MTU size of 4000.

### Question

**Is the MTU on the NVAs set to 4000?**

### Options

- **Yes** → Go to: *Consumer resource check can be automated*
- **No** → Go to: *Gateway tunnel interface MTU solution*

---

### Step 12: Gateway tunnel interface MTU solution

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

Azure Gateway Load Balancer utilizes VXLAN encapsulation to transmit packets, so the provider backend must support an MTU size of 4000.

---

### Step 13: Consumer resource check can be automated

### Guidance

A Standard public Load Balancer or a Standard IP configuration of a virtual machine can be chained to a Gateway Load Balancer. "Chaining" refers to the load balancer frontend or NIC IP configuration containing a reference to a Gateway Load Balancer frontend IP configuration. For more information, please refer to [Gateway Load balancer chaining](https://learn.microsoft.com/en-us/azure/load-balancer/gateway-overview#configuration-and-supported-scenarios).

### Question

**What is the type of consumer resource?**

### Options

- **Standard public IP attached to a virtual machine** → Go to: *NSG configuration consumer vm*
- **Standard public Load Balancer** → Go to: *Consumer LB Probe up or Down*

---

### Step 14: NSG configuration consumer vm

### Guidance

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

Standard public IP addresses are closed to inbound connections unless permitted by Network Security Groups. NSGs are used to explicitly permit allowed traffic. If you don't have an NSG on a subnet or NIC of your virtual machine resource, traffic isn't allowed to reach this resource.

**Cause - UDR Misconfiguration**: Confirm if the effective routes of the backend network interface have the right route for Source Client.

### Question

**Are your NSGs and UDRs configured correctly?**

### Options

- **Yes** → Go to: *Consumer vm guest OS*
- **No** → Go to: *Consumer vm NSG UDR solution*

---

### Step 15: Consumer vm guest OS

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

We recommend that you check whether your application is correctly configured to respond to the configured health probes (protocol, port, and path) within the configured interval.

To do so:

- On Windows, use this command: `netstat -ano | findstr LISTENING | findstr 80`.

- On Linux, use this command: `netstat -ano | grep LISTEN | grep tcp | grep 80`.

Make sure that the operating system firewall is allowing the health probe port. On Windows use `wf.msc`, and on Linux use `iptables`.

If no issues have been found up to this point, it's likely that your network virtual appliance is blocking the connection. Check the appliance and consider opening a support ticket with the vendor for further assistance

---

### Step 16: Consumer vm NSG UDR solution

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:**

Standard public IP addresses are closed to inbound connections unless permitted by Network Security Groups. NSGs are used to explicitly allow permitted traffic. If you don't have an NSG on a subnet or NIC of your virtual machine resource, traffic isn't allowed to reach this resource.

**Resolution:** Confirm there is a NSG in the backend VM subnet or NIC that explicitly allows traffic from the Client IP. 

Remedy this by adding a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP Flow Verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in Azure Portal.

**Cause - UDR misconfiguration:**

**Resolution:** 

Confirm if the effective routes of the backend network interface have the right route for Source Client IP:

1. For Internet users, please check if the next hop is Internet, otherwise you need to confirm there is no asymmetric routing and firewalls in between are allowing the traffic.

2. For Azure users, please check if the next hop is the correct one and there is no asymmetric routing as well.

---

### Step 17: Consumer LB Probe up or Down

### Guidance

A Standard Load Balancer uses a distributed health-probing service that monitors your application endpoint's health according to your configuration settings. 

To check if the backend pool is responding to the health probes coming from the load balancer: 

- In the Azure portal, on the **consumer load balancer** page, select the **Metrics** tab.

- Select the **Health Probe Status** metric.

- Select **Avg** for the aggregation type.

- Apply splitting by **Backend IP Address**.

See more about [health probe monitoring](https://learn.microsoft.com/azure/load-balancer/load-balancer-standard-diagnostics#are-the-backend-instances-for-my-load-balancer-responding-to-probes).

### Question

**Are the backend instances on your consumer load balancer healthy and responding appropriately to health probes?**

### Options

- **Yes** → Go to: *Consumer LB Probe UP has floating ip*
- **No** → Go to: *Consumer LB probe down NSG check*

---

### Step 18: Consumer LB probe down NSG check

### Guidance

For the Load Balancer's health probe to mark up your instance, you must allow the IP address 168.63.129.16 in any Azure network security groups and local firewall policies. The AzureLoadBalancer service tag identifies this source IP address in your network security groups and permits health probe traffic by default. 

To learn more, see [What is IP address 168.63.129.16?](https://learn.microsoft.com/azure/virtual-network/what-is-ip-address-168-63-129-16)

### Question

**Is the network security group for the backend pool configured correctly?**

### Options

- **Yes** → Go to: *Consumer LB Probe Down Application*
- **No** → Go to: *Consumer LB probe down NSG solution*

---

### Step 19: Consumer LB probe down NSG solution

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

---

### Step 20: Consumer LB Probe Down Application

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

In order for load balancer health probes to succeed, the IP address 168.63.129.16 which is also denoted by the AzureLoadBalancer service tag must be allowed through all network security group rules.

If network security group rule are configured correctly to allow health probe, but connectivity issues still exist, we recommend that you check whether your application is responding to the configured health probe (protocol, port, and path) within the configured interval.

To do so:

- On Windows, use this command: `netstat -ano | findstr LISTENING | findstr 80`.

- On Linux, use this command: `netstat -ano | grep LISTEN | grep tcp | grep 80`.

Make sure that the operating system firewall is allowing the health probe port. On Windows use `wf.msc`, and on Linux use `iptables`.

---

### Step 21: Consumer LB Probe UP has floating ip

### Content

Check the load balancing or NAT rule to see if the floating IP option is enabled or disabled.

- **Floating IP enabled:** Azure changes the IP address mapping to the frontend IP address of the load balancer.

- **Floating IP disabled:**	Azure exposes the VM instance's IP address.

---

### Step 22: Consumer LB probe UP floating no rule

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

### Step 23: Consumer LB probe UP NSG UDR check

### Guidance

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

Standard public IP addresses are closed to inbound connections unless opened by Network Security Groups. NSGs are used to explicitly allow permitted traffic. If you don't have an NSG on a subnet or NIC of your virtual machine resource, traffic isn't allowed to reach this resource.

**Cause - UDR Misconfiguration**: Confirm if the effective routes of the backend network interface have the right route for Source Client.

### Question

**Do you have the NSG/UDR configured correctly on the backend pool of the consumer load balancer?**

### Options

- **Yes** → Go to: *Consumer LB probe Up application*
- **No** → Go to: *Consumer LB probe UP NSG UDR solution*

---

### Step 24: Consumer LB probe Up application

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

We recommend that you check whether your application is correctly configured to respond to the configured backend port.

To achieve this:

- On Windows, use this command: `netstat -ano | findstr LISTENING | findstr 80`.

- On Linux, use this command: `netstat -ano | grep LISTEN | grep tcp | grep 80`.

Make sure that the operating system firewall is allowing the destination port. On Windows use `wf.msc`, and on Linux use `iptables`.

If everything is configured correctly up to this point, we recommend consulting your network virtual appliance (NVA) vendor to determine if the NVA is blocking the connection.

---

### Step 25: Consumer LB probe UP NSG UDR solution

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

Standard public IP addresses are closed to inbound connections unless opened by Network Security Groups. NSGs are used to explicitly allow permitted traffic. If you don't have an NSG on a subnet or NIC of your virtual machine resource, traffic isn't allowed to reach this resource.

**Resolution:** Confirm there is a NSG in the backend VM Subnet or NIC that explicitly allows traffic from the Client IP. 

Remedy this by adding a rule with higher priority (lower number) allowing the traffic. You can test this using the [Network Watcher IP Flow Verify tool](https://docs.microsoft.com/azure/network-watcher/network-watcher-ip-flow-verify-overview) in Azure Portal.

**Cause - UDR Misconfiguration**

**Resolution:** 

Confirm if the effective routes of the backend network interface have the right route for Source Client IP:

1. For Internet users, check if the next hop is internet, otherwise you need to confirm there is no asymetrric routing and firewalls in between are allowing the traffic.

2. For Azure users, check if the next hop is the correct one and there is no asymmetric routing as well.

---

### Step 26: Gateway Probe Down NSG check

### Guidance

For the Load Balancer's health probe to mark up your instance, you must allow the IP address 168.63.129.16 in any Azure network security groups and local firewall policies. The AzureLoadBalancer service tag identifies this source IP address in your network security groups and permits health probe traffic by default. 

To learn more, see [What is IP address 168.63.129.16?](https://learn.microsoft.com/azure/virtual-network/what-is-ip-address-168-63-129-16)

### Question

**Is the network security group configuration for the backend pool appropriately set up?**

### Options

- **Yes** → Go to: *NVA OS is blocking health probe IP*
- **No** → Go to: *Gateway Probe Down NSG UDR solution*

---

### Step 27: Gateway Probe Down NSG UDR solution

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

---

### Step 28: NVA OS is blocking health probe IP

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

In order for load balancer health probes to succeed, the IP address 168.63.129.16 which is also denoted by the AzureLoadBalancer service tag must be allowed through all network security group rules.

If network security group rule are configured correctly to allow health probe, but connectivity issues still exist, we recommend that you check whether your NVA are configured to allow and respond appropriately to the health probes (protocol, port, and path) within the configured interval.

---

### Step 29: Consumer LB Probe UP floating enabled NSG check

### Guidance

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if it's misrouted.

**Cause - NSG misconfiguration:** Since floating IP is enabled, you need to have NSG rule to allow the connection from client IP address to the frontend IP address of the load balancer. 

**Cause - UDR misconfiguration**: Confirm if the effective routes of the backend network interface have the right route for Source Client.

### Question

**Do you have the NSG/UDR configured correctly on the backend pool of the consumer load balancer?**

### Options

- **Yes** → Go to: *Consumer LB probe Up application*
- **No** → Go to: *Consumer LB probe UP floating ip enabled loopback*

---

### Step 30: Consumer LB probe UP floating ip enabled loopback

### Support Engineer Solution

n/a

### Customer Solution

*Content type: MarkdownText*

**Issue:** Backend is not configured correctly for the Floating IP feature.

**Resolution:** Configure the guest OS for the virtual machine to receive all traffic bound for the frontend IP and port of the load balancer. Configuring the VM requires:

- Adding a loopback network interface

- Configuring the loopback with the frontend IP address of the load balancer

- Ensuring the system can send/receive packets on interfaces that don't have the IP address assigned to that interface.Windows systems require setting interfaces to use the "weak host" model. For Linux systems, this model is normally used by default.

- Configuring the host firewall to allow traffic on the frontend IP port.

Steps for [Windows:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#windows-server)

Steps for [Linux Ubuntu:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#ubuntu)

---
