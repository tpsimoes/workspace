# Debugging Web Application Firewall

> **Product:** Application Gateway  
> **Solution ID:** 5bfa47ab-c303-46ac-8aec-895fb56d6c1d  
> **Trigger words:** application, application gateway, debugging, firewall

---

## Overview

This guide provides step-by-step troubleshooting for **Debugging Web Application Firewall** under **Application Gateway**.
 The original guided troubleshooter contains 10 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: WAF Scope Check ⭐ (First Step)

### Guidance

# Select the issue that best matches your scenario to proceed with troubleshooting.  

**403 Forbidden errors**  

- WAF may be blocking requests based on Managed Rule Sets or Custom Rules. This often occurs when legitimate traffic matches a configured rule.  

**413 Request Entity Too Large**

- The request size exceeds the configured limits in WAF or backend settings. This typically happens with large file uploads or oversized requests.  

**Traffic that should be blocked is being allowed** 

- WAF rules may not be configured correctly or are missing, allowing unwanted traffic to pass through.

### Question

**Which of the following Web Application Firewall (WAF) related issues are you currently facing?**

### Options

- **403 Forbidden errors** → Go to: *fe29d14a-0889-4387-9c9c-a6bdc9533eca*
- **413 Request Entity Too Large** → Go to: *Check OWASP Version*
- **Traffic that should be blocked is being allowed** → Go to: *Check WAF state*
- **None of the above** → Go to: *None of the above*

---

### Step 2: Check OWASP Version

### Guidance

### HTTP Status Code 413

Indicates that the request payload is larger than the server is willing or able to process.

---

### Common cause

- 413 errors often occur in **Application Gateway v1** when the gateway blocks a file upload because the request wasn't properly formatted to indicate it contains a file.

- This typically happens when headers like **Content-Type**, **Content-Length**, or **Content-Disposition** are missing.

- These headers inform the gateway that the request is a file upload, not raw body content that needs to be scanned by WAF.

---

### Steps to verify the source of HTTP Status Code 413

1. Go to **Application Gateway > Monitoring > Diagnostic Settings**.

2. If a Diagnostic Setting exists:

   - Check under **Categories** and ensure **All logs** or specifically **Application Gateway Access Log** and **Application Gateway Firewall Log** are selected.

3. If no Diagnostic Setting exists:

   - Click **Add Diagnostic Setting** and enable the required categories.

4. Choose where to send the logs (e.g., **Storage Account**, **Log Analytics**, or **Event Hub**).

5. Save your settings and replicate the issue.

---

**Under Monitoring, select Logs and use following query:**

    AzureDiagnostics | where Category == "ApplicationGatewayAccessLog" | where httpStatus_d == 413

Or	 

    AGWAccessLogs | where HttpStatus == 413

---

**In the Application Gateway logs:**

- Verify if the 413 error is originating from the backend:

  - Check the **serverStatus_s** (or **ServerStatus**) in the logs.

  - If `serverStatus_s` shows **413**, the issue lies with the backend, not WAF. Further backend troubleshooting is required.

---

### Understand the error

- When encountering a 413 error blocked by WAF, recognize that this typically indicates an excessively large request body.

- This is why it doesn't appear in WAF logs.

---

### Check the CRS Version

- If the error is from Application Gateway, check the Core Rule Set (CRS) version and follow the appropriate troubleshooting steps:

  - **CRS 3.1 or lower**

  - **CRS 3.2 or newer DRS versions**

### Question

**Which version of the OWASP Core Rule Set (CRS) is your Web Application Firewall (WAF) currently using?**

### Options

- **OWASP CRS 3.1 or lower** → Go to: *413 Request Entity Too Large for Old OWASP Versions*
- **OWASP CRS 3.2 or newer DRS versions** → Go to: *413 Request Entity Too Large for New OWASP Version and DRS*

---

### Step 3: Check WAF state

### Guidance

### Why enable WAF?

Web Application Firewall (WAF) is essential for protecting applications against malicious traffic.  

