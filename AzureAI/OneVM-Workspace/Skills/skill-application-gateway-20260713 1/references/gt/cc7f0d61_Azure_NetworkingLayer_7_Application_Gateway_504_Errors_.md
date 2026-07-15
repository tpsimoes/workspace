# Azure Networking][Layer 7] Application Gateway 504 Errors

> **Product:** Application Gateway  
> **Solution ID:** cc7f0d61-8ce5-4107-bd57-89b9ad67d732  
> **Trigger words:** application, application gateway, errors, gateway, networking][layer

---

## Overview

This guide provides step-by-step troubleshooting for **Azure Networking][Layer 7] Application Gateway 504 Errors** under **Application Gateway**.
 The original guided troubleshooter contains 11 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Check Error Code And SAP ⭐ (First Step)

### Guidance

This Guided Troubleshooter will help you to troubleshoot HTTP error code 504 being returned to the user. 

If the error code being returned is different or if the issue is not related to connectivity please correct the Support Are Path and re run the Guided Troubleshooter. 

### Question

**Is the client receiving an HTTP error code 504, while trying to connect?**

### Options

- **Yes, the error is 504** → Go to: *Check the Application Gateway Version*
- **No, the error is not 504** → Go to: *Rerun the Guided Troubleshooter after Setting the correct scope*

---

### Step 2: Check the Application Gateway Version

### Content

In this Step we Check the version of applciation gateway that is tagged to the Case/ASC.

WAF and Standard are categorized as Version1

WAF_2, Standard_2 and Basic are categorized as Version2

You can manually select the SKU if you think the current selection is incorrect. 

---

### Step 3: Rerun the Guided Troubleshooter after Setting the correct scope

### Support Engineer Solution

Please change the SAP and re run the guided troubleshooter. 

This troubleshooter is only valid for the SAP Azure/Application Gateway/Facing 5xx Errors/504 Errors, and where the client receives the error 504

### Customer Solution

*Content type: MarkdownText*

Please change the SAP and re run the guided troubleshooter. 

This troubleshooter is only valid for the SAP Azure/Application Gateway/Facing 5xx Errors/504 Errors, and where the client receives the error 504

---

### Step 4: ApplicationGwV1DoesnotReturn504

### Support Engineer Solution

The application gateway is running either Standard or WAF version 1. 

Version 1 application gateways do not return error code 504. 

Please check the backend server logs to determine why is the error being returned by the backend application. 

### Customer Solution

*Content type: MarkdownText*

Application Gateway version 1 does not return http 504 error messages. 

The error seems to be coming from the backend application that application gateway is connecting to. 

Please collect application level logs to determine if the backend is returning the error. 

---

### Step 5: Check Source for 504

### Guidance

The error HTTP 504, can be returned by the backend or by the Application Gateway itself. To confirm the source of the error, you would need to look at the request response logs for the application gateway. 

The HTTP Status tells the code returned by the gateway. 

The Server Status represents the error returned by the backend. 

If the Http Status shows 504 but the Server Status is empty, it is the gateway that is returning the error. 

If the Http Status and the Server Status both show a 504, then the error is returned by the backend. 

### Question

**Is the error returned by Application Gateway?**

### Options

- **True** → Go to: *Check NVA in Path*
- **False** → Go to: *Insight Backend Returning 504*

---

### Step 6: Insight Application Gateway Returning 504

### Support Engineer Solution

Application Gateway returns and error HTTP 504 if the backend server does not respond to the HTTP request in time. 

The timeout value can be set on the HTTP setting. The time Application Gateway waited before sending the error can be seen in the Request Response log as the Time taken by backend. 

You can try to increase the time out value on the http setting and check if it fixes the issue. However it is the customer's choice to increase it or not. It is the customer who needs to baseline how long the backend should take to respond to the request. 

### Customer Solution

*Content type: MarkdownText*

