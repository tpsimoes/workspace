# Networking] Application Gateway - 4xx Errors

> **Product:** Application Gateway  
> **Solution ID:** 3c547893-f1a9-43e8-89de-42b76fee15e8  
> **Trigger words:** application, application gateway, errors, gateway, networking]

---

## Overview

This guide provides step-by-step troubleshooting for **Networking] Application Gateway - 4xx Errors** under **Application Gateway**.
 The original guided troubleshooter contains 25 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Application Gateway 404  version check

### Guidance

## 404 HTTP Status Code

Usually a 404 Https status code coming from the Application Gateway happens when there isn't a listener that can serve the "originalhost" FDQN entering the appgw.

*Note: 
    **Application Gateway v1 shouldn't return HTTP 404 responses** originated from the Application Gateway. If this is the case, open Ava post containing the description of the issue and all the information gather until now and ask for further assistance on this.*

## What to do if the Application Gateway is returning a 404 response?

Check if the customer has the appropriate rules/listeners for the URL they are using. For this you can follow this path:

- On ASC go the the Application Gateway page.
- Click on the "Diagnostics" blade
- Enter the URL under "Application Gateway Access URL" (don't forget to include http:// or https://)
- Under "Front End type" select private, if you access the website through private IP, or Public if through public IP.
- Click on "Run".
If the test ends with "Multisite Listener Host Name Mismatch" message it means there currently isn't a listener configured for this specific URL.

### Question

**Based on the results obtained previously, does the customer have a listener/rule configured for this specific URL?**

### Options

- **Yes** → Go to: *Application Gateway 404  v2 response*
- **No** → Go to: *AppGw 404 v2 No rule*

---

### Step 2: AppGw 400 response Mutual Auth Unable to get local issuer

### Support Engineer Solution

Similar to unable to get issuer certificate, the issuer certificate of the client certificate couldn't be found. This normally means the trusted client CA certificate chain is not complete on the Application Gateway.

Ask the customer to validate that the trusted client CA certificate chain uploaded on the Application Gateway is complete.

For more information on how to extract the entire trusted client CA certificate chain to upload to Application Gateway, see [how to extract trusted client CA certificate chains](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-certificate-management).

### Customer Solution

*Content type: MarkdownText*

It seems the Mutual authentication is failing with the error "It seems the Mutual authentication is failing with the error".
</br> Similar to unable to get issuer certificate, the issuer certificate of the client certificate couldn't be found. This normally means the trusted client CA certificate chain is not complete on the Application Gateway. Please validate that the trusted client CA certificate chain uploaded on the Application Gateway is complete.

You can read more about Mutual Authentication issues and troubleshooting here: [Troubleshooting mutual authentication errors in Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-troubleshooting#sslclientverify-is-failed)

---

### Step 3: AppGw 400 responses

### Guidance

### 400 HTTP Status Code

Here you may find the possible reasons why an Application Gateway replies with a 400 HTTP Status:

1. Non-HTTP / HTTPS traffic is initiated to an Application Gateway with an HTTP or HTTPS listener.
2. HTTP traffic is initiated to a listener with HTTPS, with no redirection configured.
3. Mutual authentication is configured and unable to properly negotiate.

**How to check for non HTTP/HTTPS traffic?**

1. Open the Request Response Logs used on the previous steps
2. Filter for the column named HTTP Status responses ("where httpStatus == 400")
3. Check the "httpVersion" column, if it's empty, then it was a **non**-HTTP/HTTPS request

**How to check if the customer is sending HTTP traffic on an HTTPS listener?**

1. Go to the Jarvis RequestResponseLogs table from the previous steps
2. Filter for HTTP 400 responses "where httpStatus == 400"
3. Look at the "httpMethod column" if it is not empty then it mean the client is not using an invalid protocol (non HTTP or HTTPS).
4. Look for the "sslEnabled" column, if it blank it means this was an HTTP request to an HTTPS listener.

**Mutual Authentication issues**

Now that you have validated that the HTTP 400 responses originated on the Application Gateway weren't due to an invalid protocol or due to HTTP requests on HTTPS listeners, lets look into Mutual Authentication Issues

*How to validate Mutual Authentication issues?*

1. Go to the Jarvis ReqRespLogs table from the previous steps.
2. Filter for HTTP 400 responses "where httpStatus == 400"
3. Look at the "sslClientVerify" column to validate which output is seeing between: success, failed and none.

### Question

**Based on the previous steps, which of these issues matches the most?**

### Options

- **Non HTTP/HTTPS Traffic** → Go to: *AppGw 400 response invalid protocol*
- **HTTP traffic on an HTTPS listener** → Go to: *HTTPS traffic on HTTP listener*
- **Mutual Authentication issues** → Go to: *AppGw 400 response  Mutual Auth issues*

---

### Step 4: AppGtw 400 response  other

### Support Engineer Solution

At this point you have validated that the 400 reponses are originating from the Application Gateway but are not due to an invalid protocol, HTTP traffic on an HTTPS listener or Mutual Auth issues.
</br>There shouldn't be other reasons for the Application Gateway to throw 400 responses, not originated from the backend, so please post this case on the Application Gateway Ava channel on Teams.
</br>Please don't forget to provide the Gateway SKU, the Jarvis ReqRespLogs with the HTTP 400 response, and write that you have validated this is not caused by an invalid protocol, HTTP traffic on an HTTPS listener or Mutual Auth issues.

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 5: AppGw 400 response  Mutual Auth issues

### Guidance

**Mutual Authentication issues?**

SSLClientVerify column can have these values: **SUCCESS, FAILED and NONE.** If there was a Mutual Auth issue you should see "NONE" or "FAILED" with one of the errors shown below:

- *Unable to get issuer certificate:* The issuer certificate of the client certificate could not be found. This normally means the trusted certificate chain is not complete. 

- *Self signed certificate:* The client certificate is self signed and the same certificate cannot be found in the list of trusted certificates. 

- *Unable to get local issuer certificate (Similar to “Unable to get issuer certificate”)*: The issuer certificate of the client certificate could not be found. This normally means the trusted certificate chain is not complete. 

- *Unable to verify the first/client certificate:* This error occurs specifically when the client presents only the leaf certificate, whose issuer is not trusted. 

- *Unable to verify the client certificate issuer:* This error occurs when the configuration “VerifyClientCertIssuerDN” is set to true. When the Issuer DN of the client certificate does not match any “ClientCertificateIssuerDN”, which is extracted from the trusted certificate chain uploaded by the customer.

**Additional steps you can follow:**

A packet capture can be run on the client machine, while connecting to the website (and getting the 400 response) might help further understand the client side issue.

You can follow this [Mutual Authentication Wiki](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/236992/Feature-Mutual-Authentication?anchor=tsg) for some guidance on how to analyze the packet capture and find more information related to Mutual Authentication.

### Question

**Based on the results obtained previously, what message are you seeing on the sslClientVerify column?**

### Options

- **NONE** → Go to: *AppGw 400 response Mutual Auth NONE*
- **FAILED - Unable to get issuer certificate** → Go to: *AppGw 400 response Mutual Auth unable to get issuer*
- **FAILED - Unable to get local issuer certificate** → Go to: *AppGw 400 response Mutual Auth Unable to get local issuer*
- **FAILED - Unable to verify the first certificate** → Go to: *AppGtw 400 response  Mutual Auth Unable to vrf the 1st cert*
- **FAILED - Unable to verify the client certificate issuer** → Go to: *AppGtw 400 response  Mutual Auth client cert issuer*
- **FAILED - Unsupported certificate purpose** → Go to: *AppGtw 400 response  Mutual Auth unsoported cert purpose*
- **No Mutual Authentication failure** → Go to: *AppGtw 400 response  other*

---

### Step 6: Backend Server Issue

### Support Engineer Solution

The HTTP 4xx response seems to be originating from the backend server.
Please ask the customer to check his backend server/application logs to understand why the server is giving this response.
If the backend service is also an Azure Service (such as AppService or APIM, or other PaaS services), if needed, please engage the other team for assistance on reviewing the backend application/service.

### Customer Solution

*Content type: MarkdownText*

We have detected that the HTTP 4xx response is originating from the backend server/application.
Please review your server/application logs to understand what is causing these responses.

---

### Step 7: Application Gateway 404  v2 response

### Support Engineer Solution

Application Gateway with the appropriate listener/rule configured for a specific URL shouldn't return an HTTP 404 response originated from the Application Gateway.

Go to the Application Gateway Ava Channel on Teams and ask for further assistance on this. Provide the Jarvis RequestResponse logs with the 404 response originating from the Application Gateway plus the output of the ASC diagnostics showing there is a rule/listener configured for this URL (the output from the previous TSG step).

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 8: Response origin check  4xx other

### Guidance

## 404 HTTP Status Code

Usually a 404 Https status code coming from the Application Gateway happens when there isn't a listener that can serve the "originalhost" FDQN entering the appgw.

*Note: 
    **Application Gateway v1 shouldn't return HTTP 404 responses** originated from the Application Gateway. If this is the case, open Ava post containing the description of the issue and all the information gather until now and ask for further assistance on this.*

## What to do if the Application Gateway is returning a 404 response?

Check if the customer has the appropriate rules/listeners for the URL they are using. For this you can follow this path:

- On ASC go the the Application Gateway page.
- Click on the "Diagnostics" blade
- Enter the URL under "Application Gateway Access URL" (don't forget to include http:// or https://)
- Under "Front End type" select private, if you access the website through private IP, or Public if through public IP.
- Click on "Run".
If the test ends with "Multisite Listener Host Name Mismatch" message it means there currently isn't a listener configured for this specific URL.

### Question

**Based on the results obtained previously, does the customer have a listener/rule configured for this specific URL?**

### Options

- **Yes** → Go to: *Backend Server Issue*
- **No** → Go to: *Application Gateway 4xx other*

---

### Step 9: Type of HTTP 4xx response check

### Guidance

## What is HTTP 4xx Error?

According to [RFC 7231](https://tools.ietf.org/html/rfc7231#section-6.5), the 4xx (Client Error) class of status code indicates that the client seems to have erred.

HTTP 4xx status can either be sent by Application Gateway or Backend servers behind Application gateway.

Here you may find a brief description of the errors you can find:

|HTTP Status Code  | Explanation |
|--|--|
|400  |The 400 **(Bad Request)** status code indicates that the server cannot or will not process the request due to something that is perceived to be a client error (e.g., malformed request syntax, invalid request message framing, or deceptive request routing) |
|403 | The 403 **(Forbidden)** status code indicates that the server understood the request but refuses to authorize it. |
 | 404 | The 404 **(Not Found)** mean that the server cannot find the requested resource. In the browser, this means the URL is not recognized. In an API, this can also mean that the endpoint is valid but the resource itself does not exist.  |
 | 408 | The 408 **(Request Timeout)** status code indicates that the server did not receive a complete request message within the time that it was prepared to wait. |
 | 499 | The 499 Status Code indicates that the client (the browser) closed the connection before the server responded to the request. |

### Question

**Based on the results obtained previously, what HTTP 4xx response is the customer getting?**

### Options

- **400** → Go to: *AppGw 400 responses*
- **403** → Go to: *47a18936-39a1-4329-847f-91e638485daa*
- **404** → Go to: *Application Gateway 404  version check*
- **408** → Go to: *Client closed the connection*
- **499** → Go to: *Application Gateway 499 response*
- **4xx other** → Go to: *Application Gateway 4xx other*

---

### Step 10: AppGtw 400 response  Mutual Auth unsoported cert purpose

### Support Engineer Solution

Ask the customer to ensure the client certificate designates Extended Key Usage for Client Authentication ([1.3.6.1.5.5.7.3.2](https://oidref.com/1.3.6.1.5.5.7.3.2)). More details on definition of extended key usage and object identifier for client authentication can be found in [RFC 3280](https://www.rfc-editor.org/rfc/rfc3280) and [RFC 5280](https://www.rfc-editor.org/rfc/rfc5280).

### Customer Solution

*Content type: MarkdownText*

It seems the Mutual authentication is failing with the error "Unsupported certificate purpose".
</br> Please ensure the client certificate designates Extended Key Usage for Client Authentication ([1.3.6.1.5.5.7.3.2](https://oidref.com/1.3.6.1.5.5.7.3.2)). More details on definition of extended key usage and object identifier for client authentication can be found in [RFC 3280](https://www.rfc-editor.org/rfc/rfc3280) and [RFC 5280](https://www.rfc-editor.org/rfc/rfc5280).

For more information on how to extract the entire trusted client CA certificate chain to upload to Application Gateway, see [how to extract trusted client CA certificate chains](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-certificate-management).

---

### Step 11: AppGw 404 v2 No rule

### Support Engineer Solution

On the previous step you ran the diagnostics for this specific URL and got a "Multisite Listener Host Name Mismatch" error, which means this Application Gateway doesn't currently have a listener/ rule configured for this specific URL.

</br>To fix this you have the following 2 options:

1. Ask the customer to configure a multi-site listener for this specific FQDN. In case they just want the Application Gateway to respond to specific FQDNs. A multi-site listener can also be configured with multiple hostnames, for example "*.contoso.com".

2. The second option should be to configure a Basic listener with it's respective rule in case they want the AppGw to default to this listener when no other listener matches the URL.
   - *Note: For the v2 SKU, multi-site listeners are processed before basic listeners, unless rule priority is defined. If using rule priority, wildcard listeners should be defined a priority with a number greater than non-wildcard listeners, to ensure non-wildcard listeners execute prior to the wildcard listeners.*

### Customer Solution

*Content type: MarkdownText*

You are currently seeing these "HTTP 404 Page Not found" responses because you have a v2 Application Gateway with no rule/listener matching on this specific URL.

To fix this we have two options:
1. Configure a multisite listener and rule, either for this specific FQDN/URL, or for a wildcard domain. With this approach the Application Gateway will forward to the backend the requests for the configured FQDNs/URLs, and give 404 responses to all other requests. 

   You can read more about this here:
   - [Application Gateway multiple site hosting](https://learn.microsoft.com/en-us/azure/application-gateway/multiple-site-overview)
   - [Tutorial: Create and configure an application gateway to host multiple web sites using the Azure porta](https://learn.microsoft.com/en-us/azure/application-gateway/create-multiple-sites-portal)

2. Configure a basic listener and rule, which will forward to the backend all the requests that match the configured port. You can configure this options if you want the Application Gateway to forward to the backend all the requests that arrive the the Application Gateway's IP and configured port. 

   - *Note: If you already have multisite listeners/rules, then you can also configure a basic rule with a lower priority (higher number) as a last resort, so that any request that didn't match any of your multisite rules matches on this basic rule.*

   You can read more about this here:
   - [Application Gateway listener configuration](https://learn.microsoft.com/en-us/azure/application-gateway/configuration-listeners)
   - [Application Gateway request routing rules](https://learn.microsoft.com/en-us/azure/application-gateway/configuration-request-routing-rules)
   - [Quickstart: Direct web traffic with Azure Application Gateway - Azure portal](https://learn.microsoft.com/en-us/azure/application-gateway/quick-create-porta

*(Content truncated — refer to original GT for full details)*

### Step 12: Application Gateway 4xx other

### Support Engineer Solution

If the response originated from the Applicaiton Gateway and is not listed on this TSG then try to look for the meaning of the HTTP response here [Overview of HTTP Status and Sub status codes](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/303184/Overview-of-HTTP-Status-and-Sub-status-codes?anchor=4xx%3A-client-error-codes----start-here-(subcodes-below-if-backend-is-configured-to-show-subcodes)).

A web server sends 4xx HTTP status code in the response when there is an error in the request received from the client. From troubleshooting purposes, you can assume 4xx code indicates the server can’t process the request because the browser sent a wrong request with an error.

### Customer Solution

*Content type: MarkdownText*

A web server sends 4xx HTTP status code in the response when there is an error in the request received from the client. 

From troubleshooting purposes, you can assume 4xx code indicates the server can’t process the request because the browser sent a wrong request with an error.

If this response is being originated from the Application Gateway, and not the backend server, it might indicate an issue with the requests coming from the client software/machine.

---

### Step 13: AppGw 400 response Mutual Auth unable to get issuer

### Support Engineer Solution

The issuer certificate of the client certificate couldn't be found. This normally means the trusted client CA certificate chain is not complete on the Application Gateway. Ask the customer to validate that the trusted client CA certificate chain uploaded on the Application Gateway is complete.

For more information on how to extract the entire trusted client CA certificate chain to upload to Application Gateway, see [how to extract trusted client CA certificate chains](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-certificate-management).

### Customer Solution

*Content type: MarkdownText*

It seems the Mutual authentication is failing with the error "Unable to get the issues certificate.
<br/>This means the issuer certificate of the client certificate couldn't be found. This errors comes up whenever the trusted client CA certificate chain is not complete on the Application Gateway. Please validate that the trusted client CA certificate chain uploaded on the Application Gateway is complete.

You can read more about Mutual Authentication issues and troubleshooting [here](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-troubleshooting#sslclientverify-is-failed)

---

### Step 14: HTTPS traffic on HTTP listener

### Support Engineer Solution

The customer needs to be aware of the ports and protocols configured on the Application Gateway so they can connect with the appropriate protocol.
If the customer wants to be automaticaly redirected from HTTP to HTTPS then they can configure a redirection rule.
[Add a routing rule with a redirection configuration](https://learn.microsoft.com/en-us/azure/application-gateway/redirect-http-to-https-portal#add-a-routing-rule-with-a-redirection-configuration)

### Customer Solution

*Content type: MarkdownText*

In order to be automatically redirect from HTTP to HTTPs by the Application Gateway there needs to be an HTTP listener configured with a redirect rule. For more information on how to configure this please follow this document:
[Add a routing rule with a redirection configuration](https://learn.microsoft.com/en-us/azure/application-gateway/redirect-http-to-https-portal#add-a-routing-rule-with-a-redirection-configuration)

---

### Step 15: AppGw 400 response Mutual Auth NONE

### Support Engineer Solution

If the Application Gateway is correctly set up to use Mutual Authentication and the clients are getting a 400 response, with the sslClientVerify error "NONE" then it means the clients might not be setup correctly.

This can be seen when user doesn’t send a client certificate when accessing mutual auth endpoint on AppGw. This could happen if the client isn’t configured correctly to use client certs – if server sends a request for client cert, the request doesn’t fail on client side and we fail on server side (AppGw).

Ask the customer to make sure the client machine has the required certificates correctly installed, you can use OpenSSL for this purpose:

*openssl s_client -connect <URL:PORT> -showcerts* 

### Customer Solution

*Content type: MarkdownText*

It seems that you have configured your Application Gateway to use Mutual Authentication and are currently getting HTTP 400 responses.

Looking at the Application Gateway AccessLogs we can see the sslClientVerify is NONE. This is seen when the client doesn't send a client certificate when sending a request to the Application Gateway. 

If the client sending the request to the Application Gateway isn't configured correctly to use client certificates. One way to verify that the client authentication setup on Application Gateway is working as expected is through the following OpenSSL command: 

openssl s_client -connect <hostname:port> -cert <path-to-certificate> -key <client-private-key-file>

You can read more about this here: [Troubleshooting mutual authentication errors in Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-troubleshooting#sslclientverify-is-none)

---

### Step 16: AppGtw 400 response  Mutual Auth client cert issuer

### Support Engineer Solution

This error occurs when the configuration VerifyClientCertIssuerDN is set to true. This typically happens when the Issuer DN of the client certificate doesn't match the ClientCertificateIssuerDN extracted from the trusted client CA certificate chain uploaded by the customer. For more information about how Application Gateway extracts the ClientCertificateIssuerDN, check out [Application Gateway extracting issuer DN](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-overview#verify-client-certificate-dn). 
</br>As best practice, make sure to upload only one certificate chain per file to the Application Gateway.

### Customer Solution

*Content type: MarkdownText*

It seems the Mutual authentication is failing with the error "Unable to verify the client certificate issuer".
</br>This error occurs when the configuration VerifyClientCertIssuerDN is set to true. This typically happens when the Issuer DN of the client certificate doesn't match the ClientCertificateIssuerDN extracted from the trusted client CA certificate chain uploaded by the customer. For more information about how Application Gateway extracts the ClientCertificateIssuerDN, check out [Application Gateway extracting issuer DN](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-overview#verify-client-certificate-dn). 
</br>As best practice, make sure to upload only one certificate chain per file to the Application Gateway.

For more information on how to extract the entire trusted client CA certificate chain to upload to Application Gateway, see [how to extract trusted client CA certificate chains](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-certificate-management).

---

### Step 17: AppGw 400 response  HTTP HTTPS mismatch

### Guidance

# Check the response origin
## How to check if the response originated on the backend server or the Application Gateway:
1. Go to ASC to the Application Gateway page.
2. Click on the "Diagnostics" blade
3. Scroll down and click on "[MDM Logs] Request Response Logs"
4. Filter for the time of the request you are looking for, and you can also apply the filter "where httpStatus == 499" (MQL).
5. Check the "ServerStatus" collumn.

If ServerStatus is blank, then the response originated from the Application Gateway, otherwise it originated from the Backend Server

**NOTE:** You can also get to ReqRespLog table from here: [Jarvis ReqRespLogs](https://portal.microsoftgeneva.com/s/72B776E3)
</br>Just scope for Tenant (get it from ASC), and if you want to parse through more time also filter for Region.

### Question

**Where did the response originate from?**

### Options

- **Backend Server** → Go to: *Backend issue  499*
- **Application Gateway** → Go to: *Application Gateway 499 response*

---

### Step 18: AppGw 400 response invalid protocol

### Support Engineer Solution

The Application Gateway only supports: HTTP, HTTPS, HTTP/2, and WebSocket.
If the customer needs a load balanced solution for non-HTTP/HTTPS protocol please look into the Azure Load Balancer or other 
[Load-balancing solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/load-balancing-overview).

### Customer Solution

*Content type: MarkdownText*

The Application Gateway is a Layer 7 solution which only supports HTTP, HTTPS, HTTP/2, and WebSocket protocols.
For non-HTTP(S) protocol traffic load balancing please see the following document for alternative load balacing solutions:
[Load-balancing options](https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/load-balancing-overview)

---

### Step 19: Client closed the connection

### Support Engineer Solution

An HTTP 408 response, orignated from the Application Gateway, can be observed when client requests to the frontend listener of application gateway do not respond back within 60 seconds. This error can be observed due to traffic congestion between on-premises networks and Azure, when traffic is inspected by virtual appliances, or the client itself becomes overwhelmed.

### Customer Solution

*Content type: MarkdownText*

An HTTP 408 response, orignated from the Application Gateway, can be observed when client requests to the frontend listener of application gateway do not respond back within 60 seconds. This error can be observed due to traffic congestion between on-premises networks and Azure, when traffic is inspected by virtual appliances, or the client itself becomes overwhelmed. 

---

### Step 20: Backend issue  499

### Support Engineer Solution

An HTTP 499 response means the client closed the connection before the server finished serving the request.
If this response is originated from the backend server, it mean the server might be taking more time to respond to the requests than the Application Gateway is configured to wait.
Check for performance issues on the backend server, or ask the customer to check any performance issues with the server application.
A way to mitigate/solve this issue is to increase the AppGtw Backend Settings "Request time-out" parameter to a value that would allow the backend server to respond.
You can start by increasing the value a lot, and then check the logs to see how long the requests are actually taking and readjusting the value to smaller one.

### Customer Solution

*Content type: MarkdownText*

An HTTP 499 response means the client closed the connection before the server finished serving the request.
If this response is originated from the backend server, it mean the server might be taking more time to respond to the requests than the Application Gateway is configured to wait.
Check for performance issues on the backend server and application.
A way to mitigate/solve this issue is to increase the AppGtw Backend Settings "Request time-out" parameter to a value that would allow the backend server to respond.
You can start by increasing the value a lot, and then check the logs to see how long the requests are actually taking and readjusting the value to smaller one.

---

### Step 21: AppGw TSG Scope check ⭐ (First Step)

### Guidance

## Before we start
Validate this TSG applies to Customer's scenario.

This TSG is specific to Application Gateway "HTTP 4xx errors" hence covers scenarios under the following SAP:

*Azure/Application Gateway/Connectivity/4xx errors*

If your issue is not from the list above, you may use: **Edit & Run Again** feature on the **ASC** to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results.

## What information you might want to collect first?

1. AppGw Resource ID
2. Gateway ID and/or Deployment ID
3. SKU 
4. Region
5. Time stamp of the issue

## How to look for HTTP responses?
1. On ASC go to the Application Gateway page.
2. Click on the "Diagnostics" blade
3. Scroll down and click on "[MDM Logs] Request Response Logs"
4. Filter for the time of the request you are looking for.
5. Check the "httpStatus" column.

If you are having trouble finding the right timerange for the HTTP 4xx response you can use the Shoebox Metrics Dashboard.

1. On ASC go to the Application Gateway page.</br>
2. Click on the "Diagnostics" blade.</br>
3. Scroll down and click on "[MDM Dashboard] Platform Metrics.</br>
4. Here you can filter for a wider time range (on the top right corner).</br>
5. Now look for the "AppGW Response" graph, there you can filter for "4xx".</br>
6. Take note of the time of the 4xx response and go back to ReqRespLogs table..</br>

*NOTE:* 

*- You can also get to ReqRespLog table from here [Jarvis ReqRespLogs](https://portal.microsoftgeneva.com/s/72B776E3). Scope by Gateway ID.*

*- You also can open directly the Shoebox Metric Dashboard from here: [Shoebox Metrics](https://portal.microsoftgeneva.com/s/F4B4999B?overrides=[{"query":"//*[id='ResourceId']","key":"value","replacement":""}]%20). Make sure to filter by the Application Gateway resource URI on the top right corner.*

**Recommended documents:**

* [Azure Application Gateway documentation](https://docs.microsoft.com/en-us/azure/application-gateway/)
* [4XX response codes (client error)](https://learn.microsoft.com/en-us/azure/application-gateway/http-response-codes#4xx-response-codes-client-error)
* [Troubleshoot 4XX Errors - Application Gateway (Wiki)](https://supportability.visualstudio.com/AzureNetworking/_wiki/wikis/Wiki/140182/Troubleshoot-4XX-Errors-Application-Gateway)

### Question

**After checking the Request Response Logs, is the 4xx status code coming from the Application Gateway or the backend pool?**

### Options

- **Application Gateway** → Go to: *Type of HTTP 4xx response check*
- **Backend pool** → Go to: *Backend Server Issue*

---

### Step 22: Application Gateway 499 response

### Support Engineer Solution

A 499 HTTP response is presented if a **client request that is sent to the AppGw v2 is closed before the server finished responding.** This error can be observed when a large response is returned to the client, but the client may have closed or refreshed their browser/application before the server had a chance to finish responding.

**This means this is a client side issue**, since the client closed the connection with the Application Gateway before it got a response.
This is not an error that can be fixed on our side, we either ask the users to wait for the Application Gateway/backend to respond or, if the backend is taking too long to respond, ask the customer to look into the backend server to see if there are any code/platform improvements that can be implemented so the backend answers faster.

If this just happens sporadically it might just mean the clients are having connectivity issues to the Application Gateway.

### Customer Solution

*Content type: MarkdownText*

499 HTTP status code is presented if a client (user/browser) requests that are sent to the Application Gateways using v2 SKU is closed before the server finished responding. 

This error can be observed when a large response is returned to the client, but the client may have closed or refreshed their browser/application before the server had a chance to finish responding.

**This means this is a client side issue**, where the clients are closing the connection (leaving the webpage) before the Application Gateway/backend server is able to respond.
If the clients are closing the connections because the response is taking too long you can look into the backend server code/platform to see if there are any improvements that can be implemented in order to improve the response times.

---

### Step 23: AppGtw 400 response  Mutual Auth Unable to vrf the 1st cert

### Support Engineer Solution

Unable to verify the client certificate. This error occurs specifically when the client presents only the leaf certificate, whose issuer is not trusted. Ask the customer to validate that the trusted client CA certificate chain uploaded on the Application Gateway is complete.

For more information on how to extract the entire trusted client CA certificate chain to upload to Application Gateway, see [how to extract trusted client CA certificate chains](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-certificate-management).

### Customer Solution

*Content type: MarkdownText*

It seems the Mutual authentication is failing with the error "Unable to verify the first certificate".
</br>This error occurs specifically when the client presents only the leaf certificate, whose issuer is not trusted. Please validate that the trusted client CA certificate chain uploaded on the Application Gateway is complete.

You can read more about Mutual Authentication issues and troubleshooting [here](https://learn.microsoft.com/en-us/azure/application-gateway/mutual-authentication-troubleshooting#sslclientverify-is-failed)

---

### Step 24: Backend Issue  408

### Support Engineer Solution

The HTTP 408 response is a request timeout, from the client side. It means the client didn't respond in time to the Server.
If you see the 408 response originated from the backend server it means the backend server didn't receive a  response from the Application Gateway in time.
This might indicate that there are some network performance issues between the Application Gateway and the backend server. There might be a firewall in between that could be causing the delay in communications. A packet capture on the backend server might give some indication on what is causing this delay.
</br>
This could also be caused by performance issues on the Application Gateway.
on ASC go to the Application Gateway's page -> click on the "Diagnostics" blade -> click on "[MDM Dashboard] Platform Metrics"
And look for any indication of performance issues.

### Customer Solution

*Content type: MarkdownText*

The HTTP 408 response is a request timeout, from the client side. Which means the client didn't respond in time to the Server.
If a 408 response is originating from the backend server it means the backend server didn't receive a  response from the Application Gateway in time.
This might indicate that there are some network performance issues between the Application Gateway and the backend server. If there is a firewall in between the backend server and the Application Gateway that could be causing the delay in communications.

---

### Step 25: Application Gateway 404  config check

### Guidance

# Check if the customer has the appropriate rules/listeners for the URL they are using
## How to check which rule/listener is matching for a specific URL
1. On ASC, go the the Application Gateway page.
2. Click on the "Diagnostics" blade
3. Enter the URL under "Application Gateway Access URL" (don't forget to include http:// or https://)
4. Under "Front End type" select private, if you access the website through private IP, or Public if through public IP.
5. Click on "Run".

If you get a finding with "Multisite Listener Host Name Mismatch" it means there currently isn't a listener configured for this specific URL.

### Question

**Does the customer have a listener/rule configured for this specific URL?**

### Options

- **Yes** → Go to: *Application Gateway 404  v2 response*
- **No** → Go to: *AppGw 404 v2 No rule*

---
