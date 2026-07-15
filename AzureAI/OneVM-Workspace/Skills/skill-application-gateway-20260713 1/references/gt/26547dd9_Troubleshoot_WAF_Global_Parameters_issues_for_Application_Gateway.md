# Troubleshoot WAF Global Parameters issues for Application Gateway

> **Product:** Application Gateway  
> **Solution ID:** 26547dd9-2496-4e1f-bcbf-ff5d33af1eb8  
> **Trigger words:** application, application gateway, gateway, global, parameters, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot WAF Global Parameters issues for Application Gateway** under **Application Gateway**.
 The original guided troubleshooter contains 5 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: WAF Global Parameters for Application Gateway ⭐ (First Step)

### Guidance

Each selection leads to a focused page with narrowed-down options or solutions, including relevant documentation and step-by-step instructions.

### Question

**What do you need help with?**

### Options

- **WAF Global Parameters not taking effect** → Go to: *WAF Global Parameters not taking effect*
- **Performance impact after enabling certain Global Parameters** → Go to: *Performance impact after enabling certain Global Parameters*
- **Difficulty configuring Global Parameters** → Go to: *Difficulty configuring Global Parameters*
- **Unexpected behavior due to Global Parameters** → Go to: *Unexpected behavior due to Global Parameters*

---

### Step 2: WAF Global Parameters not taking effect

### Support Engineer Solution

### WAF Global Parameters not taking effect

Global parameters are intended to modify overall WAF behavior, but sometimes changes appear not to apply as expected.

- **Common causes:**

  - WAF policy not associated to the correct scope (Application Gateway, Listener, Route Path).

  - Delays in propagation of configuration changes.

  - Overlapping policies causing overrides.

**Solutions:**

- Confirm that the WAF policy with configured global parameters is correctly associated with your Application Gateway.

- Check for policy conflicts or multiple policies that could override settings. Custom rules take precedence over managed rules.

- Use Exclusions to avoid legitimate traffic being blocked. Set exclusions by:

  - Request header name.

  - Request cookie name.

  - Request attribute name.

- Validate Azure portal or CLI changes were saved and propagated.

**Step-by-step solution:**

1. Verify WAF policy association with the Application Gateway in the Azure portal.

2. Review all applied WAF policies for overlapping or conflicting global parameter settings.

3. If using automation tools, confirm compatibility; update to latest libraries.

4. Wait for propagation (can take a few minutes) and retest.

For more information, see:

- [Configure Global Settings on Azure WAF](https://learn.microsoft.com/azure/web-application-firewall/ag/create-waf-policy-ag)

- [WAF Policy Management](https://learn.microsoft.com/azure/web-application-firewall/ag/policy-overview)

### Customer Solution

*Content type: MarkdownText*

### WAF Global Parameters not taking effect

Global parameters are intended to modify overall WAF behavior, but sometimes changes appear not to apply as expected.

- **Common causes:**

  - WAF policy not associated to the correct scope (Application Gateway, Listener, Route Path).

  - Delays in propagation of configuration changes.

  - Overlapping policies causing overrides.

**Solutions:**

- Confirm that the WAF policy with configured global parameters is correctly associated with your Application Gateway.

- Check for policy conflicts or multiple policies that could override settings. Custom rules take precedence over managed rules.

- Use Exclusions to avoid legitimate traffic being blocked. Set exclusions by:

  - Request header name.

  - Request cookie name.

  - Request attribute name.

- Validate Azure portal or CLI changes were saved and propagated.

**Step-by-step solution:**

1. Verify WAF policy association with the Application Gateway in the Azure portal.

2. Review all applied WAF policies for overlapping or conflicting global parameter settings.

3. If using automation tools, confirm compatibility; update to latest libraries.

4. Wait for propagation (can take a few minutes) and retest.

For more information, see:

- [Configure Global Settings on Azure WAF](https://learn.microsoft.com/azure/web-application-firewall/ag/create-waf-policy-ag)

- [WAF Policy Management](https://learn.microsof

*(Content truncated — refer to original GT for full details)*

### Step 3: Performance impact after enabling certain Global Parameters

### Support Engineer Solution

### Performance impact after enabling certain Global Parameters

Some global parameters, such as file upload inspection or request body buffering, may cause latency or throughput changes.

- **Common causes:**

  - Legacy modsecurity engine (CRS 3.1/lower) producing bottlenecks..

  - Increasing **maxRequestBodySizeInKb** or **fileUploadLimitInMb** significantly raises inspection workload.

  - Enabling **requestBodyCheck** or buffering large requests without scaling WAF instances.

**Solutions:**

- Upgrade to CRS 3.2+ for the latest performance improvements.

- Assess if enabled parameters are essential for your security requirements. Disable request body inspection for non-critical paths. 

- Test the impact by toggling parameters in Detection mode.

- Optimize backend resources if buffering is required.

**Step-by-step solution:**

1. Review CRS version—upgrade via WAF policy settings if below 3.2.

2. Audit global parameters (body size limits, inspection, file upload).

3. Use WAF policy associated to Route Path (e.g., /file/upload) to disable request body inspection for certain paths

4. Monitor Gateway metrics post-change for performance improvements.

5. Scale backend or Application Gateway resources if performance issues persist.

For more information, see:

- [Application Gateway Limits](https://learn.microsoft.com/azure/azure-resource-manager/management/azure-subscription-service-limits#azure-application-gateway-limits)

- [Azure WAF Performance Considerations](https://learn.microsoft.com/azure/web-application-firewall/ag/best-practices)

- [WAF Request Body Inspection](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits)

### Customer Solution

*Content type: MarkdownText*

### Performance impact after enabling certain Global Parameters

Some global parameters, such as file upload inspection or request body buffering, may cause latency or throughput changes.

- **Common causes:**

  - Legacy modsecurity engine (CRS 3.1/lower) producing bottlenecks..

  - Increasing **maxRequestBodySizeInKb** or **fileUploadLimitInMb** significantly raises inspection workload.

  - Enabling **requestBodyCheck** or buffering large requests without scaling WAF instances.

**Solutions:**

- Upgrade to CRS 3.2+ for the latest performance improvements.

- Assess if enabled parameters are essential for your security requirements. Disable request body inspection for non-critical paths. 

- Test the impact by toggling parameters in Detection mode.

- Optimize backend resources if buffering is required.

**Step-by-step solution:**

1. Review CRS version—upgrade via WAF policy settings if below 3.2.

2. Audit global parameters (body size limits, inspection, file upload).

3. Use WAF policy associated to Route Path (e.g., /file/upload) to disable request body inspection for certain paths

4. Monitor Gateway metrics post-change for performance improvements.

5. Scale backend or Ap

*(Content truncated — refer to original GT for full details)*

### Step 4: Difficulty configuring Global Parameters

### Support Engineer Solution

### Difficulty configuring Global Parameters

Configuring global parameters can be complex due to scope options, dependencies on rule set versions, or syntax (especially with automation).

- **Common causes:**

  - Outdated CLI not supporting new global parameter syntax.

  - Insufficient permissions or attempting change on old engine.

**Solutions:**

- Use Azure Portal wizards or CLI templates for guided configuration.

- Always validate the policy association — ensure it’s applied at the correct scope (Application Gateway, Listener or Route Path)

- Use the latest Azure CLI version to avoid schema mismatches.

**Step-by-step solution:**

1. Review official parameter descriptions in Azure docs.

2. Use Azure Portal guided UI or Azure CLI with latest version.

3. Apply settings incrementally and test.

4. Ensure you have adequate permissions for policy changes.

Reference Documentation:

- [Configure Azure WAF Global Settings](https://learn.microsoft.com/azure/web-application-firewall/ag/create-waf-policy-ag)

- [Azure CLI for WAF](https://learn.microsoft.com/cli/azure/network/application-gateway/waf-policy?view=azure-cli-latest)

### Customer Solution

*Content type: MarkdownText*

### Difficulty configuring Global Parameters

Configuring global parameters can be complex due to scope options, dependencies on rule set versions, or syntax (especially with automation).

- **Common causes:**

  - Outdated CLI not supporting new global parameter syntax.

  - Insufficient permissions or attempting change on old engine.

**Solutions:**

- Use Azure Portal wizards or CLI templates for guided configuration.

- Always validate the policy association — ensure it’s applied at the correct scope (Application Gateway, Listener or Route Path)

- Use the latest Azure CLI version to avoid schema mismatches.

**Step-by-step solution:**

1. Review official parameter descriptions in Azure docs.

2. Use Azure Portal guided UI or Azure CLI with latest version.

3. Apply settings incrementally and test.

4. Ensure you have adequate permissions for policy changes.

Reference Documentation:

- [Configure Azure WAF Global Settings](https://learn.microsoft.com/azure/web-application-firewall/ag/create-waf-policy-ag)

- [Azure CLI for WAF](https://learn.microsoft.com/cli/azure/network/application-gateway/waf-policy?view=azure-cli-latest)

---

### Step 5: Unexpected behavior due to Global Parameters

### Support Engineer Solution

### Unexpected behavior due to Global Parameters

Incorrect or conflicting global parameters can cause unexpected WAF behavior, such as blocking allowed requests or missed detections.

- **Common causes:**

  - Enabling global checks that conflict with custom rules.

  - Misconfiguration of request body size limits.

**Solutions:**

- Audit all global parameter settings for conflicts.

- Temporarily disable suspicious parameters to isolate issues.

- Use Detection mode to monitor before enforcing.

**Step-by-step solution:**

1. Export current WAF policy and review global parameters.

2. Disable parameters one at a time to identify root cause.

3. Switch WAF policy to Detection mode and monitor.

4. Adjust or update parameters based on findings.

For more information, see:

- [Troubleshoot Azure WAF Policies](https://learn.microsoft.com/azure/web-application-firewall/ag/web-application-firewall-troubleshoot)

- [Azure WAF Policy Basics](https://learn.microsoft.com/azure/web-application-firewall/ag/policy-overview)

### Customer Solution

*Content type: MarkdownText*

### Unexpected behavior due to Global Parameters

Incorrect or conflicting global parameters can cause unexpected WAF behavior, such as blocking allowed requests or missed detections.

- **Common causes:**

  - Enabling global checks that conflict with custom rules.

  - Misconfiguration of request body size limits.

**Solutions:**

- Audit all global parameter settings for conflicts.

- Temporarily disable suspicious parameters to isolate issues.

- Use Detection mode to monitor before enforcing.

**Step-by-step solution:**

1. Export current WAF policy and review global parameters.

2. Disable parameters one at a time to identify root cause.

3. Switch WAF policy to Detection mode and monitor.

4. Adjust or update parameters based on findings.

For more information, see:

- [Troubleshoot Azure WAF Policies](https://learn.microsoft.com/azure/web-application-firewall/ag/web-application-firewall-troubleshoot)

- [Azure WAF Policy Basics](https://learn.microsoft.com/azure/web-application-firewall/ag/policy-overview)

---
