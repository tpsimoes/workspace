# Automated] Application Gateway - Configure App Service

> **Product:** Application Gateway  
> **Solution ID:** e7c87348-5dd1-4d73-9b9c-1d2c19b73b41  
> **Trigger words:** application, application gateway, automated], configure, gateway, service

---

## Overview

This guide provides step-by-step troubleshooting for **Automated] Application Gateway - Configure App Service** under **Application Gateway**.
 The original guided troubleshooter contains 19 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Backend Pool configuration ⭐ (First Step)

### Guidance

This TSG is specific to Application Gateway "Configure App Service backend" issues. It is applicable to the following support topics:

Azure/Application Gateway/Configuration and Setup/Configure App service

If your issue is not related to app service backend pool (Connection Timeout, WAF Traffic Analysis, Failed State..,etc ), please add another solution set on the ASC to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results.

In order to confirm if the App Service is configured on the backend pool, please follow the steps below:

1. On ASC go to the Application Gateway page.

2. Go to the "Diagnostics" blade to **Application Gateway Checklist** section.

3. On the field "Application Gateway Access URL" enter the URL cx is having issues with. example: "https://www.example.com"

4. Choose the Front End Type (Public or private) and click on Run.

Expected result: 

**Multisite Listener Host Name Mismatch:** You will get this result if there is no rule configured for this FQDN 

**Backend Address Pool Empty:** You will get this result if there is no backend server configured on the backend pool

**App service in the backend pool:** If there is a backend pool configured and that backend pool has a backend server, then scroll down to the "Backend Address Pool" section and confirm the backend pool has an AppService endpoint configured. This can be any FQDN if they have a custom DNS and domain, any .azurewebsite.net domain or IP for a load balancer in case customer is using an App Service Environment (ASE).

### Question

**Is the App Service configured on the Application Gateway backend pool?**

### Options

- **Yes** → Go to: *Type of issue*
- **No, I'm not able to select the app service as a backend** → Go to: *App Service subscription*
- **No, out of TSG scope** → Go to: *Out of TSG scope*

---

### Step 2: App Service subscription

### Support Engineer Solution

**Issue:** You cannot see the App Service in the backend pool dropdown list.

**Cause:** This issue occurs when the App Service is not part of the Application Gateway Subscription.

Backend pool dropdown list only allows to select App Services in the same subscription has the AppGW.

**Resolution:** If App Service is in a different subscription, customer should choose IP address or hostname.

