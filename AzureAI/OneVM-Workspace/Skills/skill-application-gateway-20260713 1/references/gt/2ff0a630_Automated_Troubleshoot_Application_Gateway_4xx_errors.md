# Automated] Troubleshoot Application Gateway 4xx errors

> **Product:** Application Gateway  
> **Solution ID:** 2ff0a630-abb4-453a-840d-3c86a960b6cc  
> **Trigger words:** application, application gateway, automated], errors, gateway, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Automated] Troubleshoot Application Gateway 4xx errors** under **Application Gateway**.
 The original guided troubleshooter contains 16 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Scoping the error code ⭐ (First Step)

### Guidance

Please identify the HTTP error.

### Question

**Are you getting HTTP 4xx (e.g., 400, 401, 403, etc.) errors while accessing the Application Gateway?**

### Options

- **Yes** → Go to: *Bypass Application Gateway*
- **No** → Go to: *No 4xx error*

---

### Step 2: Bypass Application Gateway

### Guidance

Try accessing the web page or application directly.

### Question

**Bypass the Application Gateway (access the web page or application directly).  Do you still see a 4xx error?**

### Options

- **Yes** → Go to: *4xx is from backend*
- **No** → Go to: *Check 4xx response code*
- **Neither - I can't bypass the Application Gateway** → Go to: *Unable to bypass Application Gateway*

---

### Step 3: 4xx is from backend

### Support Engineer Solution

HTTP 4xx errors (e.g., 400, 401, 403, etc.) are coming from the backend application and not from the Application Gateway. Please check your backend application logs to investigate the reasons for the 4xx error.

### Customer Solution

*Content type: MarkdownText*

HTTP 4xx errors (e.g., 400, 401, 403, etc.) are coming from the backend application and not from the Application Gateway. Check your backend application logs to investigate the reasons for the 4xx error.

---

### Step 4: Check 4xx response code

### Guidance

HTTP 4xx error codes indicate client side errors. Common Application Gateway 4xx errors are:

- 400 Bad Request

- 401 Unauthorized

- 403 Forbidden

- 404 Page not found

- 408 Request Timeout

- 413 Request Entity Too Large

- 499 Client closed the connection

### Question

**What is the 4xx response code you are receiving?**

### Options

- **400 Bad Request** → Go to: *400 Bad Request*
- **401 Unauthorized** → Go to: *401 Unauthorized*
- **403 Forbidden** → Go to: *403 Forbidden*
- **404 Page not found** → Go to: *404 Not Found*
- **408 Request Timeout** → Go to: *408 Request Timeout*
- **413 Request Entity Too Large** → Go to: *413 Request Entity Too large*
- **499 Client closed the connection** → Go to: *499 Client closed the connection*

---

### Step 5: 400 Bad Request

### Support Engineer Solution

### Common reasons for 400 Bad Request errors:

1. The Application Gateway supports HTTP/HTTPS traffic. If non-HTTP/HTTPS traffic is sent to the Application Gateway, it may throw this error.

