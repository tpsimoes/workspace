# Troubleshoot Application Gateway IPv6 configuration

> **Product:** Application Gateway  
> **Solution ID:** 6072a4d4-1d4d-4a46-a521-af756a7db4fe  
> **Trigger words:** application, application gateway, configuration, configure, gateway, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot Application Gateway IPv6 configuration** under **Application Gateway**.
 The original guided troubleshooter contains 7 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: IPv6 configuration ⭐ (First Step)

### Guidance

Each selection leads to a focused page with narrowed-down options or solutions, including relevant documentation and step-by-step instructions.

### Question

**What do you need help with?**

### Options

- **Dual‑stack (IPv4+IPv6) Gateway creation fails or is unavailable** → Go to: *Dual stack IPv4 IPv6 Gateway creation failure or unavailable*
- **No IPv6 connectivity to front end (public)** → Go to: *No IPv6 connectivity to front end public*
- **Back end health unhealthy/unknown after enabling IPv6 front end** → Go to: *Back end health unknown after enabling IPv6 front end*
- **WAF custom rules not matching IPv6 addresses** → Go to: *WAF custom rules not matching IPv6 addresses*
- **Private Link access over IPv6 not working** → Go to: *Private Link access over IPv6 not working*
- **AGIC/Kubernetes ingress doesn’t expose IPv6** → Go to: *AGIC Kubernetes ingress does not expose IPv6*

---

### Step 2: Dual stack IPv4 IPv6 Gateway creation failure or unavailable

### Support Engineer Solution

### Dual‑stack (IPv4+IPv6) Gateway creation fails or is unavailable

**Issue:** You can’t select IPv6, create a dual‑stack frontend, or deployment fails during creation.

- **Common causes**
  - Using **Application Gateway v1 SKU** (IPv6 frontend requires v2).
  - Upgrading existing IPV4 only Application gateway to dual stack (IPv4 and IPv6).
  - VNet/subnet is missing IPv6 address space or is not dual stack.
  - No Standard SKU IPv6 Public IP to attach.

**Troubleshooting**

