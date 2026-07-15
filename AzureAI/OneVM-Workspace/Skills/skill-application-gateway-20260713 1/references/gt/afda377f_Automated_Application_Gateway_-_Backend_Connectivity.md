# Automated] Application Gateway - Backend Connectivity

> **Product:** Application Gateway  
> **Solution ID:** afda377f-355e-40c8-9cd9-d88291785211  
> **Trigger words:** application, application gateway, automated], backend, connectivity, connectivity issue, gateway

---

## Overview

This guide provides step-by-step troubleshooting for **Automated] Application Gateway - Backend Connectivity** under **Application Gateway**.
 The original guided troubleshooter contains 22 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: 502 Bad Gateway ⭐ (First Step)

### Guidance

After you configure an application gateway, one of the errors that you may see is Server Error: 502 - Web server received an invalid response while acting as a gateway or proxy server.

### Question

**Are you facing a 502 Bad Gateway Error?**

### Options

- **Yes** → Go to: *Backend Health*
- **No** → Go to: *Non 502 Errors*

---

### Step 2: Backend server timeout

### Support Engineer Solution

**Cause:** After Application Gateway sends an HTTP(S) probe request to the backend server, it waits for a response from the backend server for a configured period. If the backend server doesn't respond within the configured period (the timeout value), it's marked as Unhealthy until it starts responding within the configured timeout period again.

**Resolution:** Check why the backend server or application isn't responding within the configured timeout period, and also check the application dependencies. To fix this issue, please follow [these steps.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-server-timeout)

### Customer Solution

*Content type: MarkdownText*

**Cause:** After Application Gateway sends an HTTP(S) probe request to the backend server, it waits for a response from the backend server for a configured period. If the backend server doesn't respond within the configured period (the timeout value), it's marked as Unhealthy until it starts responding within the configured timeout period again.

**Resolution:** Check why the backend server or application isn't responding within the configured timeout period, and also check the application dependencies. To fix this issue, please follow [these steps.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-server-timeout)

---

### Step 3: Certificate Verification Failed

### Support Engineer Solution

**Cause:** This error occurs when Application Gateway can't verify the validity of the certificate.

