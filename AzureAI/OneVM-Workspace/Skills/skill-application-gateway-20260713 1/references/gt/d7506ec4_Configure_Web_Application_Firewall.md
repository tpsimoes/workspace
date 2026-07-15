# Configure Web Application Firewall

> **Product:** Application Gateway  
> **Solution ID:** d7506ec4-8639-4a42-85bb-196a874658be  
> **Trigger words:** application, application gateway, configure, firewall

---

## Overview

This guide provides step-by-step troubleshooting for **Configure Web Application Firewall** under **Application Gateway**.
 The original guided troubleshooter contains 20 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Scope of WAF configuration ⭐ (First Step)

### Guidance

The Web Application Firewall (WAF) provides centralized protection of your web applications from common exploits and vulnerabilities. To assist you in resolving common configuration issues, select the specific area where you're experiencing problems.

### Question

**Which area of your WAF configuration would you like to address?**

### Options

- **Initial WAF configuration** → Go to: *Check tier*
- **Managed ruleset** → Go to: *Managed ruleset*
- **Custom rule** → Go to: *Custom rule*
- **BOT protection** → Go to: *BOT protection*
- **None of the above** → Go to: *None of the above*

---

### Step 2: Check tier

### Guidance

The tier of your Application Gateway determines whether you're using WAF or WAFv2. Confirming the tier is essential for proceeding with the appropriate troubleshooting steps.

**To check if the Application Gateway tier is WAF or WAFv2**:

1. Navigate to **Application Gateway** > **Settings** > **Configuration**.

2. Look for the **Tier** field and see if it's **WAF** or **WAFv2**.

### Question

**Is your Application Gateway configured with the WAF or WAFv2 tier?**

### Options

- **Yes** → Go to: *Check if WAF policy is associated*
- **No** → Go to: *Upgrade Application Gateway tier to WAF or WAFv2*

---

### Step 3: Check if WAF policy is associated

### Guidance

Ensuring that your WAF policy is correctly associated with the application gateway, listener, or route path is essential for proper functionality.

To verify the WAF policy associated with the application gateway:

1. Navigate to **Application Gateway** > **Settings** > **Web Application Firewall**.

2. Check if the correct Web Application Firewall policy is linked. If it is, you'll see a reference to the associated WAF policy.

To verify the WAF policy associated with a listener or route path, you must first know the name of the policy.

1. Navigate to **Web Application Firewall** > **Settings** > **Associations**.

2. The **Association Type** will indicate whether it's linked to an **HTTP listener** or a **route path**.

If you’re using a legacy WAF configuration (local to the application gateway), you won’t see a WAF policy reference—only the WAF configuration itself. In that case, you can skip this step.

### Question

**Is the WAF policy correctly associated with the application gateway, listener, or route path?**

### Options

