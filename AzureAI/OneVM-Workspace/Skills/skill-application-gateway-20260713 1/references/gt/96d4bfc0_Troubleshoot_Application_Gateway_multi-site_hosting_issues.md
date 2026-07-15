# Troubleshoot Application Gateway multi-site hosting issues

> **Product:** Application Gateway  
> **Solution ID:** 96d4bfc0-883e-42c1-942c-942bb1a8b41e  
> **Trigger words:** application, application gateway, gateway, hosting, multi, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot Application Gateway multi-site hosting issues** under **Application Gateway**.
 The original guided troubleshooter contains 6 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Multi site hosting ⭐ (First Step)

### Guidance

Each selection leads to a focused page with narrowed-down options or solutions, including relevant documentation and step-by-step instructions.

### Question

**What do you need help with?**

### Options

- **Host multiple subdomains on the same port** → Go to: *Host multiple subdomains on the same port*
- **Use one listener for multiple hostnames** → Go to: *Use one listener for multiple hostnames*
- **Traffic is not routing correctly between sites** → Go to: *Traffic is not routing correctly between sites*
- **Backend health and probe failures** → Go to: *Backend health and probe failures*
- **401/404 errors after enabling multisite** → Go to: *4xx errors after enabling multi site*

---

### Step 2: Host multiple subdomains on the same port

### Support Engineer Solution

### Host multiple subdomains on the same port
**Description:** You want to host multiple subdomains (e.g., **app.contoso.com**, **blog.contoso.com**) on a single Application Gateway using port 443.

- **Common Causes:** 
  - Listener type set to **Basic** instead of **Multi-site**.
  - Hostnames not added to the listener configuration.
  - Routing rules not mapped correctly to backend pools.

**Solutions:**

- Use **Multi-site listeners** for host-based routing.

- Add all required subdomains as hostnames in the listener.

- Create routing rules for each hostname pointing to the correct backend pool.

**Step-by-Step:**

1. In Azure Portal, go to **Application Gateway** → **Listeners**.
2. Create or edit a **Multi-site listener** on port 443.
3. Under **Host names**, add each subdomain (e.g., **app.contoso.com**, **blog.contoso.com**).
4. Navigate to **Rules** and create routing rules for each hostname:
    - Map each hostname to its corresponding backend pool.
5. Save changes and restart Application Gateway if prompted.
6. Test by browsing each subdomain to confirm correct routing.
7. **Expected Result**: Each subdomain routes to its designated backend pool.
8. **Confirm**: Check **Backend health** and listener logs for successful routing.

