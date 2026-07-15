# Resolve issues with upgrading from Basic to Standard SKU Load Balancer

> **Product:** Load Balancer  
> **Solution ID:** 235ad95c-9d36-4a21-a790-0d2364ee5b8d  
> **Trigger words:** balancer, basic, load balancer, resolve, standard, upgrading

---

## Overview

This guide provides step-by-step troubleshooting for **Resolve issues with upgrading from Basic to Standard SKU Load Balancer** under **Load Balancer**.
 The original guided troubleshooter contains 16 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Upgrade from Basic to Standard SKU Load Balancer ⭐ (First Step)

### Guidance

This troubleshooter will help resolve any issues related to upgradation of azure Load Balancer from Basic to Standard SKU. 

### Question

**Is the issue related to the migration of Basic SKU Load Balancer?**

### Options

- **Yes** → Go to: *Migration approach*
- **No** → Go to: *Change SAP*

---

### Step 2: Migration approach

### Guidance

Refer to this document to understand the available migration options: [Upgrading from Basic Load Balancer - Guidance](https://learn.microsoft.com/azure/load-balancer/load-balancer-basic-upgrade-guidance).

### Question

**How is the migration being performed?**

### Options

- **Upgrade manually via the portal** → Go to: *Upgrade manually via portal*
- **Upgrade using automated script (recommmended)** → Go to: *Upgrade using automated script recommended*

---

### Step 3: Change SAP

### Support Engineer Solution

This troubleshooter is only valid for the SAP Azure/Load Balancer/Management/Upgrade from Basic to Standard.

If this is not related to the issue, please re-run the troubleshooter with the right information.

### Customer Solution

*Content type: MarkdownText*

This troubleshooter is applicable only for SAP Azure/Load Balancer/Management/Upgrade from Basic to Standard.

If your issue pertains to a different topic, rerun the troubleshooter with the correct information.

---

### Step 4: Upgrade manually via portal

### Support Engineer Solution

If you are upgrading manually via portal, please refer: https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-basic-upgrade-guidance

### Customer Solution

*Content type: MarkdownText*

If you're upgrading manually via the portal, see [Upgrading from Basic Load Balancer - Guidance](https://learn.microsoft.com/azure/load-balancer/load-balancer-basic-upgrade-guidance).

---

### Step 5: Upgrade using automated script recommended

### Guidance

Check if the scenario is supported before performing an upgrade, see [Unsupported scenarios](https://learn.microsoft.com/azure/load-balancer/upgrade-basic-standard-with-powershell#unsupported-scenarios).

If you're upgrading using an automated script, see [Upgrade a basic load balancer with PowerShell](https://learn.microsoft.com/azure/load-balancer/upgrade-basic-standard-with-powershell).

### Question

**Is this a supported scenario?**

### Options

- **Yes** → Go to: *Supported scenario*
- **No** → Go to: *Unsupported scenario*

---

### Step 6: Supported scenario

### Guidance

Select an option.

### Question

**Is the script throwing an error?**

### Options

- **Yes** → Go to: *Resolve script errors*
- **No** → Go to: *Migration review*

---

### Step 7: Unsupported scenario

### Support Engineer Solution

It's an unsupported scenario. Kindly validate the document and proceed further accordingly.

Document: https://learn.microsoft.com/en-us/azure/load-balancer/upgrade-basic-standard-with-powershell#unsupported-scenarios

### Customer Solution

*Content type: MarkdownText*

Review [Upgrade a basic load balancer with PowerShell](https://learn.microsoft.com/azure/load-balancer/upgrade-basic-standard-with-powershell#unsupported-scenarios) and proceed accordingly.

---

### Step 8: Resolve script errors

### Guidance

These are the most common errors when using a script.

### Question

**Which error are you encountering?**

### Options

- **ERROR: Cannot convert the "System.Object[to type "Microsoft.Azure.Commands.Network.Models.PSBackendAddressPool"** → Go to: *Error step 1*
- **ERROR: StatusCode: 400ReasonPhrase: Bad RequestErrorCode: LoadBalancerInUseByVirtualMachineScaleSetErrorMessage: Cannot delete load balancer <LB RESOURCE ID> since its child resources <INBOUND NAT POOL RESOURCE ID>,<INBOUND NATPOOL NAME> are in use by virtual machine scale set <VMSS RESOURCE ID>.** → Go to: *Error step 2*
- **ERROR:[Test-SupportedMigrationScenario] A VM NIC IP configuration in the backend pool of  the basic load balancer(s) to be migrated is associated with backend pool ID '<Backend Pool resource id>', which does not belong to the Basic Load Balancer(s) to be migrated. To migrate this scenario, use the  -MultiLBConfig parameter to specify multiple Basic Load Balancers to migrate at the same time.** → Go to: *Error step 3*
- **ERROR: The private IP address <private IP> in the vnet <vnet name>, resource group <resource group name>is not available for allocation; another new device may have claimed it. To recover, remove the device that claimed the IP <private IP> from the vnet.** → Go to: *Error step 4*
- **None of the above** → Go to: *Error step 5*

---

### Step 9: Migration review

### Guidance

Select an option.

### Question

**Load Balancer should be migrated successfully. Are you encountering connectivity issues after the migration?**

### Options

- **Yes** → Go to: *Load Balancer connectivity issue*
- **No** → Go to: *Migration successful*

---

### Step 10: Load Balancer connectivity issue

### Guidance

Select an option.

### Question

**Are you encountering an inbound or outbound connectivity issue?**

### Options

- **Inbound** → Go to: *e3c6812c-4c20-4903-b542-08a19a17aa49*
- **Outbound** → Go to: *544906a8-a2db-4da3-8788-db27a954dd6d*

---

### Step 11: Migration successful

### Support Engineer Solution

Load Balancer is successfully migrated!

### Customer Solution

*Content type: MarkdownText*

Load Balancer is successfully migrated!

---

### Step 12: Error step 1

### Support Engineer Solution

Cause: This typically occurs when using an outdated version of the Azure Load Balancer PowerShell module.

Resolution: Upgrade the module to latest version or later to resolve type conversion issues.

Please refer prequisites before migration: A supported version of PowerShell version 7 or higher is recommended for use with the AzureBasicLoadBalancerUpgrade module on all platforms including Windows, Linux, and macOS. However, PowerShell 5.1 on Windows is supported.

### Customer Solution

*Content type: MarkdownText*

**Cause**

This error typically occurs when using an outdated version of the Azure Load Balancer PowerShell module.

**Steps to resolve the issue**

Upgrade the module to latest version or later to resolve issues related to type conversion.

**Migration prerequisites**

A supported version of PowerShell version 7 or higher is recommended for use with the AzureBasicLoadBalancerUpgrade module on all platforms including Windows, Linux, and macOS. However, PowerShell 5.1 on Windows is supported.

---

### Step 13: Error step 2

### Support Engineer Solution

Cause: This typically occurs when Load balancer backend pool is empty or VMSS has 0 instances.

Resolution: The backend pool shouldn't be empty and VMSS should have atleast 1 instance. So the brief explanation is that the VMSS profile is still associated to the LB but on the LB side we do not see any backend pool instances (i.e. no VMSS instances). 

### Customer Solution

*Content type: MarkdownText*

**Cause** 

This error typically occurs when the load balancer backend pool is empty or Virtual Machine Scale Set (VMSS) has zero instances.

**Steps to resolve the issue**

Make sure that the backend pool isn't empty and that the VMSS has at least one instance. The issue occurs when the VMSS profile remains associated with the load balancer but there are no instances visible in the Load Balancer’s backend pool—meaning no VMSS instances are currently present.

---

### Step 14: Error step 3

### Support Engineer Solution

Cause: The same backend VM is part of two different load balancers.

Resolution: Need to migrate multiple Basic Load Balancers together using the -MultiLBConfig parameter in the PowerShell migration script.

### Customer Solution

*Content type: MarkdownText*

**Cause**

The same backend virtual machine is associated with two different load balancers.

**Steps to resolve the issue**

To resolve this issue, migrate multiple Basic Load Balancers together using the `-MultiLBConfig` parameter in the PowerShell migration script.

---

### Step 15: Error step 4

### Support Engineer Solution

Cause: The private IP being used by new standard LB is already allocated to another resource.

Resolution: Make sure to remove that private IP reference from another resource and retry migration.

### Customer Solution

*Content type: MarkdownText*

**Cause**

The private IP that's being used by the new Standard Load Balancer is already allocated to another resource.

**Steps to resolve the issue** 

Remove the private IP reference from the other resource and retry the migration.

---

### Step 16: Error step 5

### Support Engineer Solution

++Address the cause of the migration failure. Check the log file Start-AzBasicLoadBalancerUpgrade.log for details

++Remove the new Standard Load Balancer (if created). Depending on which stage of the migration failed, you may have to remove the Standard Load Balancer reference from the Virtual Machine Scale Set or Virtual Machine network interfaces (IP configurations) and Health Probes in order to remove the Standard Load Balancer.

++Locate the Basic Load Balancer state backup file. 

This file will either be in the directory where the script was executed, or at the path specified with the -RecoveryBackupPath parameter during the failed execution. 

The file is named: State_`<`basicLBName`>`\_`<`basicLBRGName`>`_`<`timestamp`>`.json

++ Rerun the migration script, specifying the -FailedMigrationRetryFilePathLB <BasicLoadBalancerbackupFilePath> and -FailedMigrationRetryFilePathVMSS <VMSSBackupFile> (for Virtual Machine Scale set backends) parameters instead of -BasicLoadBalancerName or passing the Basic Load Balancer over the pipeline.

### Customer Solution

*Content type: MarkdownText*

**Troubleshoot other script errors**

- Identify the cause of the migration failure. Review the log file Start-AzBasicLoadBalancerUpgrade.log for detailed information.

- Remove the new Standard Load Balancer (if created). Depending on the stage at which the migration failed, you may have to remove the Standard Load Balancer reference from the Virtual Machine Scale Set or virtual machine network interfaces (IP configurations) and health probes in order to remove the Standard Load Balancer.

- Locate the Basic Load Balancer state backup file. 

  - This file will either be in the directory where the script was executed or at the path specified with the `-RecoveryBackupPath` parameter during the failed execution. 

  - The file is named: State_`<`basicLBName`>`\_`<`basicLBRGName`>`_`<`timestamp`>`.json

- Rerun the migration script, specifying the `-FailedMigrationRetryFilePathLB <BasicLoadBalancerbackupFilePath>` and `-FailedMigrationRetryFilePathVMSS <VMSSBackupFile>` (for Virtual Machine Scale Set backends) parameters instead of `-BasicLoadBalancerName` or passing the Basic Load Balancer over the pipeline.

---