- **Yes** → Go to: *Check WAF state*
- **No** → Go to: *Associate WAF policy*
- **Skip (if you're going to use a legacy WAF for now)** → Go to: *Check WAF state*

---

### Step 4: Check WAF state

### Guidance

Ensuring that the WAF is enabled is crucial for protecting your applications from malicious traffic. If the WAF is not enabled, it will not block any traffic, leaving your applications vulnerable.

**Steps to verify if WAF is enabled:**

1. Navigate to your **Web Application Firewall** >  **Overview**.

2. Verify that the **Policy State** is set to **Enabled**.

**For legacy WAF configurations within Application Gateway:**

1. Go to **Application Gateway** > **Settings** > **Web Application Firewall**.

2. Ensure that the **WAF Status** is set to **Enabled**.

### Question

**Is the WAF policy enabled or disabled?**

### Options

- **Enabled** → Go to: *Verify WAF mode*
- **Disabled** → Go to: *WAF state is disabled*

---

### Step 5: Verify WAF mode

### Guidance

The WAF mode determines how it handles incoming traffic—whether it actively blocks threats or merely logs and monitors them.

 

**To verify the WAF mode:**

1. Navigate to your **Web Application Firewall** > **Overview**.

2. Verify the **Policy Mode**.

**For legacy WAF configurations within Application Gateway:**

1. Navigate to **Application Gateway** > **Settings** > **Web application firewall**.

2. Look for **WAF Mode**.

**Resources:**

- [WAF modes](https://learn.microsoft.com/azure/web-application-firewall/ag/ag-overview#waf-modes)

### Question

**Is the WAF mode set to Prevention or Detection?**

### Options

- **Prevention** → Go to: *Prevention mode*
- **Detection** → Go to: *Detection mode*

---

### Step 6: Upgrade Application Gateway tier to WAF or WAFv2

### Support Engineer Solution

If your Application Gateway is not configured with WAF or WAFv2 Tier, upgrading is essential to utilize Web Application Firewall(WAF) features and ensure robust protection for your Web Applications.

# **To upgrade your Application Gateway Tier to WAF or WAFv2**:
- Navigate to **Application Gateway > Settings > Web application firewall >** select **WAF V2**.
- Here you will have the option to creat a new WAF policy or associate an existing one. 

**If you already have a WAF policy:**
- The dropdown will show the available WAF policies.
- Select the correct WAF policy.
- Save the changes.

**If you do not have a WAF policy created:**
- select **Create new**.
- Provide a **Name** for the new WAF policy.
- Select **OK**.
- Save the changes.

# **After upgrading the Tier:**

If you still face issues, Rerun diagnostics and proceed with the subsequent checks to ensure your WAF configuration is properly set up.

### Customer Solution

*Content type: MarkdownText*

If your Application Gateway is not configured with WAF or WAFv2 tier, upgrading is essential to utilize WAF features and ensure robust protection for your web applications.

### Upgrade your Application Gateway tier to WAF or WAFv2

1. Navigate to **Application Gateway** > **Settings** > **Web application firewall** > select **WAF V2**.

2. Here you'll have the option to create a new WAF policy or associate an existing one. 

**If you already have a WAF policy:**

The dropdown menu will show the available WAF policies.

1. Select the correct WAF policy.

2. Save the changes.

**If you do not have a WAF policy created:**

1. Select **Create new**.

2. Provide a **Name** for the new WAF policy.

3. Select **OK**.

4. Save the changes.

### After upgrading the tier

If you still face issues, rerun diagnostics and proceed with the subsequent checks to ensure your WAF configuration is properly set up.

---

### Step 7: WAF state is disabled

### Support Engineer Solution

Your *Web Application Firewall(WAF)* is currently disabled, which means your applications are not protected from potential threats. Enabling WAF is crucial to ensure that your web applications are secure.

# **To enable Web Application Firewall(WAF)**:

- Navigate to your **Web Application Firewall(WAF) > Overview section**.

- Select "**Enable**".

- Verify that the Policy State is set to "**Enabled**".

*For legacy Web Application Firewall (WAF) configurations within Application Gateway*

- Navigate to the **Application Gateway > Settings > Web Application Firewall**.

- Click on the Toggle for WAF Status "**Enable**" & hit "**Save**"

- Verify that the WAF State is set to "**Enabled**".

**After the WAF State is Enabled**:

If you still face issues, rerun diagnostics and proceed with the subsequent checks to ensure your WAF configuration is properly set up.

### Customer Solution

*Content type: MarkdownText*

Your WAF is currently disabled, which means your applications are not protected from potential threats. Enabling WAF is crucial to ensure that your web applications are secure.

**Steps to enable WAF:**

1. Navigate to your **Web Application Firewall** > **Overview**.

2. Select **Enable**.

3. Verify that the **Policy State** is set to **Enabled**.

**For legacy WAF configurations within Application Gateway:**

1. Navigate to the **Application Gateway** > **Settings** > **Web Application Firewall**.

2. Select **Enable** for **WAF Status**, then select **Save**.

3. Verify that the WAF state is set to **Enabled**.

**After the WAF state is enabled:**

If you still face issues, rerun diagnostics and proceed with the subsequent checks to ensure your WAF configuration is properly set up.

---

### Step 8: Associate WAF policy

### Support Engineer Solution

Properly associating your Web Application Firewall(WAF) policy with the Application Gateway, Listener, or Route Path is essential for ensuring that the Web Application Firewall operates as intended and provides the necessary protection.

# **To Associate Web Application Firewall(WAF) Policy**

- Navigate to your **Web Application Firewall(WAF) > Associations > Add association**

- Add Association with respective *Application Gateway or Listener or Route Path* as per your requirement.

- Save the configuration and verify that the association is now displayed.

# **After associating Web Application Firewall(WAF):**

If you continue to face issues, rerun diagnostics and proceed with additional checks to ensure your WAF configuration is correctly set up.

### Customer Solution

*Content type: MarkdownText*

Properly associating your WAF policy with the application gateway, listener, or route path is essential for ensuring that the WAF operates as intended and provides the necessary protection.

**Steps to associate a WAF policy:**

1. Navigate to your **Web Application Firewall** > **Associations** > **Add association**.

2. Add an association with the respective application gateway, listener, or route path, as per your requirement.

3. Save the configuration and verify that the association is now displayed.

**After associating WAF:**

If you continue to face issues, rerun diagnostics and proceed with additional checks to ensure your WAF configuration is correctly set up.

---

### Step 9: Prevention mode

### Support Engineer Solution

When the *Web Application Firewall (WAF)* operates in *Prevention Mode*, any request that violates the configured rules — whether from managed or custom rule sets — is blocked. The attacker receives a **"403 Forbidden response"**, and the connection is immediately terminated. All blocked requests are recorded in the *Application gateway Firewall(WAF)* logs. 

In **Prevention Mode**:

- **Anomaly Score** is the default action for the WAF Managed Rules Microsoft Default Rule Set (DRS) and OWASP **RuleSet**. Each time a rule is triggered, the total anomaly score increases. Note that anomaly scoring does **not** apply to the **BOT Manager RuleSet**.

- Each request is logged with a **Transaction ID** and evaluated against all applicable rules. Every triggered rule contributes a severity-based score to the transaction.

- The log message will include the action value *"Matched"* for the triggered rule, and **total anomaly score** is the sum of all triggered rule severities. If this total reaches **5 or higher**, a mandatory anomaly rule will trigger with the action value *"Blocked"* and the request is blocked

**Note:** To change the default action of a rule, navigate to:

**WAF Policy > Settings > Managed Rules > [Select the rule you want to modify] > Change Action.**

The available action options are:

- **Anomaly Score**
- **Log**
- **Block**

More resources:

- [What is Azure Web Application Firewall on Azure Application Gateway?](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/ag-overview)

- [Anomaly scoring mode](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/ag-overview#anomaly-scoring-mode)

- [WAF log category](https://learn.microsoft.com/en-us/azure/application-gateway/monitor-application-gateway-reference#firewall-log-category)

- [Enable logging through the Azure portal](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-diagnostics#enable-logging-through-the-azure-portal)

- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

When the WAF operates in *Prevention mode*, any request that violates the configured rules—whether from managed or custom rule sets—is blocked. The attacker receives a "403 Forbidden response," and the connection is immediately terminated. All blocked requests are recorded in the Application Gateway WAF logs. 

**In Prevention mode:**

- *Anomaly score* is the default action for the WAF managed rules Microsoft default rule set (DRS) and Open Web Application Security Project (OWASP) Rule Set. Each time a rule is triggered, the total anomaly score increases. Note that anomaly scoring does *not* apply to the BOT Manager Rule Set.

- Each request is logged with a Transaction ID and evaluated against all applicable rules. Every triggered rule contributes a severity-based score to the transaction.



*(Content truncated — refer to original GT for full details)*

### Step 10: Detection mode

### Support Engineer Solution

When the Web Application Firewall (WAF) is set to "***Detection mode***", it logs any traffic that triggers its rules but does not block those requests. All traffic will continue to pass through the Application Gateway to your backend.

To ensure that malicious traffic is blocked, switch the Web Application Firewall(WAF) to "***Prevention mode***".

**To configure Prevention mode**:
- Navigate to **Web application firewall > Overview**
- Switch the mode to Prevention.
- Verify the Policy mode under Overview Section to confirm the update.

**Note**: Enabling Prevention Mode ensures that traffic violating WAF rules is blocked, providing stronger protection for your applications.

### Customer Solution

*Content type: MarkdownText*

When the WAF is set to *Detection mode*, it logs any traffic that triggers its rules but does not block those requests. All traffic will continue to pass through the application gateway to your backend.

To ensure that malicious traffic is blocked, switch the WAF to *Prevention mode*.

**To configure Prevention mode:**

1. Navigate to **Web application firewall** > **Overview**.

2. Switch the mode to **Prevention**.

3. Verify the policy mode under the **Overview** section to confirm the update.

**Note**: Enabling Prevention mode ensures that traffic violating WAF rules is blocked, providing stronger protection for your applications.

---

### Step 11: Managed ruleset

### Guidance

*Managed rule sets* are predefined sets of rules designed to protect your web applications from common threats. Proper management and debugging of these rule sets are essential for ensuring optimal security and functionality of your WAF.

- **OWASP Core Rule Sets (CRS)**: These include predefined rules based on OWASP standards, which are designed to protect against various web application attacks. Available versions are 3.2, 3.1, and 3.0.

- **Default Rule Set (DRS)**: The default rule set includes a collection of rules maintained by the Microsoft Threat Intelligence team that offer baseline protection against known threats and vulnerabilities. Available versions: Microsoft_DefautRuleSet_2.1.

**Resources:**

- [Web Application Firewall DRS and CRS rule groups and rules](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules?tabs=drs21%2Cowasp32)

### Question

**Which aspect of the managed rule set are you currently focused on?**

### Options

- **Debugging Web Application Firewall** → Go to: *5bfa47ab-c303-46ac-8aec-895fb56d6c1d*
- **Configuring or managing a managed rule set** → Go to: *Configuring managing managed ruleset*

---

### Step 12: Configuring managing managed ruleset

### Guidance

Configuring and managing *managed rule sets* in WAF involves setting up and adjusting rules to protect your web applications effectively. 

This includes creating exclusions for specific traffic and modifying rule behaviors to fine-tune security.

To assist you in resolving common configuration issues, select the specific area where you're experiencing problems.

### Question

**Where are you facing issues while configuring the managed rule set?**

### Options

- **Creating exclusions** → Go to: *Managed ruleset create exclusions*
- **Enabling, disabling, or modifying rule ID behavior** → Go to: *Modify rule ID behavior*

---

### Step 13: Managed ruleset create exclusions

### Support Engineer Solution

Creating exclusions within your Managed Rule-Set in *Azure Web Application Firewall(WAF)* allows you to fine-tune security by bypassing certain rules for specific traffic scenarios.<br> 

This is particularly useful for reducing false-positive or addressing specific application.

# ***To Create an Exclusion*** 
- Navigate to your Web Application Firewall (WAF) policy settings.
- Go to the Managed Rules section.
- Click on Exclusions and then Add exclusion.

**Select the Scope for Exclusion**:

Exclusions can be configured to apply to a specific set of WAF rules, to rulesets, or globally across all rules

- **Global**: Applies this exclusion across all WAF rules

- **Per-Rule Exclusion**: You can configure an exclusion for a specific rule, group of rules, or rule set. (Available in CRS 3.2, DRS, or BOT Manager 1.0 and later versions.)

If you select **Per-Rule Exclusion** (e.g., CRS/DRS/BOT Manager rule set), add the specific Rule ID(s) to which you want the exclusion to apply.

**Define Match Variable**:
- Request Header Key
- Request Header Name/Value
- Request Cookie Key
- Request Cookie Name/Value
- Request Arg Key
- Request Arg Name/Value

**Note**: Currently, request attributes by name function the same as those by value and are included solely for backward compatibility with CRS 3.1 versions. 

**For example**, 

- Suppose, you have a header:<br>

"My-Header: 1=1"
- Where WAF detects the value but you know it’s legitimate for your scenario, configure the exclusion as:<br>

RequestHeaderValue contains My-Header

- This stops evaluation of all values for the header **"My-Header"**. As mentioned, you cannot create an exclusion for a specific section of its value using Managed Exclusion.
- Conversely, if WAF flags the header name "**My-Header**" as an attack, you can configure an exclusion for the Header Key under RequestHeaderKeys. This is available only in CRS 3.2/DRS/BOT Manager 1.0.

# **Learn More:**
To understand how different match variables work for different attributes, refer to the [Web Application Firewall exclusion lists
](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-waf-configuration?tabs=portal)

# ***Still need help?***
If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)  
- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)
- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

Creating exclusions within your managed rule set in Azure Web Application Firewall allows you to fine-tune security by bypassing certain rules for specific traffic scenarios.

This is particularly useful for reducing false-positives or addressing a specific application.

**Steps to cre

*(Content truncated — refer to original GT for full details)*

### Step 14: Modify rule ID behavior

### Support Engineer Solution

 In *Web Application Firewall (WAF)*, managing Rule ID behavior allows you to fine-tune your security settings by enabling, disabling, or modifying how individual rules are applied. <br>

### **To Enable/Disable a Rule ID**

- Navigate to your *Web Application Firewall(WAF)* policy settings.

- Go to the *Managed Rules* section.

- Under *Managed Rulesets*, click on the dropdown for RuleSet.

- Identify the specific *Rule ID* you want to disable.

- Once selected, click *Disable* option above the Rule-sets. This action will disable the rule, preventing it from being evaluated in the WAF.

For further information you can refer, **[Disable rule groups and rules](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-customize-waf-rules-portal#disable-rule-groups-and-rules)**

### **With DRS, CRS 3.2 and Newer**

In addition to enabling or disabling a rule, with CRS 3.2 and newer versions, you have the flexibility to adjust the action taken when a particular Rule ID is triggered. You can choose from the following options:

- ***Anamoly Score(Default)***: The WAF uses an anomaly scoring system to determine the severity of potential threats. Each rule that matches incoming traffic contributes to the overall anomaly score based on its severity:

| **Severity** | **Value** |

|:------------:|:---------:|

|   Critical   |     5     |

|     Error    |     4     |

|    Warning   |     3     |

|    Notice    |     2     |

There is a threshold of 5 for blocking traffic. 

For example, a single Critical rule match (score 5) is enough to block a request, in Prevention mode. However, a Warning rule match (score 3) will not block the traffic unless combined with other rules that push the score above 5.

- ***Block***: Immediately block any request that triggers the selected Rule ID. This option ensures that potentially harmful traffic is stopped at the perimeter.

- ***Log***: This option logs the occurrence of a rule match without blocking the traffic. The request bypasses the anomaly score, making it suitable for monitoring and auditing without impacting the user experience.

- ***Allow*** (DRS rules only): This option allows the traffic that matches the rule to bypass inspection by the WAF. Use this when you recognize the traffic as legitimate, preventing unnecessary blocks.

For more information on CRS, DRS & BOT managed rule-sets you may refer: [Web Application Firewall DRS and CRS rule groups and rules](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules?tabs=drs21)

### ***Still need help?***

If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)  

- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](http://portal.azure.com

*(Content truncated — refer to original GT for full details)*

### Step 15: Custom rule

### Guidance

*Custom rules* in Azure Web Application Firewall let you define specific conditions to allow, block, or log requests. They also support combining multiple conditions using logical operators, making it possible to create more advanced rules to address complex security requirements.

### Important considerations

- **Priority**: Custom rules are evaluated in the order of priority, from lowest to highest. Ensure that your rules are correctly prioritized to prevent unintended behavior.

- **Combining with managed rules**: Custom rules are evaluated before managed rules. If a custom rule allows or blocks traffic, the managed rules will not be evaluated for that traffic.

### Question

**Which aspect of custom rule are you currently focused on?**

### Options

- **Configuring and managing custom rules** → Go to: *Configuring and managing custom rules*
- **Geo-location rule** → Go to: *Geolocation rule*
- **Rate-limit rule** → Go to: *Rate limiting rule*

---

### Step 16: Configuring and managing custom rules

### Support Engineer Solution

***Custom Rule*** allows us to enable effective traffic management by configuring *Azure Web Application Firewall(WAF)* custom rules to bypass, block, or log traffic based on specific content criteria. 

# ***Step to configure Custom Rule***:
- Go to the *Web Application Firewall policy*
- Navigate to Custom Rules and click "*Add Custom Rule*"
- Give the custom rule a name.
- Set *Rule Priority* for your rule. 

**Match Type**:<br>
It specified type of data this rule condition should evaluate for a match: 
- **IP Addresses**:  Match requests based on the Source IP address or Range. You may use this to Allow or block traffic from specific IP addresses. 
- **Geo-Location**: Match requests based on the geographical location of the IP address. You may use this to Allow or block traffic from specific countries or regions.
- **String**: Match requests based on specific text in the request, such as URIs, headers, or query parameters. You may use this to Allow or block traffic with specific URLs, headers, or query strings.
- **Number**: Match requests based on numerical values in query parameters or request bodies. You may use this to Allow or block traffic with specific numerical IDs or values.

**Match Variables** (must be one of the variables):<br> 
- **RemoteAddr** - IPv4 Address/Range of the remote computer connection.
- **RequestMethod** - HTTP Request method (example, GET, POST).
- **QueryString** – Variable in the URI
- **PostArgs** – Arguments sent in the POST body. Custom Rules using this match variable are only applied if the 'Content-Type' header is set to 'application/x-www-form-urlencoded' and 'multipart/form-data.' Additional content type of application/json is supported with CRS version 3.2 or greater, bot protection rule set, and geo-match custom rules.
- **RequestUri** – URI of the request
- **RequestHeaders** – Headers of the request
- **RequestBody** – This variable contains the entire request body as a whole. Custom rules using this match variable are only applied if the 'Content-Type' header is set to application/x-www-form-urlencoded media type. Additional content types of application/soap+xml, application/xml, text/xml are supported with CRS version 3.2 or greater, bot protection rule set, and geo-match custom rules.
- **RequestCookies** – Cookies of the request

**Actions**<br>
- **Allow** – Authorizes the request and skips evaluation of all other rules & managed Rules.
- **Block** -  Blocks or logs the transaction based on SecDefaultAction (detection/prevention mode). 
- **Log** –  Logs the transaction, and continues the evaluation for rest of the rules in order of priority, followed by managed Rules. 

# ***Important Considerations***:
- Custom Rules are evaluated based on their priority. Rules with a higher priority are evaluated before those with a lower priority.
- Be cautious with exceptions in rules, as they can bypass security measures.
- Utilize these variables alone or in combination to pr

*(Content truncated — refer to original GT for full details)*

### Step 17: Geolocation rule

### Support Engineer Solution

Creating a *Geo-Location Custom Rule* in *Azure Web Application Firewall(WAF)* allows you to restrict access to your web application based on the geographic location of incoming requests. 

# ***Steps to Create a Geo-Location Custom Rule***:
- Navigate to your *Web Application Firewall(WAF) policy* in the Azure portal.
- Go to Custom Rules and click "Add Custom Rule".
- Select **Geo Location** as the **Match Type**.
- Choose the *countries/regions* you want to allow or block from accessing your application.
- Include the *country code ZZ or Unknown* to capture *IP Addresses* not yet mapped to a country, avoiding false positives.
- Assign a priority to the rule. Lower values indicate higher priority. Ensure the priority is unique across all custom rules.
- Save the rule and test it in a non-production environment to ensure it works as expected.

# ***Example Scenarios***
- **Block Traffic from Specific Countries**: You can block traffic from countries known for malicious activities while allowing traffic from trusted regions.
- **Allow Traffic Only from Specific Countries**: For applications that should only be accessed from certain regions, you can allow traffic exclusively from those countries.
- **Block/Allow if specific header is required from a country**: Say, you want the request to be allowed from a certain region only if it brings a specific Cookie or Header Value

# **Reference**:
[Geomatch Custom Rules](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/geomatch-custom-rules)<br>

[Geomatch Custom Rules Examples](https://learn.microsoft.com/en-us/azure/web-application-firewall/geomatch-custom-rules-examples)

# ***Still need help?***
If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)  
- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)
- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

Creating a *geo-location custom rule* in Azure Web Application Firewall allows you to restrict access to your web application based on the geographic location of incoming requests. 

### Steps to create a geo-location custom rule

1. Navigate to your WAF in the Azure portal.

2. Go to **Custom rules** and select **Add custom rule**.

3. Select **Geo Location** as the **Match Type**.

4. Choose the **countries/regions** that you want to allow or block from accessing your application.

5. Include the **country code ZZ or Unknown** to capture IP addresses not yet mapped to a country, avoiding false positives.

6. Assign a priority to the rule. Lower values indicate higher priority. Ensure the priority is unique across all custom rules.

7. Save the rule and test it in a non-production environment to en

*(Content truncated — refer to original GT for full details)*

### Step 18: Rate limiting rule

### Support Engineer Solution

Rate limiting helps detect and block unusually high traffic levels targeting your application. By using rate limiting on Application Gateway WAF_V2, you can mitigate Layer 7 denial-of-service (DoS) attacks, protect your application from sudden bursts of requests, and regulate traffic originating from specific geographic locations.

# ***Key Concepts***:
- **Threshold Tracking**: Rate limit thresholds are counted and tracked independently for each endpoint where the WAF policy is applied. For example, a single WAF policy on five listeners will maintain separate counters and thresholds for each listener.
- **Sliding Window Algorithm**: During the initial window where the request threshold is exceeded, traffic matching the rate limit rule is dropped. In subsequent windows, traffic up to the threshold is allowed, creating a throttling effect.

# ***How to Configure Rate Limiting***:
- Navigate to your Web Application Firewall(WAF) policy in the Azure portal.
- Go to Custom Rules and click "Add Custom Rule"

- Set the rule type to ***Rate Limit***.

- **Group Rate Limit Traffic By**: Choose how to group rate-limited traffic:
    - **ClientAddr(Default)**: Applies the rate limit independently to each unique source IP address.
    - **Geo-Location**: Groups traffic by geographic location based on a Geo Match on the client IP address.
    - **None**: Groups all traffic together, counting it against the rate limit threshold without maintaining separate counters for each IP address or geography. Recommended for specific scenarios like login pages or suspicious User-Agents.

# ***Set Rate Limit Parameters***:
**Rate Limit Duration**: Define the counting duration for the rate limit. Allowed values are 1 minute or 5 minutes.
Rate Limit Threshold (Requests): Enter the maximum number of requests allowed within the specified duration. Valid values range from 1 to 5000 requests.

**Reference**:<br>
[Rate Limiting Overview](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/rate-limiting-overview)<br>
[Configure Rate Limiting](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/rate-limiting-configure?tabs=browser)

# ***Still need help?***
If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)  
- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)
- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

