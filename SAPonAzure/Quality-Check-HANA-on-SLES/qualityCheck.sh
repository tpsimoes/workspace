#!/bin/sh

################ Change Variables - Mandatory! ################

### AZ Account 
export subscriptionId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX

### Storage Account
export storage_name=sapsoftwarerepro
export RESOURCE_GROUP_STRG=rsg-mce-hana

### Local Machine - This Script Assumes that you are running on WSL System / Ubuntu
wslDistro=$(cat /etc/lsb-release | grep DISTRIB_ID | cut -d '=' -f 2)-$(cat /etc/lsb-release | grep DISTRIB_RELEASE | cut -d '=' -f 2)
localUser=$(whoami)
# this variable is to used for sensible-browser - if yu have another app to open HTML files on linux you can change the final URL
localMachine="wsl.localhost/"$wslDistro

### FW / Route Table - if you have a Route Table associated to your HANA VNET
export fwrt=null

###### Run Quality Check to validate cluster setup - TO BE REVISED
# https://github.com/Azure/SAP-on-Azure-Scripts-and-Utilities/tree/main/QualityCheck

export LOCATION=eastus;
export RESOURCE_GROUP=hana_script;
export sapvnet=vnet-sap;
export clientsubnet=client;

export adminUser=azureuser
export PASSWORD=Password2023!
export vmsapname1=hanadb1
export vmsapname2=hanadb2
export sapID=HN1

export vmjmp_size=Standard_D2s_v5
export winVmName=jumpbox
export winimage="Win2022AzureEditionCore"
export vmWinnic=jmpNicVM

az network nic create --resource-group $RESOURCE_GROUP --name $vmWinnic --vnet-name $sapvnet --subnet $clientsubnet --accelerated-networking true --private-ip-address-version IPv4 --network-security-group $sapvnet-$clientsubnet-nsg-$LOCATION

export vmjmp_ip_address=$vmWinnic-ip

##### Public IPs 
az network public-ip create --resource-group $RESOURCE_GROUP  --name $vmjmp_ip_address --sku Standard --version IPv4 --zone 1 3;
az network nic ip-config update --resource-group $RESOURCE_GROUP --nic-name $vmWinnic --name ipconfig1 --public-ip $vmjmp_ip_address;

az vm create -g $RESOURCE_GROUP --name $winVmName --location $LOCATION --image $winimage --size $vmjmp_size --generate-ssh-keys --assign-identity --role contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP --admin-username $adminUser --admin-password $PASSWORD --nics $vmWinnic --zone 1 

# dissociate momentary ROUTE_TABLE
az network vnet subnet update -g $RESOURCE_GROUP -n $clientsubnet --vnet-name $sapvnet --route-table null

######################################################################## AUTH ########################################################################
export appDisplayName=sap_pacemaker$RANDOM

# Create App AD User - to avoid AzAccount browser request
export htmlDIR=/home/$localUser/qualityCheck/html;
export dataDIR=/home/$localUser/qualityCheck/data;

mkdir -p $dataDIR;
mkdir -p $htmlDIR

az ad app create --display-name $appDisplayName --output tsv > $dataDIR/$appDisplayName.txt

# Get AD APPID and AD ObjectID
appID=$(cat $dataDIR/$appDisplayName.txt | awk '{print $3}')
objectID=$(cat $dataDIR/$appDisplayName.txt | awk '{print $14}')

# Get AD APP Password
az ad app credential reset --id $objectID --output tsv > $dataDIR/$appDisplayName-cred.txt
ApplicationId=$(cat $dataDIR/$appDisplayName-cred.txt | awk '{print $1}')
Password=$(cat $dataDIR/$appDisplayName-cred.txt | awk '{print $2}')
TenantId=$(cat $dataDIR/$appDisplayName-cred.txt | awk '{print $3}')

# AD SP Creation
az ad sp create --id $ApplicationId
az role assignment create --assignee $ApplicationId --role Contributor --scope /subscriptions/$subscriptionId --output tsv > $dataDIR/$appDisplayName-SP.txt

