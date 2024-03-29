#!/bin/sh

# Based on https://learn.microsoft.com/en-us/azure/sap/monitor/quickstart-powershell
################ Change Variables - Mandatory! ################

export subscriptionId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX
export tenantId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX
export acssKVname=""

################ INFRA > Networking Variables ################
export LOCATION=eastus;
export AMS_RESOURCE_GROUP=ams_acss_rg;
export AMS_Managed=MRG_ams_acss_script;
export sapvnet=acss-vnet-sap;
export natGateway="acss-nat-gtw"

export amssubnet=AMSSubnet;
export amssubnetaddress="10.23.3.0/24"

################################################################ SET Subscription ################################################################

# Login
az login --tenant $tenantId;

# Set Subscription
az account set --subscription $subscriptionId;

# Create Resource Group
az group create --name $AMS_RESOURCE_GROUP --location $LOCATION;

# Create AMS Subnet
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $amssubnet  --address-prefixes $amssubnetaddress --delegations Microsoft.Web/serverfarms;

# Azure Monitor Variables
export amsName="AMS-Monitor"
export amsSubnetID="/subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Network/virtualNetworks/$sapvnet/subnets/$amssubnet"
export amsRouteOption="RouteAll"

# Ensure Azure CLI version is 2.48.1. Latest version available is 2.49.0
# update AZ Cli
az upgrade

# Create Azure Monitoring Resource
az workloads monitor create -g $RESOURCE_GROUP -n $amsName --location $LOCATION --app-location $LOCATION --managed-rg-name $AMS_RESOURCE_GROUP --monitor-subnet $amsSubnetID --routing-preference $amsRouteOption

# ADD HANA Provider
# https://learn.microsoft.com/en-us/azure/sap/monitor/quickstart-powershell#create-an-sap-hana-provider
# https://learn.microsoft.com/en-us/azure/sap/center-sap-solutions/manage-with-azure-rbac#register-and-manage-existing-sap-system

# Get more info about AMS Provider
#az workloads monitor provider-instance create --monitor-name $amsName -n $provider_name -g $RESOURCE_GROUP --provider-settings "??"
#az workloads monitor provider-instance create --monitor-name $amsName -n $provider_name -g $RESOURCE_GROUP --provider-settings sap-hana="??"

# The KV => Should be Azure role-based access control (recommended) 
# # Secret will be, example: HN1-HN1-sap-password

# Create Key Vault Roles - for future AMS Configuration
export myADUserID=$(az ad signed-in-user show --query "id" --output tsv)
export provider_name="AMS-Monitor-HANA"
export instanceNumber=00;

## IF you dont put the correspondent KeyVault - it will fetch one KV that correspond to your ACSSID 

if [ -z "$acssKVname" ]; then
	acssKVname=$(az keyvault list --query "[?location=='$LOCATION'].{name:name} | [?contains(name,'$acssid')]" -o tsv | tail -1) 
	echo "\nThe acssKVname was Updated to:\n$acssKVname"
else
    echo "\nThe current acssKVname is:\n$acssKVname"
fi

# Create KV Roles to access SAP DB Secret
az role assignment create --role "Key Vault Contributor" --assignee $acssMIID --scope $acssKVID --output tsv > $credDIR/$acssMI-KV-Role.txt
az role assignment create --role "Key Vault Contributor" --assignee $myADUserID --scope $acssKVID --output tsv > $credDIR/$localUser-KV-Role.txt

# Set KV Policy to be able to get/list secrets
az keyvault set-policy -n $acssKVname --object-id $myADUserID --secret-permissions get list --output tsv > $credDIR/$localUser-KV-Policy.txt

# Get DB PAssword from KV
export acssDBPassword=$(az keyvault secret show --name "${ACSSID}-${ACSSID}-sap-password" --vault-name $acssKVname --query "value")

# Get IP from Master SAP DB 
dbVMMasterName=${acssid}dbvmpr
vmRangeIP=${dbsubnetaddress:0:8}

dbVMMasterIP=$(az vm list-ip-addresses --ids $(az vm list -g $RESOURCE_GROUP --query "[?name=='$dbVMMasterName'].id" -o tsv) | grep $vmRangeIP | sed -e 's/^\s*//' -e '/^$/d' ) 

# Create HANA Provider on AMS Resource
az workloads monitor provider-instance create --monitor-name $amsName -n $provider_name -g $RESOURCE_GROUP \
--provider-settings '{
    "sap-hana": {
        "db-name": "SYSTEMDB",
        "db-username": "SYSTEM",
        "db-password": '$acssDBPassword',
        "instance-number": "'$instanceNumber'",
        "sap-sid": "'$ACSSID'",
        "hostname": '$dbVMMasterIP',
        "sql-port": "1433",
        "ssl-preference": "Disabled"
    }
}'

# If the provider is recently added, it may take up to 15 minutes for the initial telemetry information to be available for review. Else, check if system is down, or health of AMS system is degraded.

# Check Instance/Provider Information
az workloads monitor provider-instance show --monitor-name $amsName -n $provider_name -g $RESOURCE_GROUP;
