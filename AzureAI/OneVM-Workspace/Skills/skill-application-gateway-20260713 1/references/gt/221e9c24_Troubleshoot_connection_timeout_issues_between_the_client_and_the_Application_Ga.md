# Troubleshoot connection timeout issues between the client and the Application Gateway

> **Product:** Azure Networking (General)  
> **Solution ID:** 221e9c24-a648-4210-9988-a1d6d029d5fb  
> **Trigger words:** application, azure networking (general), between, client, connection, connectivity issue, gateway, timeout, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot connection timeout issues between the client and the Application Gateway** under **Azure Networking (General)**.
 The original guided troubleshooter contains 18 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Connection timeout scoping ⭐ (First Step)

### Guidance

Check the Application Gateway URL to confirm whether a connection timeout is occurring for client requests.  

You can verify this from a browser, or run the [telnet](https://learn.microsoft.com/windows-server/administration/windows-commands/telnet) or [psping](https://learn.microsoft.com/sysinternals/downloads/psping) command from the client.

### Question

**Check the Application Gateway URL to determine if there is a connection timeout for client requests. Is there?**

### Options

- **Yes** → Go to: *DNS resolution check*
- **No** → Go to: *SSL error*

---

### Step 2: DNS resolution check

### Guidance

Connection timeouts toward Application Gateway can be experienced if the DNS server on the client side fails to resolve the Application Gateway hostname or FQDN.

From your client machine, use [nslookup](https://learn.microsoft.com/windows-server/administration/windows-commands/nslookup) to see if the DNS resolution is successful or not.

### Question

**Does the Application Gateway hostname resolve from the client machine and does the resolved IP address belong to the Application Gateway frontend IP?**

### Options

- **Yes** → Go to: *Listener configuration*
- **No** → Go to: *DNS resolution error*

---

### Step 3: Listener configuration

### Content

Application Gateway Listener is a logical entity that checks for incoming connection requests by using the port, protocol, IP address, and/or hostname. The listener must be configured with values that match the corresponding values in the incoming request on the application gateway.

---

### Step 4: NSG configuration

### Guidance

Check if a network security group is attached to your Application Gateway subnet. If there is, check all the inbound security rules to identify if any rule is blocking the client request.

### Question

**Is an inbound rule in the network security group blocking the client request?**

### Options

- **Yes** → Go to: *NSG causing connection timeout*
- **No** → Go to: *Listener rule association*

---

### Step 5: NSG causing connection timeout

### Support Engineer Solution

You must allow incoming traffic from the expected clients (as source IP or IP range), and for the destination as your application gateway's entire subnet IP prefix and inbound access ports. 

For example, if you have listeners configured for ports 80 & 443, you must allow these ports. You can also set this to **Any**.  

See [Required security rules](https://learn.microsoft.com/en-us/azure/application-gateway/configuration-infrastructure#required-security-rules)

### Customer Solution

*Content type: MarkdownText*

You must allow incoming traffic from the expected clients (as source IP or IP range) and for the destination as your application gateway's entire subnet IP prefix and inbound access ports. 

For example, if you have listeners configured for ports 80 and 443, you must allow these ports. You can also set this to *Any*.  

See [Required security rules](https://learn.microsoft.com/azure/application-gateway/configuration-infrastructure#required-security-rules).

---

### Step 6: SSL error

### Guidance

SSL connection errors will prevent you from browsing a website securely over Hypertext Transfer Protocol Secure (HTTPS). Your browser may allow you to proceed with the connection, but in most cases, it’ll tell you that you’re doing so at your own risk.  

You can run the following openssl command in a terminal window to check for SSL errors:

```

openssl s_client -connect [hostname]:[port]

```

### Question

**Are you experiencing an error related to SSL/TLS?**

### Options

- **Yes** → Go to: *Check SSL configuration*
- **No** → Go to: *Contact Support*

---

### Step 7: Listener rule association

### Guidance

Check the **Associated Rule** option for the specific listener in the **Listeners** section of your application gateway. 

### Question

**Is the listener associated with a routing rule?**

### Options

- **Yes** → Go to: *Check asymmetric routing*
- **No** → Go to: *No rule present*

---

### Step 8: DNS resolution error

### Support Engineer Solution

If the client machine cannot resolve the Application Gateway hostname, we suggest verifying if other client machines are capable of resolving this hostname.  

If other clients can resolve the hostname, it may be a problem specific to the client in question. In this case, we recommend collaborating with your Internet Service Provider (ISP) to diagnose and resolve the issue further.  

If other client machines also cannot resolve the hostname, ensure that the DNS record, which points to the Application Gateway's frontend IP or the Azure-provided DNS name, is correctly configured at your DNS provider's end.

Additionally, if the resolved IP address does not belong to Application Gateway, check if it belongs to any proxy or gateway device. 

### Customer Solution

*Content type: MarkdownText*

### Determine if other client machines resolve hostname

If the client machine can't resolve the Application Gateway hostname, verify whether other client machines can resolve this hostname.  

- If other clients can resolve the hostname, it may be a problem specific to the client in question. In this case, work with your internet service provider (ISP) to diagnose and resolve the issue further.  

- If other client machines also can't resolve the hostname, ensure that the DNS record, which points to the Application Gateway's frontend IP or the Azure-provided DNS name, is correctly configured at your DNS provider's end.

In addition, if the resolved IP address does not belong to Application Gateway, check if it belongs to any proxy or gateway device. 

---

### Step 9: Incorrect listener configuration

### Support Engineer Solution

If there is no listener configured on the Application Gateway with frontend IP and port combination which the client is trying to connect to, the Application Gateway will not respond to that request.  

Ensure that you have configured a basic/multi-site Listener for intended frontend IP and HTTP(s) port. You can refer to the following document for guidance on Listener configuration: [Application Gateway Listeners](https://learn.microsoft.com/azure/application-gateway/configuration-listeners).

### Customer Solution

*Content type: MarkdownText*

If there is no listener configured on the application gateway with the frontend IP and port combination that the client is trying to connect to, the application gateway will not respond to that request.  

Ensure that you've configured a basic/multi-site listener for the intended frontend IP and HTTP(S) port. See [Application Gateway listener configuration](https://learn.microsoft.com/en-us/azure/application-gateway/configuration-listeners) for details.

---

### Step 10: No rule present

### Support Engineer Solution

Ensure that the Listener is associated with a Request Routing rule for backend connectivity to be successful. See [Application Gateway Request Routing rules](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-components#request-routing-rules).

### Customer Solution

*Content type: MarkdownText*

Ensure that the listener is associated with a request routing rule for backend connectivity to be successful. See [Request routing rules](https://learn.microsoft.com/azure/application-gateway/application-gateway-components#request-routing-rules).

---

### Step 11: Check asymmetric routing

### Content

An incorrect configuration of the user-defined route in the route table could result in asymmetrical routing in Application Gateway.

Check if there is a user-defined route present on the Application Gateway subnet that's pointing client traffic to an Azure firewall or a virtual appliance, or if [forced tunneling](https://learn.microsoft.com/azure/application-gateway/configuration-infrastructure#supported-user-defined-routes) is happening.

See [User-defined routes](https://learn.microsoft.com/azure/virtual-network/virtual-networks-udr-overview#user-defined).

---

### Step 12: Asymmetric routing issue

### Support Engineer Solution

Any scenario where 0.0.0.0/0 needs to be redirected through any virtual appliance, a hub/spoke virtual network, or on-premises (forced tunneling) isn't supported for V2.  

For the v1 SKU, user-defined routes (UDRs) are supported on the Application Gateway subnet, as long as they don't alter end-to-end request/response communication. For example, you can set up a UDR in the Application Gateway subnet to point to a firewall appliance for packet inspection. But you must make sure that the packet can reach its intended destination after inspection. Failure to do so might result in incorrect traffic-routing behavior. 

### Customer Solution

*Content type: MarkdownText*

Any scenario where 0.0.0.0/0 needs to be redirected through a virtual appliance, a hub/spoke virtual network, or on-premises (forced tunneling) isn't supported for v2.  

For the v1 SKU, user-defined routes (UDR) are supported on the Application Gateway subnet, as long as they don't alter end-to-end request/response communication. For example, you can set up a UDR in the Application Gateway subnet to point to a firewall appliance for packet inspection, but you must make sure that the packet can reach its intended destination after inspection. Failure to do so might result in incorrect traffic-routing behavior. 

---

### Step 13: Check performance

### Guidance

Go to **Monitoring** > **Metrics** to monitor the performance of your application gateway.  

See [Metrics for Application Gateway](https://learn.microsoft.com/azure/application-gateway/application-gateway-metrics).

### Question

**Is the application gateway experiencing a performance issue?**

### Options

- **Yes** → Go to: *Performance issue*
- **No** → Go to: *Contact Support*

---

### Step 14: Performance issue

### Support Engineer Solution

If your Application Gateway is undergoing performance issue or high traffic, you can consider increasing your instance count for V1 or minimum and maximum instance count for V2 to mitigate ongoing issue.  

You can also refer to this document for more information [High traffic support](https://learn.microsoft.com/azure/application-gateway/high-traffic-support).

### Customer Solution

*Content type: MarkdownText*

If your application gateway is experiencing performance issues or high traffic, consider increasing your instance count for v1, or the minimum and maximum instance count for v2.  

See [High traffic support](https://learn.microsoft.com/azure/application-gateway/high-traffic-support).

---

### Step 15: Contact Support

### Support Engineer Solution

## Still need help?

If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/en-gb/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

## Still need help?

If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/en-gb/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

---

### Step 16: Check SSL configuration

### Guidance

### Determine the SSL/TLS version

To determine the SSL/TLS version of your client, check your browser’s settings or use the OpenSSL command. 

#### Browser settings

In the browser’s settings, look for the **Security** or **Advanced** settings and find the encryption section. The TLS version should be listed there. If it isn't listed, your browser may not support TLS.

#### OpenSSL

Enter the following command in a terminal window:

```

openssl s_client -connect [hostname]:[port]

```

### Configure your gateway

Configure your gateway with any predefined security policies or create a custom policy that’s suited to your organizational security requirements.

### Question

**Do the SSL/TLS policies and cipher suite configurations meet client requirements?**

### Options

- **Yes** → Go to: *Contact Support*
- **No** → Go to: *Incorrect SSL configuration*

---

### Step 17: Incorrect SSL configuration

### Support Engineer Solution

Here are some common reasons for incorrect TLS policy errors on your Application Gateway:

* Using custom policy and choose a protocol version or a cipher suite that is not compatible with your listener certificates or your backend server certificates. To fix this, either change your custom policy to match your certificates, or change your certificates to match your custom policy.

* Some predefined policies might not support certain types of certificates, such as ECDSA certificates or self-signed certificates. To fix this, either change your predefined policy to one that supports your certificates, or change your certificates to ones that are supported by your predefined policy.  

See [Configure TLS policy versions and cipher suites on Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-configure-ssl-policy-powershell).

### Customer Solution

*Content type: MarkdownText*

### Common reasons for incorrect TLS policy errors

There are several possible reasons for receiving an incorrect TLS policy error on your application gateway. Here are some common scenarios and their solutions.

#### Custom policy issue

If you're using a custom policy and choose a protocol version or a cipher suite that is not compatible with your listener certificates or your backend server certificates, you might get an error or a weak encryption. 

To fix this, you can either change your custom policy to match your certificates or change your certificates to match your custom policy.

#### Predefined policy issue

If you're using a predefined policy, some predefined policies might not support certain types of certificates, such as ECDSA or self-signed certificates. 

   

To fix this, you can either change your predefined policy to one that supports your certificates or change your certificates to ones that are supported by your predefined policy.  

   

For additional guidance, see [Configure TLS policy versions and cipher suites on Application Gateway](https://learn.microsoft.com/azure/application-gateway/application-gateway-configure-ssl-policy-powershell).

---

### Step 18: IP Specified is invalid

### Support Engineer Solution

The IP specified is invalid, this application gateway is not configured with the type of frontend IP selected.

Re-run this solution with the correct values or if this is not expected, review your current configuration to ensure you have a listener configured with the right frontend IP configuration desired.

### Customer Solution

*Content type: MarkdownText*

The IP specified is invalid, this application gateway is not configured with the type of frontend IP selected.

Re-run this solution with the correct values or if this is not expected, review your current configuration to ensure you have a listener configured with the right frontend IP configuration desired.

---
