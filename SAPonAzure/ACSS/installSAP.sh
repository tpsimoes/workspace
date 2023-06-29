#!/bin/sh

################ Change Variables - Mandatory! ################

export subscriptionId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX
export tenantId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX

export sap_user="USER@XXXX.com"
export sap_password="SAPPASSWORD"

export bom_base_name="S4HANA_2021_ISS_v0001ms"

# SAP S/4HANA 1909 SPS03 or SAP S/4HANA 2020 SPS 03 or SAP S/4HANA 2021 ISS 00
export softwareBOMVersion="SAP S/4HANA 2021 ISS 00";

################ INFRA > Networking Variables ################

export LOCATION=eastus;
export RESOURCE_GROUP=acss_script;
export sapvnet=acss-vnet-sap;
export appsubnet=app;
export centralsubnet=app;
export dbsubnet=db;

################################################################ SET Subscription ################################################################

#Login
az login --tenant $tenantId;

#Set Subscription
az account set --subscription $subscriptionId;

########################## StorageAccount & BOM Variables for SAP BOM File
export storage_name=acsssapscript
export storage_container_name=sapbits

storage_account_access_key=$(az storage account keys list --account-name $storage_name -g $RESOURCE_GROUP --output table | grep key1 | awk '{print $4}')

export orchestration_ansible_user="azureuser"
export BOM_directory="/home/$orchestration_ansible_user/SAP-automation-samples/SAP"
export playbook_path="/home/$orchestration_ansible_user/sap-automation/deploy/ansible/playbook_bom_downloader.yaml"

########################## Directories
export credDIR=/home/$localUser/$RESOURCE_GROUP/cred;
export dataDIR=/home/$localUser/$RESOURCE_GROUP/data;
export keyDIR=/home/$localUser/$RESOURCE_GROUP/ssh;
localUser=$(whoami)

############################################ Install SAP Software on VIS
################### After ACSS creation  
# Give all VMs - ManagedIdentity Contrib Role to the ACSS RG
# https://learn.microsoft.com/en-us/azure/sap/center-sap-solutions/quickstart-install-high-availability-namecustom-cli#create-json-configuration-file

##### Auth - Create SP to be contrib on ACSS RG - FENCING
acssVMlist=$(az vm list -g $RESOURCE_GROUP --query "[].name" -o tsv | grep $acssid)

while IFS= read -r vmsapname; do
	spID=$(az resource list -n $vmsapname -g $RESOURCE_GROUP --query "[*].identity.principalId" -o tsv)
	az role assignment create --assignee $spID --role Contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP
done <<< "$acssVMlist"
 
export fencingDisplayName=acssfence_$RANDOM

az ad app create --display-name $fencingDisplayName --output tsv > 	$credDIR/$fencingDisplayName.txt

# Get AD APPID and AD ObjectID
appID=$(cat $credDIR/$fencingDisplayName.txt | awk '{print $3}')
objectID=$(cat $credDIR/$fencingDisplayName.txt | awk '{print $14}')

# Get AD APP Password
az ad app credential reset --id $objectID --output tsv > $credDIR/$fencingDisplayName-cred.txt
fencingID=$(cat $credDIR/$fencingDisplayName-cred.txt | awk '{print $1}')
fencingPassword=$(cat $credDIR/$fencingDisplayName-cred.txt | awk '{print $2}')
TenantId=$(cat $credDIR/$fencingDisplayName-cred.txt | awk '{print $3}')

# AD SP Creation
az ad sp create --id $fencingID --output tsv > $credDIR/$fencingDisplayName-SP.txt
az role assignment create --assignee $fencingID --role Contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP --output tsv > $dataDIR/$fencingDisplayName-Role.txt

# Install Template Variables
export payloadInstallFILE=$dataDIR/$VIS-Install-template.json
export sapstgBOMUrl="${sapbits_location_base_path}/sapfiles/boms/${bom_base_name}/${bom_base_name}.yaml"
export sapBitsSTGId="/subscriptions/${subscriptionId}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Storage/storageAccounts/${storage_name}"

################## SSH Keys 
# This values must be the same used on the createInfra
# Created by this command:
# ssh-keygen -m PEM -t rsa -b 4096 -C "'${adminUser}'@'${ACSSID}'" -f $keyDIR/${ACSSID}-PEM -N '' <<<y >/dev/null 2>&1

# PEM Pub
pubKeyPEM=$(cat $keyDIR/${ACSSID}-PEM.pub)

# PEM Private Key Escape Char replacement_text
export hashKEYFile=$dataDIR/temp.file
sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g' ${keyDIR}/${ACSSID}-PEM | sed 's/\\n$//' > $hashKEYFile
replacement_text=$(<"$hashKEYFile")
escaped_replacement_text=$(sed 's/[\&/]/\\&/g; s/$/\\/' <<< "$replacement_text")

################## SAP & Infra Variables 

export ACSSID=HN1
export acssid=hn1
export VIS=ACSS$ACSSID
export enviromentType=NonProd
export visProduct=s4hana

export skuVM=gen2
export vmPublisher=SUSE
export vmImageVersion=latest
export offerImage=sles-sap-15-sp3
export versionImage=latest
export centralVMSize=Standard_E8ds_v5
export appVMSize=Standard_E8ds_v5
export dbVMSize=Standard_E16ds_v5
export adminVISUser=azureuser

################## Create JSON File for SAP Installation
#Get JSON Sample File
curl https://raw.githubusercontent.com/tpsimoes/workspace/master/SAPonAzure/ACSS/installTemplateAVSetHA.json -o $payloadInstallFILE

