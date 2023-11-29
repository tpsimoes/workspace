#!/bin/sh

################ Change Variables - Mandatory! ################

# If you have a file on a StorageAccount - this is can be obtained from: Storage Account > Containers > Shared access tokens > HTTPS/HTTP SAS Token - with Read & List > "Blob SAS URL"
#export installerZipUrl="https://<storageAccountName>/<containerName>/FILENAME/sasToken"
export installerZipUrl="https://URL/FILENAME"
export sasfileNAME='51056431.ZIP'
export subscriptionId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX

################ INFRA > Networking Variables ################

export LOCATION=eastus;
export RESOURCE_GROUP=hana_script;
export sapvnet=vnet-sap;
export sapvnetaddress="10.33.0.0/22"
export clientsubnet=client;
export fwsubnet=AzureFirewallSubnet;
export bastionsubnet=AzureBastionSubnet;
export clientsubnetaddress="10.33.0.0/24"
export bastionsubnetaddress="10.33.1.0/26"
export fwsubnetaddress="10.33.2.0/26"

################################################################ SAP HANA - HA    ################################################################
# High availability of SAP HANA on Azure VMs on SLES | Microsoft Learn
# https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability#create-sap-hana-cluster-resources

################################################################ SET Subscription ################################################################

az config set core.allow_broker=true
az account clear
az login

#Set Subscription
az account set --subscription $subscriptionId;

################################################################ Create Infra ####################################################################

#RG Create
az group create --name $RESOURCE_GROUP --location $LOCATION;

#VNET
az network vnet create --address-prefixes $sapvnetaddress --name $sapvnet --resource-group $RESOURCE_GROUP;

#Subnets  
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $clientsubnet  --address-prefixes $clientsubnetaddress;
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $fwsubnet      --address-prefixes $fwsubnetaddress;
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $bastionsubnet --address-prefixes $bastionsubnetaddress;

################ SAP / VM Variables ################
export sapID=HN1
export sapid=hn1
export instanceID=00
export PASSWORD=Password2023!
export vmsapname1=hanadb1
export vmsapname2=hanadb2

################################################################ Azure FW    ################################################################
# https://learn.microsoft.com/en-us/azure/firewall/deploy-cli#deploy-the-firewall

################ FW -  Variables ################
export VNET_ID=$(az network vnet show --resource-group $RESOURCE_GROUP --name $sapvnet --query "id" -o tsv)
export SUBNET_ID=$(az network vnet subnet show --resource-group $RESOURCE_GROUP --vnet-name $sapvnet --name $clientsubnet --query "id" -o tsv)
export fwname=AFW-SAP-HANA
export fwpip=AFW-SAP-HANA-PIP
export fwconfig=AFW-SAP-HANA-CFG

az network firewall create --name $fwname --resource-group $RESOURCE_GROUP --location $LOCATION --tier Standard --public-ip-count 1 --zones 1 3
az network public-ip create --name $fwpip --resource-group $RESOURCE_GROUP --location $LOCATION --allocation-method static --sku standard --zone 1 3;
az network firewall ip-config create --firewall-name $fwname --name $fwconfig --public-ip-address $fwpip --resource-group $RESOURCE_GROUP --vnet-name $sapvnet;
az network firewall update --name $fwname --resource-group $RESOURCE_GROUP;
az network public-ip show --name $fwpip --resource-group $RESOURCE_GROUP;
	
fwprivaddr=$(az network firewall show -g $RESOURCE_GROUP -n $fwname --query "ipConfigurations[0].privateIPAddress" --output tsv)

################ FW -  Rule Collection ################
# https://learn.microsoft.com/en-us/azure/firewall/deploy-cli#configure-a-network-rule
export fwPolName=afw-pol-mce-hana
export fwColName=afw-ruleco-mce-hana
export collectiongroup=DefaultNetworkRuleCollectionGroup

az network firewall policy create --name $fwPolName --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard --enable-dns-proxy true
#az network firewall update --name $fwname --resource-group $RESOURCE_GROUP --firewall-policy $fwPolName;

# https://learn.microsoft.com/en-us/cli/azure/network/firewall/policy/rule-collection-group/collection?view=azure-cli-latest#az-network-firewall-policy-rule-collection-group-collection-add-filter-collection-examples
# https://learn.microsoft.com/en-us/cli/azure/network/firewall/policy/rule-collection-group?view=azure-cli-latest#az-network-firewall-policy-rule-collection-group-create

az network firewall policy rule-collection-group create --name $collectiongroup --policy-name $fwPolName --priority 100 --resource-group $RESOURCE_GROUP;

az network firewall policy rule-collection-group collection add-filter-collection -g $RESOURCE_GROUP --policy-name $fwPolName --rule-collection-group-name $collectiongroup \
 --name $fwColName --action Allow --rule-name "rule-slesrepo" --rule-type NetworkRule --description "SLES REPO" \
 --source-addresses $clientsubnetaddress --destination-addresses "40.121.202.140 23.100.36.229 104.45.31.195 52.187.53.250 191.237.254.253" --destination-ports "*" --ip-protocols Any --collection-priority 100;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-storage" \
 --source-addresses $clientsubnetaddress --destination-addresses Storage --fqdn-tags Storage --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-akv" \
 --source-addresses $clientsubnetaddress --destination-addresses AzureKeyVault --fqdn-tags AzureKeyVault --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-aad" \
 --source-addresses $clientsubnetaddress --destination-addresses AzureActiveDirectory --fqdn-tags AzureActiveDirectory --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-armrest" \
 --source-addresses $clientsubnetaddress --destination-addresses AzureResourceManager --fqdn-tags AzureResourceManager --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-monitor" \
 --source-addresses $clientsubnetaddress --destination-addresses AzureMonitor --fqdn-tags AzureMonitor --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-backup" \
 --source-addresses $clientsubnetaddress --destination-addresses AzureBackup --fqdn-tags AzureBackup --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-site-recovery" \
 --source-addresses $clientsubnetaddress --destination-addresses AzureSiteRecovery --fqdn-tags AzureSiteRecovery --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-suse-cloud" \
 --source-addresses $clientsubnetaddress --destination-fqdns smt-azure.susecloud.net --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-repo3" \
 --source-addresses $clientsubnetaddress --destination-addresses 52.188.224.179 --destination-ports "*" --ip-protocols Any;

