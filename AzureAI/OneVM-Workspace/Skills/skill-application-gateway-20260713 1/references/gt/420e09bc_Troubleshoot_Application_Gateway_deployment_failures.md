# Troubleshoot Application Gateway deployment failures

> **Product:** Application Gateway  
> **Solution ID:** 420e09bc-afbf-49e7-a2f0-4b82a677cf1b  
> **Trigger words:** application, application gateway, deployment, failed state, failures, gateway, troubleshoot

---

## Overview

This guide provides step-by-step troubleshooting for **Troubleshoot Application Gateway deployment failures** under **Application Gateway**.
 The original guided troubleshooter contains 15 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Key Vault related error

### Support Engineer Solution

This error indicates that the Key Vault secret the Application Gateway is attempting to retrieve is either unavailable, or there may be a permission issue at the Key Vault's end, restricting access.  

This error can be resolved using one of the following steps:  

* If using Service Endpoints to access Key Vault, you must whitelist Application Gateway subnet in Key Vault firewall. 

* If using Private Endpoints to access Key Vault, you must link the privatelink.vaultcore.azure.net private DNS zone, containing the corresponding record to the referenced Key Vault, to the virtual network containing Application Gateway. 

* If Application Gateway Virtual Network has custom DNS servers defined, it must be able to resolve Key Vault FQDN.

* Access to Key Vault must be allowed via Network Security Groups and User-defined Routes on Application Gateway subnet.  

 