#appLocation
sed -i "s/<infraLocation>/${LOCATION}/g" $payloadInstallFILE

#deploymentType
sed -i "s/<infraDeploymentType>/ThreeTier/g" $payloadInstallFILE

#highAvailabilityType
sed -i "s/<infraHighAvailabilityType>/AvailabilitySet/g" $payloadInstallFILE

#subscriptionId
sed -i "s/<subscriptionID>/${subscriptionId}/g" $payloadInstallFILE

#resourceGroupName
sed -i "s/<resourceGroupName>/${RESOURCE_GROUP}/g" $payloadInstallFILE

#vnetName & subnet
sed -i "s/<vnetName>/${sapvnet}/g" $payloadInstallFILE
sed -i "s/<dbSubnetName>/${dbsubnet}/g" $payloadInstallFILE
sed -i "s/<centralSubnetName>/${centralsubnet}/g" $payloadInstallFILE
sed -i "s/<appSubnetName>/${appsubnet}/g" $payloadInstallFILE

#suse image
sed -i "s/<skuVM>/${skuVM}/g" $payloadInstallFILE
sed -i "s/<vmImagePublisher>/${vmPublisher}/g" $payloadInstallFILE
sed -i "s/<vmImageVersion>/${vmImageVersion}/g" $payloadInstallFILE
sed -i "s/<offerVMImage>/${offerImage}/g" $payloadInstallFILE

#App & Central Server Size
sed -i "s/<centralVMSize>/${centralVMSize}/g" $payloadInstallFILE
sed -i "s/<appVMSize>/${appVMSize}/g" $payloadInstallFILE
sed -i "s/<dbVMSize>/${dbVMSize}/g" $payloadInstallFILE

#Admin User
sed -i "s/azureuser/${adminVISUser}/g" $payloadInstallFILE

# SAP ACSSID
sed -i "s/<acssid>/${acssid}/g" $payloadInstallFILE

#appResourceGroup
sed -i "s/<appResourceGroupName>/${RESOURCE_GROUP}/g" $payloadInstallFILE

# SAP FQDN
sed -i "s/<sapFqdn>/${acssid}.local/g" $payloadInstallFILE

# PEM Pub
sed -i 's,'"PublicSSHKey"','${pubKeyPEM}',' "$payloadInstallFILE"

# PEM Private Key Escape Char replacement_text
awk -v replacement="$escaped_replacement_text" '{gsub(/PrivateSSHKey/, replacement)} 1' FS="\n" OFS="\n" "$payloadInstallFILE" > temp && mv temp "$payloadInstallFILE";

# SAP BOOM
escaped_sapstgBOMUrl=$(printf '%s\n' "$sapstgBOMUrl" | sed -e 's/[[\.*^$/]/\\&/g')
sed -i "s/<sapstgBOMUrl>/$escaped_sapstgBOMUrl/g" "$payloadInstallFILE"

escaped_softwareBOMVersion=$(printf '%s\n' "$softwareBOMVersion" | sed -e 's/[[\.*^$/]/\\&/g')
sed -i "s/<softwareBOMVersion>/$escaped_softwareBOMVersion/g" "$payloadInstallFILE"

escaped_sapBitsSTGId=$(printf '%s\n' "$sapBitsSTGId" | sed -e 's/[[\.*^$/]/\\&/g')
sed -i "s/<sapBitsSTGId>/$escaped_sapBitsSTGId/g" "$payloadInstallFILE"

sed -i "s/<fencingID>/${fencingID}/g" $payloadInstallFILE
sed -i "s/<fencingPassword>/${fencingPassword}/g" $payloadInstallFILE

# Installation process
# Nº	Step										Description																																									Estimated Time
# 1		Configuring installation support packages	Configuring SAP installation toolkit (e.g. Ansible, Python, JQ, Wheel, etc ), uploading secrets, etc.																		~5-7 	min
# 2		Running Validations							Verifying storage account details, validating SAP parameters, checking network connectivity.																				~1-2 	min
# 3		Downloading SAP media						Preparing to download SAP media from storage account																														~25-180 min
# 4		Installing ASCS								Installing software on ASCS server(s). If it is an HA setup, HA configuration will also be carried out																		~20-60 	min
# 5		Installing database							Installing software on the database server(s).																																~15-60 	min
# 6		Readying database							Preparing database schema such as creating appropriate directories, loading sap parameters on database server(s) (e.g. ASCS hostname, database virtual hostname, etc.)		~45-90 min
# 7		Configuring HA for database(s)**			Configuring high availability for database servers using clustering software. Only valid in the case of HA setup.															~20-60 min
# 8		PAS install									Installing software on primary (first) application server.																													~15-60 min
# 9		App install									Installing software on additional application server(s). Only applicable in the cases where there is more than one application server else the step will be skipped			~15-60 min
# 10	Starting post-install Discovery				Logging progress and discovering metadata for the Virtual Instance for SAP solution(VIS) [e.g message server IP address, port, ICM Port, Database Port, etc.]				~5-10 min

# * Estimated time for each task to complete could be less or more depending upon various factors such as deployment type, network bandwidth, retries, etc.
# ** This step will be carried out only when the deployment type is "Distributed with High Availability".

az workloads sap-virtual-instance create -g $RESOURCE_GROUP -n $ACSSID --environment $enviromentType --sap-product $visProduct --configuration $payloadInstallFILE \
--identity "{type:UserAssigned,userAssignedIdentities:{$acssMIRGID:{}}}"

# Expected Result After:
  # "name": "HN1",
  # "provisioningState": "Succeeded",
  # "resourceGroup": "acss_script",
  # "sapProduct": "S4HANA",
  # "state": "RegistrationComplete",