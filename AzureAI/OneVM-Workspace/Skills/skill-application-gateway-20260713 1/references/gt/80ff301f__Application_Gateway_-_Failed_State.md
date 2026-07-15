# Application Gateway - Failed State

> **Product:** Application Gateway  
> **Solution ID:** 80ff301f-3310-45b9-bc99-9824227fbf71  
> **Trigger words:** application, application gateway, failed, failed state, gateway, state

---

## Overview

This guide provides step-by-step troubleshooting for **Application Gateway - Failed State** under **Application Gateway**.
 The original guided troubleshooter contains 14 steps covering scoping, diagnosis, and resolution.

## Troubleshooting Steps

### Step 1: Is the Application Gateway in a failed state ⭐ (First Step)

### Guidance

Navigate to ASC and verify the Application Gateway provisioning state.

### Question

**Is the Application Gateway in a failed state**

### Options

- **Yes** → Go to: *Check CRUD dashboard using recent failed PUT operation ID Error Exception in NRP*
- **No** → Go to: *Exit*

---

### Step 2: Check CRUD dashboard using recent failed PUT operation ID Error Exception in NRP

### Guidance

Review the error details in the NRP logs.

Navigate to ASC → Operations, locate the first failed operation, and review the error message.

Ex:

Internal Server Error

ValidateKeyVaultSecrets exception

ApplicationGatewayCertificateDataOrKeyVaultSecretIdMustBeSpecified/ ApplicationGatewaySslCertificateDataMustBeSpecified 

### Question

**Identify the error you observed.**

### Options

- **Internal Server Error** → Go to: *Internal Server Error*
- **ValidateKeyVaultSecrets exception** → Go to: *Keyvault related issues*
- **Other causes** → Go to: *Other causes of Application Gateway failure*

---

### Step 3: Exit

### Support Engineer Solution

If the Application Gateway provisioning state is Succeeded, exit from the GT.

### Customer Solution

*Content type: MarkdownText*

If the Application Gateway provisioning state is Succeeded, exit from the GT.

---

### Step 4: Internal Server Error

### Support Engineer Solution

## Check NSG & UDR 

Check the NSG and UDR on the Application Gateway subnet. Ensure that the default route (0.0.0.0/0) is not force-tunneled from on-premises for the Public Application Gateway. The required NSG rules must be present according to the gateway SKU (V1 or V2).
https://learn.microsoft.com/en-us/azure/application-gateway/configuration-infrastructure#network-security-groups

================  

## Check for IP conflicts:

Error code : ApplicationGatewayILBDeploymentFailureDueToPrivateIPInUse

Frontend Operations Events:
https://portal.microsoftgeneva.com/s/4C073D09

Verify the conflicts exist between the Application Gateway instance IP addresses and the frontend private IP address.

“If the conflict is observed"

Resolution :

Private Frontend IP without a listener attached :

Delete the existing private frontend IP configuration either through the portal or by using the PowerShell command below.

$AppGw = Get-AzApplicationGateway -Name "appgw-test" -ResourceGroupName "dnstest-rg"
Remove-AzApplicationGatewayFrontendIPConfig -ApplicationGateway $AppGw -Name appGwPrivateFEIp
Set-AzApplicationGateway -ApplicationGateway $AppGw

Once this is done, perform a small PUT operation on the Application Gateway, and it will move to the Succeeded state.

If the private frontend IP is already attached to existing listeners and the customer does not want to delete the private frontend IP, follow the below steps :

Moving the listener to the public Frontend temporarily to delete the private Frontend Ip, then recreate it.

Note : Creating private frontend IP does not ensure that the IP address is reserved. If this frontend IP is not associated with any Listener and Routing rule, it is free to use and can get assigned to an instance during scaling events or VMSS repairs.

As a best practice, allocate the frontend private IP from the last available usable IP in the subnet, ensuring the broadcast IP remains reserved. If the IP is already selected from the last usable range and conflicts still occur, the subnet may be exhausted, and it is recommended to use a larger subnet. https://learn.microsoft.com/en-us/azure/application-gateway/configuration-infrastructure#size-of-the-subnet