Application Gateway returns and error HTTP 504 if the backend server does not respond to the HTTP request in time. 

The timeout value can be set on the HTTP setting. The time Application Gateway waited before sending the error can be seen in the Request Response log as the Time taken by backend. 

You can try to increase the time out value on the http setting and check if it fixes the issue. However you would need to confirm the expected time the backend application needs to respond to the HTTP request.  

---

### Step 7: Insight Backend Returning 504

### Support Engineer Solution

Since the Backend is returning error 504, ask the customer to check why the backend servers are returning error 504. They can collect application specific data on the backend to check why the backend is returning the error

### Customer Solution

*Content type: MarkdownText*

The Backend Application server is returning error 504 and is out of scope of Application Gateway. 

In this scenario, you will need to collect application level logs on the backend server to determine why the application server is returning the error code. 

You could also try to access the backend server directly using the same HTTP request and check if the same error is returned. This will rule the application gateway out. 

---

### Step 8: Check NVA in Path

### Guidance

Application gateway returns an 504 error if the backend server does not respond in time. While it might seem an issue on the backend application, at times devices in the path can also add delays. In this step we determine if the request from the Gateway to the Backend goes directly or through an NVA. 

To determine if there is an NVA in path, perform a test traffic on the gateway instances to test the path the instance is taking to reach the backend server. 

To do this please follow the below steps:

1. Locate the Gateway Subscription ID from ASC. This will be different from the Customer's Subscription ID

2. Add the subscription ID to ASC

3. Look for the resource group called armrg-{GatewayID}

4. Under Microsoft Compute you should be able to see the Application gateway instances

5. You can then perform an outbound test traffic(Diagnostics Tab) on the instances to verifiy the next hop. Set the destination ip as the backend IP and the Source IP as the instance IP. 

Also check the effective route table at the end of the test traffic to determine the next hop for the backend servers. 

### Question

**Is there a NVA or VPN device in the path?**

### Options

- **True** → Go to: *Check if NVA is causing the issue*
- **False** → Go to: *Insight Application Gateway Returning 504*

---

### Step 9: Check if NVA is causing the issue

### Guidance

Since there is a NVA/VPN device in the path of the application gateway, these devices can cause delays on the network causing the request to time out. 

Below are few checkes that can be performed:

1. Is this the desired path?

2. Is the NVA causing delays? This is something that the customer can confirm. We can have them collect network traces on the NVA and the backend. We can take network traces on the instances and check if there are delays

3. Bypass the NVA to validate if the issue gets resolved.  

### Question

**Is the NVA causing delays on the network?**

### Options

- **True** → Go to: *Insigth NVA Causing Delay*
- **False** → Go to: *Insight Application Gateway Returning 504*

---

### Step 10: Insigth NVA Causing Delay

### Support Engineer Solution

If Bypassing the NVA fixes the issue or if the customer has ruled this out to delays on the NVA, have the customer involve the vendor of the NVA and check for the cause 

If the delay is expected, then have the customer increase the time out value on the HTTP settings on the application gateway. 

### Customer Solution

*Content type: MarkdownText*

We have identified that the delay is being caused by a third party device between the application gateway instances and the backend servers. 

Since the device is not owned by Microsoft, we would recommend that you involve the vendor of the device to check the cause for the delay. 

If you do not desire to go through the device, then please make changes to the routes that the application gateway subnet is receiving. 

However if the delay is expected we recommend that you increase the Timeout value on the HTTP setting on the Application gateway. 

---

### Step 11: Validate the Appgw version manually

### Guidance

In this Step we Check the version of Application gateway that is tagged to the Case/ASC.

WAF and Standard are categorized as Version1

WAF_2, Standard_2 and Basic are categorized as Version2

Manually select the appropriate SKU. 

### Question

**What is the version of AppGW?**

### Options

- **Version1** → Go to: *ApplicationGwV1DoesnotReturn504*
- **Version2** → Go to: *Check Source for 504*

---