az network firewall policy rule-collection-group collection rule add --collection-name $fwColName --rcg-name $collectiongroup  --resource-group $RESOURCE_GROUP --policy-name $fwPolName --rule-type NetworkRule \
 --name "rule-github" \
 --source-addresses $clientsubnetaddress --destination-fqdns raw.githubusercontent.com --destination-ports "*" --ip-protocols Any;

############# Create RT/Route & Associate
export fwrt=rt-mce-hana
export fwrt_route=fw_rt-mce-hana

az network route-table create --name $fwrt --resource-group $RESOURCE_GROUP --location $LOCATION  --disable-bgp-route-propagation false;
az network route-table route create --resource-group $RESOURCE_GROUP --name $fwrt_route --route-table-name $fwrt  --address-prefix 0.0.0.0/0 --next-hop-type VirtualAppliance --next-hop-ip-address $fwprivaddr

# Associate the route table to the subnet
az network vnet subnet update -n $clientsubnet -g $RESOURCE_GROUP --vnet-name $sapvnet --address-prefixes $clientsubnetaddress --route-table $fwrt

################################################################   Create Internal LoadBalancer  ################################################################
# https://learn.microsoft.com/en-us/azure/load-balancer/quickstart-load-balancer-standard-internal-cli#create-the-load-balancer
export LB_NAME=LB-HANA
export backendpool=client-pool
export lbfrontIPname=client-lb-ip
export lbhealthPROB=client-lb-prob
export lbhealthRULE=client-lb-rule
export lbPort=62500

# Create an internal load balancer
az network lb create --resource-group $RESOURCE_GROUP --name $LB_NAME --sku Standard --vnet-name $sapvnet --subnet $clientsubnet  --backend-pool-name $backendpool --frontend-ip-name $lbfrontIPname

# Create a health probe 
az network lb probe create --resource-group $RESOURCE_GROUP --lb-name $LB_NAME --name $lbhealthPROB --protocol tcp --port $lbPort;

# Create a load balancer rule
# https://learn.microsoft.com/en-us/cli/azure/network/lb/rule?view=azure-cli-latest#az-network-lb-rule-create
az network lb rule create --resource-group $RESOURCE_GROUP --lb-name $LB_NAME --name $lbhealthRULE --protocol tcp --frontend-port $lbPort --backend-port $lbPort --frontend-ip-name $lbfrontIPname --backend-pool-name $backendpool \
    --probe-name $lbhealthPROB --idle-timeout 30 --enable-tcp-reset false --enable-floating-ip true;
	
# aqui a PROBE ta com interval 15 - deveria ser 5
# MISSING HA Ports Enabled - Can Only be done via Portal!

echo "************ Atention Probe - To be Changed ***************"
echo "1 - PROBE must be 5 - Can Only be done via Portal"
echo "2 - MISSING HA Ports Enabled - Can Only be done via Portal"
echo "***********************************************************"

################################################################   Create VM  ################################################################

# Create two network interfaces
# https://learn.microsoft.com/en-us/azure/load-balancer/quickstart-load-balancer-standard-internal-cli#create-network-interfaces-for-the-virtual-machines

array=(sapNicVM1 sapNicVM2)
  for vmnic in "${array[@]}"
  do
    az network nic create --resource-group $RESOURCE_GROUP --name $vmnic --vnet-name $sapvnet --subnet $clientsubnet --accelerated-networking true --private-ip-address-version IPv4 --network-security-group $sapvnet-$clientsubnet-nsg-$LOCATION
  done

export vmsap1nic_client=sapNicVM1
export vmsap2nic_client=sapNicVM2

export vmsap1_ip_address=$vmsapname1-hana-ip
export vmsap2_ip_address=$vmsapname2-hana-ip

##### Public IPs 
az network public-ip create --resource-group $RESOURCE_GROUP  --name $vmsap1_ip_address --sku Standard --version IPv4 --zone 1 3;
az network public-ip create --resource-group $RESOURCE_GROUP  --name $vmsap2_ip_address --sku Standard --version IPv4 --zone 1 3;

# TO CONFIRM !!!!!
# az network nic ip-config update --resource-group $RESOURCE_GROUP --nic-name $vmsap1nic_client --name ipconfig1 --public-ip $vmsap1_ip_address;
# az network nic ip-config update --resource-group $RESOURCE_GROUP --nic-name $vmsap2nic_client --name ipconfig1 --public-ip $vmsap2_ip_address;

################ Size and Image ################

# https://learn.microsoft.com/en-us/azure/virtual-machines/linux/multiple-nics#create-a-vm-and-attach-the-nics 
export vmdb_size=Standard_E8ds_v5
#export suseimage="SUSE:sles-15-sp3:gen2:latest";
export suseimage="SUSE:sles-sap-15-sp4:gen2:2023.02.05";
export adminUser=azureuser
# get suse images by provider
#az vm image list -p suse;

#When specifying an existing NIC, do not specify NSG, public IP, ASGs, VNet or subnet.
# https://learn.microsoft.com/en-us/previous-versions/azure/virtual-machines/linux/tutorial-availability-sets

# https://learn.microsoft.com/en-us/azure/virtual-machines/linux/create-cli-availability-zone
# https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/qs-configure-cli-windows-vm#system-assigned-managed-identity

# az vm create -g $RESOURCE_GROUP --name $vmsapname1 --location $LOCATION --image $suseimage --size $vmdb_size --public-ip-address $vmsap1_ip_address --generate-ssh-keys --assign-identity --role contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP --admin-username $adminUser --admin-password $PASSWORD --nics $vmsap1nic_client --zone 1 
# az vm create -g $RESOURCE_GROUP --name $vmsapname2 --location $LOCATION --image $suseimage --size $vmdb_size --public-ip-address $vmsap2_ip_address --generate-ssh-keys --assign-identity --role contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP --admin-username $adminUser --admin-password $PASSWORD --nics $vmsap2nic_client --zone 3

