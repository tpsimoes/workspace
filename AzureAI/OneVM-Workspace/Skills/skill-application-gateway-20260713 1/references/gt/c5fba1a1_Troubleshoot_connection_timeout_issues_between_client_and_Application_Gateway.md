# Troubleshoot connection timeout issues between client and Application Gateway

> **Product:** Application Gateway  
> **Solution ID:** c5fba1a1-7163-442e-97cf-a9400b9e7830  
> **Trigger words:** application, application gateway, between, client, connection, connectivity issue, gateway, timeout, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot connection timeout issues between client and Application Gateway** under **Application Gateway**.
 The original guided troubleshooter contains 18 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Connection timeout scoping ⭐ (First Step)

### Guidance

### Check for connection timeout

Check the application gateway URL to confirm whether a connection timeout is occurring for client requests.  

You can verify this from a browser, or run the [telnet](https://learn.microsoft.com/windows-server/administration/windows-commands/telnet) or [psping](https://learn.microsoft.com/sysinternals/downloads/psping) command from the client.

If the browser hangs for a long time and eventually displays one of these error messages:

- This site can’t be reached
- Connection timed out
- ERR_CONNECTION_TIMED_OUT
- The server took too long to respond

This indicates a connection timeout.

### Question

**Check the application gateway URL to determine if there is a connection timeout for client requests. Is there?**

### Options

- **Yes** → Go to: *DNS resolution check*
- **No** → Go to: *SSL error*

---

### Step 2: DNS resolution check

### Guidance

Connection timeouts toward Application Gateway can occur if the DNS server on the client side fails to resolve the application gateway hostname or fully qualified domain name (FQDN).

From your client machine, use [nslookup](https://learn.microsoft.com/windows-server/administration/windows-commands/nslookup) to see if the DNS resolution is successful or not.

**Step 1: Open Command Prompt or Terminal.**

Press **Win+R**, type **cmd**, and press **Enter**.

**Step 2: Use the `nslookup` command.**

Run the following command, replacing *api.contoso.com* with your domain name:

```

nslookup api.contoso.com

```

**Expected result:**

If successful: shows DNS server and resolved IP address.

If failed: shows an error like "Non-existent domain" or "Server can't find."

**Step 3: If successful, compare the resolved IP address with the frontend IP address of the application gateway to confirm they match.**

### Question

**Does the Application Gateway hostname resolve from the client machine and does the resolved IP address belong to the Application Gateway frontend IP?**

### Options

- **Yes** → Go to: *Listener configuration*
- **No** → Go to: *DNS resolution error*

---

### Step 3: Listener configuration

### Content

An application gateway listener is a logical entity that checks for incoming connection requests by using the port, protocol, IP address, and/or hostname. The listener must be configured with values that match the corresponding values in the incoming request on the application gateway.

---

### Step 4: NSG configuration

### Guidance

Check if a network security group (NSG) is attached to your application gateway subnet. If there is, check all the inbound security rules to identify if any rule is blocking the client request.

### Steps to review the NSG rules from the Azure portal

1. **Identify the subnet and NSG**.
   - Go to the **Overview page** of your application gateway.
   - Select **Virtual network/subnet**.
   - Go to the **Subnets** tab and locate the **subnet** used by the application gateway.
   - Check if an NSG is associated with that subnet.

2. **Review NSG rules**.
   - Open the NSG linked to the subnet.
   - Review **Inbound** rules:
     - Make sure you have a rule allowing incoming traffic from the expected clients. The **Destination** must be set as the application gateway's **entire subnet IP prefix** or **Any**. The **destination ports** must match listener rules.

  

    | Source         | Source ports | Destination         | Destination ports | Protocol | Access |
    |----------------|--------------|---------------------|-------------------|----------|--------|
    | as per need  | Any          | Subnet IP prefix  | listener ports  | TCP      | Allow  |

   - If you have any **Deny All** rules or any overlapping **Deny** rules, make sure the allow rule has higher priority.

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

| Source           | Source ports        | Destination                | Destination ports   | Protocol   | Access   |

|:----------------:|:-------------------:|:--------------------------:|:-------------------:|:----------:|:--------:|

| as per need      | Any                 | Subnet IP Prefix           | listener ports      | TCP        | Allow    |

  If you have any **Deny All** rules or any overlapping **Deny** rules, make sure the allow rule is having higher priority.

See [Required security rules](https://learn.microsoft.com/en-us/azure/application-gateway/configuration-infrastructure#required-security-rules)

### Customer Solution

*Content type: MarkdownText*

You must allow incoming traffic from the expected clients (as source IP or IP range), and for the destination as your application gateway's entire subnet IP prefix and inbound access ports. 

For example, if you have listeners configured for ports 80 and 443, you must allow these ports. You can also set this to **Any**.  

| Source           | Source ports        | Destination                | Destination ports   | Protocol   | Access   |

|:----------------:|:-------------------:|:--------------------------:|:-------------------:|:----------:|:--------:|

| as per need      | Any                 | Subnet IP Prefix           | listener ports      | TCP        | Allow    |

  If you have any **Deny All** rules or any overlapping **Deny** rules, make sure the allow rule has higher priority.

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
- **No** → Go to: *Contact support*

---

### Step 7: Listener rule association

### Guidance

Check the **Associated Rule** option for the specific listener in the **Listeners** section of your application gateway. 

Steps:
1. From the Azure portal, navigate to your application gateway.
2. Under the **Settings** section, select **Listeners**.
3. You'll then see a table listing all configured listeners. Check the **Associated Rule** column.
    - If a listener is linked to a rule, the name of the rule will appear in this column.
    - If the column shows a dash (**–**), it means the listener is not associated with any rule.

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

If the client machine can't resolve the application gateway hostname, verify whether other client machines can resolve this hostname.  

- If other clients can resolve the hostname, it may be a problem specific to the client in question. In this case, work with your internet service provider (ISP) to diagnose and resolve the issue further.  

- If other client machines also can't resolve the hostname, ensure that the DNS record, which points to the application gateway's frontend IP or the Azure-provided DNS name, is correctly configured at your DNS provider's end.

In addition, if the resolved IP address does not belong to the application gateway, check if it belongs to any proxy or gateway device. 

---

### Step 9: Incorrect listener configuration

### Support Engineer Solution

If there is no listener configured on the Application Gateway with frontend IP and port combination which the client is trying to connect to, the Application Gateway will not respond to that request.  

Ensure that you have configured a basic/multi-site Listener for intended frontend IP and HTTP(s) port. You can refer to the following document for guidance on Listener configuration: [Application Gateway Listeners](https://learn.microsoft.com/azure/application-gateway/configuration-listeners).

### Customer Solution

*Content type: MarkdownText*

If there is no listener configured on the application gateway with the frontend IP and port combination that the client is trying to connect to, the application gateway will not respond to that request.  

Ensure that you've configured a basic/multi-site listener for the intended frontend IP and HTTP(S) port. See [Application Gateway listener configuration](https://learn.microsoft.com/azure/application-gateway/configuration-listeners) for details.

---

### Step 10: No rule present

### Support Engineer Solution

Without an associated rule, the listener cannot process incoming traffic. This means it will not function as intended and will not route requests to backend resources.

To enable the listener to function properly, you need to:

1. Create a request routing rule in your Application Gateway.

2. Associate the rule with the existing listener.

Steps to follow:

1. Go to your Application Gateway in the Azure portal.

2. Select **“Rules”** from the left-hand menu.

3. Click “**+ Routing rule”** to create a new request routing rule.

4. In the rule configuration:

    - Provide a name for the rule.

    - Define the rule priority.

    - Select the existing listener you want to associate.

    - Go to the Backend targets tab, Choose or create a backend pool and Backend settings.

5. Click “Add” to finalize the rule.

More details regarding request routing rules can be round at: https://learn.microsoft.com/en-us/azure/application-gateway/configuration-request-routing-rules. 

### Customer Solution

*Content type: MarkdownText*

Without an associated rule, the listener can't process incoming traffic. This means it will not function as intended and will not route requests to backend resources.

To enable the listener to function properly, you need to:

1. Create a request routing rule in your application gateway.

2. Associate the rule with the existing listener.

Steps to follow:

1. Go to your application gateway in the Azure portal.

2. Select **Rules** from the left-hand menu.

3. Select **Routing rule** to create a new request routing rule.

4. In the rule configuration:

   - Provide a name for the rule.

   - Define the rule priority.

   - Select the existing listener you want to associate.

   - Go to the **Backend targets** tab, choose or create a backend pool and backend settings.

5. Select **Add** to finalize the rule.

For details, see [Application Gateway request routing rules](https://learn.microsoft.com/azure/application-gateway/configuration-request-routing-rules). 

---

### Step 11: Check asymmetric routing

### Content

An incorrect configuration of the user-defined route in the route table could result in asymmetrical routing in Application Gateway.

Check if there is a user-defined route present on the Application Gateway subnet that's pointing client traffic to an Azure firewall or a virtual appliance, or if [forced tunneling](https://learn.microsoft.com/azure/application-gateway/configuration-infrastructure#supported-user-defined-routes) is happening.

See [User-defined routes](https://learn.microsoft.com/azure/virtual-network/virtual-networks-udr-overview#user-defined).

---

### Step 12: Asymmetric routing issue

### Support Engineer Solution

For user-defined routes(UDRs), any scenario where 0.0.0.0/0 needs to be redirected through any virtual appliance, a hub/spoke virtual network, or on-premises (forced tunneling) **isn't supported** for application gateway V2.  
- If your route table attached to the Application Gateway subnet includes a UDR for 0.0.0.0/0 pointing to a virtual appliance, please **remove this route** to avoid traffic disruption.
- If you have any force tunneling routes for 0.0.0.0/0 from VPN/Expressroute configurations, there're 2 options to resolve the issue.

  - Option 1: Configure a UDR for 0.0.0.0/0 with **next hop set to Internet**. This route will take precedence over BGP-learned forced tunneling routes due to UDR priority.
  - Option 2: Turn off BGP route propagation on the route table associated with the Application Gateway subnet.
    Note: This will prevent the Application Gateway from learning any routes from on-premises networks via VPN or ExpressRoute.
    Steps to do this:
      - From the  Azure portal, go to the route table assoicated to the application gateway.
      - Under Settings, click **Configuration**.
      - Toggle Propagate gateway routes to **No**.
      - Click **Save**.

  

For the v1 SKU, user-defined routes (UDRs) are supported on the Application Gateway subnet, as long as they don't alter end-to-end request/response communication. For example, you can set up a UDR in the Application Gateway subnet to point to a firewall appliance for packet inspection. But you must make sure that the packet can reach its intended destination after inspection. Failure to do so might result in incorrect traffic-routing behavior. 

### Customer Solution

*Content type: MarkdownText*

For user-defined routes (UDRs), any scenario where 0.0.0.0/0 needs to be redirected through any virtual appliance, a hub/spoke virtual network, or on-premises (forced tunneling) is *not* supported for Application Gateway v2.  

- If your route table attached to the Application Gateway subnet includes a UDR for 0.0.0.0/0 pointing to a virtual appliance, **remove this route** to prevent traffic disruption.

- If you have any forced-tunneling routes for 0.0.0.0/0 from VPN/ExpressRoute configurations, there are two options to resolve the issue:

  - Option 1: Configure a UDR for 0.0.0.0/0 with next hop set to **internet**. This route will take precedence over BGP-learned forced-tunneling routes due to UDR priority.

  - Option 2: Turn off BGP route propagation on the route table associated with the Application Gateway subnet.

    Note: This will prevent the application gateway from learning any routes from on-premises networks via VPN or ExpressRoute.

    Steps to do this:

    - From the  Azure portal, go to the route table associated to the application gateway.

    - Under **Settings**, select **Configuration**.

    - Toggle **Propagate gateway routes** to **No**.

    - Select **Save**.

  

For the v1 SKU, user-defined routes (UDRs) are s

*(Content truncated — refer to original GT for full details)*

### Step 13: Check performance

### Guidance

If your application gateway is experiencing high traffic or performance degradation, it may result in connection timeout errors for some requests. To assess the current status and identify potential causes, you can review key metrics available in the Azure portal.

Steps to follow:

1. From the Azure portal, navigate to your application gateway.

2. Under the **Monitoring** section, select **Metrics**.

From the Metrics page, review the following based on your gateway version:

**For Application Gateway V1**

- CPU utilization

  - If CPU usage exceeds 80%, the gateway may be under strain, potentially leading to performance issues.

**For Application Gateway V2**

- Current compute units

  - A spike in compute units may indicate high CPU utilization.

    

- Current capacity units

  - A spike here suggests the gateway is handling a high volume of traffic.

**Additional metrics to review**

 - Application Gateway total time

   This metric includes:

   - Gateway processing time

   - Backend server response time

   - Network latency

   A spike in total time does not necessarily indicate a gateway issue. To gain a complete picture, also review:

   - Client RTT

   - Backend connect time

   - Backend first byte response time

   - Backend last byte response time

For detailed explanations of each metric, see [Metrics for Application Gateway](https://learn.microsoft.com/azure/application-gateway/application-gateway-metrics).

### Question

**Is the application gateway experiencing a performance issue?**

### Options

- **Yes** → Go to: *Performance issue*
- **No** → Go to: *Contact support*

---

### Step 14: Performance issue

### Support Engineer Solution

If your Azure Application Gateway is experiencing performance degradation or high traffic, follow these steps to mitigate the issue and maintain service quality.

For V1 SKU:

- If CPU utilization exceeds 80%, increase the instance count.

- V1 supports up to 32 instances.

- Add a buffer of 10–20% above peak usage to handle traffic spikes.

For V2 SKU:

- Autoscaling:

  

  - Scaling takes 3–5 minutes to provision new instances.

  - During short traffic spikes, existing instances may be stressed, causing latency or dropped requests.

  - Set maximum instance count to 125 to allow full autoscaling flexibility. You are billed only for the actual capacity units used.

  - Compute unit metric is a representation of your gateway's CPU utilization and based on your peak usage divided by 10, you can set the minimum number of instances required. 

- Manual Scaling: 

  - Increase instance count if performance issues are observed.

  - Compute unit metric is a representation of your gateway's CPU utilization and based on your peak usage divided by 10, you can set the number of instances required, since 1 application gateway instance can handle a minimum of 10 compute units

See [High traffic support](https://learn.microsoft.com/azure/application-gateway/high-traffic-support).

### Customer Solution

*Content type: MarkdownText*

If your Azure Application Gateway is experiencing performance degradation or high traffic, follow these steps to mitigate the issue and maintain service quality.

**For V1 SKU:**

- If CPU utilization exceeds 80%, increase the instance count.

- V1 supports up to 32 instances.

- Add a buffer of 10–20% above peak usage to handle traffic spikes.

**For V2 SKU:**

- Autoscaling:

  - Scaling takes 3–5 minutes to provision new instances.

  - During short traffic spikes, existing instances may be stressed, causing latency or dropped requests.

  - Set maximum instance count to 125 to allow full autoscaling flexibility. You're billed only for the actual capacity units used.

  - Compute unit metric is a representation of your gateway's CPU utilization and based on your peak usage divided by 10, you can set the minimum number of instances required. 

- Manual scaling: 

  - Increase instance count if performance issues are observed.

  - The compute unit metric is a representation of your gateway's CPU utilization and based on your peak usage divided by 10; you can set the number of instances required, since one application gateway instance can handle a minimum of 10 compute units

See [Application Gateway high traffic support](https://learn.microsoft.com/azure/application-gateway/high-traffic-support).

---

### Step 15: Contact support

### Support Engineer Solution

## Still need help?

If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/en-gb/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

### Still need help?

If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure portal support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

---

### Step 16: Check SSL configuration

### Guidance

### Determine the SSL/TLS version

To determine the SSL/TLS version of your client, check your browser’s settings or use the OpenSSL command. 

**Browser settings**

In the browser’s settings, look for the **Security** or **Advanced** settings and find the encryption section. The TLS version should be listed there. If it isn't listed, your browser may not support TLS.

**OpenSSL**

Enter the following command into a terminal window:

```

openssl s_client -connect [hostname]:[port]

```

### Configure your gateway

Configure your gateway with any predefined security policies, or create a custom policy that suits your organizational security requirements.

### Question

**Do the SSL/TLS policies and cipher suite configurations meet client requirements?**

### Options

- **Yes** → Go to: *Contact support*
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

**Custom policy issue**

If you're using a custom policy and choose a protocol version or a cipher suite that is not compatible with your listener certificates or your backend server certificates, you might get an error or a weak encryption. 

To fix this, you can either change your custom policy to match your certificates or change your certificates to match your custom policy.

**Predefined policy issue**

If you're using a predefined policy, some predefined policies might not support certain types of certificates, such as ECDSA or self-signed certificates. 

   

To fix this, you can either change your predefined policy to one that supports your certificates or change your certificates to ones that are supported by your predefined policy.  

   

For additional guidance, see [Configure TLS policy versions and cipher suites on Application Gateway](https://learn.microsoft.com/azure/application-gateway/application-gateway-configure-ssl-policy-powershell).

---

### Step 18: IP specified is invalid

### Support Engineer Solution

The IP specified is invalid, this application gateway is not configured with the type of frontend IP selected.

Re-run this solution with the correct values or if this is not expected, review your current configuration to ensure you have a listener configured with the right frontend IP configuration desired.

### Customer Solution

*Content type: MarkdownText*

The IP specified is invalid; this application gateway is not configured with the type of frontend IP selected.

Rerun this solution with the correct values, or if this is not expected, review your current configuration to ensure that you have a listener configured with the correct frontend IP configuration desired.

---