**Resolution**: To resolve this issue, verify that the certificate on your server was created properly. For example, you can use [OpenSSL](https://www.openssl.org/docs/manmaster/man1/verify.html) to verify the certificate and its properties and then try reuploading the certificate to the Application Gateway HTTP settings.

### Customer Solution

*Content type: MarkdownText*

**Cause:** This error occurs when Application Gateway can't verify the validity of the certificate.

**Resolution**: To resolve this issue, verify that the certificate on your server was created properly. For example, you can use [OpenSSL](https://www.openssl.org/docs/manmaster/man1/verify.html) to verify the certificate and its properties and then try reuploading the certificate to the Application Gateway HTTP settings.

---

### Step 4: DNS Resolution Error

### Support Engineer Solution

**Cause:** If the backend pool is of type IP Address, FQDN or App Service, Application Gateway resolves to the IP address of the FQDN entered through DNS (custom or Azure default). The application gateway then tries to connect to the server on the TCP port mentioned in the HTTP settings. But if this message is displayed, it suggests that Application Gateway couldn't successfully resolve the IP address of the FQDN entered.

**Resolution:**

1.	Verify that the FQDN entered in the backend pool is correct and that it's a public domain, then try to resolve it from your local machine.
2.	If you can resolve the IP address, there might be something wrong with the DNS configuration in the virtual network.
3.	Check whether the virtual network is configured with a custom DNS server. If it is, check the DNS server about why it can't resolve to the IP address of the specified FQDN.
4.	If you're using Azure default DNS, check with your domain name registrar about whether proper A record or CNAME record mapping has been completed.
5.	If the domain is private or internal, try to resolve it from a VM in the same virtual network. If you can resolve it, restart Application Gateway and check again. To restart Application Gateway, you need to [stop](https://learn.microsoft.com/en-us/powershell/module/azurerm.network/stop-azurermapplicationgateway) and [start](https://learn.microsoft.com/en-us/powershell/module/azurerm.network/start-azurermapplicationgateway) by using the PowerShell commands described in these linked resources.

### Customer Solution

*Content type: MarkdownText*

**Cause:** If the backend pool is of type IP Address, FQDN or App Service, Application Gateway resolves to the IP address of the FQDN entered through DNS (custom or Azure default). The application gateway then tries to connect to the server on the TCP port mentioned in the HTTP settings. But if this message is displayed, it suggests that Application Gateway couldn't successfully resolve the IP address of the FQDN entered.

**Resolution:**

1.	Verify that the FQDN entered in the backend pool is correct and that it's a public domain, then try to resolve it from your local machine.

2.	If you can resolve the IP address, there might be something wrong with the DNS configuration in the virtual network.

3.	Check whether the virtual network is configured with a custom DNS server. If it is, check the DNS server about why it can't resolve to the IP address of the specified FQDN.

4.	If you're using Azure default DNS, check with your domain name registrar about whether proper A record or CNAME record mapping has been completed.

5.	If the domain is private or internal, try to resolve it from a VM in the same virtual network. If you can resolve it, restart Application Gateway and check again. To restart Application Gateway, you need to [stop](https://learn.microsoft.com/en-us/powershell/module/azurerm.network/stop-azurermapplicationgateway) and [start](https://learn.micr

*(Content truncated — refer to original GT for full details)*

### Step 5: Healthy Backend Server Status

### Support Engineer Solution

If the backend health status for a server is healthy, it means that Application Gateway will forward the requests to that server. Check if 502 is being served by the backend.

### Customer Solution

*Content type: MarkdownText*

If the backend health status for a server is healthy, it means that Application Gateway will forward the requests to that server. Check if 502 is being served by the backend.

---

### Step 6: HTTP response body mismatch

### Support Engineer Solution

**Cause:** When you create a custom probe, you can mark a backend server as Healthy by matching a string from the response body. For example, you can configure Application Gateway to accept "unauthorized" as a string to match. If the backend server response for the probe request contains the string **unauthorized**, it will be marked as Healthy. Otherwise, it will be marked as Unhealthy with this message.

**Resolution**: 

1.	Access the backend server locally or from a client machine on the probe path and check the response body.

2.	Verify that the response body in the Application Gateway custom probe configuration matches what's configured.

3.	If they don't match, change the probe configuration so that it has the correct string value to accept.

### Customer Solution

*Content type: MarkdownText*

**Cause:** When you create a custom probe, you can mark a backend server as Healthy by matching a string from the response body. For example, you can configure Application Gateway to accept "unauthorized" as a string to match. If the backend server response for the probe request contains the string **unauthorized**, it will be marked as Healthy. Otherwise, it will be marked as Unhealthy with this message.

**Resolution**: 

1.	Access the backend server locally or from a client machine on the probe path and check the response body.

2.	Verify that the response body in the Application Gateway custom probe configuration matches what's configured.

3.	If they don't match, change the probe configuration so that it has the correct string value to accept.

---

### Step 7: HTTP Status code mismatch

### Support Engineer Solution

**Cause:** After the TCP connection has been established and a TLS handshake is done (if TLS is enabled), Application Gateway will send the probe as an HTTP GET request to the backend server. As described earlier, the default probe will be to &lt;protocol&gt;://127.0.0.1:&lt;port&gt;/, and it considers response status codes in the range 200 through 399 as Healthy. If the server returns any other status code, it will be marked as Unhealthy with this message.

**Resolution:** Depending on the backend server's response code, you can take the [following steps.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#http-status-code-mismatch) 

### Customer Solution

*Content type: MarkdownText*

**Cause:** After the TCP connection has been established and a TLS handshake is done (if TLS is enabled), Application Gateway will send the probe as an HTTP GET request to the backend server. As described earlier, the default probe will be to &lt;protocol&gt;://127.0.0.1:&lt;port&gt;/, and it considers response status codes in the range 200 through 399 as Healthy. If the server returns any other status code, it will be marked as Unhealthy with this message.

**Resolution:** Depending on the backend server's response code, you can take the [following steps.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#http-status-code-mismatch) 

---

### Step 8: Non 502 Errors

### Support Engineer Solution

Refer to [Application Gateway HTTP Response Codes](https://learn.microsoft.com/en-us/azure/application-gateway/http-response-codes) for other application gateway response codes and their possible mitigations.

### Customer Solution

*Content type: MarkdownText*

Refer to [Application Gateway HTTP Response Codes](https://learn.microsoft.com/en-us/azure/application-gateway/http-response-codes) for other application gateway response codes and their possible mitigations.

---

### Step 9: TCP Connect Error

### Support Engineer Solution

**Cause:** After the DNS resolution phase, Application Gateway tries to connect to the backend server on the TCP port that's configured in the HTTP settings. If Application Gateway can't establish a TCP session on the port specified, the probe is marked as Unhealthy with this message.

**Resolution:** To fix this issue, please follow [these steps.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#tcp-connect-error)

### Customer Solution

*Content type: MarkdownText*

**Cause:** After the DNS resolution phase, Application Gateway tries to connect to the backend server on the TCP port that's configured in the HTTP settings. If Application Gateway can't establish a TCP session on the port specified, the probe is marked as Unhealthy with this message.

**Resolution:** To fix this issue, please follow [these steps.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#tcp-connect-error)

---

### Step 10: Unknown Backend Server Status

### Support Engineer Solution

This behavior can occur for one or more of the following reasons:

1. The NSG on the Application Gateway subnet is blocking inbound access to ports 65503-65534 (v1 SKU) or 65200-65535 (v2 SKU) from **Internet.**

2. The UDR on the Application Gateway subnet is set to the default route (0.0.0.0/0) and the next hop is not specified as **Internet.**

3. The default route is advertised by an ExpressRoute/VPN connection to a virtual network over BGP.

4. The custom DNS server is configured on a virtual network that can't resolve public domain names.

5. Application Gateway is in an Unhealthy state.

For more details on how to verify the above, please [visit this documentation.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-health-status-unknown)

### Customer Solution

*Content type: MarkdownText*

This behavior can occur for one or more of the following reasons:

1. The NSG on the Application Gateway subnet is blocking inbound access to ports 65503-65534 (v1 SKU) or 65200-65535 (v2 SKU) from **Internet.**

2. The UDR on the Application Gateway subnet is set to the default route (0.0.0.0/0) and the next hop is not specified as **Internet.**

3. The default route is advertised by an ExpressRoute/VPN connection to a virtual network over BGP.

4. The custom DNS server is configured on a virtual network that can't resolve public domain names.

5. Application Gateway is in an Unhealthy state.

For more details on how to verify the above, please [visit this documentation.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-health-status-unknown)

---

### Step 11: Unhealthy Backend Server Status

### Content

After you receive an unhealthy backend server status for all the servers in a backend pool, requests aren't forwarded to the servers, and Application Gateway returns a "502 Bad Gateway" error to the requesting client. 

---

### Step 12: Backend Health

### Guidance

By default, Azure Application Gateway probes backend servers to check their health status and to check whether they're ready to serve requests. In each case, if the backend server doesn't respond successfully, Application Gateway marks the server as Unhealthy and stops forwarding requests to the server. After the server starts responding successfully, Application Gateway resumes forwarding the requests.

To check the health of your backend pool, you can use the **Backend Health** page on the Azure portal. Or, you can use [Azure PowerShell](https://learn.microsoft.com/en-us/powershell/module/az.network/get-azapplicationgatewaybackendhealth), [CLI](https://learn.microsoft.com/en-us/cli/azure/network/application-gateway#az-network-application-gateway-show-backend-health), or [REST API](https://learn.microsoft.com/en-us/rest/api/application-gateway/applicationgateways/backendhealth). If your user doesn't have permission to see backend health status, No results. will be shown.

### Question

**What is the Backend Health status shown?**

### Options

- **Healthy** → Go to: *Healthy Backend Server Status*
- **Unhealthy** → Go to: *Unhealthy Backend Server Status*
- **Unknown** → Go to: *Unknown Backend Server Status*

---

### Step 13: Updates to the DNS entries of the backend pool

### Support Engineer Solution

**Cause:** Application Gateway resolves the DNS entries for the backend pool at time of startup and doesn't update them dynamically while running.

**Resolution:** Application Gateway must be restarted after any modification to the backend server DNS entries to begin to use the new IP addresses. This operation can be completed via Azure PowerShell or Azure CLI. To troubleshoot the issue, follow [these steps](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#updates-to-the-dns-entries-of-the-backend-pool).

### Customer Solution

*Content type: MarkdownText*

**Cause:** Application Gateway resolves the DNS entries for the backend pool at time of startup and doesn't update them dynamically while running.

**Resolution:** Application Gateway must be restarted after any modification to the backend server DNS entries to begin to use the new IP addresses. This operation can be completed via Azure PowerShell or Azure CLI. To troubleshoot the issue, follow [these steps](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#updates-to-the-dns-entries-of-the-backend-pool).

---

### Step 14: Common Name does not match

### Support Engineer Solution

**Cause:** (For V2) This occurs when you have selected HTTPS protocol in the backend setting, and neither the Custom Probe’s nor Backend Setting’s hostname (in that order) matches the Common Name (CN) of the backend server’s certificate.

(For V1) The FQDN of the backend pool target doesn’t match the Common Name (CN) of the backend server’s certificate.

**Resolution:** The hostname information is critical for backend HTTPS connection since that value is used to set the Server Name Indication (SNI) during TLS handshake. You can fix this issue by following [these steps](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#common-name-cn-doesnt-match).

### Customer Solution

*Content type: MarkdownText*

**Cause:** (For V2) This occurs when you have selected HTTPS protocol in the backend setting, and neither the Custom Probe’s nor Backend Setting’s hostname (in that order) matches the Common Name (CN) of the backend server’s certificate.

(For V1) The FQDN of the backend pool target doesn’t match the Common Name (CN) of the backend server’s certificate.

**Resolution:** The hostname information is critical for backend HTTPS connection since that value is used to set the Server Name Indication (SNI) during TLS handshake. You can fix this issue by following [these steps](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#common-name-cn-doesnt-match).

---

### Step 15: Backend certificate has expired

### Support Engineer Solution

**Cause:** An expired certificate is deemed unsafe and hence the application gateway marks the backend server with an expired certificate as unhealthy.

**Resolution:** The solution depends on which part of the certificate chain has expired on the backend server. Please follow [these steps](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-certificate-has-expired) to fix the issue.

### Customer Solution

*Content type: MarkdownText*

**Cause:** An expired certificate is deemed unsafe and hence the application gateway marks the backend server with an expired certificate as unhealthy.

**Resolution:** The solution depends on which part of the certificate chain has expired on the backend server. Please follow [these steps](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#backend-certificate-has-expired) to fix the issue.

---

### Step 16: The intermediate certificate was not found

### Support Engineer Solution

**Cause:** The intermediate certificate(s) is not installed in the certificate chain on the backend server.

**Resolution:** An Intermediate certificate is used to sign the Leaf certificate and is thus needed to complete the chain. Check with your Certificate Authority (CA) for the necessary Intermediate certificate(s) and install them on your backend server. This chain must start with the Leaf Certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate. For more details please [visit this documentation.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#the-intermediate-certificate-was-not-found)

### Customer Solution

*Content type: MarkdownText*

**Cause:** The intermediate certificate(s) is not installed in the certificate chain on the backend server.

**Resolution:** An Intermediate certificate is used to sign the Leaf certificate and is thus needed to complete the chain. Check with your Certificate Authority (CA) for the necessary Intermediate certificate(s) and install them on your backend server. This chain must start with the Leaf Certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate. For more details please [visit this documentation.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#the-intermediate-certificate-was-not-found)

---

### Step 17: The leaf or server certificate was not found

### Support Engineer Solution

**Cause:** The Leaf (also known as Domain or Server) certificate is missing from the certificate chain on the backend server.

**Resolution:** You can get the leaf certificate from your Certificate Authority (CA). Install this leaf certificate and all its signing certificates (Intermediate and Root CA certificates) on the backend server. This chain must start with the Leaf Certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate. For reference, look at the certificate chain example under [Leaf must be topmost in chain.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#leaf-must-be-topmost-in-chain)

### Customer Solution

*Content type: MarkdownText*

**Cause:** The Leaf (also known as Domain or Server) certificate is missing from the certificate chain on the backend server.

**Resolution:** You can get the leaf certificate from your Certificate Authority (CA). Install this leaf certificate and all its signing certificates (Intermediate and Root CA certificates) on the backend server. This chain must start with the Leaf Certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate. For reference, look at the certificate chain example under [Leaf must be topmost in chain.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#leaf-must-be-topmost-in-chain)

---

### Step 18: Server certificate is not issued by a publicly known CA

### Support Engineer Solution

**Cause:** You have chosen “well-known CA certificate” in the backend setting, but the Root certificate presented by the backend server is not publicly known.

**Resolution:** When a Leaf certificate is issued by a private Certificate Authority (CA), the signing Root CA’s certificate must be uploaded to the application gateway’s associated Backend Setting. This enables your application gateway to establish a trusted connection with that backend server. To fix this, go to the associated backend setting, choose “not a well-known CA” and upload the Root CA certificate (.CER). To identify and download the root certificate, you can follow the same steps as described under [Trusted root certificate mismatch.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#trusted-root-certificate-mismatch-root-certificate-is-available-on-the-backend-server)

### Customer Solution

*Content type: MarkdownText*

**Cause:** You have chosen “well-known CA certificate” in the backend setting, but the Root certificate presented by the backend server is not publicly known.

**Resolution:** When a Leaf certificate is issued by a private Certificate Authority (CA), the signing Root CA’s certificate must be uploaded to the application gateway’s associated Backend Setting. This enables your application gateway to establish a trusted connection with that backend server. To fix this, go to the associated backend setting, choose “not a well-known CA” and upload the Root CA certificate (.CER). To identify and download the root certificate, you can follow the same steps as described under [Trusted root certificate mismatch.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#trusted-root-certificate-mismatch-root-certificate-is-available-on-the-backend-server)

---

### Step 19: The Intermediate cert is NOT signed by a publicly known CA

### Support Engineer Solution

**Cause:** You have chosen “well-known CA certificate” in the backend setting, but the Intermediate certificate presented by the backend server is not signed by any publicly known CA.

**Resolution:** When a certificate is issued by a private Certificate Authority (CA), the signing Root CA’s certificate must be uploaded to the application gateway’s associated Backend Setting. This enables your application gateway to establish a trusted connection with that backend server. To fix this, contact your private CA to get the appropriate Root CA certificate (.CER) and upload that CER file to the Backend Setting of your application gateway by selecting “not a well-known CA”. We also recommend installing the complete chain on the backend server, including the Root CA certificate, for easy verification.

### Customer Solution

*Content type: MarkdownText*

**Cause:** You have chosen “well-known CA certificate” in the backend setting, but the Intermediate certificate presented by the backend server is not signed by any publicly known CA.

**Resolution:** When a certificate is issued by a private Certificate Authority (CA), the signing Root CA’s certificate must be uploaded to the application gateway’s associated Backend Setting. This enables your application gateway to establish a trusted connection with that backend server. To fix this, contact your private CA to get the appropriate Root CA certificate (.CER) and upload that CER file to the Backend Setting of your application gateway by selecting “not a well-known CA”. We also recommend installing the complete chain on the backend server, including the Root CA certificate, for easy verification.

---

### Step 20: Trusted root certificate mismatch 1

### Support Engineer Solution

**Cause:** None of the Root CA certificates uploaded to the associated Backend Setting have signed the Intermediate certificate installed on the backend server. The backend server has only Leaf and Intermediate certificates installed.

**Resolution:** A Leaf certificate is signed by an Intermediate certificate, which is signed by a Root CA certificate. When using a certificate from Private Certificate Authority (CA), you must upload the corresponding Root CA certificate to the application gateway. Contact your private CA to get the appropriate Root CA certificate (.CER) and upload that CER file to the Backend setting of your application gateway.

### Customer Solution

*Content type: MarkdownText*

**Cause:** None of the Root CA certificates uploaded to the associated Backend Setting have signed the Intermediate certificate installed on the backend server. The backend server has only Leaf and Intermediate certificates installed.

**Resolution:** A Leaf certificate is signed by an Intermediate certificate, which is signed by a Root CA certificate. When using a certificate from Private Certificate Authority (CA), you must upload the corresponding Root CA certificate to the application gateway. Contact your private CA to get the appropriate Root CA certificate (.CER) and upload that CER file to the Backend setting of your application gateway.

---

### Step 21: Trusted root certificate mismatch 2

### Support Engineer Solution

**Cause:** This error occurs when none of the Root certificates uploaded to your application gateway’s backend setting matches the Root certificate present on the backend server.

**Resolution:** This applies to a backend server certificate issued by a Private Certificate Authority (CA) or is a self-signed one. Identify and upload the right Root CA certificate to the associated backend setting.

**Tips:** To identify and download the root certificate, please follow [these steps](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#trusted-root-certificate-mismatch-root-certificate-is-available-on-the-backend-server).

### Customer Solution

*Content type: MarkdownText*

**Cause:** This error occurs when none of the Root certificates uploaded to your application gateway’s backend setting matches the Root certificate present on the backend server.

**Resolution:** This applies to a backend server certificate issued by a Private Certificate Authority (CA) or is a self-signed one. Identify and upload the right Root CA certificate to the associated backend setting.

**Tips:** To identify and download the root certificate, please follow [these steps](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#trusted-root-certificate-mismatch-root-certificate-is-available-on-the-backend-server).

---

### Step 22: Leaf must be topmost in chain

### Support Engineer Solution

**Cause:** The Leaf (also known as Domain or Server) certificate is not installed in the correct order on the backend server.

**Resolution:** The certificate installation on the backend server must include an ordered list of certificates comprising the leaf certificate and all its signing certificates (Intermediate and Root CA certificates). This chain must start with the leaf certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate. For more details please [visit this documentation.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#leaf-must-be-topmost-in-chain)

### Customer Solution

*Content type: MarkdownText*

**Cause:** The Leaf (also known as Domain or Server) certificate is not installed in the correct order on the backend server.

**Resolution:** The certificate installation on the backend server must include an ordered list of certificates comprising the leaf certificate and all its signing certificates (Intermediate and Root CA certificates). This chain must start with the leaf certificate, then the Intermediate certificate(s), and finally, the Root CA certificate. We recommend installing the complete chain on the backend server, including the Root CA certificate. For more details please [visit this documentation.](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#leaf-must-be-topmost-in-chain)

---
