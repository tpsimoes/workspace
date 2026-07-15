# Inbound connectivity issue through Gateway Load balancer

> **Product:** Load Balancer  
> **Solution ID:** 1921d987-de74-44bf-8c1b-5b00b64948c1  
> **Trigger words:** balancer, connectivity, connectivity issue, gateway, inbound, issue, load balancer, through

---

## Overview

This guide provides step-by-step troubleshooting for **Inbound connectivity issue through Gateway Load balancer** under **Load Balancer**.
 The original guided troubleshooter contains 30 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Scoping ⭐ (First Step)

### Guidance

This guided troubleshooter is specific to Gateway Load Balancer inbound issues.

To verify the SKU of the load balancer, simply look at the Properties section in ASC for the SKU field.

### Question

**Is the customer experiencing inbound issues with their Gateway Load Balancer?**

### Options

- **Yes** → Go to: *LB SKU*
- **No, its inbound issue with another SKU** → Go to: *454c4292-c3c0-4c42-9ed9-a8e4428b0d21*
- **No, Its not an inbound issue** → Go to: *Out of TSG scope*

---

### Step 2: Out of TSG scope

### Support Engineer Solution

Please add another solution set on the ASC to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results.

### Customer Solution

*Content type: MarkdownText*

n/a

---

### Step 3: LB SKU

### Content

To verify the SKU of the load balancer, simply look at the Properties section in ASC for the SKU field.

---

### Step 4: Gateway Probe UP or Down

### Guidance

Health probes are used to check the status of a backend pool instance. If the health probe fails to get a response from a backend instance then no new connections will be sent to that backend instance until the health probe succeeds again.

**Recommended Steps**

To check health probe status of the gateway load balancer:

In ASC, browse to the Diagnostics tab of the relevant load balancer and scroll down to "DIP Availability". Click on the link for the relevant frontend IP and port. This will open a new tab with the DipAvailability_HealthProbeStatus Dashboard with the parameters filled out. If you are looking to root cause a prior issue, adjust the time parameter of the dashboard. Be sure to note time zones to ensure you are look at the right point in time.

On the top set of charts under "Data Path Availability (VipAvailability)," look to see if there are jumps in FailureCount. If you see an increase in NoFowardingDip, the customer is unable to connect to their load balancer because all members of the backend pool were unhealthy.

### Question

**Are the backend instances healthy and responding to health probes?**

### Options

- **Yes** → Go to: *VIP availability check*
- **No** → Go to: *Gateway Probe Down NSG check*

---

### Step 5: VIP availability check

### Guidance

To check the VIP Availability status of the gateway load balancer:

In ASC, browse to the Diagnostics tab of the relevant load balancer and scroll down to "VIP Availability". Click on the link for the relevant frontend IP and port. This will open a new tab with the VipAvailability_DataPathAvailability Dashboard with the parameters filled out. If you are looking to root cause a prior issue, adjust the time parameter of the dashboard. Be sure to note time zones to ensure you are look at the right point in time.

### Question

**Is the VIP Availability metric reporting 100%?**

### Options

- **Yes** → Go to: *Gateway Chaining*
- **No** → Go to: *Platform Issue*

---

### Step 6: Platform Issue

### Support Engineer Solution

Check the corresponding reason you see under the Failure Reasons count graph, the following information will help you understand what exact issue was the customer facing:

**Success:** The ping was sent out, routed to a host, bounced off VFP, and successfully returned

**NoForwardingDip:** All Dips behind this endpoint are probed down. This failure is usually caused by customer side configuration.

**Unreachable NonPlatform:** False The ping was sent out but didn't return as expected before the timeout. This is a platform failure, often this is caused by vfp, unhealthy nodes/T0-2s.

**Unreachable NonPlatform:** True The ping was sent out but didn't return as expected before the timeout. This is a non-platform failure and caused by customer configuration.

**NoEndpoint:** The mux does not have this endpoint (vip+port) configured in the goal state. This is platform failure.

**NoVipGoalState:** The mux does not have this vip configured in the goal state at all. This is platform failure.

If you're unable to diagnose the issue, please post your case in Ava, including all the troubleshooting steps you've taken. A TA will then review it to determine if an ICM is necessary.

### Customer Solution

*Content type: MarkdownText*

n/a

---

### Step 7: Gateway Chaining

### Guidance

