# CRUD Issues with Load Balancer

> **Product:** Load Balancer  
> **Solution ID:** ee87a493-e494-42b8-8ad8-fa4c5b633e33  
> **Trigger words:** balancer, create delete update failed, load balancer

---

## Overview

This guide provides step-by-step troubleshooting for **CRUD Issues with Load Balancer** under **Load Balancer**.
 The original guided troubleshooter contains 7 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Migration Happening from V1 to V2 ⭐ (First Step)

### Guidance

Please selection Yes or No to the question below

### Question

**Is there a migration happening from V1 to V2 where the load balancer is stuck in its migration phase. Something like the following error "Please check audit logs for more details.(Code:ResourceGroupDeletionTimeout) Operation is not allowed on Load balancer, because it's being migrated from Microsoft.ClassicNetwork (v1 APIs) to Microsoft.Network (v2 API). (Code: OperationNotAllowedOnResourceDuringMigration, Target: LB-Resource"**

### Options

- **Yes** → Go to: *Solution if Yes is selected for v1 to v2 conversion*
- **No** → Go to: *Check for LB*

---

### Step 2: Solution if Yes is selected for v1 to v2 conversion

### Support Engineer Solution

This message is seen or something similar regarding a CRUD issue and a load balancer:
```
Deletion of resource group 'rg-name' did not finish within the allowed time as resources 
with identifiers 'Microsoft.Network/loadBalancers/lb-resource, 
Microsoft.Network/publicIPAddresses/public-ip-resource' could not be deleted. 
The provisioning state of the resource group will be rolled back. 
The tracking Id is 'Some-ID'.Please check audit logs for more details.(Code:ResourceGroupDeletionTimeout)
Operation is not allowed on Load balancer, because it's being migrated from Microsoft.ClassicNetwork (v1 
APIs) to Microsoft.Network (v2 API). (Code: OperationNotAllowedOnResourceDuringMigration, 
Target: LB-Resource
```
What are next steps? Follow below: 

Step 1:) Go into ASC and go the Operations tab and check out under the ARM/NRP operations section that you can verify the error in the ticket and see if there is any extra data which may help. 

Step 2:) Ask the customer for a correlation ID and a time stamp. Once provided by the customer you can go to the subscription where the resource is provisioned and click on the subscription ID-> Go to Operations and filter via the time and date and check out the ARM and NRP operations and check to see if it provides more detail to troubleshoot.

Step 3:) Try to perform a GET operation on the load balancer as outlined here with the customer to see if that does anything to get it out of the migration state: [GET Request Load balancer](https://learn.microsoft.com/en-us/rest/api/load-balancer/load-balancers/get?tabs=HTTP)

Step 4:) If the above steps fail try the following at this point (if you haven't already it may be a good idea to involve a TA via Ava and provide your findings but also continue troubleshooting below):

Q: **Why did your original operation on the load balancer fail?**
A: This kusto query may be able to help with figuring that out:
```
let ['_startTime']=datetime('YYYY-MM-DD HR:MIN');
let ['_endTime']=datetime('YYYY-MM-DD HR:MIN');
cluster('rdfeprod.kusto.windows.net').database('rdfeprodDB').DeploymentContextActivityEtwTable
| where OperationId == "Get me from ASC under the operations tab for the subscription"
| where TIMESTAMP >= _startTime and TIMESTAMP < _endTime
| project TIMESTAMP, EventName,OperationId,OperationName,Message,HostedServiceName,DeploymentName,DeploymentId,SubscriptionId,Tenant,Role,RoleInstance,Level
| order by TIMESTAMP asc
```
Q:**What is the current migration status?**
A: This kusto query can let us know but we will need a deployment ID from ASC/Jarvis.Once you have the Operation ID feel free to use this link to find the deployment ID [Link for Deployment ID need Operation ID first](https://portal.microsoftgeneva.com/s/A003AB3B)

If you encounter a scenario where a customer attempted to migrate their resources from classic to ARM and either stopped the process mid-migration or closed out of the window due to receiving errors and now their resources

*(Content truncated — refer to original GT for full details)*

### Step 3: You selected No

### Support Engineer Solution

If you select "No" here post your information to Ava including time stamp operations, if its about updating, the backend pool information and any kusto queries run regarding this and relevant kusto queries.

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 4: Possible Solution for load balancers

### Support Engineer Solution

-Once you identify the resource that is in a failed state, go to [Azure Resource Explorer](https://resources.azure.com/) 

-Identify the resource in this state.

-Update the toggle on the right-hand top corner to Read/Write.Select Edit for the resource in failed state.Select PUT followed by GET to ensure the provisioning state was updated to Succeeded.

-You can then proceed with other actions as the resource is out of failed state.

-If this doesn't work please go to Ava and provide you're troubleshooting there.

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 5: Decision with fabric controllerChoice

### Support Engineer Solution

Contact the virtual machine team as the error may be related to this: [Network Internal Operation Error](https://supportability.visualstudio.com/AzureIaaSVM/_wiki/wikis/AzureIaaSVM/495442/NetworkingInternalOperationError_Start-Stop?anchor=causehttp://)

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 6: decision with fabric controller

### Guidance

Do you need to contact the VM team?

### Question

**Do you see an error regarding the NetworkingInternalOperationError? or regarding availability sets?**

### Options

- **Yes** → Go to: *Decision with fabric controllerChoice*
- **No** → Go to: *You selected No*

---

### Step 7: Check for LB

### Guidance

Please answer the following question to see if your load balancer is stuck in a failed or updated state but not getting the above error?

### Question

**Is your load balancer stuck in an updated or failed state? (That doesn't mention the prior error?)**

### Options

- **Yes** → Go to: *Possible Solution for load balancers*
- **No** → Go to: *decision with fabric controller*

---
