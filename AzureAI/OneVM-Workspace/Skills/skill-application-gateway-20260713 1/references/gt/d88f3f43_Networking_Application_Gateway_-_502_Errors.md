# Networking] Application Gateway - 502 Errors

> **Product:** Application Gateway  
> **Solution ID:** d88f3f43-0cc3-4143-aced-c4820b56e8ec  
> **Trigger words:** application, application gateway, errors, gateway, networking]

---

## Overview

This guide provides step-by-step troubleshooting for **Networking] Application Gateway - 502 Errors** under **Application Gateway**.
 The original guided troubleshooter contains 33 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Application Gateway 502 TSG Scope Check ⭐ (First Step)

### Guidance

## Verify if the customer issue matches this TSG

This TSG is specific to Application Gateway \\"502 - Bad Gateway\\" errors. It is applicable to the below mentioned support topics.

* Azure/Application Gateway/502 errors
* Azure/Application Gateway/502 errors/Unhealthy backend pool
* Azure/Application Gateway/502 errors/Unknown backend health
* Azure/Application Gateway/502 errors/Others

**Note**  
If your issue is not from the list above, you may use **Edit & Run Again** feature on the **ASC** to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results.

If you are not sure that the issue is related to 502 errors, here‘s how to identify:

* If it is a public/Internet-facing App Gateway, you can browse the App Gateway URL or public IP and see if you get **\\"502-Bad Gateway Error\\"**
* Look at the **HTTPStatus** field in [ReqRespLog](https://jarvis-west.dc.ad.msft.net/C3BF963B) table which can be located at:  
  `Jarvis Logs > AppGWT > ReqRespLog ` or  
  `[MDM Logs] Request Response` link under Diagnostic section of the given Application Gateway in ASC

### Recommended documents

* [Azure Application Gateway documentation](https://docs.microsoft.com/en-us/azure/application-gateway/)
* [Troubleshooting bad gateway errors in Application Gateway](https://docs.microsoft.com/en-us/azure/application-gateway/application-gateway-troubleshooting-502)

### Question

**Is the issue related to Application Gateway 502 error?**

### Options

- **Yes** → Go to: *Backend Response Check*
- **No** → Go to: *2c6753c5-262d-4e00-bd88-e017d9c2b337*

---

### Step 2: Intermittent 502 false  backend unhealthy  Unknown CA

### Support Engineer Solution

#### Backend server certificate not issued by a publicly known CA
When a Leaf and Intermediate certificate is issued by a private Certificate Authority (CA), the signing Root CA’s certificate must be uploaded to the application gateway’s associated Backend Setting. This error occurs if customer has chosen “well-known CA certificate” in the backend setting, but the Root certificate presented by the backend server is not publicly known.  

Customer can view and export the root certificate by following the steps mentioned in the article [Export Trusted Root certificates](https://learn.microsoft.com/en-us/azure/application-gateway/certificates-for-backend-authentication#export-trusted-root-certificate-for-v2-sku)

### Customer Solution

*Content type: MarkdownText*

We have identified that you have selected “well-known CA” in the backend HTTP setting, but the Root certificate presented by the backend server is not publicly known.   Please upload the root certificate of the backend server certificate in backend settings. 

---

### Step 3: Intermittent 502 false  backend unhealthy  CN mismatch

### Support Engineer Solution

#### Common Name Mismatch  

This error occurs when customer has selected HTTPS protocol in the backend setting, and neither the Custom Probe’s nor Backend Setting’s hostname (in that order) matches the Common Name/Subject Alternative Name(if present) of the backend server’s certificate.  
In case of V1,  the FQDN of the backend pool target doesn’t match the Common Name (CN) of the backend server’s certificate.  

Veridy if the Application Gateway is V1 or V2 and if it is using a default probe or custom probe configuration.  
**Application Gateway V2**:  
**Default Probe**: Specify the Common Name of the backend server certificate in the associated Backend Setting of the application gateway. You can select “Override with specific hostname” or “Pick hostname from backend target” in the backend setting.  
**Custom Probe**: You can use the “host” field to specify the Common Name of the backend server certificate. Alternatively, if the Backend Setting is already configured with the same hostname, you can choose “Pick hostname from backend setting” in the probe settings.

**Application Gateway V1**:  
Add the Common Name (CN) of the backend server certificate in the backend pool FQDN.

How to determine the CN of the backend server certificate is mentioned in the following documentation: [https://aka.ms/CNMismatch](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#common-name-cn-doesnt-match)

### Customer Solution

*Content type: MarkdownText*

This occurs when you have selected HTTPS protocol in the backend setting, and neither the Custom Probe’s nor Backend Setting’s hostname (in that order) matches the Common Name (CN) of the backend server’s certificate.
(For V1) The FQDN of the backend pool target doesn’t match the Common Name (CN) of the backend server’s certificate.

---

### Step 4: Intermittent 502 true  instance issue

### Support Engineer Solution

#### Application Gateway Instance issue  
If a particular instance(s) of Application gateway is marking the backend pool as unhealthy and/or giving 502 responses, please check `Application Gateway Instance logs` and see if there are any reported errors.  
You may also check [NetVMA](https://netvma.azure.net/) of the App Gateway or the specific instance to see if there are any platform issues.

**Logs can be located at**:  
`Jarvis Logs > AppGWT > ApplicationGatewayTenant, RequestRespErrorLog, InformationLogEvent, ApplicationGatewayBootstrap`  

**Sample link**: [Instance Logs](https://jarvis-west.dc.ad.msft.net/6ECF05D)

### Customer Solution

*Content type: MarkdownText*

The Error 502 you are receiving looks specific to some Application Gateway instance(s) in your scenario. You can either try to make a cosmetic change to the configuration and see if it helps. Stopping and starting Application Gateway may help as well.  

Please note that restarting the Application Gateway will cause a temporary disruption in traffic. If you have an Application Gateway V1, beware that the public IP Address for the Application Gateway will change with stop/start operation.

---

### Step 5: Intermittent 502 false  Backend unknown

### Support Engineer Solution

### Backend Health is Unknown  

Unknown indicates that there is a connectivity issue between Application Gateway and the platform (Gateway Manager) and the platform does not known if the Application Gateway got healthy response from backend or not.  

**Possible Causes**  
This behavior can occur for one or more of the following reasons:

* The NSG on the Application Gateway subnet is blocking inbound access to ports 65503-65534 (V1 SKU) or 65200-65535 (V2 SKU) from “Internet."  
* The UDR on the Application Gateway subnet is set to the default route (0.0.0.0/0) and the next hop is not specified as "Internet."  
* The default route is advertised by an ExpressRoute/VPN connection to a virtual network over BGP.  
* The custom DNS server is configured on a virtual network that can't resolve public domain names.  
* Application Gateway is in an Unhealthy state.  

**Reference Documents**  
The mititgation steps are mentioned in our public documentation "[Backend health status: unknown](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-health-status-unknown)".

### Customer Solution

*Content type: MarkdownText*

Backend health "Unknown" indicates that there is connectivity issue between the Application Gateway and the platform and the platform does not known if the Application Gateway got healthy response from backend or not.  

---

### Step 6: Intermittent 502 false  unhealthy  leaf cert missing

### Support Engineer Solution

#### Leaf certificate not found or missing from the chain  
The backend server certificate chain must start with the Leaf Certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate. 

To verify if the backend is presenting the complete chain or not, customer can run following OpenSSL commands:  

`s_client -connect FQDN:443 -showcerts`  
Or  
`s_client -connect IPaddress:443 -servername <TLS SNI hostname> -showcerts`  

Resolution steps are mentioned in our public documentation "[The leaf or server certificate was not found](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#the-leaf-or-server-certificate-was-not-found)".

### Customer Solution

*Content type: MarkdownText*

We have identified that the leaf certificate is missing from the certificate chain presented by the backend server.    

The backend server certificate chain must start with the Leaf Certificate, then the Intermediate certificate(s), and finally, the Root CA certificate.

---

### Step 7: Intermittent 502 true  Request timeout

### Support Engineer Solution

#### 502 error due to Request Timeout

**Request timeout** is the number of seconds that the Application Gateway waits to receive a response from the backend server.

The default timeout value for a response is 20 seconds (this is configurable in Backend HTTP Setting).  
If Application Gateway V1 does not receive a response from the backend in 20 seconds, it will send 502 response to the client.

**Mitigation steps**  
Customer should increase the request timeout value in backend HTTP setting depending on their application requirement.   

If the backend is expected to respond within the configured timeout value, customer needs to investigate why application is taking longer to respond. 

### Customer Solution

*Content type: MarkdownText*

When a user request is received, the application gateway applies the configured rules to the request and routes it to a backend pool instance. It waits for a configurable interval of time for a response from the backend instance. By default, this interval is 20 seconds. In Application Gateway v1, if the application gateway doesn't receive a response from backend application in this interval, the user request gets a 502 error.

Ensure that the backend is responding within the configured timeout value `Request time-out (seconds)` value on the `Backend settings` for the given Application Gateway. You may want to increase it to fix the error.

**Reference document**  
[Request time-out](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-troubleshooting-502#request-time-out) documentation.

---

### Step 8: Intermittent 502 true  public backend pool

### Support Engineer Solution

#### Backend pool contains Public IP or FQDN

The frontend IP of the external Application Gateway belongs to a Load Balancer and therefore a maximum of 64,000 SNAT ports are allocated.  
If the backend pool member is a Public IP, the Application Gateway will use these SNAT ports for probe and live traffic. Thus, depending on the probe intervals and traffic load, SNAT exhaustion can happen on the Frontend IP address of the given Application Gateway.

**Mitigation Step**  
Customer can increase the minimum instance count on Application Gateway.  

**Reference document**  
As per our [**Default port allocation table**](https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-outbound-connections#preallocatedports) document, any Azure Virtual Machine can have a maximum of 1024 SNAT ports by default. Say, if the the active instance count of the the Application Gateway is 5, we will be limited to 5120 SNAT ports. Any SNAT connections beyond this limit will see a 502 error.

### Customer Solution

*Content type: MarkdownText*

In your scenario, the backend pool member is a public IP or a public FQDN and we have observed SNAT exhaustion intermittently.

If backend pool consists of public IP or public FQDN, Application Gateway will use its frontend public IP for both probe and live traffic and this can cause SNAT port exhaustion when the traffic is high. Typically one instance can cater roughly 1000 (1024 to be precise) SNAT ports.

To mitigate this behavior we suggest to increase the `Minimum instance count` of the Application Gateway.

---

### Step 9: Intermittent 502 false  backend unhealthy  TCP error

### Support Engineer Solution

### TCP Connectivity issue

#### Things to check
* **NSG issue:** Check whether the NSG on the Application Gateway subnet allows outbound public/private traffic to the backend, and also check the NSG on the backend subnet whether inbound connections to the configured port are allowed.
* **Backend port issue:** Confirm if the backend port is in listening state. 
* **User-defined route issue:** Check if there is a route table on App Gateway subnet containing UDR which is forwarding traffic destined for backend subnet to a virtual appliance/firewall.  
Also, check if the default route is being advertised to the Application Gateway subnet via Azure ExpressRoute and/or VPN.
* **Guest OS firewall issue:** If backend is an IaaS server, check OS firewall settings to make sure that incoming traffic to the port is allowed.  

Resolution steps are mentioned in our public documentation: [https://aka.ms/servernotreachable](https://aka.ms/servernotreachable)

**Note**: In ASC, you can run **Test Traffic** from Application Gateway instances and it would identify any blocker in routing and NSG from Application Gateway standpoint.  

Please utilize ASC tool "**Backend Connectivity Diagnostic (for v2 SKU)** to check if there is a connectivity issue between Application Gateway and the backend pool.    

### Customer Solution

*Content type: MarkdownText*

This error message indicates that there is a TCP connectivity issue between Application Gateway and the backend. It could be an issue related to NSG, routing, firewall or application.  

---

### Step 10: Intermittent 502 true  failed state

### Support Engineer Solution

#### Application Gateway in failed state  
Failed state of a resource can impact its dataplane connectivity so we must restore it to "Succeeded" provisioning state.

For further assistance on failed state issue, please check this TSG: [Link to external TSG](https://asctsgreporting.azurewebsites.net/AuthoringGraph/145175)

### Customer Solution

*Content type: MarkdownText*

We have identified that your Application Gateway is in failed provisioned state.  
This might impact the dataplane connectivity and may result in intermittent 502 errors. 

You may try reverting the previous change or make some alteration to the same operation so that the Application Gateway is back to a stable state.

Alternatively, you can try to do a get and set operation for the Application Gateway, which will try to reprovision the gateway as mentioned on the document "[Troubleshoot Azure Microsoft.Network failed provisioning state](https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state)".  
`Get-AzApplicationGateway -Name "your_resource_name" -ResourceGroupName "your_resource_group_name" | Set-AzApplicationGateway`

---

### Step 11: Intermittent 502 false  backend unhealthy  HTTP error

### Support Engineer Solution

#### HTTP Connectivity issue  

**Default probe**  
The default probe will be to protocol://127.0.0.1:port/ and Application Gateway will accept HTTP status code between 200-399 as a healthy response from backend. If the backend responds with any other status code other than this range, the Application Gateway will mark the backend as unhealthy.  
If customer think the response is legitimate and they want Application Gateway to accept other status codes as Healthy, please suggest them to create a custom probe. 

**Custom probe**  
The probe will be to protocol, host and port defined in the custom probe settings. The host can be entered manually or taken from Backend HTTP settings if "pick hostname from backend settings" is enabled. 

Resolution are mentioned in our public documentation: [https://aka.ms/StatusCodeMismatch](https://aka.ms/StatusCodeMismatch)

### Customer Solution

*Content type: MarkdownText*

After the TCP connection has been established and a TLS handshake is done (if TLS is enabled), Application Gateway will send the probe as an HTTP GET request to the backend server. As described earlier, the default probe will be to protocol://127.0.0.1:port/, and it considers response status codes in the range 200 through 399 as Healthy. If the server returns any other status code, the Application Gateway will mark the backend as unhealthy.

---

### Step 12: Intermittent 502 false  backend unhealthy  cert invalid

### Support Engineer Solution

#### This error can occur due to several reasons as listed below  

* **Certificate has expired**  
If the current date is not within the "Valid from" and "Valid to" date range on the certificate, the certificate is marked as invalid as it is not deemed safe by the Application Gateway.  

* **Incomplete certificate chain**  
If the backend server is not presenting complete certificate chain, the Application Gateway v1 can mark the backend as unhealthy.  
To verify the chain completeness, we can use the following OpenSSL commands.
`s_client -connect <FQDN>:443 -showcerts`  
Or  
`s_client -connect <IPaddress>:443 -servername <TLS SNI hostname> -showcerts`  

* **SNI Mismatch**  
The Application Gateway indicates which hostname it is attempting to connect to at the start of the handshaking process by SNI (Server Name Indication).  
**SNI Behavior for probe traffic in Application Gateway V1**  
SNI header (Server Name Indication) during a TLS handshake with the backend server will be set as FQDN from the backend pool as per RFC 6066.
If the backend pool address is an IP address, SNI (server_name) won’t be set.  
If you have packet captures collected on Application gateway and/or backend, you will be able to see `Server Name Indication extension` under `Extension: server_name` in TLS Client Hello packet.  
If you don't see this extension in TLS Client Hello, this means that the Application Gateway is not sending SNI.  
If there’s no default/fallback certificate configured in the backend server and SNI is expected, the server will reset the connection.  

**Reference Document**  
[Troubleshoot backend health issues in Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting)

### Customer Solution

*Content type: MarkdownText*

The issue appears to be related to , expired or an incomplete certificate. Please ensure the certificate is valid by following one of these documents:

* [Troubleshoot backend health issues in Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting)
   * [Common Name (CN) doesn't match](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#common-name-cn-doesnt-match)
   * [Backend certificate has expired](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-certificate-has-expired)
   * [The intermediate certificate was not found](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#the-intermediate-certificate-was-not-found)

---

### Step 13: Intermittent 502 false  backend unhealthy  expired cert

### Support Engineer Solution

#### Backend server certificate has expired  
An expired certificate is deemed unsafe and hence the application gateway marks the backend server with an expired certificate as unhealthy.  

Resolution steps are mentioned in our public documentation "[Backend certificate has expired
](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-certificate-has-expired)".  

**Note:**  
When importing the .pfx on an IIS server, prioritize selecting the WebHosting as the Certificate store. Unlike the Personal Certificate store, the WebHosting store offers wider accessibility to other services and applications on the system, making it the preferred choice, especially when importing a pfx onto IIS.

### Customer Solution

*Content type: MarkdownText*

We have identified that your backend server certificate has expired. An expired certificate is deemed unsafe and hence the application gateway marks the backend server with an expired certificate as unhealthy.

**Note:**  

When importing the .pfx on an IIS server, prioritize selecting the WebHosting as the Certificate store. Unlike the Personal Certificate store, the WebHosting store offers wider accessibility to other services and applications on the system, making it the preferred choice, especially when importing a pfx onto IIS.

---

### Step 14: Intermittent 502 true  Other

### Support Engineer Solution

**If your cause is not listed in the last tile, it may require scenario-based troubleshooting.**

Please check **ReqRespErrorLog**(V2) and **InformationLogEvent**(V1) as it may indicate the cause of 502 errors given by Application Gateway.

Data can be located at:  
**Application Gateway V1**: `Jarvis > AppGWT > InformationLogEvent`  
Or  
**Application Gateway V2**: `Jarvis > AppGWT > ReqRespErrorLog`  

Some common errors to look out for:  

* Connection refused 
* Upstream prematurely closed the connection
* Connection reset by peer  

**Collect & Analyze simultaneous network traces**    
Please collect simultaneous network traces on backend and/or Application Gateway during repro of the 502 error. 

Raise an Ava request if need be.

### Customer Solution

*Content type: MarkdownText*

Provide an action plan or solution  to the customer based on Recommended action listed under Support Engineer solution instructions.

---

### Step 15: Intermittent 502 false  backend unhealthy  V2 SNI issue

### Support Engineer Solution

**SNI Behavior for probe traffic in Application Gateway V2**  
SNI header is set as the hostname in the custom probe attached to the HTTP settings or, `override hostname` set in HTTP settings or backend pool (in that order).  
If no custom probe is configured and no hostname is set on HTTP settings or backend pool, then no SNI is set.   

**How to identify**  
If you have packet captures collected on Application gateway and/or backend, you will be able to see `Server Name Indication extension` under `Extension: server_name` in TLS Client Hello packet.  
If you don't see this extension in TLS Client Hello, this means that the Application Gateway is not sending SNI.  

If there’s no default/fallback certificate configured in the backend server and SNI is expected, the server will reset the connection.

### Customer Solution

*Content type: MarkdownText*

It is observed that the Application Gateway is trying to connect to the backend a server name that is different than what the backend is expecting. This is could be because of the misspelled name or connectivity issues.  
Suggest to double check on the server name the Application Gateway is trying to connect to.

---

### Step 16: Intermittent 502 true  Performance

### Support Engineer Solution

#### Application Gateway performance issue  
If Application Gateway's instances CPU or memory utilization or overall gateway utilization is consistently high > 75%, App Gateway can throw 502 errors intermittently for client requests.

You can also use this [App Gateway V2 dashboard](https://jarvis-east.dc.ad.msft.net/dashboard/share/1262C8B1?overrides=[{"query":"//*[id='applicationGatewayId']","key":"value","replacement":"00000000-0000-0000-0000-000000000000"},{"query":"//*[id='VipAddress']","key":"value","replacement":""}]&globalStartTime=1684825147379&globalEndTime=1685429947379&pinGlobalTimeRange=true) to view metrics on the performance and usage of the Application Gateway instances. 

### Customer Solution

*Content type: MarkdownText*

We have identified that your Application Gateway utilization is regularly high and this may result in 502 errors.   

Ensure that the Application Gateway is not being overutlilized. Check for metrics such as CPU, memory, overall gateway utilization, autoscaling operations on the Monitoring section for the given Application Gateway on Azure Portal. Please consider increasing the instance count to manage the incoming load to the Application Gateway. 

---

### Step 17: Backend Response 502

### Support Engineer Solution

#### Error 502 received from Backend

Check **ReqRespErrorLog** (V2) or **InformationLogEvent** (V1) to ensure that there is no connection failure between App Gateway and backend.  
These logs can be filtered with Client IP and the URI of the HTTP request which got 502 response as found from [ReqRespLog](https://portal-eu.microsoftgeneva.com/s/E224DE15).

**Data location:** 

**Application Gateway V2**: Jarvis > AppGWT > [ReqRespErrorLog](https://jarvis-west.dc.ad.msft.net/FED7E7D7)  
**Application Gateway V1**: Jarvis > AppGWT > [InformationLogEvent](https://jarvis-west.dc.ad.msft.net/1ACDE539)  

If there are no errors found in Application Gateway logs and the 502 response can be seen coming from the backend, customer needs to check the backend application logs and dig further at application level.

### Customer Solution

*Content type: MarkdownText*

It appears that the 502 response is coming from Application Gateway's Backend, and not from the gateway itself.

Suggest to investigate backend application logs.

---

### Step 18: Intermittent 502 false  backend unhealthy  DNS issue

### Support Engineer Solution

### DNS Resolution issue  

#### Things to check

**Custom DNS:**  
1. If the Application Gateway Virtual Network is configured with custom DNS servers, make sure that Application Gateway is able to communicate with those custom DNS server(s).  
2. Try nslookup to the backend FQDN from a VM in same VNet as the Application Gateway to confirm if custom DNS server is able to resolve the FQDN.  
  
**Azure DNS:**  
1. If the FQDN is a public domain, you can try to resolve it from your local machine or from a VM in same virtual Network as the Application Gateway.
2. If it is a private or internal custom domain, check if a private DNS zone is linked to the Virtual Network and A or CNAME record is created in the private DNS zone.  

Resolution steps are mentioned in our public documentation: [https://aka.ms/dnsresolutionerror](https://aka.ms/dnsresolutionerror)  
Also refer:  [https://aka.ms/UnknownBackendHealth](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#updates-to-the-dns-entries-of-the-backend-pool)

**Note 1**: If customer has changed DNS servers on the VNet recently, please make sure that customer has done **Stop-Start** on the Application Gateway for the DNS changes to take effect.  
**Note 2**: If you are not seeing logs for the target FQDN in BackendServerDiagnosticHistory or ReqRespErrorLog/InformationLogEvent, you can manually trigger a backend health check from:  
`Jarvis Actions > Brooklyn > Application Gateways > Get Application Gateway Backend Health`  
**Note 3**: Please utilize ASC tool "**Backend Connectivity Diagnostic (for v2 SKU)** to confirm if the Gateway is able to resolve backend FQDN.  

### Customer Solution

*Content type: MarkdownText*

If the backend pool is of type FQDN or App Service, Application Gateway resolves to the IP address of the FQDN using the DNS servers (custom or Azure-provided) defined on the Virtual Network. The application gateway then tries to connect to the server on the TCP port mentioned in the HTTP settings. But if this message is displayed, it suggests that Application Gateway couldn't successfully resolve the IP address of the backend FQDN. 
 

---

### Step 19: Intermittent 502 true  config limits

### Support Engineer Solution

#### Application Gateway configuration limits exceeded  
If the Application Gateway configuration is running over the published limits, this can lead to 502 errors and also cause instability and slowness.  
For example, if Listener Limits exceed 100 active listeners for Standard/WAF SKU with CRS 3.2 or higher, OR 40 active listeners for CRS 3.1 or lower, this may result in 502 error. 

### Customer Solution

*Content type: MarkdownText*

We have found that your current configuration is not within the published limits for Application Gateway. Ensure that the Application Gateway configuration such as HTTP listener, backend targets per pool count etc. is within the recommended limits. See [Application Gateway limits](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits#application-gateway-limits) for more information.

---

### Step 20: Intermittent 502 false  V1 cert not whitelisted

### Support Engineer Solution

### Backend server certificate is not whitelisted with Application Gateway  

This error occurs when the Authentication Certificate added in Backend Settings does not match with the certificate presented by the backend server.  
The Application Gateway v1 SKU uses an exact match of the authentication certificate (public key of the backend server certificate and not the root certificate) to be uploaded to the HTTP settings. 

To resolve this error, we must ensure that the public key of the backend server certificate (in ".cer" format) is added as an Authentication Certificate in Backend Setting.  

Customer can export authentication certificate by following this document: [Export authentication certificate for v1 SKU](https://learn.microsoft.com/en-us/azure/application-gateway/certificates-for-backend-authentication#export-authentication-certificate-for-v1-sku)

### Customer Solution

*Content type: MarkdownText*

The Application Gateway v1 SKU uses an exact match of the authentication certificate (public key of the backend server certificate and not the root certificate) to be uploaded to the HTTP settings.  

You can export authentication certificate by following this document: [Export authentication certificate for v1 SKU](https://learn.microsoft.com/en-us/azure/application-gateway/certificates-for-backend-authentication#export-authentication-certificate-for-v1-sku)

---

### Step 21: Intermittent 502 false  backend unhealthy  Probe timeout

### Support Engineer Solution

#### Probe timeout issue  

After Application Gateway sends an HTTP(S) probe request to the backend server, it waits for a response from the backend server for a configured period. If the backend server doesn't respond within the configured period (the timeout value), it's marked as Unhealthy until it starts responding within the configured timeout period again.  
The default probe has a 30-second timeout value. This can be increased by configuring a custom probe.

Resolution steps are mentioned in our public documentation: [https://aka.ms/ProbeTimeOut](https://aka.ms/ProbeTimeOut)

### Customer Solution

*Content type: MarkdownText*

After Application Gateway sends an HTTP(S) probe request to the backend server, it waits for a response from the backend server for a configured period. If the backend server doesn't respond within the configured period (the timeout value), it's marked as unhealthy until it starts responding within the configured timeout period again.   

Please investigate why your backend server or application isn't responding within the configured timeout period. If the application is expected to respond after the current timeout period, increase the timeout value from the custom probe settings.  

---

### Step 22: Intermittent 502 false  unhealthy  IntermediateCertMissing

### Support Engineer Solution

#### Intermediate Certificate not found

An Intermediate certificate is used to sign the Leaf certificate and is thus needed to complete the chain. Check with your Certificate Authority (CA) for the necessary Intermediate certificate(s) and install them on your backend server.

To verify if the backend is presenting the complete chain or not, customer can run following OpenSSL commands:  

`sclient -connect <span style="color:green">FQDN</span>:443 -showcerts`  
or  
`sclient -connect <span style="color:green">IPaddress</span>:443 -servername <span style="color:green">TLS SNI hostname</span> -showcerts`  

You will see an output such as:  
<span style="color:tomato">verify error:num=20: unable to get local issuer certificate in the above means the intermediate cert is missing from the chain</span>  
It means the intermediate cert is missing from the chain.

Resolution steps are mentioned in our public documentation "[The intermediate certificate was not found](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#the-intermediate-certificate-was-not-found)".

### Customer Solution

*Content type: MarkdownText*

We have identified that the intermediate certificate is missing from the certificate chain presented by the backend server.  
An Intermediate certificate is used to sign the Leaf certificate and is thus needed to complete the chain. Check with your Certificate Authority (CA) for the necessary Intermediate certificate(s) and install them on your backend server.

---

### Step 23: Intermittent 502 false  unhealthy  CertOrderingIncorrect

### Support Engineer Solution

#### Backend Certificate chain incorrectly ordered  
The backend server certificate chain must start with the leaf certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate.

To check if the certificate is bundled correctly and the backend is presenting the complete chain, please advise customer to run following OpenSSL commands from a VM in same Virtual Network as the Application Gateway:  

`s_client -connect <FQDN>:443 -showcerts`   
Or  
`s_client -connect <IPaddress>:443 -servername <TLS SNI hostname> -showcerts`   

Resolution steps are mentioned in our public documentation: [https://aka.ms/LeafMustbeTopmostinChain](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#leaf-must-be-topmost-in-chain)

### Customer Solution

*Content type: MarkdownText*

We have identified that your backend server certificate is not correctly ordered.  
The backend server certificate chain must start with the leaf certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate.

---

### Step 24: Intermittent 502 false  backend unhealthy  V2 cert issue

### Guidance

### Common certificate issues in V2  

* #### Common Name mismatch  
**Customer facing Message**: *The Common Name of the leaf certificate presented by the backend server does not match the Probe or Backend Setting hostname of the application gateway.*   
**Application Gateway V2**: Error in [BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11) `ngx_http_upstream_check_err_BackendCertificateCNMismatchWithProbeHostName`  

* #### Certificate ordering issue  
**Customer facing Message**: *The Leaf certificate is not the topmost certificate in the chain presented by the backend server. Ensure the certificate chain is correctly ordered on the backend server.*   
**Application Gateway V2**: Error in [BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11) `err_IncorrectBackendCertificateChainLeafCertificateIsNotTopmostCertificate`  

**Customer facing Message**: *The backend server is presenting an incomplete certificate chain, including only the leaf certificate. Please ensure that the certificate chain is fully configured with all necessary certificates in the correct order.*   
**Application Gateway V2**: Error in [BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11) `ngx_http_upstream_check_err_IncompleteBackendCertificateChainOnlyLeafCertificateIsPresent`  

* #### Server/intermediate certificate is not issued by a publicly known CA  
**Customer facing Message**: *The backend server certificate is not signed by a well-known Certificate Authority (CA). To use unknown CA certificates, its Root certificate must be uploaded to the Backend Setting of the application gateway.*    
Or  
**Customer facing Message**: *The Intermediate certificate is not signed by a well-known Certificate Authority (CA). Ensure the certificate chain is complete and correctly ordered on the backend server.*    
**Application Gateway V2**: Error in [BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11) will be similar to `CertificateNotTrustedByWellKnownCA`  

* #### Leaf certificate is missing or not found  
**Customer facing Message**: *The leaf certificate is missing from the certificate chain presented by the backend server. Please ensure that the certificate chain is complete and correctly ordered.*    
**Application Gateway V2:**: Error in [BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11) `ngx_http_upstream_check_err_IncorrectBackendCertificateChainMissingLeafCertificate`  

* #### The intermediate certificate not found  
**Customer facing Message**: *The Intermediate certificate is missing from the certificate chain presented by the backend server. Ensure the certificate chain is complete and correctly ordered on the backend server.*    
**Application Gateway V2**: Error in [BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11) `err_BackendServerCertificateNotTrustedByWellKnownCAsDueToIncompleteOrIncorrectIn

*(Content truncated — refer to original GT for full details)*

### Step 25: Intermittent 502 false  backend unhealthy  V1 cert issue

### Guidance

### Common certificate issues in V1

*New backend health messages for certificate errors are available for V2 SKU only.*   

* ####Backend server certificate not whitelisted  
**Customer facing message**:  *Backend server certificate is not whitelisted with Application Gateway. Make sure that the certificate uploaded to Application Gateway matches with the certificate configured in your backend server. To learn more visit - https://aka.ms/authcertificatemismatch*  
**Application Gateway V1**: Error in [InformationLogEvent](https://jarvis-west.dc.ad.msft.net/D680BFE0): `BackendServerCertificateNotWhitelisted`  

* ####Certificate marked invalid 
**Customer facing message**: *Backend certificate has been marked invalid. Either the certificate is not within its validity period, or it has been revoked by the issuing authority, or there is a problem with the certificate chain.*  
**Application Gateway V1**: Error in [InformationLogEvent](https://jarvis-west.dc.ad.msft.net/D680BFE0): `BackendSecureConnectionError`

### Question

**Are you able to identify one of the below mentioned behaviors?**

### Options

- **Backend server certificate is not whitelisted** → Go to: *Intermittent 502 false  V1 cert not whitelisted*
- **Certificate marked invalid** → Go to: *Intermittent 502 false  backend unhealthy  cert invalid*

---

### Step 26: Intermittent 502 false  backend healthy

### Guidance

#### Backend status is Healthy

**If the status of the backend stays *Healthy*, you may want to investigate some common causes of 502 errors mentioned below**  

* **HTTP Request Timeout**  
Check `serverResponseLatency` field in ReqRespLog table. If it is exceeding the request timeout value configured in the backend setting, it is usually an indication that the backend is not responding within the configured timeout value and thus, Application Gateway V1 will send 502 response to the client.

* **Application Gateway performance issue**  
Check Application Gateway instances' CPU, memory, overall gateway utilization, autoscaling operations from [Platform Metrics dashboard](https://jarvis-west.dc.ad.msft.net/dashboard/share/12C7E6AF?overrides=[{"query":"//*[id='applicationGatewayId']","key":"value","replacement":""},{"query":"//*[id='GatewayId']","key":"value","replacement":""},{"query":"//*[id='roleInstance']","key":"value","replacement":""}]%20).

* **Specific Application Gateway instance(s) giving 502 error**  
Check `RoleInstance` column ReqRespLog to confirm if all the gateway instances are giving 502 errors intermittently or if the 502 response is given by certain instances only. 

* **Application Gateway configuration limits exceeded**  
Check if Application Gateway configuration (HTTP listener, backend targets per pool count etc.) is within the limits. See [Application Gateway limits](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits#application-gateway-limits)

* **Backend pool member is a public IP address or a public FQDN**  
If backend pool consists of public IP or public FQDN, Application Gateway will use its frontend public IP for both probe and live traffic and this can cause SNAT port exhaustion.  
You can check if SNAT exhaustion is happening on App Gateway frontend IP from [SNAT dashboard](https://portal.microsoftgeneva.com/s/207BCE8F?overrides=[{"query":"//dataSources","key":"account","replacement":""},{"query":"//*[id='VipAddress']","key":"value","replacement":""}]&globalStartTime=1685098964792&globalEndTime=1685102564792&pinGlobalTimeRange=true)

* **Application Gateway is in failed state**  
If the provisioning state of Application Gateway is `Failed`, it can cause dataplane to be impacted and result in 502 errors.

Based on our findings for the given scenario, the scenarios and solutions may vary. Please compose the customer messaging accordingly.

### Question

**Are you able to identify one of the below mentioned behaviors?**

### Options

- **HTTP Request Timeout** → Go to: *Intermittent 502 true  Request timeout*
- **Application Gateway performance issue** → Go to: *Intermittent 502 true  Performance*
- **Application Gateway configuration limits exceeded** → Go to: *Intermittent 502 true  config limits*
- **Backend pool member is a public IP address or a public FQDN** → Go to: *Intermittent 502 true  public backend pool*
- **Application Gateway is in 

*(Content truncated — refer to original GT for full details)*

### Step 27: Intermittent 502

### Guidance

### Check if the error is intermittent

* Customer is complaining that some of the requests are getting 502 responses from App Gateway.
* Alternatively, you can see `httpStatus` as **502** for some of the requests in [ReqRespLog](https://jarvis-west.dc.ad.msft.net/C3BF963B) for the reported timestamps. 

### Question

**Are the 502 responses intermittent?**

### Options

- **Yes** → Go to: *Intermittent 502 true*
- **No** → Go to: *Intermittent 502 false  Check backend Health*

---

### Step 28: Intermittent 502 true  backend health

### Guidance

#### Backend Health issue  

Look at the **Healthy** field in **[BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11)** table which can be located at:

* `Jarvis Logs > AppGWT > BackendServerDiagnosticHistory` or  
* `[MDM Logs] Backend Server Diagnostics History` link under **Diagnostic** section of the given Application Gateway in **ASC**.

If the backend pool is getting marked unhealthy intermittently, it will result in intermittent 502 errors from App gateway.

To find out the reason for unhealthy backend pool, you can refer to following logs:  
**Application Gateway V1**: `Jarvis > AppGWT > InformationLogEvent`  
**Application Gateway V2**: `Jarvis > AppGWT > ReqRespErrorLog`

### Question

**Is the backend pool marked unhealthy?**

### Options

- **Yes** → Go to: *Intermittent 502 false  backend unhealthy*
- **No** → Go to: *Intermittent 502 false  backend healthy*
- **Unknown** → Go to: *Intermittent 502 false  Backend unknown*

---

### Step 29: Intermittent 502 false  backend unhealthy

### Guidance

### Common causes of backend health issues  
* #### DNS Resolution issue (if backend is an FQDN)
**Customer facing Message:** *Application Gateway could not create a probe for this backend. This usually happens when the FQDN of the backend has not been entered correctly.*  
Or  
*The backend health status could not be retrieved. This happens when an NSG/UDR/Firewall on the application gateway subnet is blocking traffic on ports 65503-65534 in case of v1 SKU, and ports 65200-65535 in case of the v2 SKU or if the FQDN configured in the backend pool could not be resolved to an IP address.*
#### How to identify
   **Application Gateway V1**: Check [InformationLogEvent](https://jarvis-west.dc.ad.msft.net/D680BFE0): `HostNameNotResolved`  
   **Application Gateway V2**: Check [BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11) table and look for the `ServerAddress` field. Additionally, you'll see a similar error in [ReqRespErrorLog](https://jarvis-west.dc.ad.msft.net/E8B3E6A6): `host not found in upstream`  
  **Note**: You can check if Application Gateway is able to resolve DNS names from [Jarvis Actions > Brooklyn > Application Gateways > Get List of NonResolvable Domains](https://portal.microsoftgeneva.com/actions?page=actions&acisEndpoint=Public&selectedNodeType=3&extension=Brooklyn&group=Application%20Gateways&operationId=getlistofnonresolvabledomains&operationName=Get%20List%20of%20NonResolvable%20Domains&inputMode=single¶ms=%7B%22subscriptionid%22:%229c9ca454-1f17-4dc1-8e7c-90b485c2c71a%22,%22resourcegroupname%22:%22auduk_uat_projectidea%22,%22applicationgatewayname%22:%22AUDUKSUATAGWPROJIDEA01%22,%22domainnametocheck%22:%22amcgateway-dev.uk.kworld.kpmg.com%22,%22includedefaultcontrolpathendpoints%22:false,%22includedefaultdatapathendpoints%22:false,%22smegatewaymanagerregion%22:%22UK%20South%22%7D&actionEndpoint=Brooklyn%20-%20Prod)

* #### TCP connectivity issue
**Customer facing Message**: *Application Gateway could not connect to the backend. Check that the backend responds on the port used for the probe. Also check whether any NSG/UDR/Firewall is blocking access to the IP and port of this backend.*  
#### How to identify
   **Application Gateway V1**: Error in [InformationLogEvent](https://jarvis-west.dc.ad.msft.net/D680BFE0): `ServerNotReachable`  
   **Application Gateway V2**: Error in [BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11) `ngx_http_upstream_check_err_ServerNotReachable`  

* #### HTTP connectivity issue  
**Customer facing Message:** *Status code of the backend's HTTP response did not match the probe setting. Expected:{HTTPStatusCode0} Received:{HTTPStatusCode1}.*  
Or  
*Body of the backend's HTTP response did not match the probe setting. Received response body doesn't contain {string}.*
#### How to identify 
   **Application Gateway V1**: Error in  [InformationLogEvent](https://jarvis-west.dc.ad.msft.net/D680BFE0): `HttpStatusCodeMismatch`  
   **Applica

*(Content truncated — refer to original GT for full details)*

### Step 30: Intermittent 502 true

### Guidance

### Common Causes of intermittent 502 errors

* **HTTP Request Timeout:** Check `serverResponseLatency` field in [ReqRespLog](https://jarvis-west.dc.ad.msft.net/C3BF963B) table. If it is exceeding the request timeout value configured in the backend setting, it is usually an indication that the backend is not responding within the configured timeout value and thus, Application Gateway V1 will send 502 response to the client.
* **Application Gateway performance issue:** Check Application Gateway instances' CPU, memory, overall gateway utilization, autoscaling operations from [Platform Metrics dashboard](https://jarvis-west.dc.ad.msft.net/dashboard/share/12C7E6AF?overrides=[{"query":"//*[id='applicationGatewayId']","key":"value","replacement":""},{"query":"//*[id='GatewayId']","key":"value","replacement":""},{"query":"//*[id='roleInstance']","key":"value","replacement":""}]%20).
* **Backend pool marked unhealthy intermittently:** Check BackendServerDiagnostic History table to see if the backend pool is marked unhealthy during the time when 502 errors are given.  
*Data Location:* Jarvis > AppGWT > [BackendServerDiagnosticHistory](https://jarvis-west.dc.ad.msft.net/44226C7F)
* **Specific Application Gateway instance(s) giving 502 errors:** Check `RoleInstance` column ReqRespLog to confirm if all the gateway instances are giving 502 errors intermittently or if the 502 response is given by certain instances only. 
* **Application Gateway configuration limits exceeded:** Check if App Gateway configuration (HTTP listener, backend targets per pool count etc.) is within the limits. See [Application Gateway limits](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits#application-gateway-limits)
* **Backend pool member is a public IP address or a public FQDN:** If backend pool consists of public IPs/FQDNs, App Gateway will use its Load Balancer IP for both probe and live traffic and this can lead to SNAT port exhaustion.  
You can check if SNAT exhaustion is happening on App Gateway frontend IP from [SNAT dashboard](https://portal.microsoftgeneva.com/s/207BCE8F?overrides=[{"query":"//dataSources","key":"account","replacement":""},{"query":"//*[id='VipAddress']","key":"value","replacement":""}]&globalStartTime=1685098964792&globalEndTime=1685102564792&pinGlobalTimeRange=true)
* **Application Gateway is in failed state:** Failed provisioning state of App gateway can cause dataplane to be impacted and result in 502 errors.

### Question

**Are you able to identify one of the below mentioned behaviors?**

### Options

- **HTTP Request Timeout in V1 SKU** → Go to: *Intermittent 502 true  Request timeout*
- **Application Gateway performance issue** → Go to: *Intermittent 502 true  Performance*
- **Backend pool intermittently marked unhealthy** → Go to: *Intermittent 502 true  backend health*
- **Specific Application Gateway instance giving 502 errors** → Go to: *Intermittent 502 true  instance is

*(Content truncated — refer to original GT for full details)*

### Step 31: Backend Response Check

### Guidance

### Check the backend server response

For V1: **backend_httpStatus** field or **SERVER-STATUS** in Properties field in **[ReqRespLog](https://portal.microsoftgeneva.com/s/C239F8FD)**  
For V2: **serverStatus** field in **[ReqRespLog](https://jarvis-west.dc.ad.msft.net/BE20040)**

This can also be located at:  

* `Jarvis Logs > AppGWT > ReqRespLog` or  
* `[MDM Logs] Request Response` link under **Diagnostic** section of the given App Gateway in **ASC**

### Question

**Is the 502 response coming from the backend?**

### Options

- **Yes** → Go to: *Backend Response 502*
- **No** → Go to: *Intermittent 502*

---

### Step 32: Intermittent 502 false  Check backend Health

### Guidance

### Check Backend health  

Check **Backend Connectivity Diagnostic (For v2 SKU)** under **Diagnostics** section of **ASC** for the given Application Gateway. This can be very helpful.

Look at the **Healthy** field in **[BackendServerDiagnosticHistory]( https://jarvis-west.dc.ad.msft.net/4E424D11)** table which can be located at:

* `Jarvis Logs > AppGWT > BackendServerDiagnosticHistory` or  
* `[MDM Logs] Backend Server Diagnostics History` link under **Diagnostic** section of the given Application Gateway in **ASC**.

***Please Note***: Customers may be using *'Use Probe Matching Conditions'* to set *HTTP Status Code* other than 200-399. Check *'Args'* in *BackendDiagnosticHistory* for the actual backend response. If the *Backend Response* is other than 200-399 and probe is configured for that, choose 'Yes' as an option here.

### Question

**Is the backend pool marked unhealthy?**

### Options

- **Yes** → Go to: *Intermittent 502 false  backend unhealthy*
- **No** → Go to: *Intermittent 502 false  backend healthy*
- **Unknown** → Go to: *Intermittent 502 false  Backend unknown*

---

### Step 33: Intermittent 502 false  cert issue  check GW SKU

### Content

### Check Application Gateway SKU

You can find the Application Gateway SKU from:  

**ASC** > **Application Gateway** > under **`Properties`** section.  

SKU type: "Standard: or "WAF" indicates it is V1  

SKU type: "Standard-v2" or "WAF-v2" indicates it is V2

---