##################################################################### AZ MODULES for QualityCheck ###############################################################

# Deactivate the Startup of SConfig
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts 'Set-SConfig -AutoLaunch $false'

# Install PWS 7.X
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts 'Invoke-WebRequest -Uri https://aka.ms/install-powershell.ps1 -OutFile install-powershell.ps1; .\install-powershell.ps1 -UseMSI -EnablePSRemoting -Quiet'

# https://github.com/Azure/SAP-on-Azure-Scripts-and-Utilities/tree/main/QualityCheck
# Install  - Requirements

az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts 'Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Confirm:$false'
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts 'Install-Module -Name Az -Force -Confirm:$false'
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts 'Install-Module Az.NetAppFiles -Force -Confirm:$false'
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts 'Install-Module Posh-SSH -Force -Confirm:$false'

# This will only work for Tenant that allow it!
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts 'Set-ExecutionPolicy Unrestricted -Confirm:$false'

######################################################################## Download SAP Script ########################################################################

# Download the script
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts "Invoke-WebRequest -Uri https://github.com/Azure/SAP-on-Azure-Scripts-and-Utilities/archive/refs/heads/main.zip -OutFile 'C:\Users\\$adminUser\main.zip'"

# Associate the route table to the subnet if you have
az network vnet subnet update -n $clientsubnet -g $RESOURCE_GROUP --vnet-name $sapvnet --address-prefixes $clientsubnetaddress --route-table $fwrt

# Associate the route table to the subnet
az network vnet subnet update -g $RESOURCE_GROUP -n $clientsubnet --vnet-name $sapvnet --route-table $fwrt

# unzip git file
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts "Expand-Archive -LiteralPath 'c:\Users\\$adminUser\main.zip' -DestinationPath 'C:\Users\\$adminUser\Downloads'"

############# GENERATE Key Local - Update to VM & Storage Account

myKEY=$(az storage account keys list --account-name $storage_name -g $RESOURCE_GROUP_STRG --output table | grep key1 | awk '{print $4}')

########### Create New local SSH Key
# Create a NEW Private/Public Key for AzureUser
ssh-keygen -m PEM -t rsa -b 4096 -C "'${adminUser}'@'${vmsapname1}'" -f /home/$localUser/.ssh/${vmsapname1}-cert -N '' <<<y >/dev/null 2>&1
ssh-keygen -m PEM -t rsa -b 4096 -C "'${adminUser}'@'${vmsapname2}'" -f /home/$localUser/.ssh/${vmsapname2}-cert -N '' <<<y >/dev/null 2>&1

# Update VMs with the Pub Key
# https://learn.microsoft.com/en-us/cli/azure/vm/user?view=azure-cli-latest#az-vm-user-update-examples

az vm user update -u $adminUser --ssh-key-value "$(< /home/${localUser}/.ssh/${vmsapname1}-cert.pub)" -g $RESOURCE_GROUP -n $vmsapname1
az vm user update -u $adminUser --ssh-key-value "$(< /home/${localUser}/.ssh/${vmsapname2}-cert.pub)" -g $RESOURCE_GROUP -n $vmsapname2

#[IF NEEDED] confirm is valid private key
#ssh-keygen -y -f /home/$localUser/.ssh/${vmsapname1}-cert
#ssh-keygen -y -f /home/$localUser/.ssh/${vmsapname2}-cert

##### Create Directory and Upload Files

export storage_container_name=hanakeys

# Create Container
az storage container create -g $RESOURCE_GROUP_STRG -n $storage_container_name --account-name $storage_name --public-access off;

az storage blob upload -c $storage_container_name -n ${vmsapname1}-cert --account-name $storage_name --account-key $myKEY --file /home/$localUser/.ssh/${vmsapname1}-cert
az storage blob upload -c $storage_container_name -n ${vmsapname2}-cert --account-name $storage_name --account-key $myKEY --file /home/$localUser/.ssh/${vmsapname2}-cert

