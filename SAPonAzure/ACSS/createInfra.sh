#!/bin/sh

################ Change Variables - Mandatory! ################

export subscriptionId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX
export tenantId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX

export sap_user="USER@XXXX.com"
export sap_password="SAPPASSWORD"

################ INFRA > Networking Variables ################

export LOCATION=eastus;
export RESOURCE_GROUP=acss_script;
export sapvnet=acss-vnet-sap;
export sapvnetaddress="10.23.0.0/22"
export appsubnet=app;
export dbsubnet=db;
export bastionsubnet=AzureBastionSubnet;
export appsubnetaddress="10.23.0.0/24"
export dbsubnetaddress="10.23.1.0/24"
export bastionsubnetaddress="10.23.2.0/26"

############################################################### ACSS - SAP HANA   ################################################################
# High availability of SAP HANA on Azure VMs on SLES | Microsoft Learn
# https://learn.microsoft.com/en-us/azure/sap/center-sap-solutions/prepare-network

################################################################ SET Subscription ################################################################

#Login
az login --tenant $tenantId;

#Set Subscription
az account set --subscription $subscriptionId;

################################################################ Create Infra ####################################################################
localUser=$(whoami)

#RG Create
az group create --name $RESOURCE_GROUP --location $LOCATION;

#VNET
az network vnet create --address-prefixes $sapvnetaddress --name $sapvnet --resource-group $RESOURCE_GROUP;

#Subnets  
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $appsubnet     --address-prefixes $appsubnetaddress;
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $dbsubnet      --address-prefixes $dbsubnetaddress;
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $bastionsubnet --address-prefixes $bastionsubnetaddress;

############# Bastion & NatGateway
export zone="1"
export sku="standard"
export allocationMethod="static"
export natGateway="acss-nat-gtw"
export ntgwpublicIp="nat-gtw-pip"
export bastionPublicIp="bastion-pip"
export bastionHost="acss-bastion"

# Create public IP address
echo "Creating $ntgwpublicIp"
az network public-ip create --resource-group $RESOURCE_GROUP --location $LOCATION --name $ntgwpublicIp --sku $sku --allocation-method $allocationMethod --zone $zone

# Create NAT gateway resource
echo "Creating $natGateway using $ntgwpublicIp" 
az network nat gateway create --resource-group $RESOURCE_GROUP --name $natGateway --public-ip-addresses $ntgwpublicIp --idle-timeout 10

# Create a public IP address for the bastion host
echo "Creating $bastionPublicIp"
az network public-ip create --resource-group $RESOURCE_GROUP --name $bastionPublicIp --sku $sku --zone $zone

# Create the bastion host
echo "Creating $bastionHost using $bastionPublicIp"
az network bastion create --resource-group $RESOURCE_GROUP --name $bastionHost --public-ip-address $bastionPublicIp --vnet-name $sapvnet --location $LOCATION 

# Configure NAT service for source subnet
echo "Creating $natGateway for $subnet"
az network vnet subnet update --resource-group $RESOURCE_GROUP --vnet-name $sapvnet --name $appsubnet --nat-gateway $natGateway
az network vnet subnet update --resource-group $RESOURCE_GROUP --vnet-name $sapvnet --name $dbsubnet  --nat-gateway $natGateway

########################## StorageAccount for SAP BOM File

export storage_name=acsssapscript
export storage_container_name=sapbits
export storage_sku=Standard_RAGRS

export bom_base_name="S4HANA_2021_ISS_v0001ms"
export sapbits_location_base_path="https://${storage_name}.blob.core.windows.net/$storage_container_name"

az storage account create --name $storage_name -g $RESOURCE_GROUP --location $LOCATION --sku $storage_sku --kind StorageV2
storage_account_access_key=$(az storage account keys list --account-name $storage_name -g $RESOURCE_GROUP --output table | grep key1 | awk '{print $4}')
az storage container create -g $RESOURCE_GROUP -n $storage_container_name --account-name $storage_name;

########################## AUTH x2 
# One for ACSS + STG
# One for VMS

export appDisplayName=acss_$RANDOM

export credDIR=/home/$localUser/$RESOURCE_GROUP/cred;
export dataDIR=/home/$localUser/$RESOURCE_GROUP/data;
export keyDIR=/home/$localUser/$RESOURCE_GROUP/ssh;