az vm create -g $RESOURCE_GROUP --name $vmsapname1 --location $LOCATION --image $suseimage --size $vmdb_size --generate-ssh-keys --assign-identity --role contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP --admin-username $adminUser --admin-password $PASSWORD --nics $vmsap1nic_client --zone 1 
az vm create -g $RESOURCE_GROUP --name $vmsapname2 --location $LOCATION --image $suseimage --size $vmdb_size --generate-ssh-keys --assign-identity --role contributor --scope /subscriptions/$subscriptionId/resourceGroups/$RESOURCE_GROUP --admin-username $adminUser --admin-password $PASSWORD --nics $vmsap2nic_client --zone 3

# Add the virtual machines to the backend pool with
# https://learn.microsoft.com/en-us/azure/load-balancer/quickstart-load-balancer-standard-internal-cli#add-virtual-machines-to-the-backend-pool

az network nic ip-config address-pool add --address-pool $backendpool --ip-config-name ipconfig1 --nic-name $vmsap1nic_client --resource-group $RESOURCE_GROUP --lb-name $LB_NAME;
az network nic ip-config address-pool add --address-pool $backendpool --ip-config-name ipconfig1 --nic-name $vmsap2nic_client --resource-group $RESOURCE_GROUP --lb-name $LB_NAME;
  
az network nsg rule create --resource-group $RESOURCE_GROUP --nsg-name $sapvnet-$clientsubnet-nsg-$LOCATION --name $LB_NAME-allow-inbound --protocol '*' --direction inbound --source-address-prefix '*' \
    --source-port-range '*' --destination-address-prefix '*' --destination-port-range $lbPort --access allow --priority 1000  

###########################################################  NSG Machine IP ########################################################### 

