# Application Gateway WAF: Traffic Analysis

> **Product:** Application Gateway  
> **Solution ID:** 47a18936-39a1-4329-847f-91e638485daa  
> **Trigger words:** analysis, application, application gateway, gateway, traffic

---

## Overview

This guide provides step-by-step troubleshooting for **Application Gateway WAF: Traffic Analysis** under **Application Gateway**.
 The original guided troubleshooter contains 18 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Applicaton Gateway WAF Analyze traffic Scope Check ⭐ (First Step)

### Guidance

## Check if this TSG applies to your customer's scenario
This TSG is targetted to provide steps in scenarios where the customer wants to know why a legitimate request is blocked by Application Gateway WAF or why a request that should have been blocked was allowed by Application Gateway WAF

**Note**  
If your issue is not from the list above, you may use **Edit & Run Again** feature on the **ASC** to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results.

### Question

**Is the customer looking to understand why a request was blocked/allowed by Application Gateway WAF?**

### Options

- **Yes this is my Scenario** → Go to: *Legitimate Traffic Blocked Analysis*
- **No** → Go to: *Not a WAF issue*

---

### Step 2: Traffic Blocked Due to BOT

### Support Engineer Solution

List down the Following Environment Details from ASC:

1. WAF Sku
2. WAF mode
3. Is the customer using a WAF policy or are they using the inbuilt WAF
4. What version of OWASP rule is being used
5. Confirm if BOT protection is enabled

Use the Above WAF logs to determine
1. The Client IP
2. The name of the BOT

Go to https://aka.ms/interflowweb  and search for the IP address being blocked.
If this is a valid BOT reach out to PG through AVA/TA approval to allow this traffic

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 3: Allowed Traffic Solution

### Support Engineer Solution

Collect a HAR/Fiddler from the client

Check for any custom allow rules that could be allowing the traffic based on any of the parameters in the request

Reproduce the issue using Post man by sending the same headers as the customer to see if WAF in your environment also blocks the request

Engage a TA using AVA if none of the above helps

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 4: Issue resolved for Size blocks

### Support Engineer Solution

We are glad that the issue is fixed using the above method. 

If the issue was fixed by disabling request body filtering please educate the customer that the body will no longer be inspected for malacious activity. 

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 5: Set Waf to Prevention mode

### Support Engineer Solution

When WAF is in Detection mode,no traffic will be blocked. 

App gwateway will only log the traffic in the logs, and the traffic will be allowed.

Set WAF to prevention mode.

If this does not help, run through the TSG again.

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 6: Not a WAF issue

### Support Engineer Solution

The Issue you are troubleshooting is not a WAF issue

Please set the SAP to the correct Path and re run the diagnostics

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 7: Traffic Blocked Due to Pattern Match

### Support Engineer Solution

List down the Following Environment Details from ASC:

1. WAF Sku
2. WAF mode
3. Is the customer using a WAF policy or are they using the inbuilt WAF
4. What version of OWASP rule is being used

Using the WAF logs please perform the below actions:

* Take a note of the Rule ID/s that are Matching the request. 
* Identify the Header name and the content that is being blocked. 
* If the logs are not clear you can collect a Fiddler/HAR from the client to understand the request parameters

Once the Headers and content are identified you can propose the following solution to the customer

* Create an Exception for the header in the WAF Exceptions
* Create Custom rule for the identified values
* Ask the customer to see if they can avoid sending the patterns on the request
* Disable the Rule Number that is causing the issue 

###Recommended Reading 
[Azure WAF Troubleshooting](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/133410/Application-Gateway-WAF-Troubleshooting-Guide)

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 8: Traffic Blocked Due to Size Limits

### Support Engineer Solution

You have reached this step since you have reached the Size limits and the customer is not willing to disable request body filtering or disabling request body filtering has not fixed the issue.

Reach out to a Technical Advisor through AVA or escalate following the right process

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 9: Check for Error code 403

### Guidance

If WAF is the blocking traffic the error code would be 403.
If the Error code is not 403, then the traffic is not blocked by WAF. Please set the correct SAP and re run the TSGs

### Question

**Is the client receiving 403 as an error code?**

### Options

- **Yes** → Go to: *Check Source for error code 403*
- **No** → Go to: *Not a WAF issue*

---

### Step 10: Modify Request Size Limits

### Guidance

List down the Following Environment Details from ASC:

1. WAF Sku
2. WAF mode
3. Is the customer using a WAF policy or are they using the inbuilt WAF
4. What version of OWASP rule is being used

Check the document for [Upload Limits for Azure Application Gateway WAF](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits)

* Modify the request limits if the thresholds are not breached

### Question

**Did this fix the issue?**

### Options

