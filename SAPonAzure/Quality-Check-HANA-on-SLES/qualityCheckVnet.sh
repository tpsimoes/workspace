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
localMachine="wsl.localhost/"$wslDistro

### FW / Route Table - If firewall is present - please put the FW Route Table associated to the VMs subnet
export fwrt=null

### How Many VMs present on your HANA Architecture - to generate HTML Reports | This Variable should contain the list of the desired VMs to be validated
### If you dont fill this up - it will validate ALL the VMS with "vmsapnameVM" variable on the current Resource Group
#Example
#echo $hanaVMlist
#hanadb1
#hanadb2

export hanaVMlist=
#Naming convenction for your SAP VMs ex: hanadbXXXXXX if nothing in the variable - it will fetch all VMs on your VNET/resource-group
export vmsapnameVM="hana"
# You must fill up the SAP ID for the QualityCheck can run
export sapID=HN1

# resource-group/... where you have you VNET and SAP VMs | NAme of your VNET and your VMs subnet
export LOCATION=eastus;
export RESOURCE_GROUP=hana_script;
export sapvnet=vnet-sap;
export clientsubnet=client;

################ Change Variables - Mandatory! ################

export adminUser=azureuser
export PASSWORD=XXXXXXXXX

export vmjmp_size=Standard_D2s_v5
export winVmName=jumpSapbox
export winimage="Win2022AzureEditionCore"
export vmWinnic=jmpNicVM

az network nic create --resource-group $RESOURCE_GROUP --name $vmWinnic --vnet-name $sapvnet --subnet $clientsubnet --accelerated-networking true --private-ip-address-version IPv4 --network-security-group $sapvnet-$clientsubnet-nsg-$LOCATION

export vmjmp_ip_address=$vmWinnic-ip

##### Create Public IPs / NIC / VM
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
mkdir -p $htmlDIR;

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

# https://github.com/PowerShell/PowerShell/releases/download/v7.3.4/PowerShell-7.3.4-win-x64.msi
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

# Associate the route table to the subnet
az network vnet subnet update -g $RESOURCE_GROUP -n $clientsubnet --vnet-name $sapvnet --route-table $fwrt

# unzip git file
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts "Expand-Archive -LiteralPath 'c:\Users\\$adminUser\main.zip' -DestinationPath 'C:\Users\\$adminUser\Downloads'"

######################################################################## Update SSH Keys ########################################################################

myKEY=$(az storage account keys list --account-name $storage_name -g $RESOURCE_GROUP_STRG --output table | grep key1 | awk '{print $4}')

########### Create New local SSH Key
# Create a NEW Private/Public Key for AzureUser

### Check if VM list is null - if null populate will the list of all VMs with vmsapnameVM on the naming convenction - on this resource-group

if [ -z "$hanaVMlist" ]; then
	if [ -z "$vmsapnameVM" ]; then
		hanaVMlist=$(az vm list -g $RESOURCE_GROUP --query "[].name" --output tsv)
		echo "\nThe QualityCheck will run on the folliwing VMS:\n$hanaVMlist"
	else
		hanaVMlist=$(az vm list -g $RESOURCE_GROUP --query "[].name" --output tsv | grep $vmsapnameVM)
		echo "\nThe QualityCheck will run on the folliwing VMS:\n$hanaVMlist"
	fi
else
    echo "\nThe QualityCheck will run on the folliwing VMS:\n$hanaVMlist"
fi


while IFS= read -r vmsapname; do
    ssh-keygen -m PEM -t rsa -b 4096 -C "'${adminUser}'@'${vmsapname}'" -f "/home/$localUser/.ssh/${vmsapname}-cert" -N '' <<< y >/dev/null 2>&1
done <<< "$hanaVMlist"

# Update VMs with the Pub Key
# https://learn.microsoft.com/en-us/cli/azure/vm/user?view=azure-cli-latest#az-vm-user-update-examples

while IFS= read -r vmsapname; do
    az vm user update -u $adminUser --ssh-key-value "$(< /home/${localUser}/.ssh/${vmsapname}-cert.pub)" -g $RESOURCE_GROUP -n $vmsapname
done <<< "$hanaVMlist"

#[IF NEEDED] confirm is valid private key
#ssh-keygen -y -f /home/$localUser/.ssh/${vmsapname1}-cert
#ssh-keygen -y -f /home/$localUser/.ssh/${vmsapname2}-cert

########################### Connect to Storage Account | Create .ssh Directory if not present and Download SSH Key

newContainerName="qualitycheckhtml"

##### Create Directory and Upload Files

export storage_container_name=hanakeys

# Create Container
az storage container create -g $RESOURCE_GROUP_STRG -n $storage_container_name --account-name $storage_name --public-access off;

# Upload SSH Keys to storageAccount 
while IFS= read -r vmsapname; do
    az storage blob upload -c $storage_container_name -n ${vmsapname}-cert --account-name $storage_name --account-key $myKEY --file /home/$localUser/.ssh/${vmsapname}-cert --overwrite
done <<< "$hanaVMlist"

# Updates the SAP VM List so that powershell can work with it
hanaVMlist=$(az vm list -g $RESOURCE_GROUP --query "[].name" --output json | grep $vmsapnameVM  | sed '$s/\,//g') 