export myIP=$(curl http://ifconfig.co)
export myIPnsgRULEname=AllowMyIP
export vnetNSGname=$sapvnet-$clientsubnet-nsg-$LOCATION

az network nsg rule create -g $RESOURCE_GROUP  --nsg-name $vnetNSGname -n $myIPnsgRULEname --priority 1001 \
--source-address-prefixes $myIP --source-port-ranges '*' --destination-address-prefixes '*' \
--destination-port-ranges 22 --access Allow --protocol Tcp \
--description "AllowMyIpAddressSSHInbound"

################ Add Managed Disk ################
# https://learn.microsoft.com/en-us/azure/virtual-machines/linux/add-disk?tabs=ubuntu

az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname1 --name ${vmsapname1}_DataDisk_0 --new --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname1 --name ${vmsapname1}_DataDisk_1 --new --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname1 --name ${vmsapname1}_DataDisk_2 --new --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname1 --name ${vmsapname1}_DataDisk_3 --new --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname1 --name ${vmsapname1}_DataDisk_shared --new --caching ReadOnly --size-gb 128
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname1 --name ${vmsapname1}_DataDisk_usrsap --new --caching ReadOnly --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname1 --name ${vmsapname1}_DataDisk_log --new --size-gb 128

az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname2 --name ${vmsapname2}_DataDisk_0 --new --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname2 --name ${vmsapname2}_DataDisk_1 --new --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname2 --name ${vmsapname2}_DataDisk_2 --new --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname2 --name ${vmsapname2}_DataDisk_3 --new --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname2 --name ${vmsapname2}_DataDisk_shared --new --caching ReadOnly --size-gb 128
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname2 --name ${vmsapname2}_DataDisk_usrsap --new --caching ReadOnly --size-gb 64
az vm disk attach -g $RESOURCE_GROUP --vm-name $vmsapname2 --name ${vmsapname2}_DataDisk_log --new --size-gb 128

################################################################ VM CONFIG ################################################################
#[A]: Applicable to all nodes
#[1]: Applicable only to node 1
#[2]: Applicable only to node 2
 
###### [A] Configure LVM/XFS to create the base SAP HANA volumes on both nodes
# https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability#install-sap-hana
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo pvcreate /dev/disk/azure/scsi1/lun0 && sudo pvcreate /dev/disk/azure/scsi1/lun1 && sudo pvcreate /dev/disk/azure/scsi1/lun2 && sudo pvcreate /dev/disk/azure/scsi1/lun3 && sudo pvcreate /dev/disk/azure/scsi1/lun4 && sudo pvcreate /dev/disk/azure/scsi1/lun5  && sudo pvcreate /dev/disk/azure/scsi1/lun6'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo pvcreate /dev/disk/azure/scsi1/lun0 && sudo pvcreate /dev/disk/azure/scsi1/lun1 && sudo pvcreate /dev/disk/azure/scsi1/lun2 && sudo pvcreate /dev/disk/azure/scsi1/lun3 && sudo pvcreate /dev/disk/azure/scsi1/lun4 && sudo pvcreate /dev/disk/azure/scsi1/lun5  && sudo pvcreate /dev/disk/azure/scsi1/lun6'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo vgcreate vg_hana_data_HN1 /dev/disk/azure/scsi1/lun0 /dev/disk/azure/scsi1/lun1 /dev/disk/azure/scsi1/lun2 /dev/disk/azure/scsi1/lun3 && sudo vgcreate vg_hana_shared_HN1 /dev/disk/azure/scsi1/lun4 && sudo vgcreate vg_hana_shared_usrsap_HN1 /dev/disk/azure/scsi1/lun5 && sudo vgcreate vg_hana_log_HN1 /dev/disk/azure/scsi1/lun6'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo vgcreate vg_hana_data_HN1 /dev/disk/azure/scsi1/lun0 /dev/disk/azure/scsi1/lun1 /dev/disk/azure/scsi1/lun2 /dev/disk/azure/scsi1/lun3 && sudo vgcreate vg_hana_shared_HN1 /dev/disk/azure/scsi1/lun4 && sudo vgcreate vg_hana_shared_usrsap_HN1 /dev/disk/azure/scsi1/lun5 && sudo vgcreate vg_hana_log_HN1 /dev/disk/azure/scsi1/lun6'

# to validate if needed
# az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'vgdisplay -s'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo lvcreate -i 4 -I 256 -l 100%FREE -n hana_data  vg_hana_data_HN1 && sudo lvcreate -l 100%FREE -n hana_shared  vg_hana_shared_HN1 && sudo lvcreate -l 100%FREE -n hana_usrsap vg_hana_shared_usrsap_HN1 && sudo lvcreate -l 100%FREE -n hana_log vg_hana_log_HN1'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo lvcreate -i 4 -I 256 -l 100%FREE -n hana_data  vg_hana_data_HN1 && sudo lvcreate -l 100%FREE -n hana_shared  vg_hana_shared_HN1 && sudo lvcreate -l 100%FREE -n hana_usrsap vg_hana_shared_usrsap_HN1 && sudo lvcreate -l 100%FREE -n hana_log vg_hana_log_HN1'

# Check Lv
# az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'lvs -a -o +devices -o +segtype'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo mkfs.xfs /dev/vg_hana_data_HN1/hana_data && sudo mkfs.xfs /dev/vg_hana_shared_HN1/hana_shared && sudo mkfs.xfs /dev/vg_hana_shared_usrsap_HN1/hana_usrsap && sudo mkfs.xfs /dev/vg_hana_log_HN1/hana_log && sudo mkdir -p /hana/data/HN1 && sudo mkdir -p /hana/shared/HN1 && sudo mkdir -p /usr/sap/HN1 && sudo mkdir -p /hana/log/HN1'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo mkfs.xfs /dev/vg_hana_data_HN1/hana_data && sudo mkfs.xfs /dev/vg_hana_shared_HN1/hana_shared && sudo mkfs.xfs /dev/vg_hana_shared_usrsap_HN1/hana_usrsap && sudo mkfs.xfs /dev/vg_hana_log_HN1/hana_log && sudo mkdir -p /hana/data/HN1 && sudo mkdir -p /hana/shared/HN1 && sudo mkdir -p /usr/sap/HN1 && sudo mkdir -p /hana/log/HN1'

###### [A] Mount the shared Disk volumes

export blkids=$(az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo blkid | grep '${sapID}'')

export vg_hana_shared=$(echo ${blkids} | grep vg_hana_shared_${sapID} | awk '{print $2}')
export vg_hana_shared_UUID=$(echo ${vg_hana_shared:7:36})
export vg_hana_shared_usrsap=$(echo ${blkids} | grep vg_hana_shared_usrsap_${sapID} | awk '{print $2}')
export vg_hana_shared_usrsap_UUID=$(echo ${vg_hana_shared_usrsap:7:36})
export vg_hana_data=$(echo ${blkids} | grep vg_hana_data_${sapID} | awk '{print $2}')
export vg_hana_data_UUID=$(echo ${vg_hana_data:7:36})
export vg_hana_log=$(echo ${blkids} | grep vg_hana_log_${sapID} | awk '{print $2}')
export vg_hana_log_UUID=$(echo ${vg_hana_log:7:36})

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "\n# Add the following entries\n/dev/disk/by-uuid/'${vg_hana_data_UUID}'  /hana/data/'${sapID}' xfs  defaults,nofail  0  2\n/dev/disk/by-uuid/'${vg_hana_shared_UUID}'  /hana/shared/'${sapID}' xfs  defaults,nofail  0  2\n/dev/disk/by-uuid/'${vg_hana_shared_usrsap_UUID}'  /usr/sap/'${sapID}' xfs  defaults,nofail  0  2\n/dev/disk/by-uuid/'${vg_hana_log_UUID}'  /hana/log/'${sapID}' xfs  defaults,nofail  0  2" >> /etc/fstab && mount -a'

export blkids=$(az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo blkid | grep '${sapID}'')

export vg_hana_shared=$(echo ${blkids} | grep vg_hana_shared_${sapID} | awk '{print $2}')
export vg_hana_shared_UUID=$(echo ${vg_hana_shared:7:36})
export vg_hana_shared_usrsap=$(echo ${blkids} | grep vg_hana_shared_usrsap_${sapID} | awk '{print $2}')
export vg_hana_shared_usrsap_UUID=$(echo ${vg_hana_shared_usrsap:7:36})
export vg_hana_data=$(echo ${blkids} | grep vg_hana_data_${sapID} | awk '{print $2}')
export vg_hana_data_UUID=$(echo ${vg_hana_data:7:36})
export vg_hana_log=$(echo ${blkids} | grep vg_hana_log_${sapID} | awk '{print $2}')
export vg_hana_log_UUID=$(echo ${vg_hana_log:7:36})

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "\n# Add the following entries\n/dev/disk/by-uuid/'${vg_hana_data_UUID}'  /hana/data/'${sapID}' xfs  defaults,nofail  0  2\n/dev/disk/by-uuid/'${vg_hana_shared_UUID}'  /hana/shared/'${sapID}' xfs  defaults,nofail  0  2\n/dev/disk/by-uuid/'${vg_hana_shared_usrsap_UUID}'  /usr/sap/'${sapID}' xfs  defaults,nofail  0  2\n/dev/disk/by-uuid/'${vg_hana_log_UUID}'  /hana/log/'${sapID}' xfs  defaults,nofail  0  2" >> /etc/fstab && mount -a'

###### [A] Update Hosts 
export vmsap1_client_pip=$(az vm list-ip-addresses -n $vmsapname1  -o table | grep $vmsapname1 | awk '{print $3}')
export vmsap2_client_pip=$(az vm list-ip-addresses -n $vmsapname2  -o table | grep $vmsapname2 | awk '{print $3}')

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "# Client\n'${vmsap1_client_pip}'   '${vmsapname1}'\n'${vmsap2_client_pip}'   '${vmsapname2}'\n" >> /etc/hosts';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "# Client\n'${vmsap2_client_pip}'   '${vmsapname2}'\n'${vmsap1_client_pip}'   '${vmsapname1}'\n" >> /etc/hosts';

###### [A] Before the HANA installation, set the root password
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts '(echo '${PASSWORD}'; echo '${PASSWORD}') | passwd root'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts '(echo '${PASSWORD}'; echo '${PASSWORD}') | passwd root'

# https://stackoverflow.com/questions/43235179/how-to-execute-ssh-keygen-without-prompt
###### [A]  Create Keys
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1"

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config && systemctl restart sshd.service";
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config && systemctl restart sshd.service";

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'ssh-keyscan -H '${vmsapname2}' >> /root/.ssh/known_hosts'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'ssh-keyscan -H '${vmsapname1}' >> /root/.ssh/known_hosts'

# https://www.ibm.com/docs/en/spectrum-scale-bda?topic=STXKQY_BDA_SHR/bl1adv_passwordlessroot.html
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'chmod 700 /root/.ssh/ && chmod 640 /root/.ssh/authorized_keys'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'chmod 700 /root/.ssh/ && chmod 640 /root/.ssh/authorized_keys'

# https://software.opensuse.org/download.html?project=network&package=sshpass

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "zypper addrepo -G --refresh -C https://download.opensuse.org/repositories/network/SLE_15/network.repo && zypper install -y sshpass" 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "zypper addrepo -G --refresh -C https://download.opensuse.org/repositories/network/SLE_15/network.repo && zypper install -y sshpass" 
 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sshpass -p '${PASSWORD}' ssh-copy-id -f -i /root/.ssh/id_rsa.pub root@'${vmsapname2}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sshpass -p '${PASSWORD}' ssh-copy-id -f -i /root/.ssh/id_rsa.pub root@'${vmsapname1}''

###### [A] Install additional packages, which are required for HANA 2.0 SP4
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'zypper install -y libgcc_s1 libstdc++6 libatomic1 insserv-compat libtool';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'zypper install -y libgcc_s1 libstdc++6 libatomic1 insserv-compat libtool';

################################################################ INSTALLATION ################################################################

###### [A] Decompress SAP File + Give Permissons
###### Get AZCopy Tool
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cd /usr/sap/'${sapID}' && wget -O azcopy_v10.tar.gz https://azcopyvnext.azureedge.net/release20230123/azcopy_linux_amd64_10.17.0.tar.gz && tar -xf azcopy_v10.tar.gz && chown root:root -R azcopy_linux_amd64_10.17.0 && export PATH=$PATH:/usr/sap/'${sapID}'/azcopy_linux_amd64_10.17.0'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cd /usr/sap/'${sapID}' && wget -O azcopy_v10.tar.gz https://azcopyvnext.azureedge.net/release20230123/azcopy_linux_amd64_10.17.0.tar.gz && tar -xf azcopy_v10.tar.gz && chown root:root -R azcopy_linux_amd64_10.17.0 && export PATH=$PATH:/usr/sap/'${sapID}'/azcopy_linux_amd64_10.17.0'

###### Decompress
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "cd /usr/sap/'${sapID}'/azcopy_linux_amd64_10.17.0 && ./azcopy copy '${installerZipUrl}' '/hana/shared/'${sapID}'/download/'${sasfileNAME}'' --recursive=TRUE"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'unzip -d /hana/shared/'${sapID}'/download/hanainstall /hana/shared/'${sapID}'/download/'${sasfileNAME}'' 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS && chmod +x HDB_SERVER_LINUX_X86_64 && cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS/HDB_SERVER_LINUX_X86_64;'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'chmod o+rx /hana/shared'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "cd /usr/sap/'${sapID}'/azcopy_linux_amd64_10.17.0 && ./azcopy copy '${installerZipUrl}' '/hana/shared/'${sapID}'/download/'${sasfileNAME}'' --recursive=TRUE"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'unzip -d /hana/shared/'${sapID}'/download/hanainstall /hana/shared/'${sapID}'/download/'${sasfileNAME}'' 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS && chmod +x HDB_SERVER_LINUX_X86_64 && cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS/HDB_SERVER_LINUX_X86_64;'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'chmod o+rx /hana/shared'

# https://help.sap.com/docs/SAP_HANA_PLATFORM/2c1988d620e04368aa4103bf26f17727/0c328b5e61bc45c181f6082928d3c269.html?version=2.0.01
# https://help.sap.com/docs/SAP_HANA_ONE/1c837b3899834ddcbae140cc3e7c7bdd/b1c5b5be821f4ebba0cdb5b65055158c.html
###### [A] Add Password XML File
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Passwords>\n<password><![CDATA['${PASSWORD}']]></password>\n<sapadm_password><![CDATA['${PASSWORD}']]></sapadm_password>\n<system_user_password><![CDATA['${PASSWORD}']]></system_user_password>\n<root_password><![CDATA['${PASSWORD}']]></root_password>\n</Passwords>" >> /root/hdb_passwords.xml' 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Passwords>\n<password><![CDATA['${PASSWORD}']]></password>\n<sapadm_password><![CDATA['${PASSWORD}']]></sapadm_password>\n<system_user_password><![CDATA['${PASSWORD}']]></system_user_password>\n<root_password><![CDATA['${PASSWORD}']]></root_password>\n</Passwords>" >> /root/hdb_passwords.xml' 

###### [A] Silent Install
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS/HDB_SERVER_LINUX_X86_64 && cat ~/hdb_passwords.xml | ./hdblcm --batch --action=install --components=client,server --sid='${sapID}' --number='${instanceID}' --read_password_from_stdin=xml'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS/HDB_SERVER_LINUX_X86_64 && cat ~/hdb_passwords.xml | ./hdblcm --batch --action=install --components=client,server --sid='${sapID}' --number='${instanceID}' --read_password_from_stdin=xml'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS/HDB_SERVER_LINUX_X86_64 && cat ~/hdb_passwords.xml | ./hdblcm --batch --action=install --components=client,server --sid='${sapID}' --number='${instanceID}' --read_password_from_stdin=xml'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS/HDB_SERVER_LINUX_X86_64 && cat ~/hdb_passwords.xml | ./hdblcm --batch --action=install --components=client,server --sid='${sapID}' --number='${instanceID}' --read_password_from_stdin=xml'

###### [A] Check Instalattion
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "HDB info"'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "HDB info"'

###### [A] Check SAP Host Agent before Azure VM Extension for SAP solutions
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "cd /usr/sap/hostctrl/exe && ./saphostexec -version && ./saphostexec -status"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "cd /usr/sap/hostctrl/exe && ./saphostexec -version && ./saphostexec -status"

###### [A]
# install Azure VM Extension for SAP solutions for both nodes
# https://learn.microsoft.com/en-us/azure/sap/workloads/vm-extension-for-sap-new

az extension add --name aem;

az vm aem set -g $RESOURCE_GROUP -n $vmsapname1 --install-new-extension;
az vm aem set -g $RESOURCE_GROUP -n $vmsapname2 --install-new-extension;

# Validate Azure VM Extension for SAP 
az vm aem verify -g $RESOURCE_GROUP -n $vmsapname1;
az vm aem verify -g $RESOURCE_GROUP -n $vmsapname2;

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "bash -c  '/usr/bin/python3 <(curl --location --silent https://raw.githubusercontent.com/rfparedes/susecloud-repocheck/main/sc-repocheck.py)'")
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "bash -c  '/usr/bin/python3 <(curl --location --silent https://raw.githubusercontent.com/rfparedes/susecloud-repocheck/main/sc-repocheck.py)'"

###### [A] Configure Pacemaker cluster and install required packages on both nodes.
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "zypper update -y --auto-agree-with-licenses && reboot" 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "zypper update -y --auto-agree-with-licenses && reboot" 

# az role assignment list --resource-group $RESOURCE_GROUP
# az role assignment create --assignee "{assignee}" --role "Contributor" --scope "/subscriptions/$subscriptionId/resourcegroups/$RESOURCE_GROUP/providers/Microsoft.Compute/virtualMachines/$vmsapname1"

# Checks Pacemaker
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "sudo zypper info crmsh && && zypper info pacemaker && sudo zypper in resource-agents && sudo zypper in socat && zypper info cloud-netconfig-azure" ;
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "sudo zypper info crmsh && && zypper info pacemaker && sudo zypper in resource-agents && sudo zypper in socat && zypper info cloud-netconfig-azure" ;

# Configure Pacemaker cluster parameters 

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "DefaultTasksMax=4096" >> /etc/systemd/system.conf';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "DefaultTasksMax=4096" >> /etc/systemd/system.conf';

# Check File Content
# az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cat /etc/systemd/system.conf | egrep -v "(^#.*|^$)"';
# az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cat /etc/systemd/system.conf | egrep -v "(^#.*|^$)"';

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'systemctl daemon-reload && systemctl --no-pager show | grep DefaultTasksMax'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'systemctl daemon-reload && systemctl --no-pager show | grep DefaultTasksMax'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo "vm.dirty_bytes = 629145600" >> /etc/sysctl.conf && echo "vm.dirty_background_bytes = 314572800" >> /etc/sysctl.conf && echo "vm.swappiness = 10" >> /etc/sysctl.conf'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo "vm.dirty_bytes = 629145600" >> /etc/sysctl.conf && echo "vm.dirty_background_bytes = 314572800" >> /etc/sysctl.conf && echo "vm.swappiness = 10" >> /etc/sysctl.conf'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cat /etc/sysctl.conf | egrep -v "(^#.*|^$)"';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cat /etc/sysctl.conf | egrep -v "(^#.*|^$)"';

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sed -i 's/yes/no/g' /etc/sysconfig/network/ifcfg-eth0 && cat /etc/sysconfig/network/ifcfg-eth0 | egrep -v "(^#.*|^$)"';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sed -i 's/yes/no/g' /etc/sysconfig/network/ifcfg-eth0 && cat /etc/sysconfig/network/ifcfg-eth0 | egrep -v "(^#.*|^$)"';

################################################################ Cluster Configuration ################################################################
#[A]: Applicable to all nodes
#[1]: Applicable only to node 1
#[2]: Applicable only to node 2

###### [A] Install fence-agents and other required packages. 

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'zypper install -y fence-agents python3-azure-mgmt-compute python3-azure-identity'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'zypper install -y fence-agents python3-azure-mgmt-compute python3-azure-identity'

###### [1] Install the cluster setup starting from node 1

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "#!/usr/bin/expect -f
set timeout 60
spawn bash -c \"sudo crm cluster init\"
expect {
    \"Continue*\" {
        send \"y\r\"
        exp_continue
    }
    \"Address for ring0*\" {
        send \"\r\"
        exp_continue
    }
    \"Port for ring0*\" {
        send \"\r\"
        exp_continue
    }
    \"Do you wish to use SBD (y/n)?\" {
        send \"n\r\"
        exp_continue
    }
    timeout {
        send_user \"Timed out waiting for the prompt.\\n\"
        exit 1
    }
    \"Do you wish to configure a virtual IP address (y/n)?\" {
        send \"n\r\"
        exp_continue
    }
    \"Do you want to configure QDevice (y/n)?\" {
        send \"n\r\"
        exp_continue
    }
    eof {
        after 2000
        send_user \"Cluster initialization completed.\\n\"
        exit 0
    }
}"' --output json