2. HTTP traffic is initiated towards HTTPS listener, with no HTTP to HTTPS redirection configured. To configure HTTP to HTTPS redirection, see [Redirection Configuration](https://learn.microsoft.com/en-us/azure/application-gateway/redirect-http-to-https-portal)

3. Mutual authentication has been configured and negotiation is failing.

4. The request is RFC non-compliant.

You can also refer the following document for more details: [400 - Bad Request](https://learn.microsoft.com/en-us/azure/application-gateway/http-response-codes#400--bad-request)

 

### Customer Solution

*Content type: MarkdownText*

### Common reasons for 400 Bad Request errors:

1. The Application Gateway supports HTTP/HTTPS traffic. If non-HTTP/HTTPS traffic is sent to the Application Gateway, it may throw this error.
2. HTTP traffic is initiated towards HTTPS listener, with no HTTP to HTTPS redirection configured. To configure HTTP to HTTPS redirection, see [Redirection Configuration](https://learn.microsoft.com/en-us/azure/application-gateway/redirect-http-to-https-portal)
3. Mutual authentication has been configured and negotiation is failing.
4. The request is RFC non-compliant.

See [400 - Bad Request](https://learn.microsoft.com/en-us/azure/application-gateway/http-response-codes#400--bad-request) for details.
 

---

### Step 6: 401 Unauthorized

### Support Engineer Solution

401 Unauthorized error is returned if the client is not authorized to access the backend application. Kindly check the user access.

The following are a few reasons with potential fixes:

1. If the client has access, it might have an outdated browser cache. Clear the browser cache and try accessing the application again.
2. An HTTP 401 Unauthorized response can be returned to the AppGW probe request if the backend pool is configured with NTLM authentication. In this scenario, the backend is marked as healthy. There are several ways to resolve this issue:
    - Allow anonymous access on backend pool.
    - Configure the probe to send the request to  another "fake" site that doesn't require NTLM. This is not a recommended method, as this won't tell us if the actual site behind the application gateway is active or not.
    - Configure application gateway to allow 401 responses as valid for the probes "Probe matching conditions".

These steps are also mentioned in detail in the document [401 Unauthorized](https://learn.microsoft.com/en-us/azure/application-gateway/http-response-codes#401--unauthorized). 

### Customer Solution

*Content type: MarkdownText*

A 401 Unauthorized error is returned if the client is not authorized to access the backend application. To resolve, check the user access.

The following are a few reasons with potential fixes:

1. If the client has access, it might have an outdated browser cache. Clear the browser cache and try accessing the application again.
2. An HTTP 401 Unauthorized response can be returned to the AppGW probe request if the backend pool is configured with NTLM authentication. In this scenario, the backend is marked as healthy. There are several ways to resolve this issue:
    - Allow anonymous access on backend pool.
    - Configure the probe to send the request to  another "fake" site that doesn't require NTLM. This is not a recommended method, as this won't tell us if the actual site behind the Application Gateway is active or not.
    - Configure the Application Gateway to allow 401 responses as valid for the probes "Probe matching conditions".

See [401 Unauthorized](https://learn.microsoft.com/en-us/azure/application-gateway/http-response-codes#401--unauthorized). 

---

### Step 7: 403 Forbidden

### Content

HTTP 403 Forbidden is displayed when you are using the Web Application Firewall (WAF) with Prevention mode enabled. Consider enabling [Application Gateway Firewall Logs](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-logs#firewall-log) for better troubleshooting.

---

### Step 8: Pattern Match

### Support Engineer Solution

Check the 'ruleId' and the 'message' in the WAF logs for matching requests.

* Identify the part of the HTTP request that is being blocked. Determine whether the matched pattern can be prevented from being sent.

If false positives are observed:

- You can create [WAF exclusion lists](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-configuration?tabs=portal) to exclude certain request attributes from WAF evaluation. The rest of the request is evaluated as usual.

- For Application Gateway WAF V2, create [Custom rules](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/custom-waf-rules-overview) for identified values.

- [Disable the specific Core Rule Set](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules?tabs=drs21#tuning-of-managed-rule-sets) (CRS) rules which are blocking the request.

### Customer Solution

*Content type: MarkdownText*

Check the `ruleId` and the `message` in the WAF logs for matching requests. Identify the part of the HTTP request that is being blocked. Determine whether the matched pattern can be prevented from being sent.

If false positives are observed:

- Create [WAF exclusion lists](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-configuration?tabs=portal) to exclude certain request attributes from WAF evaluation. The rest of the request is evaluated as usual.

- For Application Gateway WAF V2, create [custom rules](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/custom-waf-rules-overview) for identified values.

- [Disable the specific Core Rule Set](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules?tabs=drs21#tuning-of-managed-rule-sets) (CRS) rules which are blocking the request.

---

### Step 9: Size Limit

### Support Engineer Solution

Check the Request body size limits for your Application Gateway.

Refer to the following document for checking the Request body size limits for respective Application Gateway SKU: [Web Application Firewall request size limits](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits#limits)

If you need further assistance, kindly contact support.

### Customer Solution

*Content type: MarkdownText*

The request body size field and the file upload size limit are both configurable within the Web Application Firewall. The maximum request body size field is specified in kilobytes and controls overall request size limit excluding any file uploads. 

To resolve, check the [Request body size limits](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits#limits) for your Application Gateway.

---

### Step 10: Bot Protection

### Support Engineer Solution

Managed bot protection rule set either blocks or logs requests from known malicious IP addresses based on WAF Prevention or Detection mode.

Validate the Bot Manager Rule Set for good, bad and unknown bots.

For more information visit [Bot protection overview](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/bot-protection-overview) page.

If you need further assistance, kindly contact support.

### Customer Solution

*Content type: MarkdownText*

Managed bot protection rules set either blocks or logs requests from known malicious IP addresses based on WAF Prevention or Detection mode.

Validate the Bot Manager Rule Set for good, bad and unknown bots.

See [Bot protection overview](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/bot-protection-overview) page.

---

### Step 11: 413 Request Entity Too large

### Support Engineer Solution

HTTP 413 response may be observed when using Azure Web Application Firewall on Application Gateway and the client request size exceeds the maximum request body size limit. 

The maximum request body size field controls overall request size limit excluding any file uploads. The default value for request body size is 128 KB. For more information visit [Web Application Firewall request size limits](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits#limits) page.

### Customer Solution

*Content type: MarkdownText*

HTTP 413 response may occur when using Azure Web Application Firewall on the Application Gateway and the client request size exceeds the maximum request body size limit. 

The maximum request body size field controls the overall request size limit, excluding any file uploads. The default value for the request body size is 128 KB. 

See [Web Application Firewall request size limits](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits#limits).

---

### Step 12: 499 Client closed the connection

### Support Engineer Solution

HTTP 499 response is observed when a client closes the connection before a response is sent by the Application Gateways v2 SKU.

This error can be observed when a large response is returned by Application Gateway and the end user may have closed or refreshed the application before the entire response was sent. This may also happen when the client timeout is low.

In Application Gateway v1 SKU, "HTTP 0" response code may be raised if the client forcibly closed the connection before the entire response could be received.

### Customer Solution

*Content type: MarkdownText*

HTTP 499 response occurs when a client closes the connection before a response is sent by the Application Gateways v2 SKU.

This error occurs when a large response is returned by Application Gateway and the end user may have closed or refreshed the application before the entire response was sent. This may also happen when the client timeout is low.

In Application Gateway v1 SKU, "HTTP 0" response code may be raised if the client forcibly closed the connection before the entire response could be received.

---

### Step 13: Unable to bypass Application Gateway

### Content

Application Gateway gets provisioned under V1 or V2 SKU. If you've configured [Diagnostic Logs](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-diagnostics), check the logs for your Application Gateway.

Based on your Application Gateway SKU V1 or V2, select a matching condition:

- For V1 SKU, open Access logs, check "RequestQuery" field and look for "SERVER-STATUS".

- For V2 SKU, open Access logs, check the "serverStatus" field.

---

### Step 14: 404 Not Found

### Support Engineer Solution

Application Gateway gets provisioned under V1 or V2 SKU. You can see the SKU size in Properties blade of your Application Gateway on the portal.

If the request header, URL or Query String is too long, we can get 404 errors.

- If you are seeing this error in Application Gateway V2, it could be a configuration issue with a HTTP Listener. This may happen when the multi-site Listener that matches the IP, port and protocol of the request doesn't match the Hostname in the request. Make sure that the Host value entered in the Listener configuration is the same as the Host header in the client request.

- Application Gateway V1 generally doesn't return HTTP 404 responses. 

For further assistance, kindly contact support.

### Customer Solution

*Content type: MarkdownText*

Application Gateway gets provisioned under V1 or V2 SKU. You can see the SKU size in Properties blade of your Application Gateway on the portal.

If the request header, URL or Query String is too long, you may get 404 errors.

- If you are seeing this error in Application Gateway V2, it could be a configuration issue with a HTTP Listener. This may happen when the multi-site Listener that matches the IP, port and protocol of the request doesn't match the Hostname in the request. Make sure that the Host value entered in the Listener configuration is the same as the Host header in the client request.

- Application Gateway V1 generally doesn't return HTTP 404 responses. 

---

### Step 15: 408 Request Timeout

### Support Engineer Solution

HTTP 408 response is observed when "client requests" to the frontend HTTP Listener of the Application Gateway does not respond back within 60 seconds. This error can be due to traffic congestion between on-premises network and Azure, or the client itself is overwhelmed.

### Customer Solution

*Content type: MarkdownText*

HTTP 408 response occurs when client requests to the frontend HTTP Listener of the Application Gateway does not respond back within 60 seconds. This error can be due to traffic congestion between on-premises network and Azure, or the client itself is overwhelmed.

---

### Step 16: No 4xx error

### Support Engineer Solution

Please review the problem type and select the one that matches your problem statement.

### Customer Solution

*Content type: MarkdownText*

Please review the problem type and select the one that matches your problem statement.

---