- **Yes** → Go to: *Issue resolved for Size blocks*
- **No** → Go to: *Update to 32 Owasp*

---

### Step 11: Check if WAF is in prevention or detection mode

### Guidance

We would be looking at why WAF Is allowing traffic that should have been blocked

Check if WAF is in detection or prevention mode

### Question

**Is WAF in Prevention Mode?**

### Options

- **Yes** → Go to: *Check If backend pool is Empty*
- **No** → Go to: *Set Waf to Prevention mode*

---

### Step 12: Identify the Type of Block

### Guidance

In this step try to identify if the request is being blocked because of a:

1. Pattern Match
2. Size Limit
3. Bot Protection

To do so look at the WAF logs generated by App gateway on Jarvis Logs. 
Use the transaction ID (noted in the previous step) as a filter

**Note**

* Requests with Transaction IDs that end in a block are the ones that are getting are blocked by WAF
* For a particular Transaction ID, focus on the rules before the block rule. This will tell you if the rule was a pattern match, Waf limits or BOT 

[Application Gateway WAF Logs](https://jarvis-west.dc.ad.msft.net/EBB8567B)

Scoping/Filtering: The tenant should be updated to reflect the deployment ID of the application gateway.

Path: (Jarvis Logs > AppGWT > ApplicationGatewayFirewallLog)

### Question

**Select the rule type that results in the request being blocked**

### Options

- **Pattern Match** → Go to: *Traffic Blocked Due to Pattern Match*
- **Size Limits** → Go to: *Modify Request Size Limits*
- **Bot Protection** → Go to: *Traffic Blocked Due to BOT*

---

### Step 13: Update to 32 Owasp

### Guidance

If the customer has reached the limits, check if the customer is using OWASP 3.2. If not, have the customer move to 3.2 since the upload limits are higher in 3.2

Please do this change during a downtime, since 3.2 can add new rules that could block traffic that previously was allowed.

You can then increase the upload size limit on WAF

### Question

**Did this fix the issue?**

### Options

- **Yes** → Go to: *Issue resolved for Size blocks*
- **No** → Go to: *Disable Request Body Filtering*

---

### Step 14: Check Source for error code 403

### Guidance

Some times a 403 could be returned by the Backend. 
If that is indeed the case then WAF is not at fault. The backend needs to be investigated
Have a look at the Request Response logs and make sure the server status is empty
Also Take a note of the Transaction ID

Load the Request response log for the failing request in Jarvis. In the Reques Response logs
properties column check for the below values: 

* Http Status: This is the status returned by Application gateway to the Client
* Server Status: This is the status returned by the backend to the application gateway. 

If WAF is blocking the request the server status would be empty. 

### Question

**Is the server status empty in the request response logs?**

### Options

- **Yes** → Go to: *Identify the Type of Block*
- **No** → Go to: *Not a WAF issue*

---

### Step 15: Disable Request Body Filtering

### Guidance

If WAF has reached the maximum limits, you can disable request body filtering that will allow the request to be allowed. 

However you need to update the customer with the risks involved with this approach

### Question

**Did this fix the issue**

### Options

- **Yes** → Go to: *Issue resolved for Size blocks*
- **No** → Go to: *Traffic Blocked Due to Size Limits*

---

### Step 16: Legitimate Traffic Blocked Analysis

### Guidance

Understand from the customer if they are looking to check for a healthy traffic being blocked, or if they are trying to understand why a request that should have been blocked was allowed

### Question

**Is the Customer looking to understand why**

### Options

- **Traffic that should have been Allowed, was Blocked by Application Gateway WAF** → Go to: *Check for Error code 403*
- **Traffic that should have been blocked, was allowed by Application Gateway WAF** → Go to: *Check if WAF is in prevention or detection mode*

---

### Step 17: Check If backend pool is Empty

### Guidance

An application gateway can return an error 502, even though the response should be 403. 

This can happen if application gateway backend pool is empty i.e. the backend pool exists for that listener but there are no backends in it. 

### Question

**Is the application gateway retunring an error 502 and the backend pool is empty?**

### Options

- **Yes** → Go to: *EmptyBackend502Solution*
- **No** → Go to: *Allowed Traffic Solution*

---

### Step 18: EmptyBackend502Solution

### Support Engineer Solution

It is an expected behavior. If the listener handling the request has a backend pool with no backends in it, then the WAF check is bypassed and responds with a 502. 

### Customer Solution

*Content type: MarkdownText*

Hello <Customer Name>

The 502 is being returned instead of 403 because the backend pool to which the listener is tied to is empty. Since the backend pool is empty, WAF rules are not evaluated and a 502 is returned. 

You can add an IP address to the backend and test. 

Thank You

---