########################### Connect to Storage Account | Create .ssh Directory if not present and Download SSH Key

blobNameVM1="\$vmsapname1-cert"
blobNameVM2="\$vmsapname2-cert"
destinationPathVM1="C:\Users\\$adminUser\.ssh\\$vmsapname1-cert"
destinationPathVM2="C:\Users\\$adminUser\.ssh\\$vmsapname2-cert"
newContainerName="qualitycheckhtml"

###### [A] Get VM's Private IPs 
export vmsap1_client_pip=$(az vm list-ip-addresses -n $vmsapname1  -o table | grep $vmsapname1 | awk '{print $3}')
export vmsap2_client_pip=$(az vm list-ip-addresses -n $vmsapname2  -o table | grep $vmsapname2 | awk '{print $3}')

# Connect to AzAccount | Get Key from Storage | Run QualityCheck
cat <<EOF > scriptALLPwsh7.ps1
set-location "C:\program files\PowerShell\7"
.\pwsh.exe  -noni {
\$adminUser="${adminUser}";
\$vmsapname1="${vmsapname1}";
\$vmsapname2="${vmsapname2}";
\$RESOURCE_GROUP="${RESOURCE_GROUP}";
\$sapID="${sapID}";
\$ApplicationId = "${ApplicationId}";
\$Password = "${Password}";
\$TenantId = "${TenantId}";
\$subscriptionId = "${subscriptionId}";
\$SecuredPassword = ConvertTo-SecureString -AsPlainText \$Password -Force;
\$Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList \$ApplicationId, \$SecuredPassword;
Connect-AzAccount -ServicePrincipal -TenantId \$TenantId -Credential \$Credential;
\$sub = Get-AzSubscription -SubscriptionId \$subscriptionId;
Set-AzContext -Subscription \$sub;

\$storageAccountName = "${storage_name}";
\$containerName = "${storage_container_name}";
\$newContainerName = "${newContainerName}";
\$blobNameVM1 = "${blobNameVM1}";
\$blobNameVM2 = "${blobNameVM2}";
\$destinationPathVM1 = "${destinationPathVM1}";
\$destinationPathVM2 = "${destinationPathVM2}";
\$storageAccountKey = "${myKEY}";
\$vmsap1_client_pip = "${vmsap1_client_pip}";
\$vmsap2_client_pip = "${vmsap2_client_pip}";
\$context = New-AzStorageContext -StorageAccountName \$storageAccountName -StorageAccountKey \$storageAccountKey;
\$FolderToCreate = "C:\Users\\$adminUser\.ssh"

if (!(Test-Path \$FolderToCreate -PathType Container)) {
New-Item -ItemType Directory -Force -Path \$FolderToCreate
}

if (Test-Path \$destinationPathVM1 -PathType Leaf) {
Remove-Item -Force \$destinationPathVM1
}

if (Test-Path \$destinationPathVM2 -PathType Leaf) {
Remove-Item -Force \$destinationPathVM2
}

Get-AzStorageBlobContent -Container \$containerName -Blob \$blobNameVM1 -Destination \$destinationPathVM1 -Context \$context -Confirm:\$false
Get-AzStorageBlobContent -Container \$containerName -Blob \$blobNameVM2 -Destination \$destinationPathVM2 -Context \$context -Confirm:\$false

set-location "C:\Users\\$adminUser\Downloads\SAP-on-Azure-Scripts-and-Utilities-main\QualityCheck"

C:\Users\\$adminUser\Downloads\SAP-on-Azure-Scripts-and-Utilities-main\QualityCheck\QualityCheck.ps1 -LogonAsRootSSHKey -VMOperatingSystem SUSE -VMDatabase HANA -VMRole DB -AzVMResourceGroup \$RESOURCE_GROUP -AzVMName \$vmsapname1 -VMHostname \$vmsap1_client_pip -VMUsername \$adminUser -SSHKey "C:\Users\\$adminUser\.ssh\\$vmsapname1-cert" -HighAvailabilityAgent FencingAgent -VMConnectionPort 22 -DBDataDir /hana/data/\$sapID -DBLogDir /hana/log/\$sapID -DBSharedDir /hana/shared/\$sapID -Hardwaretype VM -HANADeployment OLTP
\$latestVM1 = (Get-ChildItem -Attributes !Directory | Sort-Object -Descending -Property LastWriteTime | select -First 1)
\$latest_filenameVM1 = \$latestVM1.Name
\$PathFile ="C:\Users\\$adminUser\Downloads\SAP-on-Azure-Scripts-and-Utilities-main\QualityCheck\\\$(\$latest_filenameVM1)"

\$containerExist = Get-AzStorageContainer -Name \$newContainerName*  -Context \$context;
if (\$containerExist.name -eq \$null ) {New-AzStorageContainer -Name \$newContainerName -Context \$context -Permission Blob}
Set-AzStorageBlobContent -File \$PathFile -Container \$newContainerName -Blob \$latest_filenameVM1 -Context \$Context

C:\Users\\$adminUser\Downloads\SAP-on-Azure-Scripts-and-Utilities-main\QualityCheck\QualityCheck.ps1 -LogonAsRootSSHKey -VMOperatingSystem SUSE -VMDatabase HANA -VMRole DB -AzVMResourceGroup \$RESOURCE_GROUP -AzVMName \$vmsapname2 -VMHostname \$vmsap2_client_pip -VMUsername \$adminUser -SSHKey "C:\Users\\$adminUser\.ssh\\$vmsapname2-cert" -HighAvailabilityAgent FencingAgent -VMConnectionPort 22 -DBDataDir /hana/data/\$sapID -DBLogDir /hana/log/\$sapID -DBSharedDir /hana/shared/\$sapID -Hardwaretype VM -HANADeployment OLTP
\$latestVM2 = (Get-ChildItem -Attributes !Directory | Sort-Object -Descending -Property LastWriteTime | select -First 1)
\$latest_filenameVM2 = \$latestVM2.Name
\$PathFile ="C:\Users\\$adminUser\Downloads\SAP-on-Azure-Scripts-and-Utilities-main\QualityCheck\\\$(\$latest_filenameVM2)"

\$containerExist = Get-AzStorageContainer -Name \$newContainerName*  -Context \$context;
if (\$containerExist.name -eq \$null ) {New-AzStorageContainer -Name \$newContainerName -Context \$context -Permission Blob}
Set-AzStorageBlobContent -File \$PathFile -Container \$newContainerName -Blob \$latest_filenameVM2 -Context \$Context

Exit;}
EOF

