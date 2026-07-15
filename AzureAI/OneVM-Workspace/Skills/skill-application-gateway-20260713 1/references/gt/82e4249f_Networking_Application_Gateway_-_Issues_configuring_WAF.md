# Networking] Application Gateway - Issues configuring WAF

> **Product:** Application Gateway  
> **Solution ID:** 82e4249f-053c-4308-9f97-c209dcd8fd57  
> **Trigger words:** application, application gateway, configuring, gateway, networking]

---

## Overview

This guide provides step-by-step troubleshooting for **Networking] Application Gateway - Issues configuring WAF** under **Application Gateway**.
 The original guided troubleshooter contains 15 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Application Gateway WAF configuration issues TSG Scope Check ⭐ (First Step)

### Guidance

# Check if this TSG applies to the customer scenario

## Verify if the customer issues matches this TSG

This TSG is specific to Application Gateway "WAF configuration" issues. It is applicable to the below mentioned support topic.

* Application Gateway/Web Application Firewall (WAF)/Configure WAF

**Note**  
If your issue is not from the list above, you may use **Edit & Run Again** feature on the **ASC** to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results.

### Recommended documents

* [Azure Application Gateway documentation](https://docs.microsoft.com/en-us/azure/application-gateway/)
* [WAF engine on Azure Application Gateway](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/waf-engine)
* [Web Application Firewall CRS rule groups and rules](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules?tabs=owasp32)
* [Azure Web Application Firewall (WAF) policy overview](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/policy-overview?source=recommendations)
* [Tutorial: Create an application gateway with a Web Application Firewall using the Azure portal](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-web-application-firewall-portal)

### Question

**Is the customer experiencing issues configuring the Application Gateway WAF**

### Options

- **Yes** → Go to: *check the Application Gateway SKU*
- **No** → Go to: *2c6753c5-262d-4e00-bd88-e017d9c2b337*

---

### Step 2: Exclusion list

### Support Engineer Solution

We have some public documentation on how the Exclusion lists work and how to configure them:
- [Web Application Firewall exclusion lists](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-configuration?tabs=portal)

### Customer Solution

*Content type: MarkdownText*

We have some public documentation on how the Exclusion lists work and how to configure them:
- [Web Application Firewall exclusion lists](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-configuration?tabs=portal)

---

### Step 3: Request size limits

### Support Engineer Solution

We have some public documentation on what are the request size limits and how to change them:</br>
 - [Web Application Firewall request size limits](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits)

### Customer Solution

*Content type: MarkdownText*

We have some public documentation on what are the request size limits and how to change them:</br>
 - [Web Application Firewall request size limits](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits)

---

### Step 4: Enable the WAF

### Support Engineer Solution

It seems this Application Gateway has the right SKU, but the WAF feature is currently disabled.
Ask the customer to enable the WAF features.
This can be done through the Azure Portal, on the Application Gateway page.
Go to the "Web application firewall" blade under "Settings" and change the "WAF mode" to "Enabled".

### Customer Solution

*Content type: MarkdownText*

It seems your Application Gateway has the right SKU, but the WAF feature is currently disabled.</br>
You can enable it through the Azure Portal, on the Application Gateway page.</br>
Go to the "Web application firewall" blade under "Settings" and change the "WAF mode" to "Enabled".

---

### Step 5: Configure custom rules

### Support Engineer Solution

We have some public documentation with some examples on how to configure custom rules:</br>
 - [Custom rules for Web Application Firewall v2 on Azure Application Gateway](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/custom-waf-rules-overview)</br>
 - [Create and use Web Application Firewall v2 custom rules on Application Gateway](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/create-custom-waf-rules)</br>
 - [Geomatch custom rules](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/geomatch-custom-rules)

### Customer Solution

*Content type: MarkdownText*

We have some public documentation with some examples on how to configure custom rules:</br>
 - [Custom rules for Web Application Firewall v2 on Azure Application Gateway](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/custom-waf-rules-overview)</br>
 - [Create and use Web Application Firewall v2 custom rules on Application Gateway](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/create-custom-waf-rules)</br>
 - [Geomatch custom rules](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/geomatch-custom-rules)

---

### Step 6: Enable and Disable WAF rules

### Support Engineer Solution

We have some public documentation on the WAF rules and how to enable disable them.</br>
We do advise to have all rules enabled, but in case cx wants to change some rules, here is some information on the rules and how to enable/disable them:</br>
- [Web Application Firewall CRS rule groups and rules](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules?tabs=owasp32)</br>
- [Customize Web Application Firewall rules using the Azure portal](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-customize-waf-rules-portal)</br>

### Customer Solution

*Content type: MarkdownText*

Please go through these documents on the OWASP rules used and how to enable or disable specific ones:</br>
- [Web Application Firewall CRS rule groups and rules](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules?tabs=owasp32)</br>
- [Customize Web Application Firewall rules using the Azure portal](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-customize-waf-rules-portal)</br>

---

### Step 7: Change WAF mode to Prevention

### Support Engineer Solution

If the customer is complaining the WAF isn't blocking any malicious requests and the WAF mode is detection, then that is the issue.
detection mode should only be logging the requests.
Ask the customer to change the WAF mode from Detection to Prevention.

### Customer Solution

*Content type: MarkdownText*

We have detected that your WAF is currently set to Detection, which means it will only log any WAF violation, but it will still allow it through.
In order to block these malicious requests you need to change your WAF mode from Detection to Prevention.

---

### Step 8: Migrate to WAF policy

### Support Engineer Solution

We have some public documentation on how to migrate to a WAF Policy:</br>
- [Migrate Web Application Firewall policies using Azure PowerShell](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/migrate-policy)

It is also possible to migrate it through the Azure Portal, by going to the Application Gateway's page, clicking on "Web application firrewall". And there you have a button with "Upgrade from WAF configuration"

### Customer Solution

*Content type: MarkdownText*

We have some documentation on how to migrate to a WAF Policy:</br>
- [Migrate Web Application Firewall policies using Azure PowerShell](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/migrate-policy)

It is also possible to migrate it through the Azure Portal, by going to the Application Gateway's page, clicking on "Web application firrewall". And there you have a button with "Upgrade from WAF configuration"

---

### Step 9: How to no covered in TSG

### Support Engineer Solution

It seems the feature the customer wants to implement is not covered on this Wiki.
Please select the frown on the TSG feedback form and explain what WAF scenario is missing from this TSG.
<br>Please search the Application Gateway WAF documentation for guidance on how to implement the requested feature: [What is Azure Web Application Firewall on Azure Application Gateway?](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/ag-overview)
<br>Use the "Filter" bar on the left to search within the WAF documents, by title.
<br>You can also use the "Download PDF" button at the bottom left to search the entire WAF documentation for a specific key word or phrase.
<br>If you still can't find any information, please post the ask on the Application Gateway Teams Channel: [AppGtw Teams channel](https://teams.microsoft.com/l/channel/19%3a47d113be696e4d9a8246eacc76497bbb%40thread.skype/%255BL7%255D%2520Application%2520Gateway?groupId=c3e00ac7-3f76-4350-ba3b-e335a6bbbe21&tenantId=72f988bf-86f1-41af-91ab-2d7cd011db47)

### Customer Solution

*Content type: MarkdownText*

N/A

---

### Step 10: Upgrade Application Gateway SKU to WAFWAFv2

### Support Engineer Solution

In order to use the WAF capabilities the APplication Gateway needs to have the appropriate SKU, which is WAF or WAF_v2.
</br>Ask the customer to upgrade the Application Gateway SKU.
</br>This can be done on the Azure Portal on the Application Gateway's page, on the Configuration blade.
</br>Change the "Tier" option from Standard to WAF, or Standard V2 to WAF V2.

### Customer Solution

*Content type: MarkdownText*

It seems your current Application Gateway SKU doesn't support the WAF capabilities.
</br>This can be solved by upgrading the Application Gateway's SKU to WAF or WAFv2 (depending if you have a v1 or v2 gateway).
</br>To achieve this you can do the follwoing:</br>
1. Go to the Azure Portal</br>
2. open your Application Gateway's page</br>
3. click on "Configuration" (it's on the left side blade)</br>
4. under "Tier" change the value to WAF (or WAF V2).

---

### Step 11: Check if WAF is enabled

### Content

# Check if the WAF is enabled on the Application Gateway
1. On ASC go to the Application Gateway page.
2. Go to the "Properties" blade
3. Scroll down to "WAF Config"
4. Check the "Enabled" parameter

If it is True then the WAF is enabled, if it is False it is not.

---

### Step 12: Check if WAF is in prevention mode

### Content

# Is the WAF not blocking any requests?
Is the WAF not blocking any requests?</br>
If the WAF is in Detection mode it will not block any requests, it will only log them.</br>
1. Go to ASC, to the Application Gateway's page</br>
2. Go to the "Properties" blade</br>
3. Scroll down to "WAF Config" section</br>
4. Check the "Firewall mode"</br>

If it is already in Prevention mode then please select the "Prevention" option to proceed to the "Troubleshoot WAF responses" TSG.

---

### Step 13: Check if cx wants to troubleshoot WAF decisions

### Guidance

# Is the customer seeing the WAF blocking legitimate traffic or allowing malicious requests?

Once the WAF is fully configured and running, sometimes the customers might see some unexpected blocks or allows.
If the WAF is blocking traffic that should be legitimate, this is called a False Positive detection.
If the WAF is allowing harmful or malicious requests this is called a False negative.
For both these issues you need to follow the appropriate TSG for troubleshooting WAF responses.

### Question

**Does the customer want to troubleshoot unexpected WAF responses?**

### Options

- **Yes** → Go to: *Check if WAF is in prevention mode*
- **No** → Go to: *HOW TOs*

---

### Step 14: check the Application Gateway SKU

### Content

# Check if the Application Gateway has the right SKU
1. On ASC go to the Application Gateway page.
2. Go to the "Properties blade" blade
3. Look for "SKU type"

If it is WAF or WAF_v2, then this Application Gateway has the right SKU.

---

### Step 15: HOW TOs

### Question

**Does the customer need assistance configuring on the following features?**

### Options

- **How to configure custom rules** → Go to: *Configure custom rules*
- **How to migrate to a WAF policy** → Go to: *Migrate to WAF policy*
- **How to enable or disable rules** → Go to: *Enable and Disable WAF rules*
- **How to configure an exclusion** → Go to: *Exclusion list*
- **How to change Request size limits** → Go to: *Request size limits*
- **Feature not covered by this TSG** → Go to: *How to no covered in TSG*

---
