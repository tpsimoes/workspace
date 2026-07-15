# Application Gateway Web Application Firewall (WAF)/WAF Per-Site Policy

> **Product:** Application Gateway  
> **Solution ID:** 09cf2a5a-9164-4d0b-93d6-4ffc9ff7bd45  
> **Trigger words:** (waf)/waf, application, application gateway, firewall, gateway, policy

---

## Overview

This guide provides step-by-step troubleshooting for **Application Gateway Web Application Firewall (WAF)/WAF Per-Site Policy** under **Application Gateway**.
 The original guided troubleshooter contains 18 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Confirm Scope ⭐ (First Step)

### Guidance

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

### Question

**Is the customer's issue related to per-listener WAF policies on APPGW V2?**

### Options

- **Yes** → Go to: *Select issue type*
- **No** → Go to: *Not In Scope*

---

### Step 2: Not In Scope

### Support Engineer Solution

This issue is not in scope for this troubleshooting guide. Please change the SAP and refresh to follow the appropriate TSG.

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

---

### Step 3: Select issue type

### Guidance

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

### Question

**Is the issue related to WAF false positives, WAF false negatives, or CRUD issues?**

### Options

- **False Positives** → Go to: *False Positive Select Action*
- **False Negatives** → Go to: *False Negative Confirm Config Is Correct*
- **CRUD issues** → Go to: *CRUD Select Issue Type*

---

### Step 4: False Positive Select Action

### Guidance

 https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

### Question

**Locate an example request in the WAF logs. Is the WAF action "Matched"?**

### Options

- **Yes** → Go to: *False Positive Next Steps*
- **No** → Go to: *False Positive Not In Scope*

---

### Step 5: False Positive Next Steps

### Support Engineer Solution

In the WAF logs, locate the "ruleid" field to determine what rules is being triggered, then locate the "message" field and determine what portion of the request is triggering the rule. 

The customer can either disable the rule completely, create an exclusion, or create a custom allow rule for this traffic.

Please review the following wiki for guidance on creating exclusions: 
https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/767495/How-to-identify-the-section-that-triggered-the-WAF-rule-from-the-request

**Note that custom allow rules authorize the transaction, skipping all other rules.** The specified request is added to the allowlist and once matched, the request stops further evaluation and is sent to the backend pool. Rules that are on the allowlist aren't evaluated for any further custom rules or managed rules.

### Customer Solution

*Content type: MarkdownText*

https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/767495/How-to-identify-the-section-that-triggered-the-WAF-rule-from-the-request

---

### Step 6: False Positive Not In Scope

### Support Engineer Solution

The scenario described is not a false positive. A false positive is when the customer does not expect a certain request to be blocked, but it is. Please change the case's SAP and refresh, or revert to a previous step and proceed.

If the WAF action is marked as "Blocked" on 949110, you need to look for a "matched" action instead, as this rule is simply anomaly scoring. For details on how anomaly scoring works, please read this documentation: https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/ag-overview#anomaly-scoring-mode

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

---

### Step 7: False Negative Confirm Config Is Correct

### Guidance

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

### Question

**Ensure all of the following are true: Rule is enabled, rule is part of a policy which is applied to the correct listener, WAF policy is set to prevention.**

### Options

- **These are all true.** → Go to: *False Negative Review Logging*
- **Not all of these are true.** → Go to: *False Negative Improper Config*

---

### Step 8: False Negative Review Logging

### Guidance

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

### Question

**Reproduce or have the CX reproduce the false negative, preferably while taking a HAR trace. Check the WAF logs. Does a log entry exist in the WAF logs for this request?**

### Options

- **Yes, the WAF action is Log or Allow.** → Go to: *False Negative Next Steps*
- **Yes, the WAF action is Block.** → Go to: *False Negative Not In Scope*
- **No WAF log entry exists for this request.** → Go to: *False Negative Check Access Logs*

---

### Step 9: False Negative Not In Scope