=============

## Unable to resolve the OCSP and custom error page FQDNs.

If Application Gateway instances cannot resolve or reach the OCSP URLs and custom error page FQDNs, verify that the custom DNS server is reachable from the Application Gateway VNet on port 53 and ensure the DNS server can resolve these endpoints and is accessible from the App Gateway subnet.
https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-dns-resolution

Check the Tenant/Instance logs to observe the error:
https://portal.microsoftgeneva.com/s/708248E9

 Jarvis actions from the SAW (To check whether AppGW instances are able to resolve FQDNs) :
 
 Brooklyn > Application Gateways > Get List of NonResolvable Domains 
 https://portal.microsoftgeneva

*(Content truncated — refer to original GT for full details)*

### Step 5: Keyvault related issues

### Guidance

From the list below, select the Key Vault error that was observed.

### Question

**Identify the error shown below.**

### Options

- **Error: Microsoft.Azure.Networking.ApplicationGateway.ObjectModel.Exceptions.ApplicationGatewayKeyVaultException: An unknown error occurred [DNS related]** → Go to: *Unable to resolve the keyvault FQDN*
- **Problem occured while accessing and validating KeyVault Secrets associated with Application Gateway. Azure.RequestFailedException: Caller is not authorized to perform action on resource.  [Connectivity issues to the Keyvault endoint with Layer 4 issues]** → Go to: *Unable to connect to the Keyvault endpoint Layer 4 issue*
- **Error in getting certificate [Secret not able to fetch] from the key vault and also issues related to the Managed identity.** → Go to: *Error in getting certificate Secret not able to fetch from the key vault and also issues related to the Managed identity*
- **ApplicationGatewayCertificateDataOrKeyVaultSecretIdMustBeSpecified / ApplicationGatewaySslCertificateDataMustBeSpecified** → Go to: *Unable to update listener SSL certificate*

---

### Step 6: Unable to resolve the keyvault FQDN

### Guidance

If the Application Gateway is unable to resolve the Key Vault FQDN, follow the steps below.

### Question

**Are custom DNS servers configured on the AppGW VNET**

### Options

- **Yes** → Go to: *If keyvault using Privateendpoint*
- **No** → Go to: *If the ApplicationGateway VNET doesnot have CustomDNS Server*

---

### Step 7: If keyvault using Privateendpoint

### Guidance

If the Key Vault is using a private endpoint or not, follow the steps below.

### Question

**Is KeyVault configured with a private endpoint**

### Options

- **Yes** → Go to: *KeyVault is configured with a private endpoint*
- **No** → Go to: *KeyVault is not configured to use a private endpoint*

---

### Step 8: KeyVault is configured with a private endpoint

### Support Engineer Solution

 ## Layer 4 Connectivity to the Custom DNS Server on Port 53.

 ApplicationGateway subnet should have L4 connectivity to the custom DNS server on port 53.

Check the Tenant/Instance logs to observe the error :

https://portal.microsoftgeneva.com/s/708248E9

 Jarvis actions from the SAW (To check whether AppGW instances are able to resolve FQDNs) :

 

 Brooklyn > Application Gateways > Get List of NonResolvable Domains 

 https://portal.microsoftgeneva.com/4EA1EBF0?genevatraceguid=50e337ee-229d-4db8-9e2c-b36bec2a4c75

## If Custom DNS server is hosted in Azure :

If the custom DNS server is hosted in Azure, ensure that the custom DNS server VNET is linked to the Private DNS zone of the Key Vault private endpoint. Also, ensure that an A record or a DNS forwarder exists on the custom DNS server and that it resolves to the Key Vault private endpoint IP.

https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-dns-resolution#using-custom-dns-servers

## If Custom DNS server is hosted in On-premises:

If the custom DNS server is hosted on-premises and the customer is using a forwarder to forward records to Azure—either via a Private Resolver or a DNS server—make sure to link the respective VNet to the Private DNS Zone of the Keyvault Private endpoint.Also, ensure that an A record or a DNS forwarder exists on the custom DNS server and that it resolves to the Key Vault private endpoint IP.

