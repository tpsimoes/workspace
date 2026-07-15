# Upgrading from Basic to Standard SKU load balancer

> **Product:** Load Balancer  
> **Solution ID:** bda22259-128a-4184-a0d0-873d80054496  
> **Trigger words:** balancer, basic, load balancer, standard, upgrading

---

## Overview

This guide provides step-by-step troubleshooting for **Upgrading from Basic to Standard SKU load balancer** under **Load Balancer**.
 The original guided troubleshooter contains 16 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Upgrade load balancer from basic to standard SKU ⭐ (First Step)

### Guidance

This Guided Troubleshooter will help you to troubleshoot issues related to upgradation of basic SKU load balancer to Standard SKU.

If the issue is not related to this, please correct the Support Area Path and re-run the Guided Troubleshooter.

### Question

**Is the issue related to migration of Basic SKU Load balancer?**

### Options

- **Yes** → Go to: *Migration approach*
- **No** → Go to: *Change SAP*

---

### Step 2: Migration approach

### Guidance

How is the migration being performed?

### Question

**How is the migration being performed?**

### Options

- **Upgrade manually via Portal** → Go to: *Upgrade manually via Portal*
- **Upgrade using automated script(Recommmended)** → Go to: *Upgrade using automated script*

---

### Step 3: Change SAP

### Support Engineer Solution

Please change the SAP and re-run the Guided Troubleshooter.

This troubleshooter is only valid for the SAP Azure/Load Balancer/Management/Upgrade from Basic to Standard.

### Customer Solution

*Content type: MarkdownText*

Please change the SAP and re-run the Guided Troubleshooter.

This troubleshooter is only valid for the SAP Azure/Load Balancer/Management/Upgrade from Basic to Standard.

---

### Step 4: Upgrade manually via Portal

### Support Engineer Solution

For an advisory assistance, please refer: https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-basic-upgrade-guidance#upgrade-manually.

### Customer Solution

*Content type: MarkdownText*

For an advisory assistance, please refer: https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-basic-upgrade-guidance#upgrade-manually

---

### Step 5: Upgrade using automated script

### Guidance

If you are upgrading using automated script, please follow this document: https://learn.microsoft.com/en-us/azure/load-balancer/upgrade-basic-standard-with-powershell. 

Check if the scenario is supported before doing an upgrade.

Refer - https://learn.microsoft.com/en-us/azure/load-balancer/upgrade-basic-standard-with-powershell#unsupported-scenarios

### Question

**Is this scenario supported?**

### Options

- **No** → Go to: *Unsupported scenario*
- **Yes** → Go to: *Supported scenario*

---

### Step 6: Unsupported scenario

### Support Engineer Solution

It's an unsupported scenario. Kindly validate the document and proceed further accordingly.

Document: https://learn.microsoft.com/en-us/azure/load-balancer/upgrade-basic-standard-with-powershell#unsupported-scenarios

### Customer Solution

*Content type: MarkdownText*

It's an unsupported scenario. Kindly validate the document and proceed further accordingly.

Document: https://learn.microsoft.com/en-us/azure/load-balancer/upgrade-basic-standard-with-powershell#unsupported-scenarios

---

### Step 7: Supported scenario

### Guidance

While running upgradation script, if you are facing any errors then select the step accordingly.

### Question

**Is the script throwing an error?**

### Options

- **Yes** → Go to: *Resolve script errors*
- **No** → Go to: *Migration review*

---

### Step 8: Resolve script errors

### Guidance

If you are facing issues with script, here are some common errors. Please select accordingly.

### Question

**Please select the error you are encountering.**

### Options

- **ERROR: Cannot convert the "System.Object[to type "Microsoft.Azure.Commands.Network.Models.PSBackendAddressPool"** → Go to: *Error Step 1*
- **ERROR: StatusCode: 400ReasonPhrase: Bad RequestErrorCode: LoadBalancerInUseByVirtualMachineScaleSetErrorMessage: Cannot delete load balancer <LB RESOURCE ID> since its child resources <INBOUND NAT POOL RESOURCE ID>,<INBOUND NATPOOL NAME> are in use by virtual machine scale set <VMSS RESOURCE ID>.** → Go to: *Error Step 2*
- **[Error]:[Test-SupportedMigrationScenario] A VM NIC IP configuration in the backend pool of  the basic load balancer(s) to be migrated is associated with backend pool ID '<Backend Pool resource id>', which does not belong to the Basic Load Balancer(s) to be migrated. To migrate this scenario, use the  -MultiLBConfig parameter to specify multiple Basic Load Balancers to migrate at the same time.** → Go to: *Error Step 3*
- **ERROR: The private IP address <private IP> in the vnet <vnet name>, resource group <resource group name>is not available for allocation; another new device may have claimed it. To recover, remove the device that claimed the IP <private IP> from the vnet.** → Go to: *Error Step 4*
- **None of them** → Go to: *None of them*

---

### Step 9: Migration review

### Guidance

LB should be migrated successfully. If not, select next step accordingly.

### Question

**Are you facing connectivity issues post migration?**

### Options

- **Yes** → Go to: *LB connectivity issue*
- **No** → Go to: *Migration successful*

---