- Deploy a **new v2** Application Gateway with dual‑stack frontend. (Existing IPv4 application gateways **can't** be upgraded to dual stack application gateways.)
- Add IPv6 prefixes to VNet and create a subnet which contains both IPv4 and IPv6 address space. (IPv6-only subnet will not work, the selected subnet has to be dual stack.)
- Create/associate a **Standard SKU** IPv6 Public IP.

**Step-by-step solution**

1. Confirm SKU = **v2** (Portal → AppGW → Overview). If v1, plan new v2 deployment.
2. Verify VNet has IPv6 prefixes. Make sure to create a subnet which contains both IPv4 and IPv6 address spaces.
3. Create a **Standard** Public IP (IPv6) and associate it as a frontend IP. (**Note**: This is not required for private-only gateways.)
4. Re-run deployment or use ARM/CLI quickstart for IPv6 AppGW to validate.

### Resources 

- [Configure AppGW with public IPv6 frontend (Portal)](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)
- [Frontend IP configuration (dual‑stack note)](https://learn.microsoft.com/azure/application-gateway/configuration-frontend-ip)
- [Public IP addresses (Standard/IPv6)](https://learn.microsoft.com/azure/virtual-network/ip-services/public-ip-addresses)
- [ARM quickstart: IPv6 AppGW](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-arm-template)

### Customer Solution

*Content type: MarkdownText*

### Dual‑stack (IPv4+IPv6) Gateway creation fails or is unavailable

**Issue:** You can’t select IPv6, create a dual‑stack frontend, or deployment fails during creation.

**Common causes**

  - Using **Application Gateway v1 SKU** (IPv6 frontend requires v2).

  - Upgrading existing IPV4 only Application gateway to dual stack (IPv4 and IPv6).

  - VNet/subnet is missing IPv6 address space or is not dual stack.

  - No Standard SKU IPv6 Public IP to attach.

**Troubleshooting**

- Deploy a **new v2** Application Gateway with dual‑stack frontend. (Existing IPv4 application gateways **can't** be upgraded to dual stack application gateways.)

- Add IPv6 prefixes to VNet and create a subnet which contains both IPv4 and IPv6 address space. (IPv6-only subnet will not work, the selected subnet has to be dual stack.)

- Create/associate a **Standard SKU** IPv6 Public IP.

**Step-by-step solution**

1. Confirm SKU = **v2** (Portal → AppGW → Overview). If v1, plan new v2 deployment.

2. Verify VNet has IPv6 prefixes. Make sure to create a subnet which contains both I

*(Content truncated — refer to original GT for full details)*

### Step 3: No IPv6 connectivity to front end public

### Support Engineer Solution

### No IPv6 connectivity to front end (public)

**Issue:** IPv6 clients can’t reach the site; ping -6 or HTTP over v6 fails.

**Common causes**
  - No IPv6 frontend IP configured/associated.
  - DNS AAAA not published or misconfigured.
  - NSG/UDR filtering IPv6 traffic to AppGw subnet.
  - Using Basic SKU Public IP (no IPv6 for AppGW v2).

**Troubleshooting**

- Add/verify **IPv6 Public Frontend** and listener binding.
- Publish/verify **AAAA** record or CNAME to AppGW DNS name.
- Ensure NSG allows inbound v6 to frontend IP(s).
- Use **Standard SKU** Public IP (IPv6).

**Step-by-step resolution**

1. Check AppGW → Frontends: confirm an **IPv6 Public IP** exists/attached.
2. Validate **Listener** is bound to the IPv6 frontend and correct port/host.
3. Verify DNS: **dig AAAA yourhost** returns the correct IPv6 or CNAME to AppGW DNS.
4. Inspect NSG rules on AppGwSubnet for IPv6 allow (destination = frontend IP).

### Resources

- [Frontend IP configuration (dual‑stack)](https://learn.microsoft.com/azure/application-gateway/configuration-frontend-ip)
- [Public IP addresses in Azure](https://learn.microsoft.com/azure/virtual-network/ip-services/public-ip-addresses)

### Customer Solution

*Content type: MarkdownText*

### No IPv6 connectivity to front end (Public)

**Issue:** IPv6 clients can’t reach the site; ping -6 or HTTP over v6 fails.

**Common causes**

  - No IPv6 frontend IP configured/associated.

  - DNS AAAA not published or misconfigured.

  - NSG/UDR filtering IPv6 traffic to AppGw subnet.

  - Using Basic SKU Public IP (no IPv6 for AppGW v2).

**Troubleshooting**

- Add/verify **IPv6 Public Frontend** and listener binding.

- Publish/verify **AAAA** record or CNAME to AppGW DNS name.

- Ensure NSG allows inbound v6 to frontend IP(s).

- Use **Standard SKU** Public IP (IPv6).

**Step-by-step resolution**

1. Check AppGW → Frontends: confirm an **IPv6 Public IP** exists/attached.

2. Validate **Listener** is bound to the IPv6 frontend and correct port/host.

3. Verify DNS: **dig AAAA yourhost** returns the correct IPv6 or CNAME to AppGW DNS.

4. Inspect NSG rules on AppGwSubnet for IPv6 allow (destination = frontend IP).

### Resources

- [Frontend IP configuration (dual‑stack)](https://learn.microsoft.com/azure/application-gateway/configuration-frontend-ip)

- [Public IP addresses in Azure](https://learn.microsoft.com/azure/virtual-network/ip-services/public-ip-addresses)

---

### Step 4: Back end health unknown after enabling IPv6 front end

### Support Engineer Solution

### Back end health unhealthy/unknown after enabling IPv6 Frontend

**Issue:** Back ends show **Unhealthy/Unknown** in **Back end health** after adding IPv6 front end.

**Common causes:**
  - Attempting to use **IPv6 back end addresses** (unsupported).
  - Back end pool is FQDN and resolving to IPv6 address or resolving to both IPv4 and IPv6 addresses.
  - Probe hostname/path/port mismatch, TLS issues, or NSG/UDR blocks.

**Troubleshooting**

- Ensure **back end pool targets are IPv4** and reachable. 
- Configure custom probes with correct host/path/status codes and TLS.

**Step-by-step resolution**

1. Open **Back end health** and note error messages per server.
2. Confirm back end addresses are IPv4; replace IPv6 targets. If back end pool is FQDN, make sure the FQDN is resolving to ipv4 addresses only.
3. Review probe source IP expectations and NSG allowance.
4. Create or adjust a **Custom health probe** with correct host/path and expected codes.

### Resources 

- [IPv6 limitations (no IPv6 backends)](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)
- [Health probes overview](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-probe-overview)
- [Backend health](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health)

### Customer Solution

*Content type: MarkdownText*

### Back end health unhealthy/unknown after enabling IPv6 Frontend

**Issue:** Back ends show **Unhealthy/Unknown** in **Back end health** after adding IPv6 front end.

**Common causes:**

  - Attempting to use **IPv6 back end addresses** (unsupported).

  - Back end pool is FQDN and resolving to IPv6 address or resolving to both IPv4 and IPv6 addresses.

  - Probe hostname/path/port mismatch, TLS issues, or NSG/UDR blocks.

**Troubleshooting**

- Ensure **back end pool targets are IPv4** and reachable. 

- Configure custom probes with correct host/path/status codes and TLS.

**Step-by-step resolution**

1. Open **Back end health** and note error messages per server.

2. Confirm back end addresses are IPv4; replace IPv6 targets. If back end pool is FQDN, make sure the FQDN is resolving to ipv4 addresses only.

3. Review probe source IP expectations and NSG allowance.

4. Create or adjust a **Custom health probe** with correct host/path and expected codes.

### Resources 

- [IPv6 limitations (no IPv6 backends)](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)

- [Health probes overview](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-probe-overview)

- [Backend health](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health)

---

### Step 5: WAF custom rules not matching IPv6 addresses

### Support Engineer Solution

### WAF custom rules not matching IPv6 addresses

**Description:** Custom rules intended to match IPv6 addresses fail.

**Common causes (limitation):**
  - **AppGW WAF custom rules don’t support IPv6 match conditions**.

**Troubleshooting**

- Use **managed rule sets** and non‑IP conditions (headers, geography) where suitable; log and monitor traffic.

**Step-by-step resolution**

1. Review current custom rules and remove **IPv6 IPMatch** conditions.
2. Replace with alternative criteria (GeoMatch, headers, paths) where feasible. 
3. Validate via WAF logs.

### Resources

- [IPv6 limitations (WAF custom rules IPv6 unsupported)](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)
- [WAF v2 custom rules](https://learn.microsoft.com/azure/web-application-firewall/ag/custom-waf-rules-overview)
- [Q&A confirmation on IPv6 custom rules](https://learn.microsoft.com/answers/questions/2120382/waf-ipv6-custom-match-rules-for-application-gatewa)

### How to allow or block an IPv6 address using WAF custom rules

If your upstream service (CDN, proxy, NGINX, etc.) adds the client IPv6 address into headers such as **`X-Real-IP`** or **`X-Forwarded-For`**, you can still whitelist or block it using a **string match** rule.

**Example:** Block all traffic except one IPv6 address

1. Make sure your proxy injects the client IP into the `X-Real-IP` header.
2. Create a WAF Custom Rule:
   - **Match variable:** Request header → `X-Real-IP`  
   - **Match type:** String  
   - **Operator:** `Not equal to`  
   - **Value:** `IPv6-address`  
   - **Action:** **Deny**

This rule denies any request where `X-Real-IP` is not the specific IPv6 address.

**Example:** Block a specific IPv6 address

Use the same setup but change:
- **Operator:** `Equal to`  
- **Action:** **Deny**

This blocks only the unwanted IPv6 address.

### Customer Solution

*Content type: MarkdownText*

### WAF custom rules not matching IPv6 addresses

**Description:** Custom rules intended to match IPv6 addresses fail.

**Common causes (limitation):**

  - **AppGW WAF custom rules don’t support IPv6 match conditions**.

**Troubleshooting**

- Use **managed rule sets** and non‑IP conditions (headers, geography) where suitable; log and monitor traffic.

**Step-by-step resolution**

1. Review current custom rules and remove **IPv6 IPMatch** conditions.

2. Replace with alternative criteria (GeoMatch, headers, paths) where feasible. 

3. Validate via WAF logs.

### Resources

- [IPv6 limitations (WAF custom rules IPv6 unsupported)](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)

- [WAF v2 custom rules](https://learn.microsoft.com/azure/web-application-firewall/ag/custom-waf-rules-overview)

- [Q&A confirmation on IPv6 custom rules](https://learn.microsoft.com/answers/questions/2120382/waf-ipv6-custom-match-rules-for-application-gatewa)

### How to allow or block an IPv6 address using WAF custom rules

If 

*(Content truncated — refer to original GT for full details)*

### Step 6: Private Link access over IPv6 not working

### Support Engineer Solution

### Private Link access over IPv6 not working

**Issue:** Clients over IPv6 can’t reach AppGW via Private Link.

**Common causes (limitation):**

  - **Private Link over IPv6 is not supported for AppGW**; Private Link works, but IPv6 is not available.

**Troubleshooting**

- Use **IPv4** for Private Link connectivity and dual‑stack for public ingress if required.

**Step-by-step resolution**

1. Verify Private Link configuration is associated with the **frontend I**P (IPv4).
2. Ensure clients can resolve and reach the **Private Endpoint IPv4** address.

### Resources

- [Application Gateway Private Link](https://learn.microsoft.com/azure/application-gateway/private-link)
- [IPv6 limitations](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)

### Customer Solution

*Content type: MarkdownText*

### Private Link access over IPv6 not working

**Issue:** Clients over IPv6 can’t reach AppGW via Private Link.

**Common causes (limitation):**

  - **Private Link over IPv6 is not supported for AppGW**; Private Link works, but IPv6 is not available.

**Troubleshooting**

- Use **IPv4** for Private Link connectivity and dual‑stack for public ingress if required.

**Step-by-step resolution**

1. Verify Private Link configuration is associated with the **frontend I**P (IPv4).

2. Ensure clients can resolve and reach the **Private Endpoint IPv4** address.

### Resources

- [Application Gateway Private Link](https://learn.microsoft.com/azure/application-gateway/private-link)

- [IPv6 limitations](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)

---

### Step 7: AGIC Kubernetes ingress does not expose IPv6

### Support Engineer Solution

### AGIC / Kubernetes ingress doesn’t expose IPv6

**Issue:** AGIC-managed AppGW fails to expose IPv6 endpoints.

**Common causes (limitation):**

  - **AGIC currently doesn’t support IPv6 configuration**.

**Troubleshooting**

- Front with a dual‑stack AppGW managed outside AGIC; or use Azure Front Door for IPv6 edge + AppGW internal.

**Step-by-step solution**

1. Separate IPv6 frontend management from AGIC; deploy dual‑stack AppGW and bind listeners manually.

2. Optionally, place **Azure Front Door** at the edge for global IPv6 ingress and route to AppGW.

### Resources

- [IPv6 limitations (AGIC)](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)

- [Azure load balancing options overview](https://learn.microsoft.com/azure/architecture/guide/technology-choices/load-balancing-overview)

### Customer Solution

*Content type: MarkdownText*

### AGIC / Kubernetes ingress doesn’t expose IPv6

**Issue:** AGIC-managed AppGW fails to expose IPv6 endpoints.

**Common causes (limitation):**

  - **AGIC currently doesn’t support IPv6 configuration**.

**Troubleshooting**

- Front with a dual‑stack AppGW managed outside AGIC; or use Azure Front Door for IPv6 edge + AppGW internal.

**Step-by-step solution**

1. Separate IPv6 frontend management from AGIC; deploy dual‑stack AppGW and bind listeners manually.

2. Optionally, place **Azure Front Door** at the edge for global IPv6 ingress and route to AppGW.

### Resources

- [IPv6 limitations (AGIC)](https://learn.microsoft.com/azure/application-gateway/ipv6-application-gateway-portal)

- [Azure load balancing options overview](https://learn.microsoft.com/azure/architecture/guide/technology-choices/load-balancing-overview)

---