For more information, see [TLS termination with Key Vault certificates](https://learn.microsoft.com/azure/application-gateway/key-vault-certs)

### Customer Solution

*Content type: MarkdownText*

This error indicates that the Key Vault secret that your Application Gateway is trying to retrieve is either unavailable, or there may be a permission issue at the Key Vault, restricting access.  

This error can be resolved using one of the following steps:  

* If using Service Endpoints to access Key Vault, you must allow-list Application Gateway subnet in Key Vault firewall. 

* If using Private Endpoints to access Key Vault, you must link the **privatelink.vaultcore.azure.net**  private DNS zone, containing the corresponding record to the referenced Key Vault, to the virtual network containing Application Gateway. 

* If Application Gateway Virtual Network has custom DNS servers defined, it must be able to resolve Key Vault Fully Qualified Domain name (FQDN).

* Access to Key Vault must be allowed via Network Security Groups and user-defined routes on Application Gateway subnet.  

 

For more information, see [TLS termination with Key Vault certificates](https://learn.microsoft.com/en-us/azure/application-gateway/key-vault-certs)

---

### Step 2: Invalid certificate data

### Support Engineer Solution

This error indicates that the certificate you are trying to upload in the Backend Settings does not have valid data.  

This could happen if you are trying to upload certificate that is not in .cer format or if the .cer certificate uploaded is in DER encoded binary format instead of Base64 encoded.  

For more information, see [Create certificates to allow the backend with Azure Application Gateway](https://learn.microsoft.com/azure/application-gateway/certificates-for-backend-authentication).

### Customer Solution

*Content type: MarkdownText*

This error indicates that the certificate you are trying to upload in the backend settings does not have valid data. This may occur for either of the following reasons:

-  You are trying to upload certificate that is not in .cer format.

-  The .cer certificate uploaded is in DER encoded binary format instead of Base64 encoded.  

For more information, see 

[Create certificates to allow the backend with Azure Application Gateway](https://learn.microsoft.com/azure/application-gateway/certificates-for-backend-authentication).

---

### Step 3: Duplicate authentication and root certificate

### Support Engineer Solution

Application Gateway certificate renewal errors occur if the certificate already exists in authentication or trusted root certificate store.  

You can validate existing authentication and trusted root certificate list, and delete the duplicate certificate or use it in the backend settings. 

For more information, see [Get-AzApplicationGatewayTrustedRootCertificate](https://learn.microsoft.com/en-us/powershell/module/az.network/get-azapplicationgatewaytrustedrootcertificate?view=azps-10.3.0)

and [Remove-AzApplicationGatewayTrustedClientCertificate](https://learn.microsoft.com/en-us/powershell/module/az.network/remove-azapplicationgatewaytrustedclientcertificate?view=azps-10.3.0).

### Customer Solution

*Content type: MarkdownText*

Application Gateway certificate renewal error occurs if the certificate already exists in authentication or trusted root certificate store.  

You can validate existing authentication and trusted root certificate list, and either delete the duplicate certificate or use it in the Backend Settings. 

For more information, see  [Get-AzApplicationGatewayTrustedRootCertificate](https://learn.microsoft.com/powershell/module/az.network/get-azapplicationgatewaytrustedrootcertificate?view=azps-10.3.0)

and [Remove-AzApplicationGatewayTrustedClientCertificate](https://learn.microsoft.com/powershell/module/az.network/remove-azapplicationgatewaytrustedclientcertificate?view=azps-10.3.0).

---

### Step 4: Failed state

### Guidance

If your Application Gateway is in failed state, perform a **Get/Set** Powershell command, and then check to see if the issue is resolved. 

```

$AppGW = Get-AzApplicationGateway -Name "AppGWName" -ResourceGroupName "RGName"

Set-AzApplicationGateway -ApplicationGateway $AppGW

```

For more information, see [Troubleshoot Azure Microsoft.Network failed provisioning state](https://learn.microsoft.com/azure/networking/troubleshoot-failed-state#microsoftnetworkapplicationgateways).

### Question

**Does performing the Get/Set operation fix the issue?**

### Options

- **Yes** → Go to: *Issue resolved*
- **No** → Go to: *Application Gateway errors*

---

### Step 5: Key vault errors

### Guidance

Identify the Key Vault related error message.

### Question

**Which Key Vault related error are you seeing?**

### Options

- **Error while accessing and validating Key Vault** → Go to: *Key Vault related error*
- **Failed to retrieve secret from Key Vault** → Go to: *Non CRUD issue*

---

### Step 6: Authentication certificate size limit

### Support Engineer Solution

The total size of all authentication certificates uploaded on Application Gateway V1 must be 131072 bytes or below. You can remove the unused authentication certificate from the Application Gateway or you can upgrade to V2 SKU.  

For more information, see [Remove-AzApplicationGatewayAuthenticationCertificate](https://learn.microsoft.com/en-us/powershell/module/az.network/remove-azapplicationgatewayauthenticationcertificate?view=azps-10.3.0)

### Customer Solution

*Content type: MarkdownText*

The total size of all authentication certificates uploaded on Application Gateway V1 must be 131072 bytes or below. You can remove the unused authentication certificate from the Application Gateway or you can upgrade to V2 SKU.  

For more information, see [Remove-AzApplicationGatewayAuthenticationCertificate](https://learn.microsoft.com/powershell/module/az.network/remove-azapplicationgatewayauthenticationcertificate?view=azps-10.3.0)

---

### Step 7: Application Gateway state ⭐ (First Step)

### Guidance

 This guided troubleshooter helps you to troubleshoot Application Gateway deployment failures.

### Question

**Identify your issue**

### Options

- **Application Gateway in failed state** → Go to: *Failed state*
- **Specific failed operation notification** → Go to: *Application Gateway errors*
- **Failed to save configuration changes to application gateway** → Go to: *Failed to save changes due to conflict with NSG*
- **None of the above** → Go to: *Non CRUD issue*

---

### Step 8: Application Gateway errors

### Guidance

Identify the error message that occurs in the activity logs, or the notification panel.

### Question

**Identify your error**

### Options

- **Errors related to certificates** → Go to: *Certificate errors*
- **Errors related to KeyVault** → Go to: *Key Vault related error*
- **Internal Error** → Go to: *Internal server error*
- **Failed to save configuration changes to application gateway** → Go to: *Failed to save changes due to conflict with NSG*
- **My error is not listed** → Go to: *Different error*

---

### Step 9: Certificate errors

### Guidance

Identify the certificate related error message.

### Question

**Identify your certificate error**

### Options

- **Data for certificate is invalid** → Go to: *Invalid certificate data*
- **Authentication certificate size is greater than the allowed 131072 bytes** → Go to: *Authentication certificate size limit*
- **Cannot have same certificate used across two trusted root certificate elements** → Go to: *Duplicate authentication and root certificate*
- **Invalid root certificate** → Go to: *Invalid certificate error*

---

### Step 10: Invalid certificate error

### Support Engineer Solution

This error occurs in Application Gateway V2 if you are trying to upload leaf or server certificate or complete certificate chain.  

Validate and make sure you are uploading only the root certificate in the Backend Settings.

  

For more information, see [Create certificates to allow the backend with Azure Application Gateway](https://learn.microsoft.com/azure/application-gateway/certificates-for-backend-authentication).

### Customer Solution

*Content type: MarkdownText*

This error occurs in Application Gateway V2 if you are trying to upload leaf or server certificate or complete certificate chain.  

Validate and make sure you are uploading only the root certificate in the Backend Settings.

  

For more information, see [Create certificates to allow the backend with Azure Application Gateway](https://learn.microsoft.com/azure/).

---

### Step 11: Issue resolved

### Support Engineer Solution

If you are facing additonal issues, you can restart the support request workflow using a different problem category to find a more relevant troubleshooter. 

### Customer Solution

*Content type: MarkdownText*

If you are facing additonal issues, you can restart the support request workflow using a different problem category to find a more relevant troubleshooter. 

---

### Step 12: Non CRUD issue

### Support Engineer Solution

Since your issue is not related to Create, read, update and delete (CRUD) failure, click **Start Again** to refresh your search.

### Customer Solution

*Content type: MarkdownText*

Since your issue is not related to Create, Read, Update and Delete (CRUD) failure, restart your request to better identify the issue you are experiencing. 

---

### Step 13: Different error

### Support Engineer Solution

Since your error is not listed in this troubleshooter, contact support for further assistance.

### Customer Solution

*Content type: MarkdownText*

Since your error is not listed in this troubleshooter, contact support for further assistance.

---

### Step 14: Internal server error

### Support Engineer Solution

If you are seeing an "Internal Server Error" message, refer to [Application Gateway infrastructure configuration](https://learn.microsoft.com/azure/application-gateway/configuration-infrastructure) to validate NSG, UDR, DNS settings on the Application Gateway virtual network.

If you are facing additonal issues, you can restart the support request workflow using a different problem category to find a more relevant troubleshooter. 

### Customer Solution

*Content type: MarkdownText*

If you are seeing an "Internal Server Error" message, refer to [Application Gateway infrastructure configuration](https://learn.microsoft.com/azure/application-gateway/configuration-infrastructure) to validate NSG, UDR, DNS settings on the Application Gateway virtual network.

If you are facing additonal issues, you can restart the support request workflow using a different problem category to find a more relevant troubleshooter. 

---

### Step 15: Failed to save changes due to conflict with NSG

### Support Engineer Solution

When you set up your application gateway to use the same port for both public and private listeners, an **Allow** rule in the Application Gateway's subnet associated NSG is required, allowing communication with both Private and Public Frontend IPs.

1. Go to the Overview section.

2. Take note of the Frontend IP addresses and Virtual network/subnet name.

3. Navigate to the NSG associated to the Application Gateway's subnet.

4. Create a inbound rule in the NSG allowing the APPGW Frontend Ip addresses as destination.

5. Set the rule priority value higher than any deny rule (smaller values represent a higher priority).

6. In the same inbound rule, allow the ports used by the listeners.

**Note:** The rule's source address should meet your connectivity requirements.

### Customer Solution

*Content type: MarkdownText*

1. Go to the Overview section.

2. Take note of the Frontend public IP address and Virtual network/subnet name.

3. Navigate to the NSG associated to the Application Gateway's subnet.

4. Create a inbound rule in the NSG allowing the APPGW Frontend public IP address as destination (the source will depend on the connectivity requirements).

5. In the same inbound rule, allow the ports used by the listeners.

---