Gateway Load Balancer chaining refers to the process of referencing a Gateway Load Balancer from a Standard public Load Balancer frontend or a Standard public IP configuration on a virtual machine.

[Chain load balancer frontend to Gateway Load Balancer](https://learn.microsoft.com/en-us/azure/load-balancer/tutorial-gateway-portal#chain-load-balancer-frontend-to-the-gateway-load-balancer)

### Question

**Is the Gateway Load Balancer chained to a consumer resource?**

### Options

- **Yes** → Go to: *Gateway Tunnel interfaces*
- **No** → Go to: *No Chaining Found*

---

### Step 8: No Chaining Found

### Support Engineer Solution

To ensure that traffic to and from your application endpoint is directed to your Gateway Load Balancer, a Standard public Load Balancer frontend or a Standard IP configuration on a virtual machine needs to reference the Gateway Load Balancer.

See more about [Load Balancer chaining](https://learn.microsoft.com/en-us/azure/load-balancer/gateway-overview#benefits).

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

To ensure that traffic to and from your application endpoint is directed to your Gateway Load Balancer, please reference the Gateway Load Balancer in your Standard public Load Balancer frontend or Standard IP configuration on a virtual machine.

For more details, refer to [Load Balancer chaining](https://learn.microsoft.com/en-us/azure/load-balancer/gateway-overview#benefits).

Best regards,

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
- **No** → Go to: *Gateway Tunnel Interface Solution*

---

### Step 10: Gateway Tunnel Interface Solution

### Support Engineer Solution

Refer the customer to the configuration guide provided by the NVA partner [here](https://learn.microsoft.com/en-us/azure/load-balancer/gateway-partners). If customer requires additional information, it may be necessary to open a support ticket with the third-party vendor.

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

Gateway Load Balancer backend pools have a component called tunnel interfaces. The tunnel interface enables the network virtual appliances (NVAs) in the backend to receive and send traffic using VXLAN tunnels. Each backend pool can have up to two tunnel interfaces. Tunnel interfaces can be either internal or external. For traffic going to your backend pool, otherwise known as untrusted traffic, you should use the external tunnel. For traffic going from the NVAs to the application, otherwise known as trusted traffic, you should use the internal tunnel.

Verify that the tunnel interface on the appliance side matches the configuration in the backend pool of the Gateway Load Balancer.matches the configuration in the backend pool of the Gateway Load Balancer. See more about [Gateway load balancer configuration guide](https://learn.microsoft.com/en-us/azure/load-balancer/tutorial-gateway-portal#create-gateway-load-balancer).

Please refer to the configuration guide provided by your NVA partner [here](https://learn.microsoft.com/en-us/azure/load-balancer/gateway-partners). If you require additional information, it may be necessary to open a support ticket with the third-party vendor.

Best regards,

---

### Step 11: Gateway tunnel interface MTU

### Guidance

Azure Gateway Load Balancer utilizes VXLAN encapsulation to transmit packets, so the provider backend must support an MTU size of 4000.

See more, [MTU limit](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/641221/TSG-GWLB?anchor=2---troubleshoot-the-provider%3A-gwlb)

### Question

**Is the MTU on the NVAs set to 4000?**

### Options

- **Yes** → Go to: *Consumer resource check*
- **No** → Go to: *Resolving Gateway Tunnel Interface MTU Issues*

---

### Step 12: Resolving Gateway Tunnel Interface MTU Issues

### Support Engineer Solution

Azure Gateway Load Balancer utilizes VXLAN encapsulation to transmit packets, so the provider backend must support an MTU size of 4000.

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

Azure Gateway Load Balancer utilizes VXLAN encapsulation to transmit packets, so the provider backend must support an MTU size of 4000.

Best regards,

---

### Step 13: Consumer resource check

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

- **Yes** → Go to: *Consumer VM Operating System*
- **No** → Go to: *Network Security Group and User Defined Route Solution*

---

### Step 15: Consumer VM Operating System

### Support Engineer Solution

We recommend that you check whether your application is correctly configured to respond to the configured health probes (protocol, port, and path) within the configured interval.

To do so:

- On Windows, use this command: `netstat -ano | findstr LISTENING | findstr 80`.

- On Linux, use this command: `netstat -ano | grep LISTEN | grep tcp | grep 80`.

Make sure that the operating system firewall is allowing the health probe port. On Windows use `wf.msc`, and on Linux use `iptables`.

If no issues have been found up to this point, it's likely that your network virtual appliance is blocking the connection. Check the appliance and consider opening a support ticket with the vendor for further assistance

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

We recommend that you check whether your application is correctly configured to respond to the configured health probes (protocol, port, and path) within the configured interval.

To do so:

On Windows, use this command: netstat -ano | findstr LISTENING | findstr 80

On Linux, use this command: netstat -ano | grep LISTEN | grep tcp | grep 80

Make sure that the operating system firewall is allowing the health probe port. On Windows, use wf.msc, and on Linux, use iptables.

If no issues have been found up to this point, it's likely that your network virtual appliance is blocking the connection. Please check the appliance and consider opening a support ticket with the vendor for further assistance.

Best regards, 

---

### Step 16: Network Security Group and User Defined Route Solution

### Support Engineer Solution

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

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

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

Best regards,

---

### Step 17: Consumer LB Probe up or Down

### Guidance

A Standard Load Balancer uses a distributed health-probing service that monitors your application endpoint's health according to your configuration settings. 

To check if the backend pool is responding to the health probes coming from the load balancer: 

- In ASC, go to the Diagnostics tab of the regional load balancer.

- Scroll down to "DIP Availability" and click the link for the relevant frontend IP and port.

- A new tab will open with the DipAvailability_HealthProbeStatus Dashboard filled out with parameters.

- Adjust the time parameter of the dashboard if you are trying to find the root cause of a prior issue, ensuring the correct time zones are noted.

- On the top charts under "Data Path Availability (VipAvailability)", check for any jumps in FailureCount.

- If there is an increase in NoFowardingDip, it means the customer is unable to connect to their load balancer because all members of the backend pool were unhealthy.

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

- **Yes** → Go to: *Application Responding to LB Probe Down*
- **No** → Go to: *Resolution for NSG Causing Probe Down*

---

### Step 19: Resolution for NSG Causing Probe Down

### Support Engineer Solution

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

To resolve this issue, please add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag.

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

Best regards,

---

### Step 20: Application Responding to LB Probe Down

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

In order for load balancer health probes to succeed, the IP address 168.63.129.16, also denoted by the AzureLoadBalancer service tag, must be allowed through all network security group rules.

If network security group rules are configured correctly to allow the health probe but connectivity issues still persist, we recommend checking whether your application is responding to the configured health probe (protocol, port, and path) within the configured interval.

To do so:

On Windows, use this command: netstat -ano | findstr LISTENING | findstr 80

On Linux, use this command: netstat -ano | grep LISTEN | grep tcp | grep 80

Make sure that the operating system firewall is allowing the health probe port. On Windows, use wf.msc, and on Linux, use iptables.

Best regards,

---

### Step 21: Consumer LB Probe UP has floating ip

### Content

Check the load balancing or NAT rule to see if the floating IP option is enabled or disabled.

- **Floating IP enabled:** Azure changes the IP address mapping to the frontend IP address of the load balancer.

- **Floating IP disabled:**	Azure exposes the VM instance's IP address.

---

### Step 22: Consumer LB probe UP floating no rule

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

### Step 23: Consumer LB probe UP NSG UDR check

### Guidance

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if its misrouted.

**Cause - NSG misconfiguration:** 

Standard public IP addresses are closed to inbound connections unless opened by Network Security Groups. NSGs are used to explicitly allow permitted traffic. If you don't have an NSG on a subnet or NIC of your virtual machine resource, traffic isn't allowed to reach this resource.

**Cause - UDR Misconfiguration**: Confirm if the effective routes of the backend network interface have the right route for Source Client.

### Question

**Do you have the NSG/UDR configured correctly on the backend pool of the consumer load balancer?**

### Options

- **Yes** → Go to: *Application Responding*
- **No** → Go to: *NSG and UDR Configuration*

---

### Step 24: Application Responding

### Support Engineer Solution

We recommend that you check whether your application is correctly configured to respond to the configured backend port.

To achieve this:

- On Windows, use this command: `netstat -ano | findstr LISTENING | findstr 80`.

- On Linux, use this command: `netstat -ano | grep LISTEN | grep tcp | grep 80`.

Make sure that the operating system firewall is allowing the destination port. On Windows use `wf.msc`, and on Linux use `iptables`.

If everything is configured correctly up to this point, we recommend consulting your network virtual appliance (NVA) vendor to determine if the NVA is blocking the connection.

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

We recommend that you check whether your application is correctly configured to respond to the configured backend port.

To achieve this:

On Windows, use this command: netstat -ano | findstr LISTENING | findstr 80

On Linux, use this command: netstat -ano | grep LISTEN | grep tcp | grep 80

Make sure that the operating system firewall is allowing the destination port. On Windows, use wf.msc, and on Linux, use iptables.

If everything is configured correctly up to this point, we recommend consulting your network virtual appliance (NVA) vendor to determine if the NVA is blocking the connection.

Best regards, 

---

### Step 25: NSG and UDR Configuration

### Support Engineer Solution

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

To resolve this issue, please add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

Best regards,

---

### Step 26: Gateway Probe Down NSG check

### Guidance

For the Load Balancer's health probe to mark up your instance, you must allow the IP address 168.63.129.16 in any Azure network security groups and local firewall policies. The AzureLoadBalancer service tag identifies this source IP address in your network security groups and permits health probe traffic by default. 

To learn more, see [What is IP address 168.63.129.16?](https://learn.microsoft.com/azure/virtual-network/what-is-ip-address-168-63-129-16)

### Question

**Is the network security group configuration for the backend pool appropriately set up?**

### Options

- **Yes** → Go to: *NVA OS is blocking health probe IP*
- **No** → Go to: *NSG and UDR Configuration Solution*

---

### Step 27: NSG and UDR Configuration Solution

### Support Engineer Solution

To resolve this issue, add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

To resolve this issue, please add a rule with a higher priority (lower number) to allow traffic from the AzureLoadBalancer service tag. 

See [Health probe source IP address](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview#probe-source-ip-address).

Best regards,

---

### Step 28: NVA OS is blocking health probe IP

### Support Engineer Solution

In order for load balancer health probes to succeed, the IP address 168.63.129.16 which is also denoted by the AzureLoadBalancer service tag must be allowed through all network security group rules.

If network security group rule are configured correctly to allow health probe, but connectivity issues still exist, we recommend that you check whether your NVA are configured to allow and respond appropriately to the health probes (protocol, port, and path) within the configured interval.

### Customer Solution

*Content type: MarkdownText*

Dear [Customer],

In order for load balancer health probes to succeed, the IP address 168.63.129.16, also denoted by the AzureLoadBalancer service tag, must be allowed through all network security group rules.

If network security group rules are correctly configured to allow the health probe but connectivity issues still exist, we recommend checking whether your NVA is configured to allow and respond appropriately to the health probes (protocol, port, and path) within the configured interval.

Best regards, 

---

### Step 29: Consumer LB Probe UP floating enabled NSG check

### Guidance

**Issue:** Data path issues may occur due to the path being blocked (NSGs, Firewalls) or if it's misrouted.

**Cause - NSG misconfiguration:** Since floating IP is enabled, you need to have NSG rule to allow the connection from client IP address to the frontend IP address of the load balancer. 

**Cause - UDR misconfiguration**: Confirm if the effective routes of the backend network interface have the right route for Source Client.

### Question

**Do you have the NSG/UDR configured correctly on the backend pool of the consumer load balancer?**

### Options

- **Yes** → Go to: *Application Responding*
- **No** → Go to: *Consumer LB probe UP floating ip enabled loopback*

---

### Step 30: Consumer LB probe UP floating ip enabled loopback

### Support Engineer Solution

**Issue:** Backend is not configured correctly for the Floating IP feature.

**Resolution:** Configure the guest OS for the virtual machine to receive all traffic bound for the frontend IP and port of the load balancer. Configuring the VM requires:

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

**Resolution:** Configure the guest OS for the virtual machine to receive all traffic bound for the frontend IP and port of the load balancer. Configuring the VM requires:

- Adding a loopback network interface

- Configuring the loopback with the frontend IP address of the load balancer

- Ensuring the system can send/receive packets on interfaces that don't have the IP address assigned to that interface.Windows systems require setting interfaces to use the "weak host" model. For Linux systems, this model is normally used by default.

- Configuring the host firewall to allow traffic on the frontend IP port.

Steps for [Windows:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#windows-server)

Steps for [Linux Ubuntu:](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-floating-ip#ubuntu)

Best regards,

---