# https://social.technet.microsoft.com/wiki/contents/articles/52870.powershell-finding-ip-of-vm-from-azure-portal-az-module.aspx
# Create a Variable with the system current date - so it can in the end work with the HTML reports generated after this timestamp
systemDate=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Connect to AzAccount | Get Key from Storage | Run QualityCheck
cat <<EOF > scriptALLPwsh7.ps1
set-location "C:\program files\PowerShell\7"
.\pwsh.exe  -noni {
\$adminUser="${adminUser}";
\$RESOURCE_GROUP="${RESOURCE_GROUP}";
\$hanaVMlist=${hanaVMlist};
\$vmsapnameVM="${vmsapnameVM}";
\$sapID="${sapID}";
\$ApplicationId = "${ApplicationId}";
\$Password = "${Password}";
\$TenantId = "${TenantId}";
\$subscriptionId = "${subscriptionId}";

# Connect to Azure
\$SecuredPassword = ConvertTo-SecureString -AsPlainText \$Password -Force;
\$Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList \$ApplicationId, \$SecuredPassword;
Connect-AzAccount -ServicePrincipal -TenantId \$TenantId -Credential \$Credential;
\$sub = Get-AzSubscription -SubscriptionId \$subscriptionId;
Set-AzContext -Subscription \$sub;

\$storageAccountName = "${storage_name}";
\$containerName = "${storage_container_name}";
\$newContainerName = "${newContainerName}";
\$storageAccountKey = "${myKEY}";

\$context = New-AzStorageContext -StorageAccountName \$storageAccountName -StorageAccountKey \$storageAccountKey;
\$FolderToCreate = "C:\Users\\$adminUser\.ssh"

if (!(Test-Path \$FolderToCreate -PathType Container)) {
New-Item -ItemType Directory -Force -Path \$FolderToCreate
}

# VMS List
#foreach (\$vmsap in Get-AzVM -ResourceGroupName \$RESOURCE_GROUP -Name "*\$vmsapnameVM*") {
foreach (\$vmsap in \$hanaVMlist) {
 \$vmsap 
 #\$vmsapname=\$vmsap.name
 \$vmsapname=\$vmsap
 \$vmsapname
 \$blobNameVM="\$vmsapname-cert"
 \$blobNameVM
 \$destinationPathVM="C:\Users\\$adminUser\.ssh\\\$blobNameVM"
 \$destinationPathVM

 if (Test-Path \$destinationPathVM -PathType Leaf) {
 # This is remove old files if they exist
 Remove-Item -Force \$destinationPathVM
 }
 
 # Download latest ssh key
 Get-AzStorageBlobContent -Container \$containerName -Blob \$blobNameVM -Destination \$destinationPathVM -Context \$context -Confirm:\$false
 
 #Get Current VM Private IPAddress - this is assuming that you only have one NIC attached
 \$VM = Get-AzVm -name "\$vmsapname"
 \$Profile=\$VM.NetworkProfile.NetworkInterfaces.Id.Split("/") | Select -Last 1
 \$IPConfig = Get-AzNetworkInterface -Name \$Profile
 \$vmIPAddress = \$IPConfig.IpConfigurations.PrivateIpAddress
 
 set-location "C:\Users\\$adminUser\Downloads\SAP-on-Azure-Scripts-and-Utilities-main\QualityCheck"

 C:\Users\\$adminUser\Downloads\SAP-on-Azure-Scripts-and-Utilities-main\QualityCheck\QualityCheck.ps1 -LogonAsRootSSHKey -VMOperatingSystem SUSE -VMDatabase HANA -VMRole DB -AzVMResourceGroup \$RESOURCE_GROUP -AzVMName \$vmsapname -VMHostname \$vmIPAddress -VMUsername \$adminUser -SSHKey "C:\Users\\$adminUser\.ssh\\\$blobNameVM" -HighAvailabilityAgent FencingAgent -VMConnectionPort 22 -DBDataDir /hana/data/\$sapID -DBLogDir /hana/log/\$sapID -DBSharedDir /hana/shared/\$sapID -Hardwaretype VM -HANADeployment OLTP
 \$latestVM = (Get-ChildItem -Attributes !Directory | Sort-Object -Descending -Property LastWriteTime | select -First 1)
 \$latest_filenameVM = \$latestVM.Name
 \$PathFile ="C:\Users\\$adminUser\Downloads\SAP-on-Azure-Scripts-and-Utilities-main\QualityCheck\\\$(\$latest_filenameVM)"
 
 \$containerExist = Get-AzStorageContainer -Name \$newContainerName*  -Context \$context;
 if (\$containerExist.name -eq \$null ) {New-AzStorageContainer -Name \$newContainerName -Context \$context -Permission Blob}
 Set-AzStorageBlobContent -File \$PathFile -Container \$newContainerName -Blob \$latest_filenameVM -Context \$Context
}

Exit;}
EOF

# Run Script QualityCheck to all your SAP HANA VMs on your list
az vm run-command invoke -g $RESOURCE_GROUP --name $winVmName --command-id RunPowerShellScript --scripts @scriptALLPwsh7.ps1 --query "value[].message" -o tsv;

######## OPEN LOCALLY HTML - This Assuming that you are running on a WSL System !
sudo apt update -y;
sudo apt install x11-apps -y;

htmlFileList=$(az storage blob list --container-name $newContainerName --account-name $storage_name --account-key $myKEY --query "[?properties.creationTime>'${systemDate}'].name" --output tsv | grep $vmsapnameVM)
filenameVM1=$(az storage blob list --container-name $newContainerName --account-name $storage_name --account-key $myKEY --query "[?properties.creationTime>'${systemDate}'].name" --output tsv  | grep $vmsapnameVM | head -n 1 )

# Download HTML generated from this script execution - after the previous timestamp
while IFS= read -r filename; do
	az storage blob download --container-name $newContainerName --account-name $storage_name --account-key $myKEY --name "$filename" --file "$htmlDIR/$filename"; 
done <<< "$htmlFileList"

# Due to possible amount of html files we will open the HTML Directory and first report only
explorer.exe  "file://$localMachine$htmlDIR/"
wslview "file://$localMachine$htmlDIR/$filenameVM1"