https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns-integration#on-premises-workloads-using-a-dns-forwarder-without-azure-private-resolver

======================

## AppGateway with Private only Front end IP(networkIsolationEnabled: True)

The private application gateway deployment is designed to separate the customer’s data plane and management plane traffic. Therefore, having default Azure DNS or custom DNS servers has no effect on the critical management endpoints name resolutions. However, when using custom DNS servers, you must take care of name resolutions required for any data path operations.

The resolution of all management endpoints goes via management plane traffic that directly interacts with the Azure-provided DNS.

https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-dns-resolution#gateways-with-private-ip-address-only-networkisolationenabled-true

### Customer Solution

*Content type: MarkdownText*

 ## Layer 4 Connectivity to the Custom DNS Server on Port 53.

 ApplicationGateway subnet should have L4 connectivity to the custom DNS server on port 53.

Check the Tenant/Instance logs to observe the error :

https://portal.microsoftgeneva.com/s/708248E9

 Jarvis actions from the SAW (To check whether AppGW instances are able to resolve FQDNs) :

 

 Brooklyn > Application Gateways > Get List of NonResolvable Domains 

 https://portal.microsoftgeneva.com/4EA1EBF0?genevatraceguid=50e337ee-229d-4db8-9e2c-b36bec2a4c75

## If Custom DNS server is hosted i

*(Content truncated — refer to original GT for full details)*

### Step 9: KeyVault is not configured to use a private endpoint

### Support Engineer Solution

## DNS resolution to the Key Vault FQDN using the public IP from the custom DNS server.

Custom DNS server should be able to resolve the Key Vault FQDN to its public IP.

Check the Tenant/Instance logs to observe the error

https://portal.microsoftgeneva.com/s/708248E9

 Jarvis actions from the SAW (To check whether AppGW instances are able to resolve FQDNs) :

 

 Brooklyn > Application Gateways > Get List of NonResolvable Domains 

 https://portal.microsoftgeneva.com/4EA1EBF0?genevatraceguid=50e337ee-229d-4db8-9e2c-b36bec2a4c75

If the customer’s DNS server is unable to resolve the Key Vault FQDN to its public IP address, investigate the cause of the resolution failure. Verify whether a DNS forwarder is configured to the Azure default DNS IP :168.63.129.16 or to another public DNS service (for example, Google DNS) for resolving internet endpoints. Ensure that the DNS server is able to resolve the Key Vault FQDN, and adjust the DNS configuration accordingly to enable proper resolution.

### Customer Solution

*Content type: MarkdownText*

## DNS resolution to the Key Vault FQDN using the public IP from the custom DNS server.

Custom DNS server should be able to resolve the Key Vault FQDN to its public IP.

Check the Tenant/Instance logs to observe the error

https://portal.microsoftgeneva.com/s/708248E9

 Jarvis actions from the SAW (To check whether AppGW instances are able to resolve FQDNs) :

 

 Brooklyn > Application Gateways > Get List of NonResolvable Domains 

 https://portal.microsoftgeneva.com/4EA1EBF0?genevatraceguid=50e337ee-229d-4db8-9e2c-b36bec2a4c75

If the customer’s DNS server is unable to resolve the Key Vault FQDN to its public IP address, investigate the cause of the resolution failure. Verify whether a DNS forwarder is configured to the Azure default DNS IP :168.63.129.16 or to another public DNS service (for example, Google DNS) for resolving internet endpoints. Ensure that the DNS server is able to resolve the Key Vault FQDN, and adjust the DNS configuration accordingly to enable proper resolution.

---

### Step 10: If the ApplicationGateway VNET doesnot have CustomDNS Server

### Support Engineer Solution

## If the Application Gateway VNET uses the default DNS server and the Key Vault has a private endpoint :

If the Application Gateway VNET is using Azure-provided (default) DNS: 168.63.129.16 and the Key Vault is using a private endpoint, ensure that the Application Gateway VNET is linked to the Private DNS zone of the keyvault privatelink.vaultcore.azure.net and that the zone contains an A record resolving to the private endpoint IP address.

