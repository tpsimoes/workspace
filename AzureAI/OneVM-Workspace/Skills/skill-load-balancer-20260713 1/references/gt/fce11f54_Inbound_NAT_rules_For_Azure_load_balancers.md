# Inbound NAT rules For Azure load balancers

> **Product:** Load Balancer  
> **Solution ID:** fce11f54-72fd-49e4-adfe-f172dadfce15  
> **Trigger words:** balancers, inbound, load balancer, rules

---

## Overview

This guide provides step-by-step troubleshooting for **Inbound NAT rules For Azure load balancers** under **Load Balancer**.
 The original guided troubleshooter contains 20 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Scope for azure load balancer Inbound NAT rules ⭐ (First Step)

### Guidance

This Guided Troubleshooter will help you to troubleshoot issues related to Inbound NAT rules creation, update & Connectvity.

In this step we would like to confirm if the issue faced by the customer is related to NAT rules.

### Question

**Does your issue fall under the scope of inbound NAT rule?**

### Options

- **YES** → Go to: *Select the scenario that needs help*
- **NO** → Go to: *In Correct Support Area Path on the Support Case*

---

### Step 2: Select the scenario that needs help

### Guidance

In this step please select the scenario that best describes the customer's issue

### Question

**Which scenario is the customer seeking help with?**

### Options

- **Unable to connect to Backend Resources using NAT rules** → Go to: *Verify the Port mapping is correct form the front end IP to backend can be verified from the Azure portal for load balancer under inbound NAT rule*
- **Unable to create NAT rule/pool** → Go to: *Does Inbound NAT rules and load balancing rules share the same frontend ports*
- **Migration from NATv1 to NATv2** → Go to: *Migrating from Inbound NAT V1 rules to NAT V2 rules*
- **Identify the NAT rule version** → Go to: *Identify if the inbound NAT rules are v1 or v2 rules*
- **Issues related to SKU migration because of NAT rules** → Go to: *Is the Issue related to load balancer SKU migration due to inbound NAT rules*

---

### Step 3: In Correct Support Area Path on the Support Case

### Support Engineer Solution

Since the issue is not related to NAT rules, we would recommend that you set the support ticket with the right Support Area Path and re run the guided troubleshooter section. 

### Customer Solution

*Content type: MarkdownText*

Since the issue is not related to NAT rules, we would recommend that you set the support ticket with the right Support Area Path and re run the guided troubleshooter section. 

---

### Step 4: Migrating from Inbound NAT V1 rules to NAT V2 rules

### Support Engineer Solution

# Migrating Inbound NAT Rules from V1 to V2

If the customer has **inbound NAT rules V1** and wants to migrate to **V2**, this can be done **manually** or through a **script**.

---

##  Manual Migration

To manually update:

1. Delete the existing **V1 rules**.

2. Create **V2 rules** through the **Azure Portal** or **CLI**.