### Step 10: Migration successful

### Support Engineer Solution

LB migration is successful!

### Customer Solution

*Content type: MarkdownText*

LB migration is successful!

---

### Step 11: LB connectivity issue

### Guidance

If there is an issue post migration, select the next step accordingly.

### Question

**What issue are you facing with standard LB?**

### Options

- **Inbound Connectivity** → Go to: *454c4292-c3c0-4c42-9ed9-a8e4428b0d21*
- **Outbound Connectivity** → Go to: *b637c3a5-7627-47b3-812f-75e5356041d2*

---

### Step 12: Error Step 1

### Support Engineer Solution

Cause: This typically occurs when using an outdated version of the Azure Load Balancer PowerShell module.

Resolution: Upgrade the module to latest version or later to resolve type conversion issues.

Please refer prequisites before migration: A supported version of PowerShell version 7 or higher is recommended for use with the AzureBasicLoadBalancerUpgrade module on all platforms including Windows, Linux, and macOS. However, PowerShell 5.1 on Windows is supported.

### Customer Solution

*Content type: MarkdownText*

Cause: This typically occurs when using an outdated version of the Azure Load Balancer PowerShell module.

Resolution: Upgrade the module to latest version or later to resolve type conversion issues.

Please refer prequisites before migration: A supported version of PowerShell version 7 or higher is recommended for use with the AzureBasicLoadBalancerUpgrade module on all platforms including Windows, Linux, and macOS. However, PowerShell 5.1 on Windows is supported.

---

### Step 13: Error Step 2

### Support Engineer Solution

Cause: This typically occurs when Load balancer backend pool is empty or VMSS has 0 instances.

Resolution: The backend pool shouldn't be empty and VMSS should have atleast 1 instance. So the brief explanation is that the VMSS profile is still associated to the LB but on the LB side we do not see any backend pool instances (i.e. no VMSS instances). 

### Customer Solution

*Content type: MarkdownText*

Cause: This typically occurs when Load balancer backend pool is empty or VMSS has 0 instances.

Resolution: The backend pool shouldn't be empty and VMSS should have atleast 1 instance. So the brief explanation is that the VMSS profile is still associated to the LB but on the LB side we do not see any backend pool instances (i.e. no VMSS instances). 

---

### Step 14: Error Step 3

### Support Engineer Solution

Cause: The same backend VM is part of two different load balancers.

Resolution: Need to migrate multiple Basic Load Balancers together using the -MultiLBConfig parameter in the PowerShell migration script.

### Customer Solution

*Content type: MarkdownText*

Cause: The same backend VM is part of two different load balancers.

Resolution: Need to migrate multiple Basic Load Balancers together using the -MultiLBConfig parameter in the PowerShell migration script.

---

### Step 15: Error Step 4

### Support Engineer Solution

Cause: The private IP being used by new standard LB is already allocated to another resource.

Resolution: Make sure to remove that private IP reference from another resource and retry migration.

### Customer Solution

*Content type: MarkdownText*

Cause: The private IP being used by new standard LB is already allocated to another resource.

Resolution: Make sure to remove that private IP reference from another resource and retry migration.

---

### Step 16: None of them

### Support Engineer Solution

++Address the cause of the migration failure. Check the log file Start-AzBasicLoadBalancerUpgrade.log for details

++Remove the new Standard Load Balancer (if created). Depending on which stage of the migration failed, you may have to remove the Standard Load Balancer reference from the Virtual Machine Scale Set or Virtual Machine network interfaces (IP configurations) and Health Probes in order to remove the Standard Load Balancer.

++Locate the Basic Load Balancer state backup file. 

This file will either be in the directory where the script was executed, or at the path specified with the -RecoveryBackupPath parameter during the failed execution. 

The file is named: State_<basicLBName>_<basicLBRGName>_<timestamp>.json

++ Rerun the migration script, specifying the -FailedMigrationRetryFilePathLB <BasicLoadBalancerbackupFilePath> and -FailedMigrationRetryFilePathVMSS <VMSSBackupFile> (for Virtual Machine Scale set backends) parameters instead of -BasicLoadBalancerName or passing the Basic Load Balancer over the pipeline.

### Customer Solution

*Content type: MarkdownText*

++Address the cause of the migration failure. Check the log file Start-AzBasicLoadBalancerUpgrade.log for details

++Remove the new Standard Load Balancer (if created). Depending on which stage of the migration failed, you may have to remove the Standard Load Balancer reference from the Virtual Machine Scale Set or Virtual Machine network interfaces (IP configurations) and Health Probes in order to remove the Standard Load Balancer.

++Locate the Basic Load Balancer state backup file. 

This file will either be in the directory where the script was executed, or at the path specified with the -RecoveryBackupPath parameter during the failed execution. 

The file is named: State_<basicLBName>_<basicLBRGName>_<timestamp>.json

++ Rerun the migration script, specifying the -FailedMigrationRetryFilePathLB <BasicLoadBalancerbackupFilePath> and -FailedMigrationRetryFilePathVMSS <VMSSBackupFile> (for Virtual Machine Scale set backends) parameters instead of -BasicLoadBalancerName or passing the Basic Load Balancer over the pipeline.

---
