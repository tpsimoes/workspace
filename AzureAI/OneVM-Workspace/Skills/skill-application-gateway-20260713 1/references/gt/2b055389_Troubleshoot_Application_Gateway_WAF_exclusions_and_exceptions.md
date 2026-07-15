# Troubleshoot Application Gateway WAF exclusions and exceptions

> **Product:** Application Gateway  
> **Solution ID:** 2b055389-dc60-4cd7-92e0-ec21bb3bcc74  
> **Trigger words:** application, application gateway, exceptions, exclusions, gateway, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot Application Gateway WAF exclusions and exceptions** under **Application Gateway**.
 The original guided troubleshooter contains 5 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: WAF exclusions and exceptions for Application Gateway ⭐ (First Step)

### Guidance

Each selection leads to a focused page with narrowed-down options or solutions, including relevant documentation and step-by-step instructions.

### Question

**What do you need help with?**

### Options

- **Legitimate requests are being blocked (false positives)** → Go to: *Legitimate requests are being blocked false positives*
- **Exclusion rules or custom exceptions are not working as expected** → Go to: *Exclusion rules or custom exceptions not working as expected*
- **502 bad gateway errors after enabling WAF** → Go to: *502 bad gateway errors after enabling WAF*
- **Understand what WAF rules were triggered** → Go to: *Understand what WAF rules were triggered*

---

### Step 2: Legitimate requests are being blocked false positives

### Support Engineer Solution

### Legitimate requests are being blocked (false positives)

Sometimes WAF blocks legitimate traffic due to false positives, where benign request components trigger security rules incorrectly.

- **Common causes:** 
  - Authentication tokens or custom headers triggering SQL injection or cross-site scripting rules. 
  - Complex query strings that match patterns flagged by WAF.

**Solutions:**

- Analyze WAF logs to pinpoint the blocking rule and request element.

- Add exclusions for specific headers, cookies, or query parameters causing false positives.

- Test changes in Detection mode before enforcement.

**Step-by-step:**

1. Access WAF logs in Azure Monitor to identify blocked requests and triggered rule IDs.
2. Determine which part of the request caused the block (header, cookie, query param).
3. Create exclusions in the WAF policy targeting the attribute and relevant rules.
4. Enable Detection mode and verify legitimate requests pass.
5. Switch back to Prevention mode once validated.

**Reference documentation:**

