# Troubleshoot Azure Load Balancer uneven traffic distribution

> **Product:** Load Balancer  
> **Solution ID:** ca1c2d47-131f-40cf-925a-57cd3579d8bf  
> **Trigger words:** balancer, distribution, load balancer, traffic, troubleshoot, uneven

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot Azure Load Balancer uneven traffic distribution** under **Load Balancer**.
 The original guided troubleshooter contains 26 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Start options ⭐ (First Step)

### Guidance

This guide is for troubleshooting Azure Load Balancer uneven load distribution.

If your Load Balancer has another issue, select it from the list. 

### Question

**What do you need help with?**

### Options

- **I have questions about how Azure Load Balancer distribution works and need guidance.** → Go to: *Advisory documents*
- **I'm facing issues due to incorrect load distribution in Azure Load Balancer and need help troubleshooting.** → Go to: *SKU selection*
- **I can't connect to resources behind Azure Load Balancer through a Virtual IP.** → Go to: *e3c6812c-4c20-4903-b542-08a19a17aa49*
- **I need assistance upgrading from Basic to Standard Load Balancer.** → Go to: *235ad95c-9d36-4a21-a790-0d2364ee5b8d*
- **I can't connect to the internet from backend resources of a Load Balancer.** → Go to: *544906a8-a2db-4da3-8788-db27a954dd6d*
- **Unhealthy backend/health probe failures** → Go to: *5822ba65-5b5a-4583-a7fe-c75ed3a3bc0d*
- **Inbound connectivity failures using Gateway Load Balancer** → Go to: *ce0b18c3-025d-4c9a-87ed-137480eac3e2*
- **Inbound connectivity issues using Global Load Balancer** → Go to: *ccaeb9da-acc8-408f-abe1-afbfabd72f98*

---

### Step 2: Advisory documents

### Support Engineer Solution

If you're looking to understand how Azure Load Balancer distributes traffic or how to configure it effectively, the following Microsoft Learn documentation provides detailed guidance:

- [Azure Load Balancer Concepts](https://learn.microsoft.com/en-us/azure/load-balancer) including how it works, the types of load balancers available (public and internal), and key components like frontend IPs, backend pools, health probes, and load balancing rules.

- [Distribution-mode-concepts](https://learn.microsoft.com/en-us/azure/load-balancer/distribution-mode-concepts), such as 5-tuple and 3-tuple hashing. This guide explains how traffic is distributed across backend instances and how to choose the right mode for your application.

- [load-balancer-best-practices](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-best-practices) It covers topics like high availability, performance tuning, monitoring, and troubleshooting to help you get the most out of your deployment.

### Customer Solution

*Content type: MarkdownText*

If you're looking to understand how Azure Load Balancer distributes traffic or how to configure it effectively, the following Microsoft Learn documentation provides detailed guidance:

- [Azure Load Balancer concepts](https://learn.microsoft.com/azure/load-balancer) including how it works, the types of load balancers available (public and internal), and key components like frontend IPs, backend pools, health probes, and load balancing rules.

- [Distribution mode concepts](https://learn.microsoft.com/azure/load-balancer/distribution-mode-concepts), such as 5-tuple and 3-tuple hashing. This guide explains how traffic is distributed across backend instances and how to choose the right mode for your application.

- [Load balancer best practices](https://learn.microsoft.com/azure/load-balancer/load-balancer-best-practices) It covers topics like high availability, performance tuning, monitoring, and troubleshooting to help you get the most out of your deployment.

---

### Step 3: SKU selection

### Guidance

Select the appropriate SKU of the load balancer you are observing issues with regarding load distribution.

### Question

**What is the SKU of the Load Balancer?**

### Options

- **Basic SKU** → Go to: *Basic SKU retirement*
- **Standard SKU** → Go to: *Standard SKU troubleshooting start*

---

### Step 4: Basic SKU retirement

### Guidance

On September 30, 2025, Basic Load Balancer will be retired. We recommend that you move to the Standard SKU and then see if you still observe any issues. For more information, see the [official announcement](https://azure.microsoft.com/updates/azure-basic-load-balancer-will-be-retired-on-30-september-2025-upgrade-to-standard-load-balancer/). If you're currently using Basic Load Balancer, make sure to upgrade to Standard Load Balancer prior to the retirement date. This article will help guide you through the upgrade process.

[Upgrading from Basic Load Balancer - Guidance](https://learn.microsoft.com/azure/load-balancer/load-balancer-basic-upgrade-guidance)

### Question

**Do you require further assistance with upgrading from Basic to Standard SKU of the load balancer?**

### Options

- **Yes** → Go to: *Upgrade to Standard insight*
- **No** → Go to: *End of troubleshooter*

---

### Step 5: End of troubleshooter

### Support Engineer Solution

You have reached the end of this troubleshooter. 

We hope the steps provided helped clarify or resolve your issue. However, we understand that not all problems can be fully addressed through automated guidance. If you're still experiencing difficulties or need more personalised assistance, we’re here to help.

Please consider raising a support case so our dedicated team can work with you directly to find a resolution tailored to your situation.

Thank you for your patience, and we appreciate the opportunity to support you.

### Customer Solution

*Content type: MarkdownText*

You've reached the end of this troubleshooter. 

We hope the steps provided helped clarify or resolve your issue. However, we understand that not all problems can be fully addressed through automated guidance. If you're still experiencing difficulties or need more personalized assistance, we’re here to help.

Consider raising a support case so our dedicated team can work with you directly to find a resolution tailored to your situation.

Thank you for your patience, and we appreciate the opportunity to support you.

---

### Step 6: Standard SKU troubleshooting start

### Guidance

### Check backend virtual machine health for optimal load distribution

Azure Load Balancer uses a tuple-based hashing algorithm to distribute traffic across backend pool members. The effectiveness of this distribution depends on several factors:

**Session persistence:** The setting you choose (None, Client IP, or Client IP and Protocol) influences how traffic is routed.

**Application behavior:** If your application reuses the same TCP/UDP tuple (e.g., long-lived connections), it may result in uneven distribution.

**Backend virtual machine health:** If some backend virtual machines are unhealthy or not responding to health probes, the load balancer will stop sending traffic to them. This can lead to perceived imbalance in traffic distribution.

We recommend verifying the health status of your backend virtual machines. Ensuring all instances are healthy and responsive to probes is crucial for consistent and balanced traffic flow.

### Question

**Are all backend pool members healthy?**

### Options

- **Yes** → Go to: *What type of load distribution is expected*
- **No** → Go to: *Incorrect distribution due to backend unhealthy*

---

### Step 7: Incorrect distribution due to backend unhealthy

### Guidance

In the **Metrics** section, check the metric **Health Probe Status** and verify if all the backend IP configurations under the relevant backend pool are in a healthy state.

Incorrect load distribution is expected when some backend pool members are unhealthy. The load balancer marks these members as unhealthy due to failed health probes and stops sending traffic to those IP configurations. As a result, all traffic is shifted to the healthy members.

### Question

**Do you need help identifying why the backend pool members are reporting unhealthy?**

### Options

- **Yes** → Go to: *5822ba65-5b5a-4583-a7fe-c75ed3a3bc0d*
- **No** → Go to: *End of troubleshooter*

---

### Step 8: What type of load distribution is expected

### Guidance

Select an option.

### Question

**What type of load balancing scenario do you need help with?**

### Options

- **I'm expecting 1:1 mapping in terms of source and destination where each source should map to one backend pool member.** → Go to: *Check if inbound NAT rules are present*
- **I'm expecting equal or near-equal load distribution.** → Go to: *Equal distribution troubleshooting start*

---

### Step 9: Check if inbound NAT rules are present

### Guidance

Validate whether you are already utilizing inbound NAT rules to achieve 1:1 mapping.

### Question

**Are you using inbound NAT rules?**

### Options

- **Yes** → Go to: *Using NAT rules already*
- **No** → Go to: *Not using NAT rules insight*

---

### Step 10: Not using NAT rules insight

### Support Engineer Solution

Inbound Network Address Translation (NAT) rules allow you to provide direct, one-to-one mapping between a specific source (client or service) and a designated backend virtual machine (VM). This setup is useful when you need direct access to individual VMs, such as for RDP or SSH.

### Key considerations

**No automatic failover**

If the backend VM targeted by the NAT rule becomes unhealthy or unavailable, Azure Load Balancer does not automatically redirect traffic to another healthy VM. The source will lose connectivity until the original VM is restored.

NAT rules do not support automatic failover or load distribution across multiple backend VMs.

**Scalability challenges**

In scale-out scenarios where backend VMs are dynamically added or removed, managing NAT rules becomes complex. Each new VM requires manual configuration of NAT rules and port mappings. This increases operational overhead and the risk of configuration errors.

NAT rules are best suited for static environments with a small, fixed number of backend VMs where scaling is infrequent or not required.

**Session persistence limitations**

While session persistence (sticky sessions) helps maintain continuity in load-balanced scenarios, it's not applicable to NAT rules.

Even if session persistence is enabled, requests from the same source may still be routed to different backend VMs. This can result in inconsistent behavior for applications expecting a persistent connection to a specific VM.

If your application requires high availability and automatic failover, consider using load balancing rules instead of NAT rules. Load balancing rules are designed to:

- Distribute traffic across multiple backend VMs.

- Support session persistence configurations.

- Provide better resilience and scalability.

### Customer Solution

*Content type: MarkdownText*

Inbound Network Address Translation (NAT) rules allow you to provide direct, one-to-one mapping between a specific source (client or service) and a designated backend virtual machine (VM). This setup is useful when you need direct access to individual VMs, such as for RDP or SSH.

### Key considerations

**No automatic failover**

If the backend VM targeted by the NAT rule becomes unhealthy or unavailable, Azure Load Balancer does not automatically redirect traffic to another healthy VM. The source will lose connectivity until the original VM is restored.

NAT rules do not support automatic failover or load distribution across multiple backend VMs.

**Scalability challenges**

In scale-out scenarios where backend VMs are dynamically added or removed, managing NAT rules becomes complex. Each new VM requires manual configuration of NAT rules and port mappings. This increases operational overhead and the risk of configuration errors.

NAT rules are best suited for static environments with a small, fixed number of backend VMs where scaling is infrequent or not required.

**Session persistence limitations**

Wh

*(Content truncated — refer to original GT for full details)*

### Step 11: Using NAT rules already

### Guidance

Validate if the backend virtual machine for the dedicated NAT rule is healthy.

### Question

**Is the backend showing as unhealthy in the health probe metrics for any backend virtual machine?**

### Options

- **Yes** → Go to: *5822ba65-5b5a-4583-a7fe-c75ed3a3bc0d*
- **No** → Go to: *Packet captures routine start*

---

### Step 12: Packet captures routine start

### Guidance

We've reached a point in the troubleshooting process where we need additional information to further diagnose the connectivity issue.

In order to collect packet captures for further troubleshooting, you'll need to run a connectivity test to diagnose the distribution.

---

**TCP traffic generation:**

**Continuous TCP traffic generation for Windows and Linux**

---

### Step 1: Install the tools

**On Windows (psping)**

1. Download [PsTools](https://learn.microsoft.com/sysinternals/downloads/pstools) from the official Microsoft Sysinternals page.

2. Extract the ZIP file to a folder.

3. Open Command Prompt and navigate to the folder containing psping.exe.

**On Linux (TCPping)**

Visit [tcping.org](https://www.tcping.org/) for installation instructions.

Alternatively, install TCPping by using a package manager if available:

```

sudo apt install tcping  # For Debian/Ubuntu (if available)

```

### Step 2: Run TCP traffic

**On Windows**

Use the following command to send continuous TCP traffic:

```

psping -n 0 -h 5 <destination_ip>:<port>

```

Explanation of flags:

```

-n 0: Run indefinitely (until manually stopped)

-h 5: Display histogram every 5 seconds

<destination_ip>:<port>: Target IP and port (e.g., 10.0.0.5:443)

```

**On Linux**

Use the following command to send TCP pings:

```

tcping -i 1 <destination_ip> <port>

```

### Step 3: Verify connectivity

- Ensure the destination IP and port are reachable.

- Confirm firewalls allow TCP traffic on the specified port.

- Monitor output for latency, dropped packets, and connection stability.

- Use **Ctrl+C** to stop the traffic test.

---

**UDP traffic generation:**

**Continuous UDP traffic generation for Windows and Linux**

---

### Step 1: Install iperf3

**On Windows**

1. Download iperf3 from [iperf.fr](https://iperf.fr).

2. Extract the ZIP file to a folder.

3. Open Command Prompt and navigate to the folder containing iperf3.exe.

**On Linux**

Run the following command in the terminal:

```

sudo apt install iperf3  # For Debian/Ubuntu

```

### Step 2: Start the server

```

iperf3 -s

```

This starts iperf3 in server mode, listening on port 5201 by default.

### Step 3: Run the client

On the sender machine, execute the following command to start sending continuous UDP traffic:

```

iperf3 -c <destination_ip> -u -b 10M -t 0

```

**Explanation of flags**

```

-c <destination_ip>: IP address of the server machine.

-u: Use UDP protocol.

-b 10M: Bandwidth (e.g., 10 Mbps). You can adjust this value.

-t 0: Run indefinitely (until manually stopped).

```

### Step 4: Verify connectivity

- Ensure both machines are on the same network or have proper routing.

- Make sure firewalls allow traffic on port 5201.

- Confirm that the server is running before starting the client.

- Monitor the output for metrics like packet loss, jitter, and latency.

To stop the traffic, press **Ctrl+C** in the terminal or command prompt.

### Question

**Do you have traffic 

*(Content truncated — refer to original GT for full details)*

### Step 13: End of packet capture routine

### Support Engineer Solution

**You need to further collect packet captures on both the source/client and destination (backend pool member) simultaneously.**

## Windows:

[Netsh](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/138467/Netsh)

[Pktmon](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/720781/Pktmon)

Common Netsh commands to collect captures on windows:

Run the following command from an

elevated command prompt to start a packet capture:

```

netsh trace start capture=yes

packettruncatebytes=512 tracefile=C:\trace1.etl maxsize=512

filemode=circular overwrite=yes report=no

```

 

Run the following command when you want to stop the capture:

```

netsh trace stop

```

You can also use tools like [Wireshark](https://www.wireshark.org/download.html)/[Netmon](https://www.microsoft.com/en-in/download/details.aspx?id=4865&msockid=17b8263405c268ff19133247046f69b9) using GUI to collect captures.

## Linux:

[TCPdump](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/140089/TCPdump)

Common TCP Dump Command to collect capture:

```

tcpdump -i any -s0 -w /tmp/capture.cap

```

Once you’ve completed the connectivity test and collected the relevant data, we recommend opening a support case with us to continue troubleshooting the issue.

Please include the packet capture and test results when submitting the case. This information will help our support engineers analyse the traffic patterns and determine the root cause of the uneven load distribution across your backend pool.

We appreciate your cooperation and look forward to assisting you further.

### Customer Solution

*Content type: MarkdownText*

**You need to collect packet captures on both the source/client and destination (backend pool member) simultaneously.**

For Windows:

- [Netsh](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/138467/Netsh)

- [Pktmon](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/720781/Pktmon)

Common Netsh commands to collect captures on Windows:

Run the following command from an elevated command prompt to start a packet capture:

```

netsh trace start capture=yes

packettruncatebytes=512 tracefile=C:\trace1.etl maxsize=512

filemode=circular overwrite=yes report=no

```

 

Run the following command when you want to stop the capture:

`netsh trace stop`

You can also use tools like [Wireshark](https://www.wireshark.org/download.html) or  [Netmon](https://www.microsoft.com/download/details.aspx?id=4865&msockid=17b8263405c268ff19133247046f69b9) with a GUI to collect captures.

For Linux:

- [TCPdump](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/140089/TCPdump)

TCP dump command to collect capture:

`tcpdump -i any -s0 -w /tmp/capture.cap`

Once you’ve completed the connectivity test and collected the relevant data, we recommend opening a support case with us to continue troubleshooting the issue.

Inclu

*(Content truncated — refer to original GT for full details)*

### Step 14: Equal distribution troubleshooting start

### Guidance

Azure Load Balancer operates at Layer 4 (Transport Layer) and uses a five-tuple hashing algorithm to distribute incoming TCP/UDP traffic. This algorithm considers:

- Source IP address

- Source port

- Destination IP address

- Destination port

- Protocol (TCP/UDP)

This method ensures traffic is routed based on connection characteristics, without inspecting or modifying application-layer data such as HTTP headers or TLS handshakes.

**TLS termination:**

Azure Load Balancer does not offload TLS. Encryption and decryption are handled entirely by the backend virtual machines (VMs), enabling secure, end-to-end encrypted connections.

**Backend pool capacity:**

The load balancer’s capacity depends on the number and size of backend VMs. Only VMs that pass health probe checks are eligible to receive new traffic.

**Source IP preservation:**

Responses from backend VMs retain the original source IP, supporting scenarios that require IP-based logic or logging.

**Important note on load distribution:**

Azure Load Balancer does not use a round-robin algorithm. Uneven traffic distribution (e.g., not 50/50 across two VMs) is expected behavior due to:

- The nature of five-tuple hashing

- Long-lived or reused client connections

- Health probe status of backend VMs

- Lack of session persistence

This design ensures consistent routing and reliable performance but may result in perceived imbalance under certain conditions.

### Question

**With the provided explanation on load distribution, do you need further help with troubleshooting distribution?**

### Options

- **My load distribution observation is not 50-50 but within acceptable limit.** → Go to: *End of troubleshooter*
- **My load distribution observation is not 50-50. I understand it should not be in round-robin fashion but the distribution is still unacceptable and all available backend pool instances are supposed to receive and respond to traffic.** → Go to: *Identification of uneven load distribution*

---

### Step 15: Identification of uneven load distribution

### Guidance

Select how you are identifying the uneven load distribution.

### Question

**How are you identifying that the load balancing distribution is uneven?**

### Options

- **I'm using the Insights pane available on the Load Balancer resource, which displays differences in inbound and outbound flows across the available backend instances.** → Go to: *Session persistence check*
- **I'm using a custom application software or another method to determine the uneven distribution.** → Go to: *Custom software distribution insight*

---

### Step 16: Custom software distribution insight

### Support Engineer Solution

Go to Insights blade on the load balancer resource and Click on the "View detailed metrics" > click on the "Flow Distribution" column and check per backend inbound and outbound flows to determine the exact difference between the flows load balanced across each backend member.

This page is intended to help customers visualize and manage the number of flows their backend VMs and VMSS instances are receiving and producing.

See the number of inbound and outbound flows and creation rate for each VM and VMSS instance to ensure the number of flows is not approaching the [per VM flow limit](https://learn.microsoft.com/azure/virtual-network/virtual-machine-network-throughput?WT.mc_id=Portal-fx#flow-limits-and-recommendations)

If approaching the flow limit, you consider scaling out to more instances in your backend pool

Use the inbound flows to visualize the load distribution of your load balancer

Use the outbound flows to determine if the processes running within your VM are creating significant outbound connections

Use the network throughput to see if there are individual flows that are transmitting significantly larger than average data throughput

### Customer Solution

*Content type: MarkdownText*

Go to the **Insights** pane on the load balancer resource and select **View detailed metrics**. Select the **Flow Distribution** column and check per backend inbound and outbound flows to determine the exact difference between the flows load balanced across each backend member.

This page is intended to help you visualize and manage the number of flows your backend VMs and VMSS instances are receiving and producing.

See the number of inbound and outbound flows and the creation rate for each VM and VMSS instance to ensure the number of flows is not approaching the [per-VM flow limit](https://learn.microsoft.com/azure/virtual-network/virtual-machine-network-throughput?WT.mc_id=Portal-fx#flow-limits-and-recommendations).

If you're approaching the flow limit, consider scaling out to more instances in your backend pool.

Use the inbound flows to visualize the load distribution of your load balancer.

Use the outbound flows to determine if the processes running within your VM are creating significant outbound connections.

Use the network throughput to see if there are individual flows that are transmitting significantly larger than average data throughput.

---

### Step 17: Session persistence check

### Guidance

Session persistence specifies that traffic from a client should be handled by the same virtual machine in the backend pool for the duration of a session.

Select appropriate option from above as per your config of load balancing rule.

### Question

**Which option of session persistence is being used in the load balancer configuration?**

### Options

- **None (default persistence) – Successive requests from the same source can be handled by any backend pool member. This is based on 5-tuple hashing (source and destination IP, port, and protocol).** → Go to: *Protocol check TCP or UDP*
- **Source IP – Successive requests from the same source will be handled by the same backend pool member where the initial request was routed, since this uses 2-tuple hashing where only source and destination IPs are used for persistence.** → Go to: *2 or 3 tuple insight*
- **Source IP and protocol – Successive requests from the same source IP with the same protocol will be handled by the same backend pool member.** → Go to: *2 or 3 tuple insight*

---

### Step 18: 2 or 3 tuple insight

### Support Engineer Solution

### Session persistence and load distribution in Azure Load Balancer

Azure Load Balancer supports different session persistence modes that influence how traffic is distributed across backend instances.

**Using 2-tuple or 3-tuple session persistence**

When session persistence is set to **Client IP (2-tuple)** or **Client IP and Protocol (3-tuple)**, requests from the same source are consistently handled by the same backend instance—as long as the hash remains unchanged.

This can result in uneven load distribution, especially when multiple requests originate from the same client.

**Achieving balanced load distribution**

If your goal is to distribute traffic evenly across all available backend instances—particularly when simultaneous requests originate from the same source—we recommend setting session persistence to **None**.

This enables 5-tuple hashing, which considers:

- Source IP  

- Source port  

- Destination IP  

- Destination port  

- Protocol (TCP/UDP)

This approach allows for more dynamic and balanced traffic routing.

### Resources

[Session persistence and distribution mode in Azure Load Balancer](https://learn.microsoft.com/azure/load-balancer/distribution-mode-concepts#session-persistence)

### Customer Solution

*Content type: MarkdownText*

### Session persistence and load distribution in Azure Load Balancer

Azure Load Balancer supports different session persistence modes that influence how traffic is distributed across backend instances.

**Using 2-tuple or 3-tuple session persistence**

When session persistence is set to **Client IP (2-tuple)** or **Client IP and Protocol (3-tuple)**, requests from the same source are consistently handled by the same backend instance—as long as the hash remains unchanged.

This can result in uneven load distribution, especially when multiple requests originate from the same client.

**Achieving balanced load distribution**

If your goal is to distribute traffic evenly across all available backend instances—particularly when simultaneous requests originate from the same source—we recommend setting session persistence to **None**.

This enables 5-tuple hashing, which considers:

- Source IP  

- Source port  

- Destination IP  

- Destination port  

- Protocol (TCP/UDP)

This approach allows for more dynamic and balanced traffic routing.

### Resources

[Session persistence and distribution mode in Azure Load Balancer](https://learn.microsoft.com/azure/load-balancer/distribution-mode-concepts#session-persistence)

---

### Step 19: Protocol check TCP or UDP

### Guidance

### TCP and UDP considerations in Azure Load Balancer

**TCP considerations**

- TCP connections are stateful and often long-lived.

- Applications that reuse the same TCP connection may result in traffic concentrating on a single backend virtual machine (VM).

- This behavior is expected and can lead to uneven traffic distribution, depending on how the application initiates and maintains connections.

**UDP considerations**

- UDP is stateless and connectionless.

- Traffic distribution may vary depending on how the application generates UDP packets.

- Since each packet is treated independently, distribution can appear more random, but it still follows the hash-based distribution logic of the Azure Load Balancer.

- Session persistence is not guaranteed for UDP flows. When backend pool membership changes (e.g., VM added or removed), existing UDP flows may be rehashed and redirected to different backend VMs—even if the original VM remains healthy.

- This behavior is by design and differs from TCP, which maintains session affinity.

- Applications relying on consistent backend targeting for UDP should implement their own logic to handle rerouting or use additional mechanisms like custom health probes or connection tracking.

**Note:** Azure Load Balancer does *not* use round-robin or queue-based distribution. Only healthy backend VMs (as determined by health probes) receive new traffic.

### Resources

[Azure Load Balancer distribution mode](https://learn.microsoft.com/en-in/azure/load-balancer/distribution-mode-concepts)

### Question

**Which type of protocol is being used when the traffic with uneven distribution is sent through the load balancer in question?**

### Options

- **TCP** → Go to: *Long lived session check*
- **UDP** → Go to: *NVA check*

---

### Step 20: Long lived session check

### Guidance

Validate whether you send the majority of traffic over a long-lived TCP session.

### Question

**Are you using long-lived TCP sessions within the application that generate a heavy load of traffic within a single 5-tuple connection?**

### Options

- **Yes** → Go to: *Long lived expected behavior*
- **No** → Go to: *Multiple sources sending traffic to backend*

---

### Step 21: Long lived expected behavior

### Guidance

There are scenarios where a long-lived single TCP session generates a heavy amount of load within that connection instead of using another 5-tuple for newly generated traffic. In these cases, you may see the majority of traffic going to a single backend member since the load balancer distributes traffic based on the number of SYN packets received, not on the total amount of traffic sent in terms of bandwidth or flow count metrics.

### Question

**Does the information provided in this step help answer your queries?**

### Options

- **Yes** → Go to: *End of troubleshooter*
- **No** → Go to: *Packet captures routine start*

---

### Step 22: Multiple sources sending traffic to backend

### Guidance

Validate whether your backend virtual machine is receiving traffic from multiple sources.

### Question

**Are your backend virtual machines receiving traffic only from the load balancer?**

### Options

- **Yes** → Go to: *NVA check*
- **No** → Go to: *Expected behavior with traffic from multiple sources*

---

### Step 23: Expected behavior with traffic from multiple sources

### Support Engineer Solution

If a backend virtual machine (VM) is receiving traffic from multiple sources—not just from Azure Load Balancer—it’s possible to observe uneven traffic distribution in its metrics. This behaviour is expected because the VM may be handling:

Traffic routed through Azure Load Balancer

Direct traffic from other services or clients

Internal service-to-service communication

As a result, the overall traffic shown in the VM’s metrics reflects all incoming connections, not just those managed by the Load Balancer. This can lead to the perception of imbalance, even when Load Balancer is functioning as designed.

### Customer Solution

*Content type: MarkdownText*

If a backend virtual machine (VM) is receiving traffic from multiple sources—not just from Azure Load Balancer—it’s possible to observe uneven traffic distribution in its metrics. This behavior is expected because the VM may be handling:

- Traffic routed through Azure Load Balancer

- Direct traffic from other services or clients

- Internal service-to-service communication

As a result, the overall traffic shown in the VM’s metrics reflects all incoming connections, not just those managed by the load balancer. This can lead to the perception of imbalance, even when the load balancer is functioning as designed.

---

### Step 24: NVA check

### Guidance

Validate whether you have any additional hops, such as an NVA, in the traffic path or in the backend pool of the load balancer behind which you have your actual backend that is experiencing uneven distribution.

This can occur for both TCP and UDP traffic.

### Question

**Do you have any NVA devices in the backend pool that are sending traffic to other destination VMs in the backend, causing uneven distribution at the end destination?**

### Options

- **Yes** → Go to: *Removal of NVA*
- **No** → Go to: *Packet captures routine start*

---

### Step 25: Removal of NVA

### Guidance

To accurately assess Azure Load Balancer’s traffic distribution, we recommend temporarily removing the network virtual appliance (NVA) from the traffic path.

Azure Load Balancer distributes traffic only up to the backend virtual machines (VMs) in its pool. It does not control or influence how traffic is forwarded beyond the backend VMs. If an NVA is present after the load balancer, it may alter or redirect traffic, making it difficult to validate the load balancer’s distribution behavior.

### Question

**Did removing the additional hop help you achieve correct distribution?**

### Options

- **Yes** → Go to: *End of troubleshooter*
- **No** → Go to: *Packet captures routine start*

---

### Step 26: Upgrade to Standard insight

### Support Engineer Solution

On September 30, 2025, Basic Load Balancer will be retired. For more information, see the [official announcement](https://azure.microsoft.com/en-us/updates?id=azure-basic-load-balancer-will-be-retired-on-30-september-2025-upgrade-to-standard-load-balancer). If you are currently using Basic Load Balancer, make sure to upgrade to Standard Load Balancer prior to the retirement date. This article will help guide you through the upgrade process.

Refer the following doc for upgrading from basic to standard sku:

[load-balancer-basic-upgrade-guidance](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-basic-upgrade-guidance)

### Customer Solution

*Content type: MarkdownText*

On September 30, 2025, Basic Load Balancer will be retired. For more information, see the [official announcement](https://azure.microsoft.com/updates?id=azure-basic-load-balancer-will-be-retired-on-30-september-2025-upgrade-to-standard-load-balancer). 

If you're currently using Basic Load Balancer, make sure to upgrade to Standard Load Balancer prior to the retirement date.

See [Upgrading from Basic Load Balancer - Guidance](https://learn.microsoft.com/azure/load-balancer/load-balancer-basic-upgrade-guidance) for more information.

---