Documentation: [Configure web app](https://learn.microsoft.com/en-us/azure/application-gateway/configure-web-app)

### Customer Solution

*Content type: MarkdownText*

If you can't see the App Service in the **Backend pool** list, it is likely because the App Service is not part of the Application Gateway Subscription. The **Backend pool** list only displays App Services in the same subscription as the AppGW.

To resolve, choose the IP address or hostname. See [Configure web app](https://learn.microsoft.com/en-us/azure/application-gateway/configure-web-app).

---

### Step 3: Type of issue

### Guidance

### Common issues for Application Gateway and App Service integration and how to identify them

**a. Backend health issues**

Check Backend Connectivity Diagnostic (For v2 SKU) under Diagnostics section of ASC for the given Application Gateway. This can be very helpful.

Look at the Healthy field in BackendServerDiagnosticHistory table which can be located at:

- Jarvis Logs > AppGWT > BackendServerDiagnosticHistory or

- [MDM Logs] Backend Server Diagnostics History link under Diagnostic section of the given Application Gateway in ASC.

**b. Custom Domain configuration issues**

1. 502 HTTP errors after custom domain configuration.

Check Request Response Logs table which can be located at:

- Jarvis Logs > AppGWT > ReqRespLog or

- [MDM Logs] Request Response link under Diagnostic section of the given Application Gateway in ASC.

2. Cannot add custom domain in the App Service resource: you might see that the "Add" option is greyed out in the custom domain configuration section in the app service resource due to domain validation issues 

**c. App service URL is exposed in the browser or broken cookies issue**

- [Incorrect absolute URLs](https://learn.microsoft.com/en-us/azure/architecture/best-practices/host-name-preservation#incorrect-absolute-urls): after adding the Application Gateway associated URL, the user receives a URL that goes straight to the back-end application (App Service) and bypasses the Application Gateway.

- [Incorrect redirect URLs](https://learn.microsoft.com/en-us/azure/architecture/best-practices/host-name-preservation#incorrect-redirect-urls): the app service URL is exposed in the browser when there's a redirection 

- [Broken cookies](https://learn.microsoft.com/en-us/azure/architecture/best-practices/host-name-preservation#broken-cookies): cookies are not propagated between the browser and the App Service

To identify these issues, you can collect HAR file during the test to check the request/response headers. Steps to collect HAR file: [capture browser trace](https://learn.microsoft.com/en-us/azure/azure-portal/capture-browser-trace)

**d. Private endpoint configuration**

- 502 HTTP errors after Private Endpoint configuration. 

To confirm if the app service is configured with private endpoint go to the App Service resource in ASC:

- On the Properties page, click on the AppLens link

- Under Detectors section, choose Networking.

- On that page, you will find if the private endpoint is enabled or not.

### Question

**What type of issue are customer facing?**

### Options

- **Backend health issues** → Go to: *Message in the Backend Health*
- **Custom Domain Configuration** → Go to: *Custom Domain Configuration*
- **App Service URL is exposed in the browser or broken cookies issue** → Go to: *App Service URL is exposed in the Browser or broken cookies*
- **Private Endpoint Configuration** → Go to: *Private Endpoint Configuration*

---

### Step 4: Message in the Backend Health

### Guidance

When using App Service, you might see HTTP codes such as 401, 403 and 503 which are related with specific App Service misconfigurations. 

If you are seeing a different HTTP code, you might be facing generic App GW connectivity issues to the backend. 

**Note:** 

Application Gateway periodically logs the health probe status in [**BackendServerDiagnosticHistory**](https://portal.microsoftgeneva.com/s/5EE80A21) table in Jarvis logs, under **AppGWT** namespace.

Or by Triggering a [**Get Application Gateway Backend Health**](https://portal.microsoftgeneva.com/FD64DF6E?genevatraceguid=cd7a138a-9473-47cc-a64c-b2ffa7bf1751) in Jarvis Actions,

The output will be an operation ID, this is the GWM operation ID, Then you can check the result of the operation in **InformationLogEvent** table under **AppGWT** namespace in Jarvis Logs.

### Question

**What message are you seeing in the backend health?**

### Options

- **Probe status code mismatch: Received 401** → Go to: *HTTP Code 401*
- **Probe status code mismatch: Received 403** → Go to: *HTTP Code 403*
- **Probe status code mismatch: Received 503** → Go to: *HTTP Code 503*
- **Backend server timeout** → Go to: *Backend server timeout*
- **TCP connect error** → Go to: *TCP connect error*
- **Others** → Go to: *d88f3f43-0cc3-4143-aced-c4820b56e8ec*

---

### Step 5: App Service URL is exposed in the Browser or broken cookies

### Support Engineer Solution

**Cause:** App Service uses the host header in the request to route the request to the correct endpoint. The default domain name of App Services, *.azurewebsites.net (say, contoso.azurewebsites.net), is different from the application gateway's domain name (say, contoso.com). The backend App Service is missing the required context to generate redirect URL's or cookies that align with the domain as seen by the browser.

**Resolution:** You can choose by configuring a custom domain or by creating a rewrite rule in the Application Gateway. 

Steps available at: https://learn.microsoft.com/en-us/azure/application-gateway/troubleshoot-app-service-redirection-app-service-url

### Customer Solution

*Content type: MarkdownText*

The App Service uses the host header in the request to route the request to the correct endpoint. The default domain name of App Services, `*.azurewebsites.net` (for example, contoso.azurewebsites.net), is different from the application gateway's domain name (for example, contoso.com). The backend App Service is missing the required context to generate redirect URLs or cookies that align with the domain as seen by the browser.

**Resolution:** You can choose by configuring a custom domain or by creating a rewrite rule in the Application Gateway. 

References:

 

- [App Service Redirection](https://learn.microsoft.com/en-us/azure/application-gateway/troubleshoot-app-service-redirection-app-service-url)

- [Incorrect absolute URLs](https://learn.microsoft.com/en-us/azure/architecture/best-practices/host-name-preservation#incorrect-absolute-urls)

- [Incorrect redirect URLs](https://learn.microsoft.com/en-us/azure/architecture/best-practices/host-name-preservation#incorrect-redirect-urls)

- [Broken cookies](https://learn.microsoft.com/en-us/azure/architecture/best-practices/host-name-preservation#broken-cookies)

---

### Step 6: HTTP Code 401

### Support Engineer Solution

**Issue:** App Service is responding to the Application Gateway Health Probes with 401 HTTP Code.

**Cause:**

Application Gateway probes can't pass credentials for authentication.

You may see the 401 HTTP Code when the backend server requires authentication. 

### Check Backend health

Check Backend Connectivity Diagnostic (For v2 SKU) under Diagnostics section of ASC for the given Application Gateway, Check the **Args** column for the response that is coming from the backend server:

Look at the Healthy field in BackendServerDiagnosticHistory table which can be located at:

* **Jarvis Logs > AppGWT > BackendServerDiagnosticHistory** or

* **[MDM Logs] Backend Server Diagnostics History** link under Diagnostic section of the given Application Gateway in ASC.

**Resolution:** 

a. Configure the Health Probe to a path where the server doesn't require authentication. 

b. As an alternative you can allow "HTTP 401" in a probe status code match. To achieve this step you can:

- Go to the "Health Probes" tab in your Application Gateway resource

- Select "Yes" in the "Use probe matching conditions" section

- Add "401" HTTP code has an acceptable response to the Health Probe

Available documentation:

[Application Gateway Backend Health](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#http-status-code-mismatch)

[App Service Authentication configuration](https://learn.microsoft.com/en-us/azure/app-service/overview-authentication-authorization#authorization-behavior)

### Customer Solution

*Content type: MarkdownText*

When the App Service is responding to the Application Gateway Health Probes with 401 HTTP Code, it's because 

Application Gateway probes can't pass credentials for authentication.

You may see the 401 HTTP Code when the backend server requires authentication. 

To resolve, do one of the following:

- Configure the Health Probe to a path where the server doesn't require authentication. 

- Allow "HTTP 401" in a probe status code match. To do so:

  1. Go to **Health Probes** in your Application Gateway resource

  1. Select **Yes** in **Use probe matching conditions**.

  1. Add **401** HTTP code has a response to the Health Probe

References:

- [Application Gateway Backend Health](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#http-status-code-mismatch)

- [App Service Authentication configuration](https://learn.microsoft.com/en-us/azure/app-service/overview-authentication-authorization#authorization-behavior)

---

### Step 7: HTTP Code 403

### Support Engineer Solution

**Issue:** App Service is responding to the Application Gateway Health Probes with 403 HTTP Code.

**Cause:** Application Gateway Health Probes connections are being blocked by the App Service.

### Check Backend health

Check Backend Connectivity Diagnostic (For v2 SKU) under Diagnostics section of ASC for the given Application Gateway, Check the **Args** column for the response that is coming from the backend server:

Look at the Healthy field in BackendServerDiagnosticHistory table which can be located at:

* **Jarvis Logs > AppGWT > BackendServerDiagnosticHistory** or

* **[MDM Logs] Backend Server Diagnostics History** link under Diagnostic section of the given Application Gateway in ASC.

**Resolution:**

1. Make sure that App Service is not in a stopped state.

- You can see the App Service status by opening the App Service in the Azure Portal and check if the "Status" is Running or Stopped under its properties.

2. If the App Service is not configured with a Private Endpoint, it means that Public Access is required. Confirm that the App Service is reachable via its Public IP.

- Ask cx to open the App Service resource in Azure Portal

- Select "Network" tab

- If the App Service is reacheable via its Public IP, confirm that Public Access is allowed. 

- If Public Access is not allowed, either allow Public Access or allow access from Application Gateway Public IP.

### Customer Solution

*Content type: MarkdownText*

If the App Service is responding to the Application Gateway Health Probes with 403 HTTP Code, it is because Application Gateway Health Probes connections are being blocked by the App Service.

To resolve:

1. Make sure that App Service is not in a stopped state. You can see the App Service status by opening the App Service in the Azure Portal and checking **Properties** to if the **Status** is **Running** or **Stopped**.

2. If the App Service is not configured with a Private Endpoint, it means that Public Access is required. Confirm that the App Service is reachable via its Public IP.

   1. Open the App Service resource in Azure Portal.

   1. Select Network.

   1. If the App Service is reacheable via its Public IP, confirm that Public Access is allowed. 

   1. If Public Access is not allowed, either allow Public Access or allow access from Application Gateway Public IP.

---

### Step 8: HTTP Code 503

### Support Engineer Solution

**Issue:** App Service is returning 503 to App Gw.

**Cause:** This problem is often caused by application level issues, such as:

- requests taking a long time

- application using high memory/CPU

- application crashing due to an exception.

### Check Backend health

Check Backend Connectivity Diagnostic (For v2 SKU) under Diagnostics section of ASC for the given Application Gateway, Check the **Args** column for the response that is coming from the backend server:

Look at the Healthy field in BackendServerDiagnosticHistory table which can be located at:

* **Jarvis Logs > AppGWT > BackendServerDiagnosticHistory** or

* **[MDM Logs] Backend Server Diagnostics History** link under Diagnostic section of the given Application Gateway in ASC.

**Resolution:**

1- Scale the app

2- Use AutoHeal

3- Restart the app

If you reach this point and the issue is still there, please open a collaboration to App Service team. 

Public Doc:

[App Service 502 and 503 HTTP](https://learn.microsoft.com/en-us/azure/app-service/troubleshoot-http-502-http-503)

### Customer Solution

*Content type: MarkdownText*

If the App Service is respoding to the Application Gateway Health Probes with 503 HTTP Code, it is likely due to an application level issue, such as:

- requests taking a long time

- application using high memory/CPU

- application crashing due to an exception.

To resolve:

1. Scale the app.

2. Use AutoHeal.

3. Restart the app.

If you encounter ongoing difficulties at this stage or have additional inquiries regarding the outlined steps, create a Service Request with the App Service team for further support.

See 

[App Service 502 and 503 HTTP](https://learn.microsoft.com/en-us/azure/app-service/troubleshoot-http-502-http-503)

---

### Step 9: Private Endpoint Configuration

### Guidance

Is the Application Gateway able to resolve the App Service FQDN to the Private IP?

You can confirm this by checking either the server name within [**BackendServerDiagnosticHistory**](https://portal.microsoftgeneva.com/s/5EE80A21) table in Jarvis logs, under **AppGWT** namespace or by checking jarvis action query [**Get List of NonResolvable Domains**

](https://portal.microsoftgeneva.com/8ABEA554?genevatraceguid=fbc20328-33c1-44e4-a9ba-17aa1550837b)

### Question

**Is the Application Gateway able to resolve the App Service FQDN to the Private IP?**

### Options

- **Yes** → Go to: *Message in the Backend Health*
- **No, it is resolving to the Public IP** → Go to: *PE resolving to the Public IP*
- **No, it cannot resolve** → Go to: *PE DNS not resolving*

---

### Step 10: PE resolving to the Public IP

### Support Engineer Solution

**Issue:** App Service FQDN is resolving to its Public IP instead of its private IP (when using a Private Endpoint configuration). 

There can be different causes for this situation:

**Cause 1:** This issue can occurr when the Backend Pool in the Application Gateway was configured before linking the Private DNS Zone to the Application Gateway. Due to this, the Application Gateway will still be resolving to the old configuration (Public IP resolution).

**Resolution:** Make a PUT operation on the Application Gateway to update the configuration. 

You can use the below commands from Azure PowerShell: 

    $AppGw = Get-AzApplicationGateway -Name "AppGWName" -ResourceGroupName "RGName"

    $UpdatedAppGw = Set-AzApplicationGateway -ApplicationGateway $AppGw

**Cause 2:** The issue can occurr as well on the DNS server on the Application Gateway was changed.

**Resolution 2:** Restart the Application Gateway.

**Cause 3:** If you are using azure dns, and private dns zone [privatelink.azurewebsites.net] is not linked to the app gw vnet. 

**Resolution 3:** Link the Private DNS zone to App GW Vnet.

### Customer Solution

*Content type: MarkdownText*

The App Service FQDN is resolving to its Public IP instead of its private IP (when using a Private Endpoint configuration). 

Some causes of this are:

- The Backend Pool in the Application Gateway was configured before linking the Private DNS Zone to the Application Gateway. Due to this, the Application Gateway will still be resolving to the old configuration (Public IP resolution).

  To resolve, make a PUT operation on the Application Gateway to update the configuration. You can use the following commands from Azure PowerShell: 

  ```

  $AppGw = Get-AzApplicationGateway -Name "AppGWName" -ResourceGroupName "RGName"

  $UpdatedAppGw = Set-AzApplicationGateway -ApplicationGateway $AppGw

  ```

- The DNS server on the Application Gateway VNET was changed. See [502 HTTP code after changing VNET DNS Server](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-faq#why-am-i-seeing-502-errors-or-unhealthy-backend-servers-after-i-changed-the-dns-servers-for-the-virtual-network).

   To resolve, restart the Application Gateway. Doing so will step will cause downtime to the Application Gateway.

   See [Steps on how to Stop and Start Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-faq#why-am-i-seeing-502-errors-or-unhealthy-backend-servers-after-i-changed-the-dns-servers-for-the-virtual-network).

- You are using Azure DNS, and the Private DNS Zone configured [privatelink.azurewebsites.net] is not linked to the Application Gateway VNET.

  To resolve, link the Private DNS zone to the Application Gateway VNET. See [Create Private DNS Zone](https://learn.microsoft.com/en-us/azure/dns/private-dns-getstarted-portal#link-the-virtual-network).

---

### Step 11: Custom DNS

### Support Engineer Solution

**Cause 1:** Connectivity issue from App Gw to DNS server/s.

**Resolution 1:** You can levarage test traffic from ASC on the App Gw instances or by placing packet traces on the DNS server side to confirm if the requests are reaching there.

You can do test traffic from ASC by:

- Expanding the Application Gateway resource to the tenantVMs.

- Choose one of the instances.

- Go to diagnostics tab and run test traffic to the dns server IP. 

**Cause 2:** The "A" record for the private endpoint is missing on the custom DNS server.

**Resolution 2:** Please add the A record on the custom DNS server. 

We can check the app gw resolution for the backend using :

1- Jarvis action: [Get List of NonResolvable Domains

](https://portal.microsoftgeneva.com/8ABEA554?genevatraceguid=fbc20328-33c1-44e4-a9ba-17aa1550837b)

 2- Jarvis logs: For Application Gateway V2, Check BackendServerDiagnosticHistory table and look for the ServerAddress field.

 AppGWT > BackendServerDiagnosticsHistory [BackendServerDiagnosticsHistory](https://portal.microsoftgeneva.com/s/AD37C95A)

**Cause 3:** App Gw's Vnet might has multiple DNS servers and not all of them have the A records there, you can check all custom DNS servers resolution using the jarvis action [Get List of NonResolvable Domains

](https://portal.microsoftgeneva.com/8ABEA554?genevatraceguid=fbc20328-33c1-44e4-a9ba-17aa1550837b)

**Resolution 3:** Cx Needs to confirm if he has the correct DNS server configuration.

### Customer Solution

*Content type: MarkdownText*

If you can't resolve the App Service FQDN, review the following causes and resolutions: 

- Connectivity issue from Application Gateway to DNS server.

 

  To resolve, check network connectivity to the DNS server by using Connection Troubleshoot the network connectivity or by placing packet traces on the DNS server side to confirm if the requests are reaching it.See [Connection troubleshoot](https://learn.microsoft.com/en-us/azure/network-watcher/network-watcher-connectivity-portal).

- The "A" record for the Private Endpoint is missing on the Custom DNS server.

  To resolve, add the A record on the custom DNS server. 

- The application Gateway VNET might have multiple DNS servers and not all of them will contain the A record configured.

  To resolve, confirm that you have the correct DNS server configuration on all DNS servers.

---

### Step 12: PE DNS not resolving

### Content

Issue: In such case, the backend pool will be shown as unknown.

You can check the App Gw Vnet DNS configuration following the steps below:

- Check the Virtual Network Name on proprties page of the Application Gateway on ASC.

- Open the virtual network on ASC and check the DNS servers on proprties page.

- If its "Default (Azure-Provided)" then its Azure DNS, otherwise its a custom DNS.

---

### Step 13: Azure DNS

### Support Engineer Solution

**Cause:** This can happen if private DNS zone is linked to App GW Vnet but the "A" record for the private endpoint is not there.

You can check the private dns zone configuration following the steps below:

- Check the Virtual Network Name on proprties page of the Application Gateway on ASC.

- Open the virtual network on ASC and check the Private DNS Zones section on proprties page.

- Look for the "privatelink.azurewebsites.net" private dns zone and open it on ASC.

- Then, check the records set in "Link to Record Sets" section. 

**Resolution:** Add the "A" record on the private dns zone.

### Customer Solution

*Content type: MarkdownText*

If you can't resolve the App Service FQDN, it is likely because the Private DNS Zone is linked to Application Gateway VNET but the "A" record for the Private Endpoint is not there.

  To resolve, add the "A" record on the Private Dns Zone.

  See [Create a DNS Record](https://learn.microsoft.com/en-us/azure/dns/dns-getstarted-portal#create-a-dns-record)

---

### Step 14: Custom Domain Configuration

### Guidance

Custom domain configuration is the recommended way for production scenario and you might face multiple issues because of mis-configuration.

### Question

**Which Custom Domain issue are you facing?**

### Options

- **502 after configuring custom domain on App Service** → Go to: *Custom Domain 502*
- **Domain Validation issue in App Service -"add" button is greyed out** → Go to: *Domain Validation*

---

### Step 15: Custom Domain 502

### Support Engineer Solution

**Cause:** In a scenario of configuring a Custom Domain you may see a 502 HTTP code when accessing your Application Gateway if you are using the Custom Domain in the Backend Pool of the Application Gateway.

If the Backend Pool is the Custom Domain, and not the App Service resource, the Application Gateway will resolve the Custom Domain to its own IP, hence it will send  the Health Probe to itself. 

**Resolution:** In the Backend Pool of the Application Gateway select the App Service resource from the drop down list instead of using the custom domain in the backend pool.

### Customer Solution

*Content type: MarkdownText*

This issue may occur if you use the Custom Domain in the Backend Pool of the Application Gateway. In this case, the Application Gateway will resolve the Custom Domain to its own IP, hence it will send  the Health Probe to itself. 

The Backend Pool should be configured as the App Service resource. 

**Resolution:** In the Backend Pool of the Application Gateway select the App Service resource from the drop down list instead of using the custom domain in the backend pool.

---

### Step 16: Domain Validation

### Support Engineer Solution

**Issue:** "Add" option is greyed out in the custom domain configuration section in the app service resource due to domain validation issues

**Resolution:** Make sure that you have text record created with corresponding value that you got while creating the custom domain.

[Manage traffic to App Service - Azure Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/configure-web-app?tabs=customdomain%2Cazure-portal)

### Customer Solution

*Content type: MarkdownText*

If the **Add** option is disabled in the App Service resource custom domain configuration section, it is due to domain validation issues

 

 

To resolve, make sure that you have text record created with the corresponding value that you got while creating the custom domain.

 

[Manage traffic to App Service - Azure Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/configure-web-app?tabs=customdomain%2Cazure-portal)

---

### Step 17: Backend server timeout

### Support Engineer Solution

**Message:** Time taken by the backend to respond to application gateway's health probe is more than the timeout threshold in the probe setting.

**Cause:** After Application Gateway sends an HTTP(S) probe request to the backend server, it waits for a response from the backend server for a configured period. If the backend server doesn't respond within the configured period (the timeout value), it's marked as Unhealthy until it starts responding within the configured timeout period again.

**Resolution:** Check why the backend server or application isn't responding within the configured timeout period, and also check the application dependencies. For example, check whether the database has any issues that might trigger a delay in response. If you're aware of the application's behavior and it should respond only after the timeout value, increase the timeout value from the custom probe settings. You must have a custom probe to change the timeout value. 

For information about how to configure a custom probe, see the [documentation page](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-create-probe-portal)

For more info, you can check the following link: [Backend health issue](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#http-status-code-mismatch)

### Customer Solution

*Content type: MarkdownText*

**Message:** Time taken by the backend to respond to application gateway's health probe is more than the timeout threshold in the probe setting.

**Cause:** After Application Gateway sends an HTTP(S) probe request to the backend server, it waits for a response from the backend server for a configured period. If the backend server doesn't respond within the configured period (the timeout value), it's marked as Unhealthy until it starts responding within the configured timeout period again.

**Resolution:** Check why the backend server or application isn't responding within the configured timeout period, and also check the application dependencies. For example, check whether the database has any issues that might trigger a delay in response. If you're aware of the application's behavior and it should respond only after the timeout value, increase the timeout value from the custom probe settings. You must have a custom probe to change the timeout value. 

For information about how to configure a custom probe, see the [documentation page](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-create-probe-portal)

For more info, you can check the following link: [Backend health issue](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#http-status-code-mismatch)

---

### Step 18: TCP connect error

### Support Engineer Solution

**Message:** Application Gateway could not connect to the backend. Check that the backend responds on the port used for the probe. Also check whether any NSG/UDR/Firewall is blocking access to the Ip and port of this backend.

**Cause:** After the DNS resolution phase, Application Gateway tries to connect to the backend server on the TCP port that's configured in the HTTP settings. If Application Gateway can't establish a TCP session on the port specified, the probe is marked as Unhealthy with this message.

**Solution:** If you receive this error, follow the steps in the link below:

[TCP connect error](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#tcp-connect-error)

### Customer Solution

*Content type: MarkdownText*

**Message:** Application Gateway could not connect to the backend. Check that the backend responds on the port used for the probe. Also check whether any NSG/UDR/Firewall is blocking access to the Ip and port of this backend.

**Cause:** After the DNS resolution phase, Application Gateway tries to connect to the backend server on the TCP port that's configured in the HTTP settings. If Application Gateway can't establish a TCP session on the port specified, the probe is marked as Unhealthy with this message.

**Solution:** If you receive this error, follow the steps in the link below:

[TCP connect error](https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-backend-health-troubleshooting#tcp-connect-error)

---

### Step 19: Out of TSG scope

### Support Engineer Solution

Please add another solution set on the ASC to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right resource for better results.

### Customer Solution

*Content type: MarkdownText*

Please add another solution set on the ASC to look for new Insights and Troubleshooters. Make sure you replace the Support Topic correctly and specify right Resource for better results.

---
