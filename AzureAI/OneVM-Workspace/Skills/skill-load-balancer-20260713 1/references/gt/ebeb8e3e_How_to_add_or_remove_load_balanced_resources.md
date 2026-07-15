# How to add or remove load balanced resources

> **Product:** Load Balancer  
> **Solution ID:** ebeb8e3e-c5d4-4f1e-9fcb-cd97221d9ccc  
> **Trigger words:** balanced, load balancer, remove, resources

---

## Overview

This guide provides step-by-step troubleshooting for **How to add or remove load balanced resources** under **Load Balancer**.
 The original guided troubleshooter contains 9 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Troubleshooting load balancer backend configuration ⭐ (First Step)

### Guidance

This troubleshooter is designed to help you with any issues related to Azure Load Balancer backend pool management.

### Question

**Select your issue**

### Options

- **Adding backend** → Go to: *Adding backend*
- **Removing backend** → Go to: *Removing backend*

---

### Step 2: Adding backend

### Guidance

If you encounter issues while adding a new backend pool, select the specific problem you are experiencing.

### Question

**Select your issue**

### Options

- **VM not visible in backend pool selection** → Go to: *VM not visible*
- **Can't add because VMSS is not using latest model** → Go to: *VMSS not latest model*
- **RBAC/Permissions issue** → Go to: *RBAC issue*
- **SKU of the resource's IP address is different from the SKU of the load balancer** → Go to: *SKU of backend IP*
- **Availability set using different basic SKU and standard SKU load balancer or public IP resources is not allowed** → Go to: *Different LB SKU*
- **None of them** → Go to: *Check activity or crud logs*

---

### Step 3: Removing backend

### Support Engineer Solution

To remove backend VM from backend pool via portal, go to **Backend pools**, then click on the delete icon for the VM that needs to be removed.

