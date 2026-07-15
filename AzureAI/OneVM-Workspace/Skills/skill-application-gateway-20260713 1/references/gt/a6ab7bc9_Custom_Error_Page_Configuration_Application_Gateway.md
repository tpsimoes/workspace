# Custom Error Page Configuration (Application Gateway)

> **Product:** Application Gateway  
> **Solution ID:** a6ab7bc9-28b9-4154-9caf-26f9ad2f2d88  
> **Trigger words:** (application, application gateway, configuration, configure, custom, error, gateway)

---

## Overview

This guide provides step-by-step troubleshooting for **Custom Error Page Configuration (Application Gateway)** under **Application Gateway**.
 The original guided troubleshooter contains 11 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Origins of Custom Error Page ⭐ (First Step)

### Guidance

To check whether custom error page is originated from listener or backend, you can utilize below 2 methods :

  - ReqRespLog (Check jarvis log internally)

  - Application Gateway Access Log (Check log analytics workspace in azure portal with customer)

### Question

**Where is the custom error page originated from?**

### Options

- **Application Gateway (Listener)** → Go to: *Custom Error Page from AppGW Listener*
- **Backend Server** → Go to: *Custom error page from backend is in customer management*

---

### Step 2: Custom error page from backend is in customer management

### Support Engineer Solution

If  custom error page is originated from backend server, it is within the scope of customer management.

### Customer Solution

*Content type: MarkdownText*

If  custom error page is originated from backend server, it is within the scope of customer management.

---

### Step 3: Custom Error Page from AppGW Listener

### Guidance

Firstly, check dns server configuration of Application Gateway's VNET.

If VNET is configured with Azure Provided DNS, VNET link connectivity with private DNS zone (that is matched with custom error page domain) should not be configured, since the custom error page domain should be publicly resolved.

If VNET is configured with Custom DNS Server, it should be configured with public DNS resolution for custom error page domain.  

For reference, Application Gateway’s DNS resolution for custom error page domain can be verified with nslookup command at test VM that is installed in the same VNET of Application Gateway.

### Question

**Is there any DNS resolution issue from Application Gateway? (for custom error page domain)**

### Options

- **No** → Go to: *Network connectivity from AppGW to custom error page*
- **Yes** → Go to: *DNS Resolution from Application Gateway*

---

### Step 4: DNS Resolution from Application Gateway

### Support Engineer Solution

If the DNS configuration of the VNET is Azure-Provided DNS : 

 - Make sure the custom error page domain can be publicly resolved via DNS or not. 

 - So, there should be NO private DNS zone (that is matched with custom error page domain) linked with VNET.  

If the DNS configuration of the VNET is Custom DNS Server : 

 - Check whether public DNS resolution works properly on the custom DNS server, for custom error page domain.

For reference, Application Gateway’s DNS resolution for the custom error page domain can be verified with nslookup command at test VM installed in the same VNET.

### Customer Solution

*Content type: MarkdownText*

If the DNS configuration of the VNET is Azure-Provided DNS : 

 - Make sure the custom error page domain can be publicly resolved via DNS or not.

 - So, there should be NO private DNS zone (that is matched with custom error page domain) linked with VNET.  

If the DNS configuration of the VNET is Custom DNS Server : 

 - Check whether public DNS resolution works properly on the custom DNS server, for custom error page domain.

For reference, Application Gateway’s DNS resolution for the custom error page domain can be verified with nslookup command at test VM installed in the same VNET.

---

### Step 5: Network connectivity from AppGW to custom error page

### Guidance

To check network connectivity from Application Gateway to custom error page's hosting server, please check NSG, UDR, Firewall, VirtualHub etc, which are associated with Application Gateway.

### Question

**Is there any network connectivity issue from Application Gateway to custom error page's hosting server?**

### Options

- **No** → Go to: *Firewall Settings at Custom Error Page Hosting Server*
- **Yes** → Go to: *Check network connectivity with NSG UDR Firewall VirtualHub*

---

### Step 6: Check network connectivity with NSG UDR Firewall VirtualHub

### Support Engineer Solution

