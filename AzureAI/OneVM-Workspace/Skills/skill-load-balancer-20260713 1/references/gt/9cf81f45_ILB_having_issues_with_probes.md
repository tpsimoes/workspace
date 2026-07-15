# ILB having issues with probes.

> **Product:** Load Balancer  
> **Solution ID:** 9cf81f45-e79b-4624-9033-886297385d46  
> **Trigger words:** having, load balancer, probes.

---

## Overview

This guide provides step-by-step troubleshooting for **ILB having issues with probes.** under **Load Balancer**.
 The original guided troubleshooter contains 16 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: This TSG is when NVA devices are not responding to Azure LB ⭐ (First Step)

### Guidance

This TSG is when NVA devices are not responding to Azure load balancers.

First thing to do is to verify that the Backend VM NVA is provisioned and running state.

You can check the status by following the steps below:

* Go into ASC load balancer, see the backend pool and click the NIC associated to the backend. 

* This will open the NIC properties, from there click the virtual machine attached.

* Once you open the VM see that the state is provisioned green status.

Repeat the same for the rest of backend members.

### Question

**Are the backends up and running?**

### Options

- **Yes** → Go to: *Backends are powered on*
- **No** → Go to: *Proceed to turn on NVAs*

---

### Step 2: Proceed to turn on NVAs

### Guidance

Proceed to start /turn on the VM's in Azure side so the device can start receive and respond heatlh probes.

Advise the customer to turn on the backend NVA's from the portal by clicking start button from the overview section.