Or, use CLI method. See [az network nic ip-config address-pool remove
](https://learn.microsoft.com/en-us/cli/azure/network/nic/ip-config/address-pool?view=azure-cli-latest#az-network-nic-ip-config-address-pool-remove).

Or, use the PS method:

`$nic = Get-AzNetworkInterface -Name "<your-nic>" -ResourceGroupName "<your-rg>"
$ipconfig = $nic.IpConfigurations | Where-Object {$_.Name -eq "ipconfig1"}
$ipconfig.LoadBalancerBackendAddressPools.Clear()
Set-AzNetworkInterface -NetworkInterface $nic`

### Customer Solution

*Content type: MarkdownText*

To remove backend VM from backend pool via portal, go to **Backend pools**, then click on the delete icon for the VM that needs to be removed.

Or, use CLI method. See [az network nic ip-config address-pool remove

](https://learn.microsoft.com/en-us/cli/azure/network/nic/ip-config/address-pool?view=azure-cli-latest#az-network-nic-ip-config-address-pool-remove).

Or, use the PS method:

`$nic = Get-AzNetworkInterface -Name "<your-nic>" -ResourceGroupName "<your-rg>"

$ipconfig = $nic.IpConfigurations | Where-Object {$_.Name -eq "ipconfig1"}

$ipconfig.LoadBalancerBackendAddressPools.Clear()

Set-AzNetworkInterface -NetworkInterface $nic`

---

### Step 4: VM not visible

### Support Engineer Solution

**Possible causes:**

- VM is not in the same region or virtual network as the Load Balancer.

- VM is not in an availability set or virtual machine scale set (required for Basic Load Balancer).

- VM was recently created or cloned and metadata hasn't refreshed.

**Resolution:**

- Ensure the VM is in the same region and VNet.

- For Basic Load Balancer, ensure VMs are in the same availability set.

- Try adding the VM via **VM > Networking > Load Balancer > Add as a workaround**.

### Customer Solution

*Content type: MarkdownText*

**Possible causes:**

- VM is not in the same region or virtual network as the Load Balancer.

- VM is not in an availability set or virtual machine scale set (required for Basic Load Balancer).

- VM was recently created or cloned and metadata hasn't refreshed.

**Resolution:**

- Ensure the VM is in the same region and VNet.

- For Basic Load Balancer, ensure VMs are in the same availability set.

- Try adding the VM via **VM > Networking > Load Balancer > Add as a workaround**.

---

### Step 5: VMSS not latest model

### Support Engineer Solution

In Azure portal, select **vmss** and select the **instances** on the left. For all instances, there is a **Latest Model** column that indicates whether or not the VM is up-to-date with the latest overall scale set model.

- **True** means the VM is up-to-date with the latest model.

 - **No** indicates that you need to upgrade using either CLI or Powershell commands.

**CLI Command**: 

`az vmss update-instances --instance-ids 1 --name MyScaleSet --resource-group MyResourceGroup`

**PowerShell Command**: 

`Update-AzVmssInstance -ResourceGroupName "Group011" -VMScaleSetName "VMScaleSet001" -InstanceId "0"`

### Resources 

- [az vmss update-instances](https://learn.microsoft.com/cli/azure/vmss?view=azure-cli-latest#az-vmss-update-instances)

- [Start an upgrade of the VMSS instance](https://learn.microsoft.com/powershell/module/az.compute/update-azvmssinstance?view=azps-14.40#example-1-start-an-upgrade-of-the-vmss-instance)

### Customer Solution

*Content type: MarkdownText*

In Azure portal, select **vmss** and select the **instances** on the left. For all instances, there is a **Latest Model** column that indicates whether or not the VM is up-to-date with the latest overall scale set model.

- **True** means the VM is up-to-date with the latest model.

 - **No** indicates that you need to upgrade using either CLI or Powershell commands.

**CLI Command**: 

`az vmss update-instances --instance-ids 1 --name MyScaleSet --resource-group MyResourceGroup`

**PowerShell Command**: 

`Update-AzVmssInstance -ResourceGroupName "Group011" -VMScaleSetName "VMScaleSet001" -InstanceId "0"`

### Resources 

- [az vmss update-instances](https://learn.microsoft.com/cli/azure/vmss?view=azure-cli-latest#az-vmss-update-instances)

- [Start an upgrade of the VMSS instance](https://learn.microsoft.com/powershell/module/az.compute/update-azvmssinstance?view=azps-14.40#example-1-start-an-upgrade-of-the-vmss-instance)

---

### Step 6: RBAC issue

### Support Engineer Solution

To update a NIC and associate it with a backend pool, you must have permission to write to the NIC resource. This includes:
 
- Microsoft.Network/networkInterfaces/read
- Microsoft.Network/networkInterfaces/write
 
These permissions are included in built-in roles like:
- Network Contributor (ideal for networking tasks)
- Contributor (broader access across resources)

Another possibility is to use **Custom Role**. If using a custom role, it must include the following permissions:
- Microsoft.Network/loadBalancers/backendAddressPools/write
- Microsoft.Network/networkInterfaces/write
- Microsoft.Compute/virtualMachines/read

### Resources

- [Azure permissions for Networking](https://learn.microsoft.com/azure/role-based-access-control/permissions/networking)

### Customer Solution

*Content type: MarkdownText*

To update a NIC and associate it with a backend pool, you must have permission to write to the NIC resource. This includes:

 

- Microsoft.Network/networkInterfaces/read

- Microsoft.Network/networkInterfaces/write

 

These permissions are included in built-in roles like:

- Network Contributor (ideal for networking tasks)

- Contributor (broader access across resources)

Another possibility is to use **Custom Role**. If using a custom role, it must include the following permissions:

- Microsoft.Network/loadBalancers/backendAddressPools/write

- Microsoft.Network/networkInterfaces/write

- Microsoft.Compute/virtualMachines/read

### Resources

- [Azure permissions for Networking](https://learn.microsoft.com/azure/role-based-access-control/permissions/networking)

---

### Step 7: SKU of backend IP

### Support Engineer Solution

**Error:** The SKU of the resource's IP address is different from the SKU of the load balancer.

**Cause:** Check if the VM you are trying to add is part of an availability set or not. If yes, then add this VM to the backend pool of a Standard SKU Load Balancer, as Standard SKU does not support mixing VMs from availability sets with ones outside of it.

**Resolution:**

You need to remove and recreate the VM outside of the availability set.

### Customer Solution

*Content type: MarkdownText*

**Error:** The SKU of the resource's IP address is different from the SKU of the load balancer.

**Cause:** Check if the VM you are trying to add is part of an availability set or not. If yes, then add this VM to the backend pool of a Standard SKU Load Balancer, as Standard SKU does not support mixing VMs from availability sets with ones outside of it.

**Resolution:**

You need to remove and recreate the VM outside of the availability set.

---

### Step 8: Different LB SKU

### Support Engineer Solution

**Error:** Different basic SKU and standard SKU load balancer or public IP resources in availability set is not allowed. 

**Cause:** The same VMs cannot be part of two different load balancers of the same type.

**Resolution:** Remove from one of the load balancer to avoid this error.

### Customer Solution

*Content type: MarkdownText*

**Error:** Different basic SKU and standard SKU load balancer or public IP resources in availability set is not allowed. 

**Cause:** The same VMs cannot be part of two different load balancers of the same type.

**Resolution:** Remove from one of the load balancer to avoid this error.

---

### Step 9: Check activity or crud logs

### Support Engineer Solution

Check CRUD operations or Ocular logs to investigate the error and resolve accordingly.

### Customer Solution

*Content type: MarkdownText*

Check activity logs of load balancer to find failed operation and investigate the error accordingly.

See the following guide for information on how to check activity logs of an Azure resource: [Activity log in Azure Monitor

](https://learn.microsoft.com/azure/azure-monitor/platform/activity-log?tabs=log-analytics).

---