Rate limiting helps detect and block unusually high traffic levels targeting your application. By using rate limiting on Application Gateway WAF_V2, you can mitigate Layer 7 denial-of-service (DoS) attacks, protect your application from sudden bursts of requests, and regulate traffic originating from sp

*(Content truncated — refer to original GT for full details)*

### Step 19: BOT protection

### Support Engineer Solution

**Bot Protection Rule Set** for *Web Application Firewall(WAF)* works in conjunction with DRS or OWASP rule sets and it provides protection against malicious bots and detection of good bots. 
The rules provide granular control over bots detected by WAF by categorizing bot traffic as Good, Bad, or Unknown bots. WAF platform dynamically updates bot signatures to ensure effective protection.

# ***Steps to enable BOT Protection***:
- Navigate to the *Web Application Firewall*
- Select *Managed Rules* & Click "*Assign*"
- From the dropdown select the version of the BOT protection rule set you want to use.
Note: We recommend always using the most up-to-date rule version.

**Rule Group:**
- **Bad Bots**: Protect against Malicious bots with harmful intentions or falsified identities.
- **Good Bots**: Identify good bots.
- **Unknown Bots**: Identify unknown bots.

**Custom Actions for each BOT category:**
- **Block**: Deny access to the request.
- **Allow**: Permit the request to proceed.
- **Log**: Record the request for monitoring purposes.
- **JS Challenge**: Present a JavaScript challenge to verify if the request is from a legitimate bot.