Here is a [guide](https://microsoft.github.io/AzureTipsAndTricks/blog/tip371.html) for you to follow.

### Question

**Now that the VM is powered on, is it in Succeeded?**

### Options

- **Yes** → Go to: *Are probes working now*
- **No** → Go to: *Open collaboraton request with vm*

---

### Step 3: Backends are powered on

### Guidance

If backends are up and running and still not probing correctly, lets verfiy that the guest OS is actually receiving and responding the probes, ask the customer to please verify that the port for probing is actually open and listening in the OS

* Sign-in to NVA OS (this is customer task)

* Ask the customer to confirm the probe port is open and listening

* If the port state isn't listed as LISTENING, configure the proper port.

* Alternatively, select another port that is listed as LISTENING and update load balancer configuration accordingly.

### Question

**Once the configuration has been checked and in place, is the probe still failing?**

### Options

- **Yes** → Go to: *custom NSG at nic subnet*
- **No** → Go to: *Probes miss configuration*

---

### Step 4: Open collaboraton request with vm

### Support Engineer Solution

If the VM is unable to start, there is probably a major issue with the compute provider with that NVA.

Proceed to open a collaboration request with VM team to check the compute Resource Provider.

### Customer Solution

*Content type: MarkdownText*

The virtual machine NVA is unable to start at the host level, please open a service request with Virtual machine team to investigate why my VM is not booting up.

Here are some common scenarios you can try to follow too.

[boot issue link](https://learn.microsoft.com/en-us/troubleshoot/azure/virtual-machines/boot-error-troubleshoot#boot-errors-and-solutions)

---

### Step 5: Are probes working now

### Guidance

Once the backends are powered on and healthy state, the load balancer will start to probe the NVA's, now that probe should reach the NVA guest and reply that probe.

### Question

**Is the probe working?**

### Options

- **Yes** → Go to: *Host was powered off*
- **No** → Go to: *Backends are powered on*

---

### Step 6: Host was powered off

### Support Engineer Solution

Host and Guest were off.

As the NVA VM was powered off, the guest OS was down too, so the probes were failing making the Load balancer to process the backend is unhealthy or down.

Educate the customer that if the VM's are not running the probes will fail 100% from the load balancer perspective.

### Customer Solution

*Content type: MarkdownText*

It seems that the Azure virtual machine that contains the network virtual appliances were shut down, if the NVA's are behind a load balancer and powered off, the probes to them will fail 100%.

Here is our public [documentation](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-troubleshoot-health-probe-status#symptom-vms-behind-the-load-balancer-arent-responding-to-health-probes)

---

### Step 7: Probes miss configuration

### Support Engineer Solution

The customer has a custom port configured in the NVA backend OS for probing, other than regular SSH or HTTP/HTTPS.

The load balancer will probe to the backend on whatever customer port the backend is listening as long as the probe port is aligned with the backend OS.

### Customer Solution

*Content type: MarkdownText*

As the backend NVA Os was listening on a different port rather than SSH OR HTTPS, the load balancer is needed to probe in that custom port to validate the NVA backend is alive

Reference [Here](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-troubleshoot-health-probe-status#cause-2-load-balancer-backend-pool-vm-isnt-listening-on-the-probe-port)

---

### Step 8: custom NSG at nic subnet

### Guidance

Sometimes, customers creates custom ports for probing to their NVA's, so let's make sure that there is no NSG at NIC or Subnet level that could be blocking the traffic.

* Confirm if the NVA VM has a NSG allowing the probe port

* Also, check if a Deny All network security groups rule on the NIC of the VM or the subnet that has a higher priority than the default rule that allows LB probes & traffic (network security groups must allow Load Balancer IP of 168.63.129.16).

### Question

**Was a NSG blocking the probe traffic?**

### Options

- **Yes** → Go to: *NSG was blocking probe*
- **No** → Go to: *config probes are all in place*

---

### Step 9: NSG was blocking probe

### Support Engineer Solution

NSG blocks the traffic before it hits the Guest OS, so not allowing the probe port will cause the probe to fail.

Educate the customer that any NSG at NIC or subnet level could block traffic from the Load balancer to NVA VM.

See Reference (Here)[https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-troubleshoot-health-probe-status#cause-3-firewall-or-a-network-security-group-is-blocking-the-port-on-the-load-balancer-backend-pool-vms]

### Customer Solution

*Content type: MarkdownText*

NSG blocks the traffic before it hits the Guest OS, so not allowing the probe port port will cause the probe to fail.

Any NSG at NIC or subnet level could block traffic from the Load balancer to NVA VM.

See Reference (Here)[https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-troubleshoot-health-probe-status#cause-3-firewall-or-a-network-security-group-is-blocking-the-port-on-the-load-balancer-backend-pool-vms]

---

### Step 10: config probes are all in place

### Guidance

Now that we have validated that all configuation seems to be in place, lets take a look at the Jarvis DIP availability to confirm that the Azure Load Balancer is actually trying to probe the backend NVA.

* Go to the Load balancer in ASC

* Go to Diagnostics tab

* Scan the NVA by the probe port to confirm probes are still failing.

* Once finished, click DIP availability link

* This will open a Dashboard with all the probe information, check for the failure counts.

* At the bottom of the dashboard availability tool, you will see all the failure reasons.

### Question

**Do you see failure counts registered in the dashboard?**

### Options

- **Yes** → Go to: *Probes Errors*
- **No** → Go to: *Engage LB support*

---

### Step 11: Probes Errors

### Guidance

On the DIP dashboard, you should be able to see the failure count to the backend with any of the errors below:

*Down_Infra_ProbeSocketCreationFailure

*Down_Infra_ProbeSocketConnectionFailure

*Down_Infra_ProbeSocketConnectionPending

*Down_Infra_ProbeSocketBufferFull

*Down_Infra_HostFailedToCreateHttpProbeSession

### Question

**Do you see any of these errors?**

### Options

- **Yes** → Go to: *Engage LB support*
- **No** → Go to: *Timeout probe error*

---

### Step 12: Engage LB support

### Support Engineer Solution

If probes are not failing but not showing either in the dashboard, proceed to engage your SME / TA for further assistance in the Load balancer side as configuration form LB and backend seems to be properly setup.

### Customer Solution

*Content type: MarkdownText*

Explain to the customer that we need further investigation from Load balancer team to diagnose why probes are not successful to NVA as configuration is correctly setup.

---

### Step 13: Timeout probe error

### Guidance

If you get one of these errors like below or similar to host unreachable or timeout:

*Down_Infra_HostUnreachable

*Down_Guest_TcpProbeTimeout

*Down_Guest_HttpStatusCodeError

*Down_Guest_HttpEndpointUnreachable

This error is because the probe was sent to the backend, but there was a non succesful response back to the LB probe.

if possible proceed to collect wireshark captures in the Guest OS, to confirm probes are received and acknolwedged 

### Question

**Is the customer able to run captures in the guest OS NVA?**

### Options

- **Yes** → Go to: *Probes captures at backend OS*
- **No** → Go to: *Unified flow logs*

---

### Step 14: Probes captures at backend OS

### Support Engineer Solution

Customer should be able to run the captures from the OS, if you are able to confirm that the probes are received but Guest OS not responding, tell the customer to work with Vendor support to understand why probes are not being replied.

### Customer Solution

*Content type: MarkdownText*

Proceed to explain the customer that probes are received at guest OS level, so all Azure infrastrcuture is working regarding the health probes to the NVA.

Customer should be able to work with vendor support to investigate further on their end.

This is also explained [Here](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-troubleshoot-nva#analyze-traces)

---

### Step 15: Unified flow logs

### Guidance

If the customer is unable to run a capture, we can still try to run a unfied flow logs from the host VM via Jarvis Action.

https://portal.microsoftgeneva.com/6629DA84?genevatraceguid=54614032-f6ab-4dd6-b141-8956ea9ea009

 You can use it to take all the current connections at the host level, make sure to take the node,container Id and cluster from the NVA VM propeties.

 Once ran the Jarvis, you should be able to see traffic coming from the wireserver 168.63.129.16 as in packet probing the NVA OS.

### Question

**Are you able to see the WireServer IP 168.63.129.16 attempting connections to the NVA?**

### Options

- **Yes** → Go to: *Engage Vendor support*
- **No** → Go to: *Engage LB support*

---

### Step 16: Engage Vendor support

### Support Engineer Solution

As there are attempts from the load balancer to the Backend NVA and no answer from the guest OS, request the customer to please work with Vendor for further support in the OS.

### Customer Solution

*Content type: MarkdownText*

Educate the customer that at host level of the virtual machine we are seeing the Azure load balancer constantly trying to probe the NVA guest, but no replies are acknowledged, request the customer to please open a service request with the vendor to troubleshoot further.

---
