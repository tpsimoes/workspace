# ANP Application Gateway] 5xx errors

> **Product:** Application Gateway  
> **Solution ID:** 2fe5cb93-a2ed-4825-ab1e-908494ed507f  
> **Trigger words:** application, application gateway, errors, gateway]

---

## Overview

This guide provides step-by-step troubleshooting for **ANP Application Gateway] 5xx errors** under **Application Gateway**.
 The original guided troubleshooter contains 7 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Seeing 5xx errors ⭐ (First Step)

### Guidance

This Guided Troubleshooter will help you to troubleshoot HTTP error code 5xx being returned to the user while hitting Application Gateway URL.

If the error code being returned is different or if the issue is not related to connectivity, please correct the Support Area Path and re-run the Guided Troubleshooter.

### Question

**Is Application Gateway URL returning 5xx error to client?**

### Options

- **Yes** → Go to: *Validate source of 5xx error*
- **No** → Go to: *Rerun the Guided Troubleshooter after setting the correct SAP*

---

### Step 2: Rerun the Guided Troubleshooter after setting the correct SAP

### Support Engineer Solution

Please change the SAP and re-run the Guided Troubleshooter.

This troubleshooter is only valid for the SAP Azure/Application Gateway/Facing 5xx Errors.

### Customer Solution

*Content type: MarkdownText*

Please change the SAP and re-run the Guided Troubleshooter.

This troubleshooter is only valid for the SAP Azure/Application Gateway/Facing 5xx Errors.

---

### Step 3: Validate source of 5xx error

### Guidance

Validate the source of 5xx error whether its returned by backend(*server status*) itself or only Application Gateway(*http status*). This can be verified with the help of Request Response logs.

How to check Req Res logs, refer this wiki: [https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/257422/Log-Sources-For-Application-Gateway?anchor=request-response-logs](link)

ReqRes logs : [https://portal.microsoftgeneva.com/s/D147CB74](link)

**NOTE:** In v1, server status can be found in properties section. In v2, there is a seperate column named "server_status".

### Question

**Is the error returned by backend?**

### Options

- **Yes** → Go to: *Backend returning error*
- **No** → Go to: *Application gateway returning error*

---

### Step 4: Backend returning error

### Support Engineer Solution

Check ReqRespErrorLog (V2) or InformationLogEvent (V1) to ensure that there is no connection failure between App Gateway and backend. These logs can be filtered with Client IP and the URI of the HTTP request which got 5xx response as found from ReqRespLog.

Data location:

Application Gateway V2: Jarvis > AppGWT > **ReqRespErrorLog**

Application Gateway V1: Jarvis > AppGWT > **InformationLogEvent**

If there are no errors found in Application Gateway logs and the 5xx response can be seen coming from the backend, customer needs to check the backend application logs and dig further at application level. If customer does not agree, ask them to access backend application directly(bypassing Application Gateway) from another VM in same VNET as of backend server and you should get same 5xx response.

Please ask the customer to check backend server/application logs to understand why the server is giving this response. If the backend service is also an Azure Service (such as AppService or APIM, or other PaaS services), if needed, please engage the other team for assistance on reviewing the backend application/service.

### Customer Solution

*Content type: MarkdownText*

The Backend Application server is returning 5xx error and needs to be investigated on backend application itself.

In this scenario, kindly check backend server/application logs to understand why the server is returning this response. If the backend service is also an Azure Service (such as AppService or APIM, or other PaaS services), we can help you engage respective team from our end if needed.

If you need to verify this, try to access backend application directly(bypassing Application Gateway) from another VM in same VNET as of backend server and you should get same 5xx response.

---

### Step 5: Application gateway returning error

### Guidance

If Application Gateway is returning the error, then check which specific error code being returned. Confirm it using Req Res logs as checked in previous step.

### Question

**Which status code?**

### Options

- **500** → Go to: *500 status code*
- **502** → Go to: *d88f3f43-0cc3-4143-aced-c4820b56e8ec*
- **503** → Go to: *503 status code*
- **504** → Go to: *cc7f0d61-8ce5-4107-bd57-89b9ad67d732*

---

### Step 6: 500 status code

### Support Engineer Solution

**"INTERNAL SERVER ERROR"**
The server encountered an unexpected condition that prevented it from fulfilling the request.

This can be expected behavior for V2 application gateway during crud operations. Config change requires restart web server on the application gateway. During restart process, App gateway can present 500 error messages for a brief period of time. Confirm for any CRUD operation happened on Appgw during same time.

Control plane dashboard: [https://portal.microsoftgeneva.com/s/F79E02F8?overrides=[{"query":"//*[id='ResourceUri']","key":"value","replacement":""},{"query":"//*[id='ResourceId']","key":"value","replacement":""}]%20](link)

### Customer Solution

*Content type: MarkdownText*

**"INTERNAL SERVER ERROR"**

The server encountered an unexpected condition that prevented it from fulfilling the request.

This can be expected behavior for V2 application gateway during crud operations. Config change requires restart web server on the application gateway. During restart process, App gateway can present 500 error messages for a brief period of time. Confirm for any CRUD operation happened on Appgw during same time.

Control plane dashboard: [https://portal.microsoftgeneva.com/s/F79E02F8?overrides=[{"query":"//*[id='ResourceUri']","key":"value","replacement":""},{"query":"//*[id='ResourceId']","key":"value","replacement":""}]%20](link)

---

### Step 7: 503 status code

### Support Engineer Solution

**"SERVICE UNAVAILABLE"**
Server is not able to handle the connections since it is either overloaded or is refusing the connection.

An app gateway can only generate specific HTTP status codes, so whether its v1 or v2, this error indicates that the issue lies in the backend pool rather than the app gateway itself, meaning that a collab with backend service team will most likely be necessary.

Example wiki(for API management gateway and App service as backend): [https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/140221/Troubleshooting-Gateway-503-errors](link)

### Customer Solution

*Content type: MarkdownText*

**"SERVICE UNAVAILABLE"**

Server is not able to handle the connections since it is either overloaded or is refusing the connection.

An app gateway can only generate specific HTTP status codes, so whether its v1 or v2, this error indicates that the issue lies in the backend pool rather than the app gateway itself, meaning that a collab with backend service team will most likely be necessary.

Example wiki(for API management gateway and App service as backend): [https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/140221/Troubleshooting-Gateway-503-errors](link)

---