**Note**
Azure JavaScript Challenge is currently in preview. To know more about this feature you can  refer article: [Azure JavaScript Challenge](https://learn.microsoft.com/en-us/azure/web-application-firewall/waf-javascript-challenge).

# ***Reference***:
[BOT Protection Overview](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/bot-protection-overview)

[Configure bot protection for Web Application Firewall](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/bot-protection)

# ***Still need help?***
If you still need help with your issue, you can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)  
- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)
- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

The *Bot Protection rule set* for WAF works in conjunction with DRS or OWASP rule sets, and it provides protection against malicious bots and detection of good bots. 

The rules provide granular control over bots detected by WAF by categorizing bot traffic as good, bad, or unknown bots. The WAF platform dynamically updates bot signatures to ensure effective protection.

### Steps to enable BOT Protection

1. Navigate to the WAF.

2. Select **Managed Rules** and then **Assign**.

3. From the dropdown menu, select the version of the BOT protection rule set that you want to use.

  **Note**: We recommend always using the most up-to-date rule version.

**Rule group:**

- **Bad bots**: Protect against malicious bots with harmful intentions or falsified identities.

- **Good bots**: Identify goo

*(Content truncated — refer to original GT for full details)*

### Step 20: None of the above

### Support Engineer Solution

As your issue is not listed, open a *Support Request(SR)* with detailed information about the problem. You can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/en-gb/answers/tags/148/azure-application-gateway)  

- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

For initial assistance with WAF and if you are getting started with WAF, please visit below reference links:

- [Web Application Firewall](https://learn.microsoft.com/en-us/azure/web-application-firewall/)

- [Best practices for Azure Web Application Firewall (WAF) on Azure Application Gateway](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/best-practices)

- [Frequently asked questions for Azure Web Application Firewall on Application Gateway](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-faq)

### Customer Solution

*Content type: MarkdownText*

If your issue is not listed, open a support request with detailed information about the problem. You can use the following resources to continue troubleshooting: 

- [Ask the Azure Community](https://learn.microsoft.com/en-gb/answers/tags/148/azure-application-gateway)  

- [Check Azure Stack Overflow ](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure portal support page](http://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

For initial assistance with WAF, or if you're getting started with WAF, see the following resources:

- [Web Application Firewall](https://learn.microsoft.com/azure/web-application-firewall/)

- [Best practices for Azure Web Application Firewall (WAF) on Azure Application Gateway](https://learn.microsoft.com/azure/web-application-firewall/ag/best-practices)

- [Frequently asked questions for Azure Web Application Firewall on Application Gateway](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-waf-faq)

---