https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-dns-resolution#using-default-azure-provided-dns

Check the Tenant/Instance logs to observe the error

https://portal.microsoftgeneva.com/s/708248E9

 Jarvis actions from the SAW (To check whether AppGW instances are able to resolve FQDNs) :

 

 Brooklyn > Application Gateways > Get List of NonResolvable Domains 

 https://portal.microsoftgeneva.com/4EA1EBF0?genevatraceguid=50e337ee-229d-4db8-9e2c-b36bec2a4c75

### Customer Solution

*Content type: MarkdownText*

## If the Application Gateway VNET uses the default DNS server and the Key Vault has a private endpoint :

If the Application Gateway VNET is using Azure-provided (default) DNS: 168.63.129.16 and the Key Vault is using a private endpoint, ensure that the Application Gateway VNET is linked to the Private DNS zone of the keyvault privatelink.vaultcore.azure.net and that the zone contains an A record resolving to the private endpoint IP address.

https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-dns-resolution#using-default-azure-provided-dns

Check the Tenant/Instance logs to observe the error

https://portal.microsoftgeneva.com/s/708248E9

 Jarvis actions from the SAW (To check whether AppGW instances are able to resolve FQDNs) :

 

 Brooklyn > Application Gateways > Get List of NonResolvable Domains 

 https://portal.microsoftgeneva.com/4EA1EBF0?genevatraceguid=50e337ee-229d-4db8-9e2c-b36bec2a4c75

---

### Step 11: Unable to connect to the Keyvault endpoint Layer 4 issue

### Support Engineer Solution

 ## Issue Description : Key Vault is configured with restricted network access.

From the ASC insights you may observe the below Error :

Failed to download secrets from Key Vault: Application Gateway failed to download secret(s) from xxxx.vault.azure.net with exception KeyVaultHasRestrictedAccess.

From the Tenant/Instance logs error message:

https://portal.microsoftgeneva.com/s/BFFBEC81

Exception thrown while getting Secret: https://xxxxx.vault.azure.net/secrets/xxxxxxx

Azure.RequestFailedException: Client address is not authorized and caller is not a trusted service.

Status: 403 (Forbidden)

ErrorCode: Forbidden

You can execute the Kusto query below to check the error log.

cluster('Hybridnetworking').database('aznwmds').

ApplicationGatewayTenant 

| where GatewayId contains "xxxxxxxxxxxxxxxxxxx"

| where ComponentName contains "KeyVaultSecretRetriever"

| where PreciseTimeStamp >= ago(1d) //| take 1

| project PreciseTimeStamp, ActivityName, Level, Msg

| limit 1000 

## Resolution :

Check the connectivity between the Application Gateway VNET/Subnet to the Keyvault PublicIP/Privateendpoint IP.

Check the NSG and UDR on the Application Gateway subnet, and also validate the return traffic (routing) from the Key Vault in a private endpoint scenario.

Ensure that there is connectivity between AppGW & Keyvault.

## From the keyvault side :

In Key Vault, open the Networking pane.

Select the Firewalls and virtual networks tab, and select Private endpoint and selected networks.

Then, using Virtual Networks, add your Application Gateway's virtual network and subnet. During the process, also configure 'Microsoft.KeyVault' service endpoint by selecting its checkbox.

Finally, select Yes to allow Trusted Services to bypass Key Vault's firewall.

https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-key-vault-common-errors#error-code-keyvaulthasrestrictedaccess

### Customer Solution

*Content type: MarkdownText*

 ## Issue Description : Key Vault is configured with restricted network access.

From the ASC insights you may observe the below Error :

Failed to download secrets from Key Vault: Application Gateway failed to download secret(s) from xxxx.vault.azure.net with exception KeyVaultHasRestrictedAccess.

From the Tenant/Instance logs error message:

https://portal.microsoftgeneva.com/s/BFFBEC81

Exception thrown while getting Secret: https://xxxxx.vault.azure.net/secrets/xxxxxxx

Azure.RequestFailedException: Client address is not authorized and caller is not a trusted service.