###### [2] Join to the cluster started on the node 1

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "#!/usr/bin/expect -f
set timeout 60
spawn bash -c \"sudo crm cluster join\"
expect {
    \"IP address or hostname of existing node*\" {
        send \"'${vmsap1_client_pip}'\r\"
        exp_continue
    }
    \"Continue*\" {
        send \"y\r\"
        exp_continue
    }
    \"Address for ring0*\" {
        send \"\r\"
        exp_continue
    }
    timeout {
        send_user \"Timed out waiting for the prompt.\\n\"
        exit 1
    }
    eof {
        after 2000
        send_user \"Cluster Join completed.\\n\"
        exit 0
    }
}"' --output json

###### [A] Configure cluster setup on both nodes 

###### [A] set the hacluster password & token values
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts '(echo '${PASSWORD}'; echo '${PASSWORD}') | passwd hacluster'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts '(echo '${PASSWORD}'; echo '${PASSWORD}') | passwd hacluster'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sed -i '/token_retransmits_before_loss_const: 10/a consensus:      36000' /etc/corosync/corosync.conf"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "cat /etc/corosync/corosync.conf | grep -a3 token_retransmits_before_loss_const";
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts  "sed -i '/token_retransmits_before_loss_const: 10/a consensus:      36000' /etc/corosync/corosync.conf"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts  "cat /etc/corosync/corosync.conf | grep -a3 token_retransmits_before_loss_const";

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo service corosync restart"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts  "sudo service corosync restart"