- [Configure WAF Exclusion Lists](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-waf-configuration)
- [WAF Troubleshooting Guide](https://learn.microsoft.com/azure/web-application-firewall/ag/web-application-firewall-troubleshoot)

### Customer Solution

*Content type: MarkdownText*

### Legitimate requests are being blocked (false positives)

Sometimes WAF blocks legitimate traffic due to false positives, where benign request components trigger security rules incorrectly.

- **Common causes:** 

  - Authentication tokens or custom headers triggering SQL injection or cross-site scripting rules. 

  - Complex query strings that match patterns flagged by WAF.

**Solutions:**

- Analyze WAF logs to pinpoint the blocking rule and request element.

- Add exclusions for specific headers, cookies, or query parameters causing false positives.

- Test changes in Detection mode before enforcement.

**Step-by-step:**

1. Access WAF logs in Azure Monitor to identify blocked requests and triggered rule IDs.

2. Determine which part of the request caused the block (header, cookie, query param).

3. Create exclusions in the WAF policy targeting the attribute and relevant rules.

4. Enable Detection mode and verify legitimate requests pass.

5. Switch back to Prevention mode once validated.

**Reference documentation:**

- [Configure WAF Exclusion Lists](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-waf-configuration)

- [WAF Troubleshooting Guide](https://learn.microsoft.com/azure/web-application-firewall/ag/web-application-firewall-troubleshoot)

---

### Step 3: Exclusion rules or custom exceptions not working as expected

### Support Engineer Solution

### Exclusion rules or custom exceptions not working as expected

Exclusions or custom exceptions may fail to apply correctly due to misconfiguration or scope mismatches.

- **Common causes:**
  - Incorrect attribute syntax or naming when configuring exclusions.
  - Applying exclusions at incorrect scope level (rule set vs specific rule).
  - Using outdated WAF ruleset versions without proper adjustments.

**Solutions:**

- Verify attribute names, scopes, and WAF ruleset versions are correct.

- Confirm exclusions match targeted rules or rule groups.

- Check for conflicts or incorrect rule priorities.

**Step-by-step:**

1. Review the exclusion or custom rule configuration for correct scope and attribute.
2. Cross-check WAF policy version compatibility.
3. Test changes in Detection mode, monitoring logs for expected changes.
4. Adjust or remove conflicting rules if needed.
5. Deploy updated policy and monitor.

**Reference documentation:**
- [WAF Policy Configuration](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/policy-overview)
- [Troubleshoot WAF Policies](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot)

### Customer Solution

*Content type: MarkdownText*

### Exclusion rules or custom exceptions not working as expected

Exclusions or custom exceptions may fail to apply correctly due to misconfiguration or scope mismatches.

- **Common causes:**

  - Incorrect attribute syntax or naming when configuring exclusions.

  - Applying exclusions at incorrect scope level (rule set vs specific rule).

  - Using outdated WAF ruleset versions without proper adjustments.

**Solutions:**

- Verify attribute names, scopes, and WAF ruleset versions are correct.

- Confirm exclusions match targeted rules or rule groups.

- Check for conflicts or incorrect rule priorities.

**Step-by-step:**

1. Review the exclusion or custom rule configuration for correct scope and attribute.

2. Cross-check WAF policy version compatibility.

3. Test changes in Detection mode, monitoring logs for expected changes.

4. Adjust or remove conflicting rules if needed.

5. Deploy updated policy and monitor.

**Reference documentation:**

- [WAF Policy Configuration](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/policy-overview)

- [Troubleshoot WAF Policies](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot)

---

### Step 4: 502 bad gateway errors after enabling WAF

### Support Engineer Solution

### 502 bad gateway errors after enabling WAF

502 errors often occur when WAF blocks traffic essential for backend health or when backend endpoints are unreachable.

- **Common causes:**

  - WAF blocking health probe requests unintentionally.

  - Backend service misconfiguration or downtime combined with WAF enforcement.

**Solutions:**

- Verify backend health probes and ensure traffic required for health checks is allowed.

- Analyze WAF logs to identify blocking rules causing failures.

- Add fine-grained exclusions or exceptions to allow critical traffic.

**Step-by-step:**

1. Check Application Gateway backend health status in the Azure portal.

2. Enable and review WAF diagnostic logs for blocks related to backend requests.

3. Identify and exclude problematic rules or attributes needed by backend probes.

4. Re-test backend connectivity and probe success.

**Reference documentation:**

- [Troubleshoot 502 Errors](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-troubleshooting-502)

- [Azure WAF Logs Analysis](https://learn.microsoft.com/en-us/azure/application-gateway/log-analytics)

### Customer Solution

*Content type: MarkdownText*

### 502 bad gateway errors after enabling WAF

502 errors often occur when WAF blocks traffic essential for backend health or when backend endpoints are unreachable.

- **Common causes:**

  - WAF blocking health probe requests unintentionally.

  - Backend service misconfiguration or downtime combined with WAF enforcement.

**Solutions:**

- Verify backend health probes and ensure traffic required for health checks is allowed.

- Analyze WAF logs to identify blocking rules causing failures.

- Add fine-grained exclusions or exceptions to allow critical traffic.

**Step-by-step:**

1. Check Application Gateway backend health status in the Azure portal.

2. Enable and review WAF diagnostic logs for blocks related to backend requests.

3. Identify and exclude problematic rules or attributes needed by backend probes.

4. Re-test backend connectivity and probe success.

**Reference documentation:**

- [Troubleshoot 502 Errors](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-troubleshooting-502)

- [Azure WAF Logs Analysis](https://learn.microsoft.com/en-us/azure/application-gateway/log-analytics)

---

### Step 5: Understand what WAF rules were triggered

### Support Engineer Solution

### Understand what WAF rules were triggered

Knowing which WAF rules triggered helps you fine-tune policies to balance protection and accessibility.

- **Common causes:**

  - Managed rule sets identifying patterns in requests as attacks.

  - Unusual payloads or encoded input triggering WAF patterns.

**Solutions:**

- Use Azure Monitor or Log Analytics to access detailed WAF logs.

- Analyze triggered rule IDs, matched data, and affected request parts.

- Use insights to create exclusions or custom rules as appropriate.

**Step-by-step:**

1. Open Application Gateway WAF logs in Azure Monitor/Log Analytics.

2. Filter logs by "ApplicationGatewayFirewallLog".

3. Identify triggered rules and matched data fields.

4. Document critical findings to adjust WAF policies.

**Reference documentation:**

- [Analyze WAF Logs](https://learn.microsoft.com/en-us/azure/application-gateway/log-analytics)

- [Azure WAF Policy Overview](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/policy-overview) 

### Customer Solution

*Content type: MarkdownText*

### Understand what WAF rules were triggered

Knowing which WAF rules triggered helps you fine-tune policies to balance protection and accessibility.

- **Common causes:**

  - Managed rule sets identifying patterns in requests as attacks.

  - Unusual payloads or encoded input triggering WAF patterns.

**Solutions:**

- Use Azure Monitor or Log Analytics to access detailed WAF logs.

- Analyze triggered rule IDs, matched data, and affected request parts.

- Use insights to create exclusions or custom rules as appropriate.

**Step-by-step:**

1. Open Application Gateway WAF logs in Azure Monitor/Log Analytics.

2. Filter logs by "ApplicationGatewayFirewallLog".

3. Identify triggered rules and matched data fields.

4. Document critical findings to adjust WAF policies.

**Reference documentation:**

- [Analyze WAF Logs](https://learn.microsoft.com/en-us/azure/application-gateway/log-analytics)

- [Azure WAF Policy Overview](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/policy-overview) 

---