Status: 403 (Forbidden)

ErrorCode: Forbidden

You can execute the Kusto query below to check the error log.

cluster('Hybridnetworking').database('aznwmds').

ApplicationGatewayTenant 

| where GatewayId contains "xxxxxxxxxxxxxxxxxxx"

| where ComponentName contains "KeyVaultSecretRetriever"

| where PreciseTimeStamp >= ago(1d) //| take 1

| project PreciseTimeStamp, ActivityName, Level, Msg

| limit 1000 

#

*(Content truncated — refer to original GT for full details)*

### Step 12: Other causes of Application Gateway failure

### Support Engineer Solution

## Application Gateway VNET provisioning state is Failed.

Application Gateway VNET provisioning state is in a failed state.

Do (GET-SET) from the Powershell

Get-AzVirtualNetwork -Name "your_resource_name" -ResourceGroupName "your_resource_group_name" | Set-AzVirtualNetwork

https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state#microsoftnetworkvirtualnetworks

===================

## Straightforward messages:

Sometimes, NRP provides straightforward messages explaining why the App Gateway is in a failed state, allowing you to adjust the configuration accordingly.

=====================

## For any other error messages or if the error cannot be identified:

If you see any other messages or are unable to identify the error, try performing a GET-SET on the Application Gateway. This will provide the error message indicating which dependent service is causing the issue, and sometimes it can also resolve the problem.

Get-AzApplicationGateway -Name "your_resource_name" -ResourceGroupName "your_resource_group_name" | Set-AzApplicationGateway

https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state#microsoftnetworkapplicationgateways

### Customer Solution

*Content type: MarkdownText*

## Application Gateway VNET provisioning state is Failed.

Application Gateway VNET provisioning state is in a failed state.

Do (GET-SET) from the Powershell

Get-AzVirtualNetwork -Name "your_resource_name" -ResourceGroupName "your_resource_group_name" | Set-AzVirtualNetwork

https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state#microsoftnetworkvirtualnetworks

================

## Straightforward messages:

Sometimes, NRP provides straightforward messages explaining why the App Gateway is in a failed state, allowing you to adjust the configuration accordingly.

=============

## For any other error messages or if the error cannot be identified:

If you see any other messages or are unable to identify the error, try performing a GET-SET on the Application Gateway. This will provide the error message indicating which dependent service is causing the issue, and sometimes it can also resolve the problem.

Get-AzApplicationGateway -Name "your_resource_name" -ResourceGroupName "your_resource_group_name" | Set-AzApplicationGateway

https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state#microsoftnetworkapplicationgateways

---

### Step 13: Error in getting certificate Secret not able to fetch from the key vault and also issues related to the Managed identity

### Support Engineer Solution

## SecretDisabled :

From the instance/Tenant or FrontendOperationEteEvent logs,, if we are seeing the 403 (Forbidden), operation get is not allowed on a disabled secret (Code : Secret disabled)

Tenant/Instance logs :
https://portal.microsoftgeneva.com/s/708248E9

Frontend Operations Events:
https://portal.microsoftgeneva.com/s/4C073D09
 
## Resolution :
 
Go to the keyvault,and enable the secret.
https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-key-vault-common-errors#error-code-secretdisabled

======================

## ErrorCode: SecretNotFound

Issue Description: The associated certificate has been deleted from Key Vault.

From the instance/Tenant/FrontendOperationEteEvent logs, if we are seeing "error":{"code":"SecretNotFound"}
Status: 404 (Not Found)

Tenant/Instance logs :
https://portal.microsoftgeneva.com/s/708248E9

Frontend Operations Events:
https://portal.microsoftgeneva.com/s/4C073D09

## Scenario 1)If a versionless certificate is deleted from the Key Vault.

Resolution :

Check whether the certificate is being used by any listener. If the certificate is not associated with any listener, go to the TLS Certificates blade and delete the stale entry. Then perform a small PUT operation on the Application Gateway, and it will move to the Succeeded state.

## If the certificate is associated with listener : 

To recover a deleted certificate from the keyvault:

Go to the linked key vault in the Azure portal.
Open the Certificates pane.
Use the Managed deleted certificates tab to recover a deleted certificate.
https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-key-vault-common-errors#error-code-secretdeletedfromkeyvault.

If a certificate object is permanently deleted from the Key Vault, re-upload the SSL certificate to the Key Vault using the same certificate name and perform a small PUT operation on the Gateway; it will then move to the Succeeded state.

## Scenario 2) If an old versioned certificate is deleted from the Key Vault and a new certificate is uploaded, auto-rotation will not take place because the Application Gateway is still referencing the old versioned certificate, causing it to transition to the Failed state.

Resolution :

Check whether the certificate is being used by any listener. If the certificate is not associated with any listener, go to the TLS Certificates blade and delete the stale entry. Then perform a small PUT operation on the Application Gateway, and it will move to the Succeeded state.

## If the certificate is associated with listener : 

Application Gateway uses a secret identifier in Key Vault to reference the certificates. For Azure PowerShell, the Azure CLI, or Azure Resource Manager, we strongly recommend that you use a secret identifier that doesn't specify a version. This way, Application Gateway automatically rotates the certificate if a newer version is available in your Key Vault. An example of a secret UR

*(Content truncated — refer to original GT for full details)*

### Step 14: Unable to update listener SSL certificate

### Support Engineer Solution

## Issue : Unable to update listener SSL certificate on Azure Application Gateway

Description: Customer attempted to renew the SSL certificate on the Application Gateway either by directly uploading the certificate to the Application Gateway or by uploading it to Azure Key Vault and referencing it from the Application Gateway. During this process, the Application Gateway transitioned to a Failed provisioning state.

Steps to verify that the uploaded certificate is invalid or corrupted :

Follow these steps to install the uploaded PFX on a Windows machine.

1)If it does not prompt for a password (it wasn't a password protected pfx with a private key) which is the issue.

2)On the same screen where it prompts for the password, make sure to select “Mark this key as exportable.” Complete the installation into Windows.

If this fails, it is further proof that the certificate is invalid (for example, it does not contain a private key).

3)If the certificate imports into Windows successfully, then:

Open certmgr.msc.

Locate the certificate in the Personal certificate store.

Right-click the certificate and select Export.

Choose Export the private key : If there is no option to export the private key, it means the private key is missing, which is the issue.

Select “Include all certificates in the certification path if possible.”

Set a simple password.

Save the file using TripleDES-SHA1.

Now that you have a valid, working certificate, try replacing it with the bad certificate.

Scenario 1 : Update certificate uploaded directly to Application Gateway:

$appgw = Get-AzApplicationGateway -ResourceGroupName "<ResourceGroup>" -Name "<AppGatewayName>"

$password = ConvertTo-SecureString -String "<password>" -Force -AsPlainText

Set-AzApplicationGatewaySSLCertificate -Name "<oldcertname>" -ApplicationGateway $appgw -CertificateFile "<newcertPath>" -Password $password

Set-AzApplicationGateway -ApplicationGateway $appgw

Scenario 2 : Update certificate referenced from Azure Key Vault:

Upload the valid/working certificate to the keyvault.

Then , execute below Powershell commands.

$appgw = Get-AzApplicationGateway -ResourceGroupName "<ResourceGroup>" -Name "<AppGatewayName>"

$secret = Get-AzKeyVaultSecret -VaultName "<KeyVaultName>" -Name "<CertificateName>" 

$secretId = $secret.Id.Replace($secret.Version, "") 

$cert = Set-AzApplicationGatewaySslCertificate -ApplicationGateway $AppGW -Name "<CertificateName>" -KeyVaultSecretId $secretId 

Set-AzApplicationGateway -ApplicationGateway $appgw

https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-key-vault-common-errors#application-gateway-error-codes

	

### Customer Solution

*Content type: MarkdownText*

## Issue : Unable to update listener SSL certificate on Azure Application Gateway

Description: Customer attempted to renew the SSL certificate on the Application Gateway either by directly uploading the certificate to the Application Gateway or 

*(Content truncated — refer to original GT for full details)*