**Reference Documentation:**
- [Create and configure an application gateway to host multiple web sites using the Azure portal](https://learn.microsoft.com/azure/application-gateway/create-multiple-sites-portal)

### Customer Solution

*Content type: MarkdownText*

### Host multiple subdomains on the same port

**Description:** You want to host multiple subdomains (e.g., app.contoso.com, blog.contoso.com) on a single Application Gateway using port 443.

**Common causes:** 

- Listener type set to **Basic** instead of **Multi-site**.

- Hostnames not added to the listener configuration.

- Routing rules not mapped correctly to backend pools.

**Solutions:**

- Use multi-site listeners for host-based routing.

- Add all required subdomains as hostnames in the listener.

- Create routing rules for each hostname pointing to the correct backend pool.

**Step-by-step instructions:**

1. In Azure portal, go to **Application Gateway** > **Listeners**.

2. Create or edit a **Multi-site listener** on port 443.

3. Under **Host names**, add each subdomain (e.g., app.contoso.com, blog.contoso.com).

4. Navigate to **Rules** and create routing rules for each hostname:

   - Map each hostname to its corresponding backend pool.

5. Save changes and restart Application Gateway if prompted.

6. Test by browsing each subdomain to confirm correct routing.

7. **Expected result**: Each subdomain routes to its designated backend pool.

8. **Confirm**: Check **Backend health** and listener logs for successful routing.

**Resources:**

- [Create and configure an application gateway to host multiple websites using the Azure portal](https://learn.microsoft.com/azure/application-gateway/create-multiple-sit

*(Content truncated — refer to original GT for full details)*

### Step 3: Use one listener for multiple hostnames

### Support Engineer Solution

### Use one listener for multiple hostnames
**Description:** Azure Application Gateway supports hosting multiple domains or subdomains on a single listener using multi-site hosting. This is useful when you want to simplify configuration and reduce listener count. However, there are limits and considerations that can cause routing issues if not configured correctly.

- **Common Causes:**
  - Exceeding the **five-hostname limit** per listener.
  - Missing or incorrect hostnames in listener configuration.
  - Routing rules not properly mapped to backend pools.

**Solutions:**

- Add up to **five hostnames per listener** using multi-site configuration.

- Create additional listeners if you need more than five hostnames.

- Ensure routing rules reference the correct backend pool for each hostname.

**Step-by-Step:**

1. In Azure Portal, go to **Application Gateway** → **Listeners**.
2. Select or create a **Multi-site listener** on the desired port (e.g., 443).
3. Under **Host names**, add up to five hostnames (e.g., **app.contoso.com**, **blog.contoso.com**).
4. Navigate to **Rules** and create routing rules for each hostname:
    - Map each hostname to its corresponding backend pool.
5. Save changes and restart Application Gateway if prompted.
6. Test by browsing each hostname to confirm correct routing.
7. **Expected Result**: All configured hostnames route to their respective backend pools.
8. **Confirm**: Check **Backend health** and listener logs for successful routing.

**Reference Documentation:**
- [Application gateway components](https://learn.microsoft.com/azure/application-gateway/application-gateway-components)

### Customer Solution

*Content type: MarkdownText*

### Use one listener for multiple hostnames

**Description:** Azure Application Gateway supports hosting multiple domains or subdomains on a single listener using multi-site hosting. This is useful when you want to simplify configuration and reduce listener count. However, there are limits and considerations that can cause routing issues if not configured correctly.

**Common causes:**

- Exceeding the five-hostname limit per listener.

- Missing or incorrect hostnames in listener configuration.

- Routing rules not properly mapped to backend pools.

**Solutions:**

- Add up to five hostnames per listener using multi-site configuration.

- Create additional listeners if you need more than five hostnames.

- Ensure routing rules reference the correct backend pool for each hostname.

**Step-by-step instructions:**

1. In the Azure portal, go to **Application Gateway** > **Listeners**.

2. Select or create a **Multi-site listener** on the desired port (e.g., 443).

3. Under **Host names**, add up to five hostnames (e.g., app.contoso.com, blog.contoso.com).

4. Navigate to **Rules** and create routing rules for each hostname:

   - Map each hostname to its corresponding backend pool.

5. Save changes and restart Application Gateway if prompted.

6. Test

*(Content truncated — refer to original GT for full details)*

### Step 4: Traffic is not routing correctly between sites

### Support Engineer Solution

### Route traffic correctly (rule priority issues)
**Description:** When using multi-site hosting, you may notice requests for one domain being served by the wrong backend pool. This usually happens due to misconfigured routing rules or wildcard hostname conflicts.
- **Common Causes:**
  - Wildcard hostname (***.contoso.com**) intercepting traffic meant for a specific domain.
  - Missing or incorrect **Rule Priority** settings in v2 SKU.
  - Listener hostnames not matching the incoming request..

**Solutions:**

- Assign explicit priorities to routing rules (lower number = higher priority).

- Ensure specific hostnames have higher priority than wildcard rules.

- Validate listener hostnames match the domains you expect to route.

**Step-by-Step:**

1. In Azure Portal, go to **Application Gateway** → **Rules**.
2. For each rule, check **Priority**:
    - Specific hostnames: set priority 1–10.
    - Wildcard or catch-all rules: use higher numbers (e.g., 100+).
3. Confirm listener hostnames under **Listeners** match the domain names.
4. Save changes and restart Application Gateway if prompted.
5. Test routing by browsing each domain.
6. **Expected Result**: Requests for each domain route to the correct backend pool.
7. **Confirm**: Check **Backend health** and listener logs for correct routing.

**Reference Documentation:**
- [Application Gateway configuration overview](https://learn.microsoft.com/azure/application-gateway/configuration-overview)

### Customer Solution

*Content type: MarkdownText*

### Route traffic correctly (rule priority issues)

**Description:** When using multi-site hosting, you may notice requests for one domain being served by the wrong backend pool. This usually happens due to misconfigured routing rules or wildcard hostname conflicts.

**Common causes:**

- Wildcard hostname (*.contoso.com) intercepting traffic meant for a specific domain.

- Missing or incorrect **Rule priority** settings in v2 SKU.

- Listener hostnames not matching the incoming request.

**Solutions:**

- Assign explicit priorities to routing rules (lower number = higher priority).

- Ensure specific hostnames have higher priority than wildcard rules.

- Validate listener hostnames match the domains you expect to route.

**Step-by-step instructions:**

1. In the Azure portal, go to **Application Gateway** > **Rules**.

2. For each rule, check **Priority**:

   - Specific hostnames: set priority 1–10.

   - Wildcard or catch-all rules: use higher numbers (e.g., 100+).

3. Confirm listener hostnames under **Listeners** match the domain names.

4. Save changes and restart Application Gateway if prompted.

5. Test routing by browsing each domain.

6. **Expected result**: Requests for each domain route to the correct backend pool.

7. **Confirm**: Check **Backend health** and listener logs for correct routing.

**Resources:**

- [Application Gateway configuration overview](https://learn.microsoft.com/azure/application-gateway/c

*(Content truncated — refer to original GT for full details)*

### Step 5: Backend health and probe failures

### Support Engineer Solution

### Backend health & probe failures
**Description:** After configuring multi-site hosting, some backends may appear **Unhealthy** in Application Gateway or return **502 Bad Gateway** errors. This usually happens when health probes fail or connectivity between the gateway and backend servers is blocked.

- **Common Causes:**
  - Incorrect health probe settings (wrong path, port, or protocol).
  - Host header mismatch in probe configuration.
  - NSG, firewall, or custom routes blocking traffic from Application Gateway to backend.
  - Backend application not responding on expected path or port.

**Solutions:**

- Verify and correct health probe configuration.

- Ensure backend servers allow traffic from Application Gateway IP ranges.

- Check NSG and firewall rules for required ports.

**Step-by-Step:**

1. In Azure Portal, go to **Application Gateway** → **Backend health**.
2. Identify unhealthy backends and note the error details.
3. Navigate to **Health probes**:
    - Confirm **Path** matches the backend app’s health endpoint (e.g., **/health** or **/**).
    - Ensure **Protocol** and **Port** match backend listener settings.
    - If using multi-site, set **Host** header to the correct domain for that site.
4. Validate NSG and firewall rules:
    - Allow inbound traffic from Application Gateway to backend on required ports.
    - Check UDRs for any misrouting.
5. Save changes and refresh **Backend health**.
6. **Expected Result**: Backend status changes to **Healthy**.
7. **Confirm**: Requests to the site succeed without 502 errors.

**Reference Documentation:**
- [Troubleshooting bad gateway errors in Application Gateway](https://learn.microsoft.com/azure/application-gateway/application-gateway-troubleshooting-502)

### Customer Solution

*Content type: MarkdownText*

### Backend health and probe failures

**Description:** After configuring multi-site hosting, some backends may appear **Unhealthy** in Application Gateway or return "502 Bad Gateway" errors. This usually happens when health probes fail or connectivity between the gateway and backend servers is blocked.

**Common causes:**

- Incorrect health probe settings (wrong path, port, or protocol).

- Host header mismatch in probe configuration.

- Network security group (NSG), firewall, or custom routes blocking traffic from Application Gateway to backend.

- Backend application not responding on expected path or port.

**Solutions:**

- Verify and correct health probe configuration.

- Ensure backend servers allow traffic from Application Gateway IP ranges.

- Check NSG and firewall rules for required ports.

**Step-by-step instructions:**

1. In the Azure portal, go to **Application Gateway** > **Backend health**.

2. Identify unhealthy backends and note the error details.

3. Navigate to **Health probes**:

   - Confirm **Path** matches the backend app’s health endpoint (e.g., **/health** or **/**).

   - Ensure **Protocol** and **Port** match backend li

*(Content truncated — refer to original GT for full details)*

### Step 6: 4xx errors after enabling multi site

### Support Engineer Solution

### 4xx errors after enabling multi-site
**Description:** After enabling multi-site hosting on Azure Application Gateway, some applications return **401 Unauthorized** or **404 Not Found** errors. This typically happens when the backend application relies on the original **Host** header for authentication, routing, or URL generation, and the gateway configuration overrides it.

- **Common Causes:** 
  - Backend HTTP settings override the **Host** header with a custom value.
  - Application Gateway sends a different hostname than the client requested.
  - Backend app uses strict hostname checks for cookies, redirects, or virtual hosts.

**Solutions:**

- Preserve the original **Host** header in backend HTTP settings.

- Avoid overriding the hostname unless required for backend logic.

**Step-by-Step:**

1. In the Azure Portal, go to **Application Gateway** → **HTTP Settings**.
2. Select the HTTP setting linked to the affected backend pool.
3. Check **Override with specific host name**:
    - If enabled, disable it to preserve the original Host header.
4. Save changes and restart Application Gateway if prompted.
5. Test the application by accessing the domain through the gateway.
6. **Expected Result**: Requests should return the correct content without 401 or 404 errors.
7. **Confirm**: Verify successful login and page loads for all multi-site domains.

**Reference:**
- [Application Gateway configuration overview](https://learn.microsoft.com/azure/application-gateway/configuration-overview)

### Customer Solution

*Content type: MarkdownText*

### 4xx errors after enabling multi-site

**Description:** After enabling multi-site hosting on Azure Application Gateway, some applications return "401 Unauthorized" or "404 Not Found" errors. This typically happens when the backend application relies on the original Host header for authentication, routing, or URL generation, and the gateway configuration overrides it.

**Common causes:** 

- Backend HTTP settings override the Host header with a custom value.

- Application Gateway sends a different hostname than the client requested.

- Backend app uses strict hostname checks for cookies, redirects, or virtual hosts.

**Solutions:**

- Preserve the original Host header in backend HTTP settings.

- Avoid overriding the hostname unless required for backend logic.

**Step-by-step instructions:**

1. In the Azure portal, go to **Application Gateway** > **HTTP settings**.

2. Select the HTTP setting linked to the affected backend pool.

3. Check **Override with specific host name**:

   - If it's enabled, disable it to preserve the original Host header.

4. Save changes and restart Application Gateway if prompted.

5. Test the application by accessing the domain through the gateway.

6. **Expected result**: Requests should return the correct content without 401 or 404 errors.

7. **Confirm**: Verify successful login and page loads for all multi-site domains.

**Resources:**

- [Ap

*(Content truncated — refer to original GT for full details)*