###### [1] Create a fencing device on Azure Fence Agent
# https://learn.microsoft.com/en-us/azure/sap/workloads/high-availability-guide-suse-pacemaker#create-a-fencing-device-on-the-pacemaker-cluster

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo crm configure property stonith-enabled=true"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo crm configure property concurrent-fencing=true"

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure primitive rsc_st_azure stonith:fence_azure_arm \
params msi=true subscriptionId='${subscriptionId}' resourceGroup='${RESOURCE_GROUP}' \
pcmk_monitor_retries=4 pcmk_action_limit=3 power_timeout=240 pcmk_reboot_timeout=900  \
op monitor interval=3600 timeout=120'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo crm configure property stonith-timeout=900"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo crm resource list" --output json

###### [A] Make sure that the package for the azure-events agent is already installed
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo zypper info resource-agents"

###### [1] Configure Pacemaker cluster resource for Scheduled Events. (takes a while...)
# https://learn.microsoft.com/en-us/azure/sap/workloads/high-availability-guide-suse-pacemaker#configure-pacemaker-for-azure-scheduled-events

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo crm configure property maintenance-mode=true && \
 sudo crm configure primitive rsc_azure-events ocf:heartbeat:azure-events op monitor interval=10s && \
 sudo crm configure clone cln_azure-events rsc_azure-events && \
 sudo crm configure property maintenance-mode=false"