mkdir -p $credDIR
mkdir -p $dataDIR
mkdir -p $keyDIR

# Create App AD User - to avoid AzAccount browser request
az ad app create --display-name $appDisplayName --output tsv > $credDIR/$appDisplayName.txt

# Get AD APPID and AD ObjectID
appID=$(cat $credDIR/$appDisplayName.txt | awk '{print $3}')
objectID=$(cat $credDIR/$appDisplayName.txt | awk '{print $14}')

# Get AD APP Password
az ad app credential reset --id $objectID --output tsv > $credDIR/$appDisplayName-cred.txt
ApplicationId=$(cat $credDIR/$appDisplayName-cred.txt | awk '{print $1}')
Password=$(cat $credDIR/$appDisplayName-cred.txt | awk '{print $2}')
TenantId=$(cat $credDIR/$appDisplayName-cred.txt | awk '{print $3}')

# AD SP Creation
az ad sp create --id $ApplicationId
az role assignment create --assignee $ApplicationId --role Contributor --scope /subscriptions/$subscriptionId --output tsv > $credDIR/$appDisplayName-SP.txt

############################## Jumpbox

export jmpVMsize=Standard_D2s_v5
export jmpVmName=jumpbox
export jmpVMNic=jmpNicVM
export jmpImage="Ubuntu2204";
export adminUser=azureuser
export PASSWORD=Password2023!