Check network connectivity with NSG, UDR, Firewall, VirtualHub etc, from Application Gateway to custom error page's hosting server.

 - NSG : Check outbound connectivity's allow rule
 - UDR : Check whether outbound connectivity to custom error page domain is routed via Firewall/NVA
 - Firewall/NVA : Check allow rule from Application Gateway to custom error page's hosting server
 - VirtualHub : Check whether Application Gateway's VNET is connected with VirtualHub or not, since effective route can be routed to VirtualHub

In case of UDR of Application Gateway V2 (excluding Private Only Application Gateway V2), 0.0.0.0/0 should be reached directly to Internet (not via FW//NVA),
since Application Gateway V2 can be operated only via direct connectivity to Internet. For reference, please refer to below document.

https://learn.microsoft.com/en-us/azure/application-gateway/configuration-infrastructure#v2-unsupported-scenarios 

For more information, please refer to below documents.
 - NSG for Application Gateway V2 : https://learn.microsoft.com/en-us/azure/application-gateway/configuration-infrastructure#network-security-groups
 - UDR for Application Gateway V2 : https://learn.microsoft.com/en-us/azure/application-gateway/configuration-infrastructure#supported-user-defined-routes

※ In case of Private Only Application Gateway V2, it has "Management Public IP (Implicit Public IP)" which is different from Public Application Gateway V2 that uses "Customer Public IP (Explicit Public IP)". So the Private Only Application Gateway V2 can fetch external custom error page with "Management Public IP (Implicit)". So we don't need to configure NAT Gateway or UDR(0.0.0.0/0 via FW/NVA) with Private Only Application Gateway V2.

※ However, to reach backend servers or key vault via Internet (if backend servers or key vault can only be accessed publicly), we need to configure NAT Gateway or UDR(0.0.0.0/0 via FW/NVA) with Private Only Application Gateway V2. 

※ For more reference, please refer to below official document. (It covers connectivity to public backend server and public key vault from Private Only Application Gateway V2, excluding public customer error page fetching scenario)

Outbound Internet connectivity from Private Only Application Gateway V2 : 

https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-private-deployment?tabs=portal#outbound-internet-connectivity

### Customer Solution

*Content type: MarkdownText*

Check network connectivity with NSG, UDR, Firewall, VirtualHub etc, from Application Gateway to custom error page's hosting server.

 - NSG : Check outbound connectivity's allow rule
 - UDR : Check whether outbound connectivity to custom error page domain is routed via Firewall/NVA
 - Firewall/NVA : Check allow rule from Application Gateway to custom error page's hosting server
 - VirtualHub : Check whether Application Gateway's VNET is connected with VirtualHub or not, since effective rout

*(Content truncated — refer to original GT for full details)*

### Step 7: Firewall Settings at Custom Error Page Hosting Server

### Guidance

If custom error page is hosted at VM : 

 - Check whether NSG allows application gateway's frontend IP or not

 - Check whether VM's guest OS firewall allows application gateway's frontend IP or not

If custom error page is hosted at Storage Account : 

 - Check networking menu at Storage Account, whether application gateway's frontend IP is allowed or not

### Question

**Did you check whether the firewall settings on the custom error page's hosting server allows the frontend IP of the Application Gateway?**

### Options

- **Allowed** → Go to: *Publicly Accessible Custom Error Page Domain*
- **Not Allowed** → Go to: *Allow Frontend IP of Application Gateway at Firewall*

---

### Step 8: Allow Frontend IP of Application Gateway at Firewall

### Support Engineer Solution

If custom error page is hosted at VM : 

 - Check whether NSG allows Application Gateway's frontend IP or not

 - Check whether VM's guest OS firewall allows Application Gateway's frontend IP or not

If custom error page is hosted at Storage Account : 

 - Check networking menu at Storage Account, whether it allows Application Gateway's frontend IP or not

※ In case of Private Only Application Gateway V2, Custom Error Page Hosting Server should allow Management Public IP that is used for fetching custom error page. To check the Management Public IP of Private Only Application Gateway V2, we can utilize below two methods : 

 - ASC -> Private AppGW V2 Resource -> Find "Raw Gateway Manager Config" -> Click "SAS URL" -> Find "ManagementPublicIp"

 - ASI -> Input Private Only AppGW V2 Resource Id -> Find "Management Public IP"

 - ASI Link Sample : 

 https://asi.azure.ms/services/ACE%20Network%20Tools/pages/Application%20Gateway?ResourceUri=%2Fsubscriptions%2F46628245-f946-4620-97e4-7ff843a66927%2FresourceGroups%2Frg%2Fproviders%2FMicrosoft.Network%2FapplicationGateways%2Fappgw-private-only

※ However, it's recommended to communicate with customer mentioning that Custom Error Page Hosting Server should be publicly opened so that Private Only Application Gateway V2 can fetch custom error page successfully.

### Customer Solution

*Content type: MarkdownText*

If custom error page is hosted at VM : 

 - Check whether NSG allows Application Gateway's frontend IP or not

 - Check whether VM's guest OS firewall allows Application Gateway's frontend IP or not

If custom error page is hosted at Storage Account : 

 - Check networking menu at Storage Account, whether it allows Application Gateway's frontend IP or not

※ In case of Private Only Application Gateway V2, Custom Error Page Hosting Server should be publicly opened so that Private Only Application Gateway V2 can fetch custom error page successfully.

---

### Step 9: Publicly Accessible Custom Error Page Domain

### Guidance

Check whether custom error page's hosting server can be accessed publicly.

Check whether custom error page domain's DNS can be resolved publicly.

### Question

**Did you check whether custom error page can be publicly accessed?**

### Options

- **Yes (Can access publicly)** → Go to: *Further investigations needed for custom error page issue*
- **No (Cannot  access publicly)** → Go to: *Make custom error page domain to be publicly accessed*

---

### Step 10: Make custom error page domain to be publicly accessed

### Support Engineer Solution

Make custom error page domain to be publicly resolved with DNS.

Make custom error page domain to be routed and accessed publicly. (Configure UDR if needed)

### Customer Solution

*Content type: MarkdownText*

Make custom error page domain to be publicly resolved with DNS.

Make custom error page domain to be routed and accessed publicly. (Configure UDR if needed)

---

### Step 11: Further investigations needed for custom error page issue

### Support Engineer Solution

In addition to the previous steps, check the following items further for the custom error page configuration.

(1) Ensure with customer that the custom error page size is less than 1 MB.

(2) Your application gateway doesn't periodically check the custom error page file's location to fetch a new version. 
So if the new custom error page is not retrieved by application gateway even after customer updated this, you can perform any configuration update on the application gateway to manually update the custom error page's cache.

(3) The custom error page address in listener is recommended to be registered with FQDN domain format, since IP domain format can cause issue. 

(For example, we recommend to register custom error page domain in listener as https://error-page-domain.com/index.html, not as https://4.217.194.177/index.html)

(4) In .html (custom error page) file, use absolute URLs (that are publicly accessible) for externally referenced resources like .css or .js.

(5) If the .html file and other resources (like .css or .js coded in .html) are hosted in different domains or servers, the firewall on the server hosting the .css or .js file must allow access from external clients. (This is because, after the client browser loaded .html file from application gateway, the .css or .js resources can be requested directly from the client based on the absolute URL information (for .css or .js) coded in .html)

To check additional information for custom error page issue and configuration, please refer to the official document below.
  - https://learn.microsoft.com/en-us/azure/application-gateway/custom-error#requirements

If the custom error page issue still persists, please raise AVA for further troubleshooting.

### Customer Solution

*Content type: MarkdownText*

In addition to the previous steps, check the following items further for the custom error page configuration.

(1) Ensure with customer that the custom error page size is less than 1 MB.

(2) Your application gateway doesn't periodically check the custom error page file's location to fetch a new version. 
So if the new custom error page is not retrieved by application gateway even after customer updated this, you can perform any configuration update on the application gateway to manually update the custom error page's cache.

(3) The custom error page address in listener is recommended to be registered with FQDN domain format, since IP domain format can cause issue. 

(For example, we recommend to register custom error page domain in listener as https://error-page-domain.com/index.html, not as https://4.217.194.177/index.html)

(4) In .html (custom error page) file, use absolute URLs (that are publicly accessible) for externally referenced resources like .css or .js.

(5) If the .html file and other resources (like .css or .js coded in .html) are hosted in different domains or servers, the firewall on the server hosting the .css or .js file must allow access fr

*(Content truncated — refer to original GT for full details)*
