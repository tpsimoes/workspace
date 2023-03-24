#!/bin/sh

################ Variables - Change Mandatory! ################
export subscriptionId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX;
export sapfileNAME='FILENAME.ZIP'
export sapfilePATH='/PATH/TOFILE/FILENAME.ZIP'

################################################################ SET Subscription ################################################################

az account set --subscription $subscriptionId;

################################################################# Storage Account ################################################################ 
export LOCATION=eastus;
export RESOURCE_GROUP=hana_script;
export storage_sku=Standard_RAGRS
export storage_name=mysapstorage$RANDOM
export storage_container_name=sapsoftwarerepro

az storage account create --name $storage_name -g $RESOURCE_GROUP --location $LOCATION --sku $storage_sku --kind StorageV2
az storage container create -g $RESOURCE_GROUP -n $storage_container_name --account-name $storage_name --public-access blob;

###### GET Storage Account KEYs
# Destiny
myKEY=$(az storage account keys list --account-name $storage_name -g $RESOURCE_GROUP --output table | grep key1 | awk '{print $4}')

# Generate SAS TOKEN for Download
sasTOKEN=$(az storage container generate-sas --account-name $storage_name --account-key $myKEY --name $storage_container_name --permissions rl --expiry 2024-04-30T12:00:00Z --output tsv)

# Upload File
az storage blob upload --account-name $storage_name  --account-key $myKEY --container-name $storage_container_name --type block --file $sapfilePATH --name $sapfileNAME

# Create BlobURL for AZCopy
installerZipUrl=https://$storage_name.blob.core.windows.net/$storage_container_name/?$sasTOKEN

echo ""
echo "*******************************************************************************************"
echo "** This token MUST be added to the variable installerZipUrl on the script createInfra.sh **"
echo "*******************************************************************************************"
echo ""
echo $installerZipUrl

######################################################################################################################################## 