If WAF is not enabled, harmful requests will not be blocked, leaving applications vulnerable.

---

### Verify if WAF is enabled

**For WAF policies**

1. Navigate to **Web Application Firewall (WAF)** in the Azure Portal.

2. In the **Overview** section, confirm that **Policy State** is set to ***Enabled***.

**For legacy WAF configurations within Application Gateway**

1. Go to **Application Gateway** in the Azure Portal.

2. Under **Application Gateway settings**, locate the **Web Application Firewall** section.

3. Ensure **WAF Status** is set to ***Enabled***.

### Question

**Is the WAF enabled?**

### Options

- **Yes** → Go to: *WAF Mode Prevention or Detection*
- **No** → Go to: *WAF state is disabled*

---

### Step 4: None of the above

### Support Engineer Solution

If the specific issue is not covered in this guided troubleshooter, we recommend opening a **Support Request (SR)** with detailed information about the problem. This ensures the support team can assist promptly and accurately.

**Additional resources for continued troubleshooting**

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

If the specific issue is not covered in this guided troubleshooter, we recommend opening a **Support Request (SR)** with detailed information about the problem. This ensures the support team can assist promptly and accurately.

**Additional resources for continued troubleshooting**

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

---

### Step 5: 413 Request Entity Too Large for Old OWASP Versions

### Support Engineer Solution

### For Application Gateway with Core Rule Set 3.1 or older

- **HTTP 413 Response** may occur when using Azure Web Application Firewall (WAF) on Application Gateway if the client request size exceeds the maximum request body size limit.

- The maximum request body size controls the overall request size limit (excluding file uploads), with a default value set to **128 KB**.

---

### Limits for CRS 3.1 and older versions:

| Resource                                                | Limit                                      | Note                                                                 |

|--------------------------------------------------------|-------------------------------------------|----------------------------------------------------------------------|

| **Maximum File Upload Size (Standard SKU)**           | V1 - 2GB <br> V2 - 4GB                   | The maximum size limit is shared with the request body.             |

| **Maximum File Upload Size (WAF SKU)**                | V1 Medium - 100MB <br> V1 Large - 500MB <br> V2 - 750MB | 1MB - Minimum Value <br> 100MB - Default Value                      |

| **Maximum Request Size Limit (Standard SKU without files)** | V1 - 2GB <br> V2 - 4GB                   |                                                                      |

| **Maximum Request Size Limit (WAF SKU without files)**| V1 or V2 (with CRS 3.1 and older) - 128KB | 8KB - Minimum Value <br> 128KB - Default Value                      |

| **Maximum Request Inspection Limit (WAF SKU)**        | V1 or V2 (with CRS 3.1 and older) - 128KB | 8KB - Minimum Value <br> 128KB - Default Value                      |

---

For detailed information on request size limits, visit: [Web Application Firewall request size limits](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits)

---

### Still need help?

If your issue is not resolved, use these resources to continue troubleshooting:

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

### For Application Gateway with Core Rule Set 3.1 or older

- **HTTP 413 Response** may occur when using Azure Web Application Firewall (WAF) on Application Gateway if the client request size exceeds the maximum request body size limit.

- The maximum request body size controls the overall request size limit (excluding file uploads), with a default value set to **128 KB**.

---

### Limits for CRS 3.1 and older versions:

| Resource                                                | Limit                                      | Note                                                                 |

|-------

*(Content truncated — refer to original GT for full details)*

### Step 6: 413 Request Entity Too Large for New OWASP Version and DRS

### Support Engineer Solution

### For Application Gateway with Core Rule Set 3.2 or newer

The maximum request body size and file upload size limits are significantly higher in CRS 3.2 and newer DRS versions.  

If these limits are not being breached, you can adjust the settings accordingly.  

If you have reached the maximum limits, consider disabling the enforcement of these sizes.

---

### Limits for CRS 3.2 and newer DRS versions:

| Resource                                      | Limit                                      | Note                                                                                     |

|----------------------------------------------|-------------------------------------------|-----------------------------------------------------------------------------------------|