export myIP=$(curl http://ifconfig.co)
export myIPnsgRULEname=AllowMyIP
export vnetNSGname=$sapvnet-$appsubnet-nsg-$LOCATION

az network nsg create --resource-group $RESOURCE_GROUP --name $vnetNSGname;

az network nsg rule create -g $RESOURCE_GROUP  --nsg-name $vnetNSGname -n $myIPnsgRULEname --priority 1001 \
--source-address-prefixes $myIP --source-port-ranges '*' --destination-address-prefixes '*' \
--destination-port-ranges 22 --access Allow --protocol Tcp \
--description "AllowMyIpAddressSSHInbound"

##### Public IPs 
az network nic create --resource-group $RESOURCE_GROUP --name $jmpVMNic --vnet-name $sapvnet --subnet $appsubnet --accelerated-networking true --private-ip-address-version IPv4 --network-security-group $sapvnet-$appsubnet-nsg-$LOCATION
export vmjmp_ip_address=$jmpVMNic-ip
az network public-ip create --resource-group $RESOURCE_GROUP  --name $vmjmp_ip_address --sku Standard --version IPv4 --zone 1 3;
az network nic ip-config update --resource-group $RESOURCE_GROUP --nic-name $jmpVMNic --name ipconfig1 --public-ip $vmjmp_ip_address;
az vm create -g $RESOURCE_GROUP --name $jmpVmName --location $LOCATION --image $jmpImage --size $jmpVMsize --generate-ssh-keys --assign-identity --role contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP --admin-username $adminUser --admin-password $PASSWORD --nics $jmpVMNic --zone 1 

# Test Conn from JumpBox to the Internet
az vm run-command invoke -g $RESOURCE_GROUP -n $jmpVmName --command-id RunShellScript --scripts 'nc -z -v 40.121.202.140 80' --query "value[].message" -o tsv;

############################################################## Create Bom File ##################################################################

######### Create Managed Identity for ACSS/STG 
export acssMIName=acss-managedIdentity

az identity create -g $RESOURCE_GROUP -n $acssMIName --output tsv > $credDIR/$acssMI.txt
acssMIID=$(cat $credDIR/$acssMI.txt | awk '{print $5}')

###### Create BOOM Script - to executed on VM.
# https://learn.microsoft.com/en-us/azure/sap/center-sap-solutions/get-sap-installation-media#download-sap-media-with-script

export orchestration_ansible_user="azureuser"
export BOM_directory="/home/$orchestration_ansible_user/SAP-automation-samples/SAP"
export playbook_path="/home/$orchestration_ansible_user/sap-automation/deploy/ansible/playbook_bom_downloader.yaml"

cat <<EOF > $dataDIR/scriptBOM.sh
su - azureuser;
cd /home/azureuser;

curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

az login --service-principal -u '${appID}' -p '${Password}' --tenant '${tenantId}'

sudo apt install python3-pip -y;
sudo pip3 install ansible-core==2.11.12;

sudo ansible-galaxy collection install ansible.netcommon:==5.0.0 -p /opt/ansible/collections --force
sudo ansible-galaxy collection install ansible.posix:==1.5.1 -p /opt/ansible/collections --force
sudo ansible-galaxy collection install ansible.utils:==2.9.0 -p /opt/ansible/collections --force
sudo ansible-galaxy collection install ansible.windows:==1.13.0 -p /opt/ansible/collections --force
sudo ansible-galaxy collection install community.general:==6.4.0 -p /opt/ansible/collections --force

git clone https://github.com/Azure/SAP-automation-samples.git
git clone https://github.com/Azure/sap-automation.git
cd sap-automation/;
git checkout main;

export bom_base_name='${bom_base_name}'
export s_user='${sap_user}'
export s_password='${sap_password}'
export storage_account_access_key='${storage_account_access_key}'
export sapbits_location_base_path='${sapbits_location_base_path}'
export BOM_directory='${BOM_directory}'
export orchestration_ansible_user='${orchestration_ansible_user}'
export playbook_path='${playbook_path}'

sudo ansible-playbook ${playbook_path} \
-e "bom_base_name=${bom_base_name}" \
-e "deployer_kv_name=dummy_value" \
-e "s_user=${sap_user}" \
-e "s_password=${sap_password}" \
-e "sapbits_access_key=${storage_account_access_key}" \
-e "sapbits_location_base_path=${sapbits_location_base_path}" \
-e "BOM_directory=${BOM_directory}" \
-e "orchestration_ansible_user=${orchestration_ansible_user}"

EOF

# Must be giving permission to the MI on ACSS
# Run BOM Script on your Jumpbox - this will take some time! Over 40mn to create
az vm run-command invoke -g $RESOURCE_GROUP --name $jmpVmName --command-id RunShellScript --scripts @$dataDIR/scriptBOM.sh --query "value[].message" -o tsv;

######### Create Managed Identity Roles ACSS/STG 
az role assignment create --assignee $acssMIID --role Contributor --scope /subscriptions/$subscriptionId --output tsv > $credDIR/$acssMI-RG.txt
az role assignment create --assignee $acssMIID --role Contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$storage_name --output tsv > $credDIR/$acssMI-STG.txt

############################################################## Create ACSS VIS ##################################################################

# Register Feature
az provider register --namespace 'Microsoft.Workloads'

######### Quota Check  
az vm list-usage --location $LOCATION -o table | grep vCPUs | grep -v "  0  "

# Get Sizing
#--deployment-type Allowed values: SingleServer, ThreeTier
#--environment     Allowed values: NonProd, Prod

#az workloads sap-sizing-recommendation --app-location $LOCATION --database-type "HANA" --db-memory 1024 \
#--deployment-type "ThreeTier" --environment "NonProd" --high-availability-type "AvailabilitySet" \
#--sap-product "S4HANA" --saps 7500 --location $LOCATION --db-scale-method ScaleUp;

export ACSSID=HN1
export acssid=hn1
export VIS=ACSS$ACSSID
export enviromentType=NonProd
export visProduct=s4hana
export payloadFILE=$dataDIR/$VIS-template.json

export skuVM=gen2
export vmPublisher=SUSE
export vmImageVersion=latest
export offerImage=sles-sap-15-sp3
export versionImage=latest
export centralVMSize=Standard_E8ds_v5
export appVMSize=Standard_E8ds_v5
export dbVMSize=Standard_E16ds_v5
export adminVISUser=azureuser

# Get JSON Template File
curl https://raw.githubusercontent.com/tpsimoes/workspace/master/SAPonAzure/ACSS/infraTemplateAVSetHA.json -o $payloadFILE

#appLocation
sed -i "s/<infraLocation>/${LOCATION}/g" $payloadFILE

#deploymentType
sed -i "s/<infraDeploymentType>/ThreeTier/g" $payloadFILE

#highAvailabilityType
sed -i "s/<infraHighAvailabilityType>/AvailabilitySet/g" $payloadFILE

#subscriptionId
sed -i "s/<subscriptionID>/${subscriptionId}/g" $payloadFILE

#resourceGroupName
sed -i "s/<resourceGroupName>/${RESOURCE_GROUP}/g" $payloadFILE

#vnetName & subnet
sed -i "s/<vnetName>/${sapvnet}/g" $payloadFILE
sed -i "s/<dbSubnetName>/${dbsubnet}/g" $payloadFILE
sed -i "s/<centralSubnetName>/${appsubnet}/g" $payloadFILE
sed -i "s/<appSubnetName>/${appsubnet}/g" $payloadFILE

#suse image
sed -i "s/<skuVM>/${skuVM}/g" $payloadFILE
sed -i "s/<vmImagePublisher>/${vmPublisher}/g" $payloadFILE
sed -i "s/<vmImageVersion>/${vmImageVersion}/g" $payloadFILE
sed -i "s/<offerVMImage>/${offerImage}/g" $payloadFILE

#App & Central Server Size
sed -i "s/<centralVMSize>/${centralVMSize}/g" $payloadFILE
sed -i "s/<appVMSize>/${appVMSize}/g" $payloadFILE
sed -i "s/<dbVMSize>/${dbVMSize}/g" $payloadFILE

#Admin User
sed -i "s/azureuser/${adminVISUser}/g" $payloadFILE

# SAP ACSSID
sed -i "s/<acssid>/${acssid}/g" $payloadFILE

#appResourceGroup
sed -i "s/<appResourceGroupName>/${RESOURCE_GROUP}/g" $payloadFILE

# SAP FQDN
sed -i "s/<sapFqdn>/${acssid}.local/g" $payloadFILE

# Generate SSH Key Pair for all VMs
# https://learn.microsoft.com/en-us/cli/azure/sshkey?view=azure-cli-latest#az-sshkey-create

# PEM Key
ssh-keygen -m PEM -t rsa -b 4096 -C "'${adminUser}'@'${ACSSID}'" -f $keyDIR/${ACSSID}-PEM -N '' <<<y >/dev/null 2>&1

# UPload Key to RG
az sshkey create --location $LOCATION --resource-group $RESOURCE_GROUP --name $ACSSID-cli --public-key "@$keyDIR/$ACSSID-PEM.pub"

# PEM Pub
pubKeyPEM=$(cat $keyDIR/${ACSSID}-PEM.pub)
sed -i 's,'"PublicSSHKey"','${pubKeyPEM}',' "$payloadFILE"

# PEM Private Key Escape Char replacement_text
export hashKEYFile=$dataDIR/temp.file
sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g' ${keyDIR}/${ACSSID}-PEM | sed 's/\\n$//' > $hashKEYFile
replacement_text=$(<"$hashKEYFile")
escaped_replacement_text=$(sed 's/[\&/]/\\&/g; s/$/\\/' <<< "$replacement_text")
awk -v replacement="$escaped_replacement_text" '{gsub(/PrivateSSHKey/, replacement)} 1' FS="\n" OFS="\n" "$payloadFILE" > temp && mv temp "$payloadFILE";

acssMIRGID=/subscriptions/$subscriptionId/resourcegroups/$RESOURCE_GROUP/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$acssMIName

# Create ACSS VISS
az workloads sap-virtual-instance create -g $RESOURCE_GROUP -n $ACSSID --environment $enviromentType --sap-product $visProduct --configuration $payloadFILE \
--identity "{type:UserAssigned,userAssignedIdentities:{$acssMIRGID:{}}}"

# Create Key Vault Roles - for future AMS Configuration
export myADUserID=$(az ad signed-in-user show --query "id" --output tsv)
## please keap in mind that this step is not 100% failsafe
export acssKV=$(az keyvault list --query "[?location=='$LOCATION'].{name:name} | [?contains(name,'$acssid')]" -o tsv);

az role assignment create --role "Key Vault Administrator" --assignee $acssMIID --scope /subscriptions/$subscriptionId/resourcegroups/mrg-HN1-d3e0b4/providers/Microsoft.KeyVault/vaults/hn1e58-8f50-cb5f69f0f8dd --output tsv > $credDIR/$acssMI-KV-Role.txt
az role assignment create --role "Key Vault Administrator" --assignee $myADUserID --scope /subscriptions/$subscriptionId/resourcegroups/mrg-HN1-d3e0b4/providers/Microsoft.KeyVault/vaults/hn1e58-8f50-cb5f69f0f8dd --output tsv > $credDIR/$localUser-KV-Role.txt