### Support Engineer Solution

The issue described is not a false negative. A false negative describes traffic which is expected to be blocked, but is not. 

Please restart the troubleshooter, or adjust the case's SAP and refresh ASC to follow the appropriate TSG.

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

---

### Step 10: False Negative Next Steps

### Support Engineer Solution

The request is being logged as action = log or action = allow, while the customer expects the request to be blocked. 

This indicates either that the custom rule this request is triggering is incorrectly configured with an "allow" or "log" action, or that a higher priority rule has caught the request. 

In the first case, the customer can simply change the rule's action. In the second case, the customer will have to reconsider their rule priority.

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

---

### Step 11: False Negative Check Access Logs

### Guidance

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

### Question

**Attempt to locate the request from the client-side HAR trace in the ReqRespLogs using the timestamp, request URI, and clientIP.  Is the request present?**

### Options

- **Yes** → Go to: *False Negative Har Trace Examination*
- **No** → Go to: *False Negative Missing Logs*

---

### Step 12: False Negative Missing Logs

### Support Engineer Solution

If the request does not appear in the application gateway's request/response logs, this suggests that the traffic is not traversing the application gateway at all, in which case no WAF actions can be performed.

The customer must route traffic through the gateway for the rules to be processed.

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

---

### Step 13: False Negative Improper Config

### Support Engineer Solution

In order for a rule to perform a block action, the rule must be enabled, must be part of a policy which is applied to the correct listener, and the WAF policy containing the rule must be set to prevention mode.

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

---

### Step 14: False Negative Har Trace Examination

### Support Engineer Solution

You have now verified that the rule is enabled, applied to the correct  listener, is contained in a WAF policy set to "protection" mode, and that the customer's traffic is traversing the application gateway. You have also reproduced the false negative and have a HAR trace of the request that should be blocked.

At this point, you will need to review the HAR trace with the customer and help them to determine what factors they are looking to block for, and that this is supported as a match condition. Supported natch conditions include request method, query string, erquest URI, request headers, postargs, request body, or request cookies, geo locations, and IP addresses.

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/create-custom-waf-rules

---

### Step 15: CRUD Select Issue Type

### Guidance

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot

### Question

**Is the customer's CRUD issue related to not being able to add a policy to a listener, not being able to configure a specific rule, or a failed state/failed operation?**

### Options

- **Can't add policy to listener** → Go to: *CRUD Cant Add Policy To Listener*
- **Can't add desired rule** → Go to: *CRUD Cant Add Desired Rule*
- **Failed operation/failed state** → Go to: *CRUD Failed Operation or Failed State*

---

### Step 16: CRUD Cant Add Desired Rule

### Support Engineer Solution

The customer may be trying to configure a rule using match conditions which are not supported.

A custom rule can be configured on the following conditions: 

IP address, Geo Location, Request method, Query string, Request headers, Post arguments, Request body, Request cookies.

If you cannot find a clear answer for the specific match condition the CX would like to use, please contact a fellow engineer, an APPGW SME, or create an AVA post to discuss with a TA. 

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-customize-waf-rules-portal

---

### Step 17: CRUD Failed Operation or Failed State

### Support Engineer Solution

Please change the SAP to "failed operation" or "failed state" in DFM and refresh ASC to follow the appropriate TSG.

### Customer Solution

*Content type: MarkdownText*

https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/140206/Troubleshooting-Azure-Networking-CRUD-Failures

---

### Step 18: CRUD Cant Add Policy To Listener

### Support Engineer Solution

Ensure the following are true: 

1. GW SKU is WAF_V2, 

2. CX is attempting to configure the per-listener WAF policy using either powershell or the WAF policy portal page. CX can not use the app gateway's portal page. 

3. The WAF policy is AGW SKU and not AFD SKU.

CX should be able to associate a policy within the same subscription from the policy's portal page.

### Customer Solution

*Content type: MarkdownText*

https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/per-site-policies

---
