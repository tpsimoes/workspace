# Networking] Load Balancer - Configure load distribution

> **Product:** Load Balancer  
> **Solution ID:** 4b9d578a-3dc9-48ad-82fb-a8f310d14b6e  
> **Trigger words:** balancer, configure, distribution, load balancer, networking]

---

## Overview

This guide provides step-by-step troubleshooting for **Networking] Load Balancer - Configure load distribution** under **Load Balancer**.
 The original guided troubleshooter contains 12 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Check Scope ⭐ (First Step)

### Guidance

# Check if this TSG applies to the customer scenario
## Verify that the customer issues match this TSG
This TSG is specific to Azure Load Balancer distribution issues and configuration. It is applicable to the following support topics:

* Azure/Load Balancer/Configuration and Setup/Configure load distribution
* Azure/Load Balancer/Performance/Load distribution issues

**Note:** If your issue is not from the list above, you may use **Edit & Run Again** feature on the **ASC** to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results. 
### Recommended documents
* [Azure Load Balancer algorithm](https://learn.microsoft.com/en-us/azure/load-balancer/concepts)
* [Azure Load Balancer distribution modes](https://learn.microsoft.com/en-us/azure/load-balancer/distribution-mode-concepts)

### Question

**Is the customer having issues related to load balancer load distribution?**

### Options

- **Yes** → Go to: *Clarify problem statement*
- **No** → Go to: *This issue is outside the scope for this TSG*

---

### Step 2: Discussing distribution concepts with customer

### Support Engineer Solution

If the customer has additional questions after discussing the information from the previous step, use the public documentation to guide further discussions as necessary:

* [Azure Load Balancer algorithm](https://learn.microsoft.com/en-us/azure/load-balancer/concepts)
* [Azure Load Balancer distribution modes](https://learn.microsoft.com/en-us/azure/load-balancer/distribution-mode-concepts)
* [Azure Load Balancer portal settings](https://learn.microsoft.com/en-us/azure/load-balancer/manage?source=recommendations#add-load-balancing-rule)

If further assistance is still needed, reach out to SME's or TA's for more guidance.

Reference: [Teams Posting Guidelines](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/261526/Teams-Posting-Guidelines)

When all the customer queries are satisfied, proceed with the normal case confirmation and closure process.

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 3: Solution for Configuration Advisory

### Support Engineer Solution

If the customer has questions regarding how load balancer distribution works or how to configure it, use the following public documentation to guide the discussion:

* [Azure Load Balancer algorithm](https://learn.microsoft.com/en-us/azure/load-balancer/concepts)
* [Azure Load Balancer distribution modes](https://learn.microsoft.com/en-us/azure/load-balancer/distribution-mode-concepts)
* [Add load balancing rule](https://learn.microsoft.com/en-us/azure/load-balancer/manage?source=recommendations#add-load-balancing-rule)

### Customer Solution

*Content type: MarkdownText*

Hello [Customer],

Thank you for contacting us with your questions about configuring load distribution for Azure Load Balancer. Please refer to the following documentation for more information regarding load balancing methods and configuration:

* [Azure Load Balancer algorithm](https://learn.microsoft.com/en-us/azure/load-balancer/concepts)
* [Azure Load Balancer distribution modes](https://learn.microsoft.com/en-us/azure/load-balancer/distribution-mode-concepts)
* [Add load balancing rule](https://learn.microsoft.com/en-us/azure/load-balancer/manage?source=recommendations#add-load-balancing-rule)

Please let us know if you have specific questions or would like to schedule a call to discuss this further. 

Thank you,

---

### Step 4: Mitigated by changing distribution mode or application

### Support Engineer Solution

If the customer is able to resolve the issue by changing the distribution mode, continue following up with the customer as needed to address questions and drive case closure.

Use the public documentation to guide further discussions:

* [Azure Load Balancer algorithm](https://learn.microsoft.com/en-us/azure/load-balancer/concepts)
* [Azure Load Balancer distribution modes](https://learn.microsoft.com/en-us/azure/load-balancer/distribution-mode-concepts)
* [Azure Load Balancer portal settings](https://learn.microsoft.com/en-us/azure/load-balancer/manage?source=recommendations#add-load-balancing-rule)

For further assistance, reach out to SME's or TA's as needed.

Reference: [Teams Posting Guidelines](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/261526/Teams-Posting-Guidelines)

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 5: Gather more information for advanced troubleshooting

### Support Engineer Solution

Collect more information from the source VM and from the customer. Ask the customer to ensure they have continuous TCP pings running (Windows: psping, Linux: nping) if the load balancing rule is for the TCP protocol  or have continuous UDP attempts going until the resolution of the case. Ask the customer to collect packet captures. Create a DTM link for the customer. Ask the customer for concurrent packet captures from the source and destination VMs (all backend VMs) and upload the captures to DTM.

For more information on packet capture steps see the following references from the ANP wiki:

For Windows:

* [Netsh](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/138467/Netsh)
* [Pktmon](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/720781/Pktmon)

For Linux:

* [TCPdump](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/140089/TCPdump)

When you get the packet captures, check to determine if the source sent the TCP SYN packet and note the ephemeral port. Then check that one of the destinations got the inbound SYN from the client IP and ephemeral port previously noted. Check that the backend VM responded with a SYN/ACK. Lastly, check that the client VM received the SYN/ACK. If you need assistance, engage your TA via [Teams resource engagement recommendations](https://aka.ms/ANPTeamsPostingGuidelines) to reach out to SME resources in the [Load Balancer Teams Channel](https://teams.microsoft.com/l/channel/19%3ac5774cb5dd0649f9a68cc88872281084%40thread.skype/%255BMonConn%255D%2520Load%2520Balancer%2520(SLB)?groupId=c3e00ac7-3f76-4350-ba3b-e335a6bbbe21&tenantId=72f988bf-86f1-41af-91ab-2d7cd011db47)

### Customer Solution

*Content type: MarkdownText*

**If load balancing rule is TCP**

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reached a point in the troubleshooting process where we need additional information to further diagnose the connectivity issue. 

Please start continuous TCP pings (Windows: `psping -t loadBalancerFrontendIp:Port`, Linux: `nping --tcp -p [Port] -c 0 [loadBalancerFrontendIp]`) **until the resolution of the case** to prevent any troubleshooting delays. PSPing is available for download from https://docs.microsoft.com/en-us/sysinternals/downloads/psping. For Linux, consult your distribution documentation for installing the nping utility.

Please gather packet captures from on the source VM and the VMs in your backend pool simultaneously with the TCP pings running. Then send the set of files to us. This will help us determine the appropriate next steps for this case.

Best regards,

**If load balancing rule is UDP**

Dear Customer,

Thank you for contacting us about your load balancer backend pool connectivity issue. We have reached a point in the troubleshooting process where we need additional information to further diagnose the connectivity issue. 

Please sta

*(Content truncated — refer to original GT for full details)*

### Step 6: Clarify problem statement

### Guidance

Customers may be asking to help them understand and configure the distribution modes of an Azure Load Balancer. 

They may also be stating that they are having an issue with distribution not appearing to work as expected. For example, the customer may state that one backend node is receiving more requests than other backend nodes and are wondering why that may be happening.

## Recommended Steps

* Review the customer verbatim to understand the customer's ask.
* Locate the customer's load balancer in ASC. Try to determine from the verbatim what type of traffic and what the customer's potential data path may be. This should be either a public IP address in the case of external facing load balancers or a VNet IP, resource URI, or on-premises IP for internal load balancers. From the configuration data found in ASC and from what you have read from the customer verbatim, collect the following information to form a concise problem statement:

	1. Potential Client IP's (source):
	2. Load balanced frontend IP, port, and protocol (TCP or UDP - note: other protocols such as ICMP are not supported) that the client is connecting to (destination): 
	3. Load balanced rule the customer configured for the traffic pattern: 
	4. Probe configuration associated with the load balanced rule: 
	5. Load balancer SKU (standard or basic): 
	6. If intermittent/RCA request, date and time in UTC of the incident: 

### Question

**Is the customer requesting advisory on configuring load balancer distribution modes or is the customer requesting help with a load distribution problem?**

### Options

- **Customer requesting advisory for configuration** → Go to: *Solution for Configuration Advisory*
- **Customer states there is a problem with load distribution** → Go to: *Basic or Standard Load Balancer*

---

### Step 7: Inform customer connection counts are reasonably similar

### Guidance

If the SYN counts appear to have a reasonably similar distribution across the backend nodes, then the SLB is distributing connections as designed. Work with the customer to determine the nature of the traffic and what the intended outcome should be.

Many of these cases are opened because a customer sees an uneven load on their backend nodes (high resource consumption) and assumes that the load balancer is not distributing the traffic correctly. A common cause of this perception is that even though the connections are being equally distributed, the actual data flow per connection may be much higher for some connections. This can cause some nodes to have higher load due to higher workload of some individual connections. 

One thing to keep in mind here is that the load balancer can only influence distribution when an incoming SYN packet arrives. Flow count and bandwidth metrics do not necessarily always directly correlate to actual even distribution of connections.

Consider the following example:

- Client A connects to the VIP 
    - SYN packet come in, the SLB hashes and sends the connection to "backend A"
	- The TCP handshake completes, and a flow is created and maintained
- Client B connects to the VIP
	- SYN packet comes in, the SLB hashes and sends the connection to "backend B"
	- "backend B" sends a RST back (maybe because of a downstream application issue or an ACL)
	- A half-flow is initially created, but ends and is not maintained
- Client B then reconnects to the VIP
	- SYN packet comes in and this time gets distributed to "backend A"
	- If this connection is successful, then a flow is maintained 

So you now have 2 clients with active connections passing data back and forth to the same backend. At a glance, this looks like the SLB is not distributing the traffic evenly, when it really was the nature of the connections that defined how those connections occurred. 

That is just one example of how flow counts and bandwidth can have some discrepancy with actual connection distribution. What really matters is the incoming SYN distribution, since that is the only the SLB can directly influence. 

## Recommended Steps

* Discuss with the customer your findings of SYN packet counts and distribution. Be careful not to share screenshots of internal tools, however you can relay some of the information gathered (such as counts to each backend)
* Try to gather some details of what the expected application traffic should look like. For example, is it expected that some connection flows have higher demand than others?

### Question

**After discussing with the customer, was the cause of their reported issue discovered and understood?**

### Options

- **Yes** → Go to: *Discussing distribution concepts with customer*
- **No** → Go to: *Gather more information for advanced troubleshooting*

---

### Step 8: Connection counts are not similarly distributed

### Guidance

If the SYN counts show that one or several backend nodes are receiving significantly more connections than others in the pool, check the relevant load balancing rule configuration to see is session persistence is being used. 

## Recommended Steps

* In ASC, look at the load balancer: Properties > Load Balancing Rules. Under the relevant rule, look at the "Load Distribution" configuration. It will be either "Default", "SourceIP", or "SourceIPProtocol". This tells us what distribution mode is configured.
* If the configuration is anything other than "Default", keep in mind that the incoming client IP will affect load distribution. For example, if clients are coming in through a proxy that has one IP address, multiple clients behind that proxy, will appear to be coming from the same source IP. This will lead to uneven load distribution. Reference: [Azure Load Balancer distribution modes#use-cases](https://learn.microsoft.com/en-us/azure/load-balancer/distribution-mode-concepts#use-cases)
* Discuss with the customer to better understand the need for the use of session persistence and also determine if multiple clients are coming from the same source IP address (such as if they are behind a proxy).
* If the customer has session persistence configured, but the application does not require it, it is recommended to change to default (hash based) distribution and test

### Question

**Based on the gathered information and discussions with the customer, were you able to determine a cause and mitigation strategy for the uneven traffic distribution?**

### Options

- **The customer is able to mitigate by changing the session persistence to default or by other application or connectivity path changes** → Go to: *Mitigated by changing distribution mode or application*
- **The session persistence is already configured to default or there are no clear details for the traffic traversing the load balancer** → Go to: *Gather more information for advanced troubleshooting*

---

### Step 9: This issue is outside the scope for this TSG

### Support Engineer Solution

Update the support topic to match the customer issue in ASC 'Edit and Run Again' and check for a related TSG.

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 10: Basic or Standard Load Balancer

### Content

This step uses automation to try and determine the SKU of the load balancer object associated with the case. 

If the load balancer object being investigated is different than the object associated with the case, then use ASC and the data previously gathered to manually determine if the load balancer is Basic or Standard SKU.

---

### Step 11: Manual Method to Determine Connection Distribution

### Guidance

### Manual Method using Jarvis Logging to Determine Connection Distribution (Azure Basic and Standard Load Balancer)

We can use this method to gather connection counts for Basic load balancers or to verify the data from the Bandwidth dashboard for Standard SKU load balancers. This data will allow us to evaluate if connection counts are vastly different between the customer backend instances.

The overview of the basic steps are below, however for more details with screenshots please follow the [How to Identify Traffic Load Distribution on Basic and Standard ILB](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/281525/How-to-Identify-Traffic-Load-Distribution-on-Basic-and-Standard-ILB) wiki article.

1. First of all we need to identify the MAC Address of one of the VMs in the LB Backend Pool, you can get this info from ASC going to Microsoft.Compute - VirtualMachines - VM Name - Under Container Settings

2. Take note of the MAC Address and run this query - [https://portal.microsoftgeneva.com/49C8ACE2](https://portal.microsoftgeneva.com/6CA44898)

3. In Filtering Conditions use "**VMPortName**" with the MAC you just obtained above with "**External_<MACaddress>**" for example: 

>> *Filtering Conditions*

>> *VmPortName | contains | External_000D3AACD29D*

4. From the results of running the query at point 2, please note the VIP and DC (if the DCs for the VMs are different, please add both in the Scoping conditions for the next query)

5. Now run this query - https://portal.microsoftgeneva.com/49C8ACE2 
6. This time Scoping Conditions and Filtering Conditions need to be populated with DC and VIP above:

>> *Scoping Conditions*

>> *Tenant | == | <DCname>*

>> *Filtering Conditions*

>> *Vip | Contains | <VIP>*

7. Traffic Load Distribution will be based on results value "**SynAckSent**"

8. You can also click on the "Chart" and obtain a graph view

### Question

**Does the traffic appear to be reasonably equally distributed?**

### Options

- **Yes** → Go to: *Inform customer connection counts are reasonably similar*
- **No** → Go to: *Connection counts are not similarly distributed*

---

### Step 12: SLB Bandwidth Dashboard to Determine Distribution

### Guidance

### Using SLB Bandwidth Usage Dashboard to Determine Connection Distribution (Azure Standard Load Balancer SKU only)

In a Standard SKU load balancer, we can use the "SynPacketCount" metrics to determine how new connections are being distributed to the backend pool members.

1. In ASC, go to the "Diagnostics" tab of the load balancer. In the "Bandwidth Metrics" section, click the link to open the Bandwidth Metrics Dashboard that is associated to the frontend IP and port that the customer is concerned about. _Note: There will be a link for each VIP and port configured on the load balancer. If the ASC link doesn't work use this sample link: [bandwidth usage dashboard](https://portal.microsoftgeneva.com/s/23857F89?overrides=%5B%7B%22query%22%3A%22//dataSources%22%2C%22key%22%3A%22account%22%2C%22replacement%22%3A%22slbhpeastus%22%7D%2C%7B%22query%22%3A%22//*%5Bid%3D%27VipAddress%27%5D%22%2C%22key%22%3A%22value%22%2C%22replacement%22%3A%2240.71.235.233%22%7D%2C%7B%22query%22%3A%22//*%5Bid%3D%27VipPort%27%5D%22%2C%22key%22%3A%22value%22%2C%22replacement%22%3A%22%22%7D%2C%7B%22query%22%3A%22//*%5Bid%3D%27PublicIpArmIdOrILBPA%27%5D%22%2C%22key%22%3A%22value%22%2C%22replacement%22%3A%22%22%7D%5D%20)
 
2. Find the "**SynPacketCount (pps Per Protocol,FEIP : FEPort ->Adapter@Host,Connection,Direction)**" graph. This graph will break down SYN packets (indicating new TCP connections) by backend virtual NIC MAC address and PA. We will want to focus on the "In" traffic.
 
3. The "Show summary" option can be used to get raw count numbers if the graph isn't clear. Keep in mind the time frame of the dashboard. Generally, the shortest time frame that covers the issue should be used to keep the data concise.

If results are unclear, or you would like to confirm findings a different way, see the [ANP wiki for another method to determine connection counts](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/281525/How-to-Identify-Traffic-Load-Distribution-on-Standard-ILB?anchor=manual-method-using-jarvis-logging-(azure-basic-and-standard-load-balancer))

### Question

**Does the traffic appear to be reasonably equally distributed?**

### Options

- **Yes** → Go to: *Inform customer connection counts are reasonably similar*
- **No** → Go to: *Connection counts are not similarly distributed*

---