az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts @scriptALLPwsh7.ps1 --query "value[].message" -o tsv;

# List Files in Storage > container
az storage blob list --container-name $newContainerName --account-name $storage_name --account-key $myKEY --query "[*].name" --output tsv | sort -r | head -n 2

# Download the two html exports
az storage blob list --container-name $newContainerName --account-name $storage_name --account-key $myKEY --query "[*].name" --output tsv | sort -r | head -n 2 | while read -r filename; do az storage blob download --container-name $newContainerName --account-name $storage_name --account-key $myKEY --name "$filename" --file "$htmlDIR/$filename" ; done 

######## OPEN LOCALLY HTML - This Assuming that you are running on a WSL System !
sudo apt update -y;
sudo apt install x11-apps -y;

# Open HTML Files

filenameVM1=$(az storage blob list --container-name $newContainerName --account-name $storage_name --account-key $myKEY --query "[*].name" --output tsv | sort -r | head -n 1 )
filenameVM2=$(az storage blob list --container-name $newContainerName --account-name $storage_name --account-key $myKEY --query "[*].name" --output tsv | sort -r | head -n 2 | tail -n 1)

sensible-browser file://$localMachine$htmlDIR/$filenameVM1;
sensible-browser file://$localMachine$htmlDIR/$filenameVM2;