# Print Output of Crm Status
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo crm status" --query "value[].message" -o tsv;

###### [A] Update HANA HSR package on both nodes.
# https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability#configure-sap-hana-20-system-replication

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "zypper install -y SAPHanaSR"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts  "zypper install -y SAPHanaSR"

###### [1] Configure HANA System Replication starting from node 1

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "HDB start"'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "HDB info"' --query "value[].message" -o tsv;

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "HDB start"'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "#!/bin/bash
sudo su -
su - '${sapid}'adm
hdbsql -d SYSTEMDB -u SYSTEM -p \"'${PASSWORD}'\" -i '${instanceID}' \"BACKUP DATA USING FILE ('initialbackupSYS')\"
"' --output json

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "#!/bin/bash
sudo su -
su - '${sapid}'adm
hdbsql -d '${sapID}' -u SYSTEM -p \"'${PASSWORD}'\" -i '${instanceID}' \"BACKUP DATA USING FILE ('initialbackup'${sapID}'')\"
"' --output json

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'scp /usr/sap/'${sapID}'/SYS/global/security/rsecssfs/data/SSFS_'${sapID}'.DAT  '${vmsapname2}':/usr/sap/'${sapID}'/SYS/global/security/rsecssfs/data/'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'scp /usr/sap/'${sapID}'/SYS/global/security/rsecssfs/key/SSFS_'${sapID}'.KEY  '${vmsapname2}':/usr/sap/'${sapID}'/SYS/global/security/rsecssfs/key/'

# successfully enabled system as system replication source site
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "hdbnsutil -sr_enable --name=SITE1"'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "hdbnsutil -sr_state"'  --query "value[].message" -o tsv;

###### [2] Configure HANA System Replication on node 2 and check replication state. 

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "sapcontrol -nr '${instanceID}' -function StopWait 600 10"'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "hdbnsutil -sr_register --remoteHost='${vmsapname1}' --remoteInstance='${instanceID}' --replicationMode=sync --name=SITE2"'

hdbnsutil -sr_register --remoteHost=vm-mce-hana01 --remoteInstance=00 --replicationMode=sync --name=SITE2;

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "hdbnsutil -sr_state"'  --query "value[].message" -o tsv;

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "hdbnsutil -sr_state"'  --query "value[].message" -o tsv;
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "HDB info"'  --query "value[].message" -o tsv;

###### [A] Install HANA SR Python Hook and susChkSrv on both nodes
# https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability#configure-sap-hana-20-system-replication

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "sapcontrol -nr '${instanceID}' -function StopSystem"'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "sapcontrol -nr '${instanceID}' -function StopSystem"'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo zypper info SAPHANASR'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cat << EOF >> /hana/shared/'${sapID}'/global/hdb/custom/config/global.ini
# add to global.ini
[ha_dr_provider_SAPHanaSR]
provider = SAPHanaSR
path = /usr/share/SAPHanaSR
execution_order = 1

[ha_dr_provider_suschksrv]
provider = susChkSrv
path = /usr/share/SAPHanaSR
execution_order = 3
action_on_lost = fence

[trace]
ha_dr_saphanasr = info
EOF'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cat << EOF >> /hana/shared/'${sapID}'/global/hdb/custom/config/global.ini
# add to global.ini
[ha_dr_provider_SAPHanaSR]
provider = SAPHanaSR
path = /usr/share/SAPHanaSR
execution_order = 1

[ha_dr_provider_suschksrv]
provider = susChkSrv
path = /usr/share/SAPHanaSR
execution_order = 3
action_on_lost = fence

[trace]
ha_dr_saphanasr = info
EOF'

###### [A] Run these OS commands on both nodes
#  The cluster requires sudoers configuration on each cluster node for <sid>adm.
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cat << EOF > /etc/sudoers.d/20-saphana
# Needed for SAPHanaSR and susChkSrv Python hooks
'${sapid}'adm ALL=(ALL) NOPASSWD: /usr/sbin/crm_attribute -n hana_'${sapid}'_site_srHook_*
'${sapid}'adm ALL=(ALL) NOPASSWD: /usr/sbin/SAPHanaSR-hookHelper --sid='${sapID}' --case=fenceMe
EOF'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cat << EOF > /etc/sudoers.d/20-saphana
# Needed for SAPHanaSR and susChkSrv Python hooks
'${sapid}'adm ALL=(ALL) NOPASSWD: /usr/sbin/crm_attribute -n hana_'${sapid}'_site_srHook_*
'${sapid}'adm ALL=(ALL) NOPASSWD: /usr/sbin/SAPHanaSR-hookHelper --sid='${sapID}' --case=fenceMe
EOF'

###### [A] Start SAP HANA on both nodes

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "sapcontrol -nr '${instanceID}' -function StartSystem"'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "sapcontrol -nr '${instanceID}' -function StartSystem"'

###### [1] Verify the hook & susChkSrv installation

# Verify the hook installation
az vm run-command invoke --resource-group $RESOURCE_GROUP --name $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "cd /usr/sap/'${sapID}'/HDB'${instanceID}'/'${vmsapname1}'/trace && awk '\''/ha_dr_SAPHanaSR.*crm_attribute/ { printf \"%s %s %s %s\\n\",\$2,\$3,\$5,\$16 }'\'' nameserver_*"' --query "value[].message" -o tsv;

# Verify the susChkSrv hook installation
az vm run-command invoke --resource-group $RESOURCE_GROUP --name $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "cd /usr/sap/'${sapID}'/HDB'${instanceID}'/'${vmsapname1}'/trace && egrep '\''(LOST:|STOP:|START:|DOWN:|init|load|fail)'\'' nameserver_suschksrv.trc"' --query "value[].message" -o tsv;