| **Maximum File Upload Size (WAF SKU)**      | V2 (with CRS 3.2 or DRS) - 4GB           | 1MB - Minimum Value<br>100MB - Default Value<br>Can be turned On/Off                  |

| **Maximum Request Size Limit (WAF SKU without files)** | V2 (with CRS 3.2 or DRS) - 2MB           | 8KB - Minimum Value<br>128KB - Default Value<br>Can be turned On/Off                  |

| **Maximum Request Inspection Limit (WAF SKU)** | V2 (with CRS 3.2 or DRS) - 2MB           | 8KB - Minimum Value<br>128KB - Default Value<br>Can be turned On/Off                  |

For more details, see [Web Application Firewall request size limits](https://learn.microsoft.com/azure/web-application-firewall/ag/application-gateway-waf-request-size-limits).

---

To adjust settings:

- Go to **Web Application Firewall(WAF) Policy**.

- Click on **Policy Settings** and modify the limits as needed.

---

### Still need help?

If your issue is not resolved, use these resources to continue troubleshooting:

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

### For Application Gateway with Core Rule Set 3.2 or newer

The maximum request body size and file upload size limits are significantly higher in CRS 3.2 and newer DRS versions.  

If these limits are not being breached, you can adjust the settings accordingly.  

If you have reached the maximum limits, consider disabling the enforcement of these sizes.

---

### Limits for CRS 3.2 and newer DRS versions:

| Resource                                      | Limit                                      | Note                                                                                     |

|----------------------------------------------|-------------------------------------------|-----------------------------------------------------------------------------------------|

| **Maximum File Upload Size (WAF SKU)**      | V2 (with CR

*(Content truncated — refer to original GT for full details)*

### Step 7: WAF Mode Prevention or Detection

### Guidance

**Detection mode**  

A policy in *Detection* is intended for testing and tuning your WAF configuration. It does not provide protection—it only logs traffic and takes no action, such as allowing or denying requests.

**Prevention mode**  

A policy in *Prevention* mode ensures that the Web Application Firewall (WAF) actively blocks requests it identifies as malicious, providing full protection for your applications.  

---

### How to check Web Application Firewall (WAF) mode

**For Legacy WAF configurations (configured directly on Application Gateway):**

1. Navigate to **Application Gateway > Settings > Web Application Firewall**.

2. Look for **WAF Mode** under the configuration settings.

**For WAF policy:**

1. Navigate to **Web Application Firewall (WAF) Policy** in the Azure Portal.

2. Under the **Overview** section, check the **Policy Mode** to confirm whether it is set to *Detection* or *Prevention*.

### Question

**What mode is your Web Application Firewall (WAF) operating in?**

### Options

- **Detection Mode** → Go to: *WAF Mode Detection*
- **Prevention Mode** → Go to: *WAF Mode Prevention*

---

### Step 8: WAF state is disabled

### Support Engineer Solution

### Web Application Firewall (WAF) disabled

Your applications are currently **not protected** from potential threats because WAF is disabled. Enabling WAF is essential to secure your web applications.

---

### How to enable Web Application Firewall (WAF)

1. Navigate to your **Web Application Firewall (WAF)** resource.

2. In the **Overview** section, select **Enable**.

3. Verify that **Policy State** is set to **Enabled**.

---

### For Legacy WAF Configurations in Application Gateway:

1. Go to **Application Gateway > Settings > Web Application Firewall**.

2. Toggle **WAF Status** to **On**.

3. Click **Save**.

---

### Still need help?

If your issue is not resolved, use these resources to continue troubleshooting:

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

### Web Application Firewall (WAF) disabled

Your applications are currently **not protected** from potential threats because WAF is disabled. Enabling WAF is essential to secure your web applications.

---

### How to enable Web Application Firewall (WAF)

1. Navigate to your **Web Application Firewall (WAF)** resource.

2. In the **Overview** section, select **Enable**.

3. Verify that **Policy State** is set to **Enabled**.

---

### For Legacy WAF Configurations in Application Gateway:

1. Go to **Application Gateway > Settings > Web Application Firewall**.

2. Toggle **WAF Status** to **On**.

3. Click **Save**.

---

### Still need help?

If your issue is not resolved, use these resources to continue troubleshooting:

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

---

### Step 9: WAF Mode Detection

### Support Engineer Solution

When the **Web Application Firewall (WAF)** is operating in **Detection mode**, it only logs traffic without blocking it. All traffic is allowed through the Application Gateway.

To ensure malicious traffic is blocked, switch the WAF to **Prevention mode**.

---

### To configure Prevention mode

- Navigate to your **Web Application Firewall** resource.

- In the **Overview** section, change the mode to **Prevention**.

- Verify the **Policy mode** under **Overview** to confirm the update.

**Note**: Enabling **Prevention mode** will start to block traffic based on WAF rules, providing enhanced security.

---

### Still need help?

If your issue is not resolved, use these resources to continue troubleshooting:

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

When the **Web Application Firewall (WAF)** is operating in **Detection mode**, it only logs traffic without blocking it. All traffic is allowed through the Application Gateway.

To ensure malicious traffic is blocked, switch the WAF to **Prevention mode**.

---

### To configure Prevention mode

- Navigate to your **Web Application Firewall** resource.

- In the **Overview** section, change the mode to **Prevention**.

- Verify the **Policy mode** under **Overview** to confirm the update.

**Note**: Enabling **Prevention mode** will start to block traffic based on WAF rules, providing enhanced security.

---

### Still need help?

If your issue is not resolved, use these resources to continue troubleshooting:

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

---

### Step 10: WAF Mode Prevention

### Support Engineer Solution

If traffic continues to pass through even when the **Web Application Firewall (WAF)** is set to **Prevention mode**, the issue may be due to:

- Misconfigured **Custom Rules**

- Disabled **Managed Rules**

- Incorrect **Exclusions**

---

### Troubleshooting steps

1. **Create a New WAF Policy**  

   - Set up a new Web Application Firewall (WAF) policy and associate it with a Listener.  

   - This helps determine if the problem lies with the current policy configuration.

2. **Test with Tools**  

   - Use tools like **Postman**, **cURL**, or similar to send requests against the new WAF policy.  

   - A new policy with no exclusions should block malicious content if configured correctly.  

   - If traffic is still not blocked, the issue may not be related to exclusions.

3. **Modify CRS Version**  

   - Test the new WAF policy with a different **Core Rule Set (CRS)** version, especially if you are not using CRS 3.2.  

   - This helps identify if the CRS version is affecting blocking behavior.

---

### Still need help?

If your issue is not resolved, use these resources to continue troubleshooting:

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

### Customer Solution

*Content type: MarkdownText*

If traffic continues to pass through even when the **Web Application Firewall (WAF)** is set to **Prevention mode**, the issue may be due to:

- Misconfigured **Custom Rules**

- Disabled **Managed Rules**

- Incorrect **Exclusions**

---

### Troubleshooting steps

1. **Create a New WAF Policy**  

   - Set up a new Web Application Firewall (WAF) policy and associate it with a Listener.  

   - This helps determine if the problem lies with the current policy configuration.

2. **Test with Tools**  

   - Use tools like **Postman**, **cURL**, or similar to send requests against the new WAF policy.  

   - A new policy with no exclusions should block malicious content if configured correctly.  

   - If traffic is still not blocked, the issue may not be related to exclusions.

3. **Modify CRS Version**  

   - Test the new WAF policy with a different **Core Rule Set (CRS)** version, especially if you are not using CRS 3.2.  

   - This helps identify if the CRS version is affecting blocking behavior.

---

### Still need help?

If your issue is not resolved, use these resources to continue troubleshooting:

- [Ask the Azure Community](https://learn.microsoft.com/answers/tags/148/azure-application-gateway)

- [Check Azure Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

- [Check the Azure Portal Support page](https://portal.azure.com/#view/Microsoft_Azure_Support/HelpAndSupportBlade/~/overview)

---