Refer to the official documentation for detailed steps:  

 [Manual Migration Guide (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-nat-pool-migration?tabs=azure-cli#manual-migration)

---

##  Script-Based Migration

Through the script, the migration process will:

- Reuse existing **backend pools** with membership matching the NAT Pools to be migrated.  

- If **no matching backend pool** is found, the script will **exit without making changes**.

---

##  Steps to Migrate Using Script

### Step 1: Install the Migration Module

```powershell

Install-Module -Name AzureLoadBalancerNATPoolMigration -Scope CurrentUser -Repository PSGallery -Force

````

### Step 2: Connect to Azure

```powershell

Connect-AzAccount

```

### Step 3: Run the Migration Command

Replace the placeholders "loadBalancerResourceGroupName" and "loadBalancerName" with your actual resource names.

```powershell

Start-AzNATPoolMigration -ResourceGroupName loadBalancerResourceGroupName -LoadBalancerName loadBalancerName

```

---

 **Public document reference:**

[Upgrade NAT Pools to NAT Rules (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-nat-pool-migration?tabs=azure-cli#upgrade-nat-pools-to-nat-rules)

### Customer Solution

*Content type: MarkdownText*

# Dear Customer,

To migrate Azure load balancer **inbound NAT rules V1** and wants to migrate to **V2**, this can be done **manually** or through a **script**.

---

##  Manual Migration

To manually update:

1. Delete the existing **V1 rules**.

2. Create **V2 rules** through the **Azure Portal** or **CLI**.

Refer to the official documentation for detailed steps:  

 [Manual Migration Guide (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-nat-pool-migration?tabs=azure-cli#manual-migration)

---

##  Script-Based Migration

Through the script, the migration process will:

- Reuse existing **backend pools** with membership matching the NAT Pools to be migrated.  

- If **no matching backend pool** is found, the script will **exit without making changes**.

---

##  Steps to Migrate Using Script

### Step 1: Install the Migration Module

```powershell

Install-Module -Name AzureLoadBalancerNATPoolMigration -Scope CurrentUser -Repository PSGallery -Force

````

### Step 2: Connect to Azure

```powershell

Connect-AzAccount

```

### Step 3: Run the Migration Command

Replace the placeholders "loadBalancerResourceGroupName" and "loadBalancerName" with your actual resource names.

```powershell

Start-AzNATPoolMigration -ResourceGroupName loadBalancerResou

*(Content truncated — refer to original GT for full details)*

### Step 5: Identify if the inbound NAT rules are v1 or v2 rules

### Support Engineer Solution

Identify if the inbound NAT rules are v1 or v2 

  - From Azure portal for V1 the Type is Azure Virtual machine for V1 inbound NAT rules, For V2 the type is Backend pool. 

  - For Identifying programmatically refer to the JSON configuration or through CLI/power shell.  If either the backendIPConfiguration property within the InboundNATRule configuration is populated, then the deployment is version 1 of Inbound NAT rules. Version 2 rules will have the backendAddressPool property instead of the backendIPConfiguration property. 

 

### Customer Solution

*Content type: MarkdownText*

Dear "Customer Name",

Thank you for reaching out. Please find below the guidance to identify whether your Azure Load Balancer Inbound NAT rules are using Version 1 (V1) or Version 2 (V2).

✅ From Azure Portal

For V1, the Type will show Azure Virtual machine.

For V2, the Type will show Backend pool.

✅ Identifying Programmatically

You can check this via JSON configuration, Azure CLI, or PowerShell:

If the backendIPConfiguration property within the InboundNATRule configuration is populated, the deployment is Version 1.

If the rule contains backendAddressPool instead of backendIPConfiguration, the deployment is Version 2.

Public document refrence: https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-nat-pool-migration?tabs=azure-cli#how-do-i-know-if-im-using-version-1-of-inbound-nat-rules

---

### Step 6: Is the Issue related to load balancer SKU migration due to inbound NAT rules

### Support Engineer Solution

Is the Issue related to load balancer SKU migration due to inbound NAT rules.

Please change the SAP of the case to load balancer SKU upgrade “ load balancer/ management / upgrade from basic to standard” and follow the TSG “Upgrading from Basic to Standard SKU load balancer” 

### Customer Solution

*Content type: MarkdownText*

Change the SAP and exit the Guided trouble shooter

---

### Step 7: Does Inbound NAT rules and load balancing rules share the same frontend ports

### Guidance

Verify if the  the INbound NAT rules and loadbalaners rules have same frontend ports.

### Question

**Does Inbound NAT rules and load balancing rules share the same front-end ports ?**

### Options

- **YES** → Go to: *Does Inbound NAT rules and load balancing rules share the same frontend ports Insights*
- **NO** → Go to: *Do the existing NAT rules have Front end ports that overlap with the new NAT rule failing creation*

---

### Step 8: Does Inbound NAT rules and load balancing rules share the same frontend ports Insights

### Support Engineer Solution

Does Inbound NAT rules and load balancing rules share the same frontend ports?

Using the same Front-end ports for the load balancer rules and Inbound NAT rules is not supported. The front-end port and protocol combination must be unique. 

 

Error in Azure portal: 

The frontend protocol and port combination you entered matches another rule used by this load balancer. The frontend protocol and port combination of each load balancing rule and inbound NAT rule on a load balancer must be unique. 

### Customer Solution

*Content type: MarkdownText*

Dear Customer Name,

This email clarifies an important constraint regarding **Azure Load Balancer Inbound NAT Rules** when configuring your network setup. Understanding these rules is crucial for proper and functional configuration.

### ⚠️ Key Constraint Details

Please note the following critical restrictions when defining multiple **Inbound NAT Rules** on a single Azure Load Balancer:

* **Overlapping Port Ranges/Same Backend Port:** You **cannot** create multiple NAT rules if they have an **overlapping frontend port range** or if they are configured to use the **same backend port** on the destination VM/instance.

* **Unique Combination Requirement:** The combination of the **Frontend IP**, **Protocol** (TCP/UDP), and **Frontend Port** for **every** load balancing rule and inbound NAT rule on a load balancer **must be unique**.

This ensures that the load balancer can unambiguously direct incoming traffic to the correct backend resource.

### 📘 Azure Reference Documentation

For more in-depth information and tutorials on configuration, please refer to the official Microsoft documentation on Azure Load Balancer Inbound NAT rules:

* [**Inbound NAT rules - Azure Load Balancer**](https://learn.microsoft.com/en-us/azure/load-balancer/inbound-nat-rules)

* [**Manage inbound NAT rules for Azure Load Balancer**](https://learn.microsoft.com/en-us/azure/load-balancer/manage-inbound-nat-rules)

If you have any further questions or require assistance with your configuration, please don't hesitate to reach out to our support team.

***

Best regards,

[Your Name/Azure Support Team]

---

### Step 9: Do the existing NAT rules have Front end ports that overlap with the new NAT rule failing creation

### Guidance

Please check if the customer is creating Inbound NAT rules with front end ports that are already used in exesting Ibound NAT rules.

### Question

**Do the existing NAT rules have Front end ports that overlap with the new NAT rule failing creation ?**

### Options

- **YES** → Go to: *Do the existing NAT rules have Front end ports that overlap with the new NAT rule failing creation Insights*
- **NO** → Go to: *Is Customer Using Terraform to create NAT rules*

---

### Step 10: Do the existing NAT rules have Front end ports that overlap with the new NAT rule failing creation Insights

### Support Engineer Solution

Do the existing NAT rules have Front-end ports that overlap with the new NAT rule failing creation? 

The frontend protocol and port combination of each load balancing rule and inbound NAT rule on a load balancer must be unique. 

### Customer Solution

*Content type: MarkdownText*

Dear Customer Name,

This email clarifies an important constraint regarding **Azure Load Balancer Inbound NAT Rules** when configuring your network setup. Understanding these rules is crucial for proper and functional configuration.

### ⚠️ Key Constraint Details

Please note the following critical restrictions when defining multiple **Inbound NAT Rules** on a single Azure Load Balancer:

* **Overlapping Port Ranges/Same Backend Port:** You **cannot** create multiple NAT rules if they have an **overlapping frontend port range** or if they are configured to use the **same backend port** on the destination VM/instance.

* **Unique Combination Requirement:** The combination of the **Frontend IP**, **Protocol** (TCP/UDP), and **Frontend Port** for **every** load balancing rule and inbound NAT rule on a load balancer **must be unique**.

This ensures that the load balancer can unambiguously direct incoming traffic to the correct backend resource.

### 📘 Azure Reference Documentation

For more in-depth information and tutorials on configuration, please refer to the official Microsoft documentation on Azure Load Balancer Inbound NAT rules:

* [**Inbound NAT rules - Azure Load Balancer**](https://learn.microsoft.com/en-us/azure/load-balancer/inbound-nat-rules)

* [**Manage inbound NAT rules for Azure Load Balancer**](https://learn.microsoft.com/en-us/azure/load-balancer/manage-inbound-nat-rules)

If you have any further questions or require assistance with your configuration, please don't hesitate to reach out to our support team.

***

Best regards,

[Your Name/Azure Support Team]

---

### Step 11: Is Customer Using Terraform to create NAT rules

### Guidance

Is Customer Using Terraform to create NAT rules ?

### Question

**Is Customer Using Terraform to create NAT rules ?**

### Options

- **YES** → Go to: *Is Customer Using Terraform to create NAT rules Insights*
- **NO** → Go to: *CRUD END CARD*

---

### Step 12: Is Customer Using Terraform to create NAT rules Insights

### Support Engineer Solution

It recommends create NAT rules using ARM/bicep templates, as terraform modules have separate code for V1 and V2 and the examples does not cover the backend NIC for v1 and does not have backend pool members creation which are in separate modules in terraform. 

 

Refer to below Azure public document for more information on templates for Inbound NAT rules creation: 

Microsoft.Network/loadBalancers/inboundNatRules - Bicep, ARM template & Terraform AzAPI reference | Microsoft Learn 

 

Below is the Terraform reference for the V1 

azurerm_lb_nat_pool | Resources | hashicorp/azurerm | Terraform | Terraform Registry 

Below is the Terraform reference for the V2 

azurerm_lb_nat_rule | Resources | hashicorp/azurerm | Terraform | Terraform Registry 

 

### Customer Solution

*Content type: MarkdownText*

# Recommendation for Creating NAT Rules

It is **recommended to create NAT rules using ARM/Bicep templates**, as Terraform modules have **separate code for V1 and V2**.  

The provided Terraform examples **do not cover backend NIC configurations for V1** and **do not include backend pool member creation**, which are located in **separate Terraform modules**.

---

## 📘 Reference: Azure Public Documentation

For more information on templates for **Inbound NAT rules creation**, refer to the official Microsoft Learn documentation:  

🔗 [Microsoft.Network/loadBalancers/inboundNatRules – Bicep, ARM Template & Terraform AzAPI Reference](https://learn.microsoft.com/en-us/azure/templates/microsoft.network/loadbalancers/inboundnatrules)

---

## 🧩 Terraform References

### V1 – NAT Pool

🔗 [azurerm_lb_nat_pool | Resources | hashicorp/azurerm | Terraform Registry](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/lb_nat_pool)

### V2 – NAT Rule

🔗 [azurerm_lb_nat_rule | Resources | hashicorp/azurerm | Terraform Registry](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/lb_nat_rule)

---

### Step 13: CRUD END CARD

### Support Engineer Solution

Check CRUD issues for Inbound NAT Rule creation for Azure load balancer.

If the Issue still exists, please collect ARM and NRP logs as given below.

**A.** 

 [cluster('armprodgbl.eastus.kusto.windows.net').database('ARMProd')] 

 

 cluster('armprodsea.southeastasia.kusto.windows.net').database('Requests').HttpIncomingRequests 

| where PreciseTimeStamp > datetime(2024-08-15 11:10) and PreciseTimeStamp < datetime(2024-08-15 11:20) 

| where subscriptionId == "xxxxxxxxxxxx-xxxx-xxxx-xxxxxxxxxxxx" 

| where (operationName contains "Microsoft.Network") 

| where httpMethod == "PUT" | where httpStatusCode != '-1' 

| httpStatusCode !=200 //n order to filter out (exclude) successful request  

| project PreciseTimeStamp, TaskName, correlationId, operationName, httpMethod, httpStatusCode, targetResourceType, targetUri, userAgent, durationInMilliseconds, clientApplicationId, clientIpAddress

Please note down the Correlation ID along with the Time stamp for the failed requests & proceed with the below steps.

NOTE: If the global cluster and database is not working Please use the below regional clusters

cluster('armprodsea.southeastasia.kusto.windows.net').database('Requests').HttpIncomingRequests cluster('armprodeus.eastus.kusto.windows.net').database('Requests').HttpIncomingRequests cluster('armprodweu.westeurope.kusto.windows.net').database('Requests').HttpIncomingRequests

**B.** ARM Logs to check who made the changes in claims: (Global)

Execute in [Web] [Desktop] [cluster('armprodgbl.eastus.kusto.windows.net').database('ARMProd')]

 cluster('armprodsea.southeastasia.kusto.windows.net').database('Requests').EventServiceEntries | where PreciseTimeStamp > datetime(2024-08-15 11:10) and PreciseTimeStamp < datetime(2024-08-15 11:20) | where subscriptionId == "xxxxxxxxxxxxx-xxxx-xxxx-xxxxxxxxxxxx" | where CorrelationRequestId =='xxxxxxxxxxxxx-xxxx-xxxx-xxxxxxxxxxxx' | where (operationName contains "Microsoft.Network") | where resourceUri contains "NATGateway" // Replace the Natgateway with your Natgateway name | project TIMESTAMP, correlationId, operationId, TaskName, operationName, claims

NOTE: If the global cluster and database is not working Please use the below regional clusters

cluster('armprodsea.southeastasia.kusto.windows.net').database('Requests').EventServiceEntries cluster('armprodeus.eastus.kusto.windows.net').database('Requests').EventServiceEntries cluster('armprodweu.westeurope.kusto.windows.net').database('Requests').EventServiceEntries

**C.** Verify the NRP logs using the Correlation ID in Jarvis DGrep dashboard to check the status https://portal.microsoftgeneva.com/s/8B256207 Execute in [Web] [Desktop] [cluster('nrp.kusto.windows.net').database('mdsnrp')]

cluster('nrp.kusto.windows.net').database('mdsnrp').FrontendOperationEtwEvent | where (TIMESTAMP >= datetime(2024-08-15T11:01:41Z) and TIMESTAMP < datetime(2024-08-15T12:21:41Z)) | where CorrelationRequestId =='xxxxxxxxxxxxx-xxxx-xxxx-xxxxxxxxxxxx'


*(Content truncated — refer to original GT for full details)*

### Step 14: Verify the Port mapping is correct form the front end IP to backend can be verified from the Azure portal for load balancer under inbound NAT rule

### Guidance

Verify the Port mapping is correct form the front end IP to backend, can be verified from the Azure portal for load balancer under inbound NAT rule.

### Question

**Verify the Port mapping is correct form the front end IP to backend.**

### Options

- **YES** → Go to: *verification of port mapping from Front end to backend Insights*
- **NO** → Go to: *Multiple NAT rules can not exist if they have an overlapping port range or have the same backend port*

---

### Step 15: verification of port mapping from Front end to backend Insights

### Support Engineer Solution

Verify that the Port mapping is correct from the front-end IP to backend, this can be verified from the Azure portal for load balancer under inbound NAT rule. 

In azure portal navigate to Azure External Load Balancer, navigate to NAT rules --> Inbound NAT rules  --> Frontend Ports --> Backend Ports 

Check if the Customer is accessing on the port that is configured as front end port for INBOUND NAT  rule 

If port is not matching than inform customer to access on the front end port configured as per Inbound NAT rule. 

Verify the backend server is actively serving for the backend port configured. You can leverage diagnostics tab in ASC for port scan on the Virtual machine in azure. 

If access is failing on correct fornt end & Backend port, proceed to take Network traces on the Source & on the backend pool VM Destination for further validation. 

### Customer Solution

*Content type: MarkdownText*

**Dear [Customer Name],**

Thank you for reaching out to us. We have thoroughly investigated your configuration and identified an issue with port mapping for the inbound NAT rule.

To help ensure smooth connectivity and resolve the issue you are experiencing, we kindly request you to review the following steps in your Azure environment:

---

## 1. Verify Port Mapping

Please confirm that the port mapping from the front-end IP to the backend is correctly configured.

You can check this in the **Azure portal** under your **Load Balancer’s Inbound NAT Rules** section.

---

## 2. Review NAT Rule Configuration

* Navigate to **Azure Portal → External Load Balancer → NAT Rules → Inbound NAT Rules**.

* Check the **Frontend Ports** and **Backend Ports** settings.

* Ensure that you are accessing the service using the port configured as the **Frontend Port** for the Inbound NAT rule.

* If the port does not match, kindly use the correct **frontend port** as per the configuration.

---

## 3. Validate Backend Server

Please confirm that the backend server is actively serving on the configured backend port.

You can use the **Connection Troubleshoot** feature in the Azure portal to perform a port scan on the virtual machine.

---

## 4. Additional Checks

* Verify that access is allowed in the **Network Security Group (NSG)**.

* Ensure the **virtual machine** is listening on the specified port.

* If the connection still fails after these checks, we recommend collecting **network traces** for further analysis.

---

## Helpful Microsoft Learn Resources

* [Inbound NAT rules overview](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-nat-rules)

---

If you encounter any difficulties or need further assistance, please do not hesitate to revert back to me.

**Best regards,**  

[Your Name]  

[Your Organisation]

---

### Step 16: Multiple NAT rules can not exist if they have an overlapping port range or have the same backend port

### Guidance

Please verify and select NO if their is no overlapping of port-range/backend port.

### Question

**Do Multiple NAT rules exist with overlapping port range or have the same backend port ?**

### Options

- **YES** → Go to: *Multiple NAT rules cannot exist if they have an overlapping port range or have the same backend port Insights*
- **NO** → Go to: *Check if there is any NSG or ASG denying the connection to the backend IP address and backend port*

---

### Step 17: Multiple NAT rules cannot exist if they have an overlapping port range or have the same backend port Insights

### Support Engineer Solution

Multiple NAT rules can’t exist if they have an overlapping port range or have the same backend port. 

The frontend, protocol, and port combination of each load balancing rule and inbound NAT rule on a load balancer must be unique. 

In ASC Navigate to the customer load balancer and verify the Inbound NAT rules configuration for front end port and protocol. check if there are multiple rules with overlapping port range or have the same backend port.

### Customer Solution

*Content type: MarkdownText*

**Dear [Customer Name],**

Thank you for reaching out to us. We have thoroughly investigated your configuration and identified an issue with **overlapping ports** for the **inbound NAT rule**.

To help ensure smooth connectivity and resolve the issue you are experiencing, we kindly request you to review the following steps in your **Azure environment**:

---

## 1. Verify Port Mapping

Please confirm if there are multiple rules with **overlapping front-end port ranges** or that have the **same backend port**.

You can check this in the **Azure portal** under your **Load Balancer’s Inbound NAT Rules** section.

---

## 2. Review NAT Rule Configuration

* Navigate to **Azure Portal → External Load Balancer → NAT Rules → Inbound NAT Rules**.

* Check the **Frontend Ports range** and **Backend Ports** settings.

* Ensure that there is **no overlapping front-end port range** and that rules do **not share the same backend port**.

---

### Important Note

Multiple NAT rules **cannot exist** if they have an **overlapping port range** or use the **same backend port**.

The **frontend**, **protocol**, and **port combination** of each **load balancing rule** and **inbound NAT rule** on a load balancer must be **unique** and configured accordingly.

---

If you have any questions or need further assistance, please don’t hesitate to reach out.

**Best regards,**  

[Your Name]  

*Sr Tech Support Engineer, SEE*  

[Your Organisation]

---

---

### Step 18: Check if there is any NSG or ASG denying the connection to the backend IP address and backend port

### Guidance

Select yes to checek if their is NSG/ASG denying the connection to the backend Resource.

### Question

**Is there any NSG or ASG denying the connection to the backend IP address and backend port?**

### Options

- **YES** → Go to: *Check if there is any NSG or ASG denying the connection to the backend IP address and backend port Insights*
- **NO** → Go to: *Confirm if the backend server is listening on the backend port defined in the inbound NAT rule Use VM or load balancer diagnose in ASC to check the same Insights*

---

### Step 19: Check if there is any NSG or ASG denying the connection to the backend IP address and backend port Insights

### Support Engineer Solution

Check if there is any NSG/ASG denying the connection to the backend IP address and backend port

Open the VM in ASC: 

At VM NIC Level: 

Network Section --> Network Interface Card 

This will open the VM NIC & check if any NSG is attached to VM NIC 

  

NSG check at VM Subnet Level: 

Go back to the backend VM in ASC --> Network Profile --> Click on the subnet --> VM associated VNET will be open --> under Subnets go to the backend Pool Subnet --> See if NSG is shown 

If NSG is attached to NSG subnet --> check for Inbound NSG rules. 

check if there are any INBOUND custom deny rules for the frontend port & backend port. 

If yes, then inform the customer to add allow inbound NSG rule for the frontend port & backend port. 

If there is no NSG rule allowing access. To allow access, create NSG rule using the source public IP address to the destination (backend pool) server on the destination NAT port. 

### Customer Solution

*Content type: MarkdownText*

**Dear [Customer Name],**

Thank you for reaching out to us. We have observed there is NSG restricting access to the backend server, please follow the steps below to modify the **Network Security Group (NSG)** settings and allow **inbound access on port 443 (HTTPS)** to your Azure virtual machine.

---

## **Steps to Allow Inbound Access on Port 443**

1. **Sign in to the Azure Portal**

   Go to [https://portal.azure.com](https://portal.azure.com) and sign in with your Azure credentials.

2. **Locate the Network Security Group (NSG)**

   * In the search bar at the top, type **“Network Security Groups”** and select it from the results.

   * Choose the NSG associated with the **virtual machine’s network interface (NIC)** or **subnet**.

3. **Navigate to Inbound Security Rules**

   * In the left-hand menu, select **Inbound security rules**.

   * Review the existing rules to check if there’s already a rule allowing traffic on port **443**.

4. **Add a New Inbound Rule (if not present)**

   * Click on **“Add”** at the top of the Inbound security rules page.

   * Configure the rule as follows:

     * **Source:** Any (or specify an IP range if you want to restrict access)

     * **Source port ranges:** ****

     * **Destination:** Any

     * **Destination port ranges:** `443`

     * **Protocol:** TCP

     * **Action:** Allow

     * **Priority:** Assign a value lower than Deny rules (e.g., 100 or 200)

     * **Name:** `Allow-HTTPS-443`

5. **Save the Rule**

   * Click **Add** to save the configuration.

   * The rule will now appear in the list of inbound rules.

6. **Validate the Configuration**

   * Ensure that the new rule appears **above any deny rules** that might block port 443.

   * Optionally, use the **Connection Troubleshoot** tool under **Network Watcher** to test connectivity on port 443.

---

If you still experience access issues after updating the NSG, please verify that the VM’s **Windows/Linux firewall** also allows inbound connections on 

*(Content truncated — refer to original GT for full details)*

### Step 20: Confirm if the backend server is listening on the backend port defined in the inbound NAT rule Use VM or load balancer diagnose in ASC to check the same Insights

### Support Engineer Solution

Confirm if the backend server is listening on the backend port defined in the inbound NAT rule. Use VM/load balancer diagnose in ASC to check the same.

Open LB in ASC, Diagnostics --> add the frontend & backend ports in diagnostics & click on RUN. 

Check if the target VM is blocking the port as per the listed output. 

If yes than inform the Cx to check if the backend pool VM is listening on the backend port by issuing the below commands 

Windows: netstat -ano TCP | findstr "11924 

Linux: 

Ss -ano 

netstat -ano | grep LISTEN | grep 22 

If ports are not listening than inform Customer to open the port on the backend pool VMs 

If ports are listening than take network traces & see if the interested ports are blocked at VM OS level by any OS level firewall 

Issue the below commands for Windows OS VMs: 

Turn Off all Windows Firewall off for all profiles: 

netsh advfirewall set allprofiles state off 

(After executing the above command in Windows Command Prompt in Administrative mode, if the connection works than it is clear that this is Windows OS Firewall issue.) 

Issue the below command to again turn onn the OS firewall for all profiles 

netsh advfirewall set allprofiles state on 

  

Engage Windows Network team after getting approval from the Windows Net AVA channel to fix the Windows Defender OS Firewall issue. 

Inform Cx to engage their internal team who manage the 3rd party OS firewall & inform them to open the port at OS level. 

For Linux VM, involve VM team on collab after OPEX team approves on AVA to engage VM Linux Team on collab. 

Once Whitelisting is performed, check the connection again. 

 

### Customer Solution

*Content type: MarkdownText*

Dear Customer,

Please confirm if the backend server is listening on the backend port defined in the inbound NAT rule.

You can leverage connection Troubleshoot tab in Azure Portal of Virtual machine for port scan & NSG Rule check on the backend Virtual Machine in Azure Portal.

Further, Check if the target VM is blocking the port as per the listed output.

If yes than I would request you to check the backend pool VM is listening on the backend port by issuing the below commands change the port number as per application.

Windows: netstat -ano TCP | findstr "443

Linux:

Ss -ano

netstat -ano | grep LISTEN | grep 22

 

If ports are not listening than inform your application team to open the port on the backend pool VM or VMSS as per your application functionality.

 

If ports are listening than take network traces & see if the interested ports are blocked at VM OS level by any OS level firewall

Issue the below commands for Windows OS VMs:

Turn Off all Windows Firewall off for all profiles:

netsh advfirewall set allprofiles state off

(After executing the above command in Windows Command Prompt in Administrative mode, if the connection works than it is clear that this is Windows OS Firewall issue.)

Issue the below command to again turn onn the OS 

*(Content truncated — refer to original GT for full details)*