###### [1] Create SAP HANA cluster resources on Pacemaker
# https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability#create-sap-hana-cluster-resources

# Make sure :
# (1) rsc_nc_HN1_HDB00 azure-lb port == Health probe port of Azure Load Balancer (62500 aka $lbPort)
# (2) primitive rsc_ip_HN1_HDB00 ocf:heartbeat:IPaddr2 params IP == frontend IP of Azure LB (10.33.0.9)
# Don't use a private IP of node 1 or node 2, which will cause IP conflict ! 

# create the HANA topology.

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts  "sudo crm configure property maintenance-mode=true"

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure primitive rsc_st_azure stonith:fence_azure_arm \
params msi=true subscriptionId='${subscriptionId}' resourceGroup='${RESOURCE_GROUP}' \
pcmk_monitor_retries=4 pcmk_action_limit=3 power_timeout=240 pcmk_reboot_timeout=900  \
op monitor interval=3600 timeout=120'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure primitive rsc_SAPHanaTopology_'${sapID}'_HDB'${instanceID}' ocf:suse:SAPHanaTopology \
operations \$id="rsc_sap2_'${sapID}'_HDB'${instanceID}'-operations" \
op monitor interval="10" timeout="600" \
op start interval="0" timeout="600" \
op stop interval="0" timeout="300" \
params SID="'${sapID}'" InstanceNumber="'${instanceID}'"'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure clone cln_SAPHanaTopology_'${sapID}'_HDB'${instanceID}' rsc_SAPHanaTopology_HN1_HDB00 \
meta clone-node-max="1" target-role="Started" interleave="true"'

# create the HANA resources: ####### TO DO - FW!
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure primitive rsc_SAPHana_'${sapID}'_HDB'${instanceID}' ocf:suse:SAPHana \
operations \$id="rsc_sap_'${sapID}'_HDB'${instanceID}'-operations" \
op start interval="0" timeout="3600" \
op stop interval="0" timeout="3600" \
op promote interval="0" timeout="3600" \
op monitor interval="60" role="Master" timeout="700" \
op monitor interval="61" role="Slave" timeout="700" \
params SID="'${sapID}'" InstanceNumber="'${instanceID}'" PREFER_SITE_TAKEOVER="true" \
DUPLICATE_PRIMARY_TIMEOUT="7200" AUTOMATED_REGISTER="true"'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure ms msl_SAPHana_'${sapID}'_HDB'${instanceID}' rsc_SAPHana_HN1_HDB00 \
meta notify="true" clone-max="2" clone-node-max="1" \
target-role="Started" interleave="true"'

lbprivaddr="$(az network lb show -g $RESOURCE_GROUP --name $LB_NAME --query "frontendIPConfigurations[0]" --output tsv |  awk '{print $5}')"

# Frontend IP of Load Balancer 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure primitive rsc_ip_'${sapID}'_HDB'${instanceID}' ocf:heartbeat:IPaddr2 \
meta target-role="Started" \
operations \$id="rsc_ip_'${sapID}'_HDB'${instanceID}'-operations" \
op monitor interval="10s" timeout="20s" \
params ip="'${lbprivaddr}'"'
   
# Health Probe Port 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure primitive rsc_nc_'${sapID}'_HDB'${instanceID}' azure-lb port='${lbPort}' \
op monitor timeout=20s interval=10 \
meta resource-stickiness=0 '

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure group g_ip_'${sapID}'_HDB'${instanceID}' rsc_ip_'${sapID}'_HDB'${instanceID}' rsc_nc_'${sapID}'_HDB'${instanceID}''

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure colocation col_saphana_ip_'${sapID}'_HDB'${instanceID}' 4000: g_ip_'${sapID}'_HDB'${instanceID}':Started \
msl_SAPHana_'${sapID}'_HDB'${instanceID}':Master'

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure order ord_SAPHana_'${sapID}'_HDB'${instanceID}' Optional: cln_SAPHanaTopology_'${sapID}'_HDB'${instanceID}' \
msl_SAPHana_'${sapID}'_HDB'${instanceID}''

# Clean up the HANA resources. The HANA resources might have failed because of a known issue.
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm resource cleanup rsc_SAPHana_'${sapID}'_HDB'${instanceID}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure property maintenance-mode=false'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure rsc_defaults resource-stickiness=1000'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure rsc_defaults migration-threshold=5000'

################################## IF ISSUES on Automatic ### UNCOMMENT THE FOLLOWING LINES #####################################
# https://www.suse.com/support/kb/doc/?id=000020286#:~:text=The%20crm%20shell%20provides%20an%20%22%20edit%20%22,any%20changes%20that%20were%20made%20to%20the%20primitive.
#az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'crm configure show > /root/rsc_SAPHana_'${sapID}'_HDB'${instanceID}'_backup.txt'
#az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "sed -i 's/AUTOMATED_REGISTER=false/AUTOMATED_REGISTER=true/g' /root/rsc_SAPHana_'${sapID}'_HDB'${instanceID}'_backup.txt";
#az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure property maintenance-mode=true'
#az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'crm configure load replace /root/rsc_SAPHana_'${sapID}'_HDB'${instanceID}'_backup.txt'
#az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm resource cleanup rsc_SAPHana_'${sapID}'_HDB'${instanceID}''
#az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1  --command-id RunShellScript --scripts 'sudo crm configure property maintenance-mode=false'

################################## Last Checks on SAP HANA - Pacemaker #####################################

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "HDB info"' --query "value[].message" -o tsv;
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "hdbnsutil -sr_state"' --query "value[].message" -o tsv;
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'crm status' --query "value[].message" -o tsv;
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'SAPHanaSR-showAttr' --query "value[].message" -o tsv;
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'crm configure show SAPHanaSR'  --query "value[].message" -o tsv;
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "python /usr/sap/HN1/HDB00/exe/python_support/systemReplicationStatus.py"'  --query "value[].message" -o tsv;
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sudo su - '${sapid}'adm -c "python /usr/sap/HN1/HDB00/exe/python_support/landscapeHostConfiguration.py"'  --query "value[].message" -o tsv;



