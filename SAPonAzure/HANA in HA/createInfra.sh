#!/bin/sh

################ Change Variables - Mandatory! ################

# If you have a file on a StorageAccount - this is can be obtained from: Storage Account > Containers > Shared access tokens > HTTPS/HTTP SAS Token - with Read & List > "Blob SAS URL"
export installerZipUrl="https://URL/"
export subscriptionId=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX
export sapfileNAME='FILENAME.ZIP'

################ INFRA > Networking Variables ################

export LOCATION=eastus;
export RESOURCE_GROUP=hana_script;
export sapvnet=vnet-sap;
export sapvnetaddress="10.23.0.0/22"
export clientsubnet=client;
export hanasubnet=hana;
export storagesubnet=storage;
export netappsubnet=anf;
export clientsubnetaddress="10.23.0.0/24"
export hanasubnetaddress="10.23.3.0/24"
export storagesubnetaddress="10.23.2.0/24"
export routerIPforStorageNetwork="10.23.2.1"
export netappsubnetaddress="10.23.1.0/26"

INTERNAL_ADDRESS=${hanasubnetaddress:0:7}/24
netappIP=${netappsubnetaddress:0:8}4
storageIP=${storagesubnetaddress:0:7}

################################################################ SAP HANA - HA    ################################################################
# https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-scale-out-standby-netapp-files-suse
################################################################ SET Subscription ################################################################

#Set Subscription
az account set --subscription $subscriptionId;

################################################################ Create Infra ################################################################

#RG Create
az group create --name $RESOURCE_GROUP --location $LOCATION;

#VNET
az network vnet create --address-prefixes $sapvnetaddress --name $sapvnet --resource-group $RESOURCE_GROUP;

#Subnets  
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $clientsubnet  --address-prefixes $clientsubnetaddress;
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $hanasubnet    --address-prefixes $hanasubnetaddress;
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $storagesubnet --address-prefixes $storagesubnetaddress;

#NetAPP Register & Delegate Subnet
az provider register --namespace Microsoft.NetApp --wait
az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n $netappsubnet  --address-prefixes $netappsubnetaddress --delegations Microsoft.NetApp/volumes;

#check delegations & register
#az provider show --namespace Microsoft.NetApp;
#az network vnet subnet show -g $RESOURCE_GROUP  --name $netappsubnet --vnet-name $sapvnet --query delegations;

################ SAP / VM Variables ################
export sapID=HN1
export sapid=hn1
export instanceID=00
export PASSWORD=Password1!
export vmsapname1=hanadb1
export vmsapname2=hanadb2
export vmsapname3=hanadb3
export vmsapname2_role=worker
export vmsapname3_role=standby

################ ANF - Volumes Variables ################
export VNET_ID=$(az network vnet show --resource-group $RESOURCE_GROUP --name $sapvnet --query "id" -o tsv)
export SUBNET_ID=$(az network vnet subnet show --resource-group $RESOURCE_GROUP --vnet-name $sapvnet --name $netappsubnet --query "id" -o tsv)
export VOLUME_SIZE_GiB=200 # 200 GiB
export ANF_ACCOUNT_NAME=mynetappsap
export POOL_NAME="sappool"
export POOL_SIZE_TiB=4 # Size in Azure CLI needs to be in TiB unit (minimum 4 TiB)
export SERVICE_LEVEL="Ultra" # Valid values are Standard, Premium and Ultra

export ALLOWED_CLIENTS=0.0.0.0/0
export volume_data_vol1=$sapID-data-mnt00001
export volume_data_vol1_path=$sapID-data-mnt00001
export volume_data_vol2=$sapID-data-mnt00002
export volume_data_vol2_path=$sapID-data-mnt00002
export volume_data_vol3=$sapID-data-mnt00003
export volume_data_vol3_path=$sapID-data-mnt00003
export volume_log_vol1=$sapID-log-mnt00001
export volume_log_vol1_path=$sapID-log-mnt00001
export volume_log_vol2=$sapID-log-mnt00002
export volume_log_vol2_path=$sapID-log-mnt00002
export volume_log_vol3=$sapID-log-mnt00003
export volume_log_vol3_path=$sapID-log-mnt00003
export volume_shared=$sapID-shared
export volume_shared_path=$sapID-shared
export volume_usrsap1=$sapID-usrsap-$vmsapname1
export volume_usrsap1_path=$sapID-usrsap-$vmsapname1
export volume_usrsap2=$sapID-usrsap-$vmsapname2
export volume_usrsap2_path=$sapID-usrsap-$vmsapname2
export volume_usrsap3=$sapID-usrsap-$vmsapname3
export volume_usrsap3_path=$sapID-usrsap-$vmsapname3

################################################################ Create ANF & Volumes ################################################################

#https://learn.microsoft.com/en-us/azure/azure-netapp-files/azure-netapp-files-quickstart-set-up-account-create-volumes?tabs=azure-cli
az netappfiles account create -g $RESOURCE_GROUP --name $ANF_ACCOUNT_NAME -l $LOCATION;

# https://learn.microsoft.com/en-us/cli/azure/netappfiles/volume?view=azure-cli-latest#az-netappfiles-volume-create

# Create Capacity Pool & Volumes
az netappfiles pool create --resource-group $RESOURCE_GROUP --location $LOCATION --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --size $POOL_SIZE_TiB --service-level $SERVICE_LEVEL

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_data_vol1 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_data_vol1_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_data_vol2 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_data_vol2_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_data_vol3 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_data_vol3_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_log_vol1 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_log_vol1_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_log_vol2 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_log_vol2_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_log_vol3 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_log_vol3_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_shared --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_shared_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_usrsap1 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_usrsap1_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_usrsap2 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_usrsap2_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

az netappfiles volume create --resource-group $RESOURCE_GROUP --location $LOCATION \
    --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_usrsap3 --service-level $SERVICE_LEVEL \
    --vnet $VNET_ID --subnet $SUBNET_ID \
    --usage-threshold $VOLUME_SIZE_GiB --file-path $volume_usrsap3_path --protocol-types "NFSv4.1" --allowed-clients $ALLOWED_CLIENTS --rule-index 1

################ ANF / Volumes IP Variables ################

export volume_data_vol1IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_data_vol1 | grep "ipAddress" | awk '{print $2}')
volume_data_vol1IP=${volume_data_vol1IPx:1:9}

export volume_data_vol2IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_data_vol2 | grep "ipAddress" | awk '{print $2}')
volume_data_vol2IP=${volume_data_vol2IPx:1:9}

export volume_data_vol3IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_data_vol3 | grep "ipAddress" | awk '{print $2}')
volume_data_vol3IP=${volume_data_vol3IPx:1:9}

export volume_log_vol1IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_log_vol1 | grep "ipAddress" | awk '{print $2}')
volume_log_vol1IP=${volume_log_vol1IPx:1:9}

export volume_log_vol2IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_log_vol2 | grep "ipAddress" | awk '{print $2}')
volume_log_vol2IP=${volume_log_vol2IPx:1:9}

export volume_log_vol3IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_log_vol3 | grep "ipAddress" | awk '{print $2}')
volume_log_vol3IP=${volume_log_vol3IPx:1:9}

export volume_shareIPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_shared | grep "ipAddress" | awk '{print $2}')
volume_shareIP=${volume_shareIPx:1:9}

export volume_usrsap1IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_usrsap1 | grep "ipAddress" | awk '{print $2}')
volume_usrsap1IP=${volume_usrsap1IPx:1:9}

export volume_usrsap2IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_usrsap2 | grep "ipAddress" | awk '{print $2}')
volume_usrsap2IP=${volume_usrsap2IPx:1:9}

export volume_usrsap3IPx=$(az netappfiles volume show  -g $RESOURCE_GROUP --account-name $ANF_ACCOUNT_NAME --pool-name $POOL_NAME --name $volume_usrsap3 | grep "ipAddress" | awk '{print $2}')
volume_usrsap3IP=${volume_usrsap3IPx:1:9}
	
############################################################

# Firewall if Needed 
#az network vnet subnet create -g $RESOURCE_GROUP --vnet-name $sapvnet  -n FirewallSubnet --address-prefixes 10.23.4.0/26;

################################################################ Create Availbility Set ################################################################

# https://learn.microsoft.com/en-us/cli/azure/vm/availability-set?view=azure-cli-latest#az-vm-availability-set-create

export avsetname="sap-avb-set"
az vm availability-set create -n $avsetname --location $LOCATION -g $RESOURCE_GROUP --platform-fault-domain-count 3 --platform-update-domain-count 3

################ NICs & IPs Variables ################

export vmsap1nic_client=$vmsapname1-client
export vmsap1nic_hana=$vmsapname1-hana
export vmsap1nic_storage=$vmsapname1-storage

export vmsap2nic_client=$vmsapname2-client
export vmsap2nic_hana=$vmsapname2-hana
export vmsap2nic_storage=$vmsapname2-storage

export vmsap3nic_client=$vmsapname3-client
export vmsap3nic_hana=$vmsapname3-hana
export vmsap3nic_storage=$vmsapname3-storage

# https://learn.microsoft.com/en-us/azure/virtual-machines/linux/multiple-nics#create-a-vm-and-attach-the-nics
# Public IPs HANA DB's Nodes
export vmsap1_ip_address=$vmsapname1-hana-ip
export vmsap2_ip_address=$vmsapname2-hana-ip
export vmsap3_ip_address=$vmsapname3-hana-ip

# Private IPs HANA DB's Nodes
export vmsap1_hana_pip=10.23.3.4
export vmsap2_hana_pip=10.23.3.5
export vmsap3_hana_pip=10.23.3.6

export vmsap1_client_pip=10.23.0.4
export vmsap2_client_pip=10.23.0.5
export vmsap3_client_pip=10.23.0.6

export vmsap1_storage_pip=10.23.2.4
export vmsap2_storage_pip=10.23.2.5
export vmsap3_storage_pip=10.23.2.6

################################################################ Create IP / NIC ################################################################

##### Public IPs 
az network public-ip create --resource-group $RESOURCE_GROUP  --name $vmsap1_ip_address --sku Standard --version IPv4 --zone 1 2 3;
az network public-ip create --resource-group $RESOURCE_GROUP  --name $vmsap2_ip_address --sku Standard --version IPv4 --zone 1 2 3;
az network public-ip create --resource-group $RESOURCE_GROUP  --name $vmsap3_ip_address --sku Standard --version IPv4 --zone 1 2 3;

##### NICS VM Hana 1	
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap1nic_client  --vnet-name $sapvnet --subnet $clientsubnet  --accelerated-networking true --private-ip-address $vmsap1_client_pip --private-ip-address-version IPv4 --network-security-group $sapvnet-$clientsubnet-nsg-$LOCATION;
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap1nic_hana    --vnet-name $sapvnet --subnet $hanasubnet    --accelerated-networking true --private-ip-address $vmsap1_hana_pip --private-ip-address-version IPv4 --public-ip-address $vmsap1_ip_address --network-security-group $sapvnet-$hanasubnet-nsg-$LOCATION;
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap1nic_storage --vnet-name $sapvnet --subnet $storagesubnet --accelerated-networking true --private-ip-address $vmsap1_storage_pip --private-ip-address-version IPv4 --network-security-group $sapvnet-$storagesubnet-nsg-$LOCATION;

##### NICS VM Hana 2
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap2nic_client  --vnet-name $sapvnet --subnet $clientsubnet  --accelerated-networking true --private-ip-address $vmsap2_client_pip --private-ip-address-version IPv4 --network-security-group $sapvnet-$clientsubnet-nsg-$LOCATION;
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap2nic_hana    --vnet-name $sapvnet --subnet $hanasubnet    --accelerated-networking true --private-ip-address $vmsap2_hana_pip --private-ip-address-version IPv4 --public-ip-address $vmsap2_ip_address --network-security-group $sapvnet-$hanasubnet-nsg-$LOCATION;
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap2nic_storage --vnet-name $sapvnet --subnet $storagesubnet --accelerated-networking true --private-ip-address $vmsap2_storage_pip --private-ip-address-version IPv4 --network-security-group $sapvnet-$storagesubnet-nsg-$LOCATION;

##### NICS VM Hana 3
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap3nic_client  --vnet-name $sapvnet --subnet $clientsubnet  --accelerated-networking true --private-ip-address $vmsap3_client_pip --private-ip-address-version IPv4 --network-security-group $sapvnet-$clientsubnet-nsg-$LOCATION;
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap3nic_hana    --vnet-name $sapvnet --subnet $hanasubnet    --accelerated-networking true --private-ip-address $vmsap3_hana_pip --private-ip-address-version IPv4 --public-ip-address $vmsap3_ip_address --network-security-group $sapvnet-$hanasubnet-nsg-$LOCATION;
az network nic create --resource-group $RESOURCE_GROUP --name $vmsap3nic_storage --vnet-name $sapvnet --subnet $storagesubnet --accelerated-networking true --private-ip-address $vmsap3_storage_pip --private-ip-address-version IPv4 --network-security-group $sapvnet-$storagesubnet-nsg-$LOCATION;

################################################################   Create VM  ################################################################

################ Size and Image ################

# https://learn.microsoft.com/en-us/azure/virtual-machines/linux/multiple-nics#create-a-vm-and-attach-the-nics 
export vmdb_size=Standard_E8ds_v5
#export suseimage="SUSE:sles-15-sp3:gen2:latest";
export suseimage="SUSE:sles-sap-15-sp4:gen2:2023.02.05";

# get suse images by provider
#az vm image list -p suse;
#When specifying an existing NIC, do not specify NSG, public IP, ASGs, VNet or subnet.
# https://learn.microsoft.com/en-us/previous-versions/azure/virtual-machines/linux/tutorial-availability-sets

az vm create -g $RESOURCE_GROUP --name $vmsapname1 --location $LOCATION --image $suseimage --size $vmdb_size --availability-set $avsetname \
--admin-username azureadmin --generate-ssh-keys \
--nics $vmsap1nic_hana $vmsap1nic_client $vmsap1nic_storage

az vm create -g $RESOURCE_GROUP --name $vmsapname2 --location $LOCATION --image $suseimage --size $vmdb_size --availability-set $avsetname \
--admin-username azureadmin --generate-ssh-keys \
--nics $vmsap2nic_hana $vmsap2nic_client $vmsap2nic_storage

az vm create -g $RESOURCE_GROUP --name $vmsapname3 --location $LOCATION --image $suseimage --size $vmdb_size --availability-set $avsetname \
--admin-username azureadmin --generate-ssh-keys \
--nics $vmsap3nic_hana $vmsap3nic_client $vmsap3nic_storage

###########################################################  NSG Machine IP ########################################################### 

export myIP=$(curl http://ifconfig.co)
export myIPnsgRULEname=AllowMyIP
export vnetNSGname=$sapvnet-$hanasubnet-nsg-$LOCATION

az network nsg rule create -g $RESOURCE_GROUP  --nsg-name $vnetNSGname -n $myIPnsgRULEname --priority 1000 \
--source-address-prefixes $myIP --source-port-ranges '*' --destination-address-prefixes '*' \
--destination-port-ranges 22 --access Allow --protocol Tcp \
--description "AllowMyIpAddressSSHInbound"

################################################################ VM CONFIG ################################################################
#[A]: Applicable to all nodes
#[1]: Applicable only to node 1
#[2]: Applicable only to node 2
#[3]: Applicable only to node 3
 
###### [A] Create Directories
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'mkdir -p /hana/data/'${sapID}'/mnt00001 && mkdir -p /hana/data/'${sapID}'/mnt00002 && mkdir -p /hana/data/'${sapID}'/mnt00003 && mkdir -p /hana/log/'${sapID}'/mnt00001 &&  mkdir -p /hana/log/'${sapID}'/mnt00002 && mkdir -p /hana/log/'${sapID}'/mnt00003 && mkdir -p /hana/shared && mkdir -p /usr/sap/'${sapID}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'mkdir -p /hana/data/'${sapID}'/mnt00001 && mkdir -p /hana/data/'${sapID}'/mnt00002 && mkdir -p /hana/data/'${sapID}'/mnt00003 && mkdir -p /hana/log/'${sapID}'/mnt00001 &&  mkdir -p /hana/log/'${sapID}'/mnt00002 && mkdir -p /hana/log/'${sapID}'/mnt00003 && mkdir -p /hana/shared && mkdir -p /usr/sap/'${sapID}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'mkdir -p /hana/data/'${sapID}'/mnt00001 && mkdir -p /hana/data/'${sapID}'/mnt00002 && mkdir -p /hana/data/'${sapID}'/mnt00003 && mkdir -p /hana/log/'${sapID}'/mnt00001 &&  mkdir -p /hana/log/'${sapID}'/mnt00002 && mkdir -p /hana/log/'${sapID}'/mnt00003 && mkdir -p /hana/shared && mkdir -p /usr/sap/'${sapID}''

###### [A] Update Hosts 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "# Storage\n'${vmsap1_storage_pip}'   '${vmsapname1}'-storage\n'${vmsap2_storage_pip}'   '${vmsapname2}'-storage\n'${vmsap3_storage_pip}'   '${vmsapname3}'-storage\n# Client\n'${vmsap1_client_pip}'   '${vmsapname1}'\n'${vmsap2_client_pip}'   '${vmsapname2}'\n'${vmsap3_client_pip}'   '${vmsapname3}'\n# Hana\n'${vmsap1_hana_pip}'  '${vmsapname1}'-hana\n'${vmsap2_hana_pip}'    '${vmsapname2}'-hana\n'${vmsap3_hana_pip}'    '${vmsapname3}'-hana\n" >> /etc/hosts';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "# Storage\n'${vmsap1_storage_pip}'   '${vmsapname1}'-storage\n'${vmsap2_storage_pip}'   '${vmsapname2}'-storage\n'${vmsap3_storage_pip}'   '${vmsapname3}'-storage\n# Client\n'${vmsap1_client_pip}'   '${vmsapname1}'\n'${vmsap2_client_pip}'   '${vmsapname2}'\n'${vmsap3_client_pip}'   '${vmsapname3}'\n# Hana\n'${vmsap1_hana_pip}'  '${vmsapname1}'-hana\n'${vmsap2_hana_pip}'    '${vmsapname2}'-hana\n'${vmsap3_hana_pip}'    '${vmsapname3}'-hana\n" >> /etc/hosts';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo -e "# Storage\n'${vmsap1_storage_pip}'   '${vmsapname1}'-storage\n'${vmsap2_storage_pip}'   '${vmsapname2}'-storage\n'${vmsap3_storage_pip}'   '${vmsapname3}'-storage\n# Client\n'${vmsap1_client_pip}'   '${vmsapname1}'\n'${vmsap2_client_pip}'   '${vmsapname2}'\n'${vmsap3_client_pip}'   '${vmsapname3}'\n# Hana\n'${vmsap1_hana_pip}'  '${vmsapname1}'-hana\n'${vmsap2_hana_pip}'    '${vmsapname2}'-hana\n'${vmsap3_hana_pip}'    '${vmsapname3}'-hana\n" >> /etc/hosts';

###### [A] Get Storage NetworkInterface
export outputStgNetInt=$(az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'ip a | grep -i "inet '${storageIP}'"' | grep "message" | awk '{print $11}')
networkInterface=${outputStgNetInt:0:4}

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "sed -i 's/CLOUD_NETCONFIG_MANAGE=\"yes\"/CLOUD_NETCONFIG_MANAGE=\"no\"/g' /etc/sysconfig/network/ifcfg-'${networkInterface}'";
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "sed -i 's/CLOUD_NETCONFIG_MANAGE=\"yes\"/CLOUD_NETCONFIG_MANAGE=\"no\"/g' /etc/sysconfig/network/ifcfg-'${networkInterface}'";
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts "sed -i 's/CLOUD_NETCONFIG_MANAGE=\"yes\"/CLOUD_NETCONFIG_MANAGE=\"no\"/g' /etc/sysconfig/network/ifcfg-'${networkInterface}'";

###### [A] Add a network route
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "# Add the following routes \n# RouterIPforStorageNetwork - - -\n# ANFNetwork/cidr RouterIPforStorageNetwork - -\n'${routerIPforStorageNetwork}' - - -\n'${netappsubnetaddress}' '${routerIPforStorageNetwork}' - -" >> /etc/sysconfig/network/ifroute-'${networkInterface}'';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "# Add the following routes \n# RouterIPforStorageNetwork - - -\n# ANFNetwork/cidr RouterIPforStorageNetwork - -\n'${routerIPforStorageNetwork}' - - -\n'${netappsubnetaddress}' '${routerIPforStorageNetwork}' - -" >> /etc/sysconfig/network/ifroute-'${networkInterface}'';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo -e "# Add the following routes \n# RouterIPforStorageNetwork - - -\n# ANFNetwork/cidr RouterIPforStorageNetwork - -\n'${routerIPforStorageNetwork}' - - -\n'${netappsubnetaddress}' '${routerIPforStorageNetwork}' - -" >> /etc/sysconfig/network/ifroute-'${networkInterface}'';

###### [A] Reboot VMs
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'reboot'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'reboot'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'reboot'

###### [A] if needed
###### sleep 30

###### [A] Prepare the OS for running SAP HANA on NetApp Systems with NFS,
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "# Add the following entries in the configuration file\nnet.core.rmem_max = 16777216\nnet.core.wmem_max = 16777216\nnet.ipv4.tcp_rmem = 4096 131072 16777216\nnet.ipv4.tcp_wmem = 4096 16384 16777216\nnet.core.netdev_max_backlog = 300000\nnet.ipv4.tcp_slow_start_after_idle=0\nnet.ipv4.tcp_no_metrics_save = 1\nnet.ipv4.tcp_moderate_rcvbuf = 1\nnet.ipv4.tcp_window_scaling = 1\nnet.ipv4.tcp_timestamps = 1\nnet.ipv4.tcp_sack = 1\n" >> /etc/sysctl.d/91-NetApp-HANA.conf';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "# Add the following entries in the configuration file\nnet.core.rmem_max = 16777216\nnet.core.wmem_max = 16777216\nnet.ipv4.tcp_rmem = 4096 131072 16777216\nnet.ipv4.tcp_wmem = 4096 16384 16777216\nnet.core.netdev_max_backlog = 300000\nnet.ipv4.tcp_slow_start_after_idle=0\nnet.ipv4.tcp_no_metrics_save = 1\nnet.ipv4.tcp_moderate_rcvbuf = 1\nnet.ipv4.tcp_window_scaling = 1\nnet.ipv4.tcp_timestamps = 1\nnet.ipv4.tcp_sack = 1\n" >> /etc/sysctl.d/91-NetApp-HANA.conf';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo -e "# Add the following entries in the configuration file\nnet.core.rmem_max = 16777216\nnet.core.wmem_max = 16777216\nnet.ipv4.tcp_rmem = 4096 131072 16777216\nnet.ipv4.tcp_wmem = 4096 16384 16777216\nnet.core.netdev_max_backlog = 300000\nnet.ipv4.tcp_slow_start_after_idle=0\nnet.ipv4.tcp_no_metrics_save = 1\nnet.ipv4.tcp_moderate_rcvbuf = 1\nnet.ipv4.tcp_window_scaling = 1\nnet.ipv4.tcp_timestamps = 1\nnet.ipv4.tcp_sack = 1\n" >> /etc/sysctl.d/91-NetApp-HANA.conf';

###### [A] Create configuration file /etc/sysctl.d/ms-az.conf
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "# Add the following entries in the configuration file\nnet.ipv6.conf.all.disable_ipv6 = 1\nnet.ipv4.tcp_max_syn_backlog = 16348\nnet.ipv4.conf.all.rp_filter = 0\nsunrpc.tcp_slot_table_entries = 128\nvm.swappiness=10" >> /etc/sysctl.d/ms-az.conf';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "# Add the following entries in the configuration file\nnet.ipv6.conf.all.disable_ipv6 = 1\nnet.ipv4.tcp_max_syn_backlog = 16348\nnet.ipv4.conf.all.rp_filter = 0\nsunrpc.tcp_slot_table_entries = 128\nvm.swappiness=10" >> /etc/sysctl.d/ms-az.conf';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo -e "# Add the following entries in the configuration file\nnet.ipv6.conf.all.disable_ipv6 = 1\nnet.ipv4.tcp_max_syn_backlog = 16348\nnet.ipv4.conf.all.rp_filter = 0\nsunrpc.tcp_slot_table_entries = 128\nvm.swappiness=10" >> /etc/sysctl.d/ms-az.conf';

###### [A] Adjust the sunrpc settings for NFSv3 volumes
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "# Insert the following line\noptions sunrpc tcp_max_slot_table_entries=128" >> /etc/modprobe.d/sunrpc.conf';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "# Insert the following line\noptions sunrpc tcp_max_slot_table_entries=128" >> /etc/modprobe.d/sunrpc.conf';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo -e "# Insert the following line\noptions sunrpc tcp_max_slot_table_entries=128" >> /etc/modprobe.d/sunrpc.conf';

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "sed -i 's/localdomain/defaultv4iddomain.com/g' /etc/idmapd.conf";
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "sed -i 's/localdomain/defaultv4iddomain.com/g' /etc/idmapd.conf";
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts "sed -i 's/localdomain/defaultv4iddomain.com/g' /etc/idmapd.conf";
 
###### [1] Create node-specific directories for /usr/sap on HN1-shared
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'mkdir -p /mnt/tmp && mount -t nfs -o sec=sys,vers=4.1 '${volume_shareIP}':/'${sapID}'-shared /mnt/tmp && cd /mnt/tmp && mkdir shared usr-sap-'${vmsapname1}' usr-sap-'${vmsapname2}' usr-sap-'${vmsapname3}' && cd .. && umount /mnt/tmp'

###### [2,3] Create node-specific directories for /usr/sap on HN1-shared
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'mkdir /mnt/tmp && mount -t nfs -o sec=sys,vers=4.1 '${volume_shareIP}':/'${sapID}'-shared /mnt/tmp && umount /mnt/tmp'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'mkdir /mnt/tmp && mount -t nfs -o sec=sys,vers=4.1 '${volume_shareIP}':/'${sapID}'-shared /mnt/tmp && umount /mnt/tmp'

###### [A] Verify nfs4_disable_idmapping
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo "Y" > /sys/module/nfs/parameters/nfs4_disable_idmapping && echo "options nfs nfs4_disable_idmapping=Y" >> /etc/modprobe.d/nfs.conf'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo "Y" > /sys/module/nfs/parameters/nfs4_disable_idmapping && echo "options nfs nfs4_disable_idmapping=Y" >> /etc/modprobe.d/nfs.conf'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo "Y" > /sys/module/nfs/parameters/nfs4_disable_idmapping && echo "options nfs nfs4_disable_idmapping=Y" >> /etc/modprobe.d/nfs.conf'

###### [A] Create the SAP HANA group and user manually
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'groupadd -g 1001 sapsys && useradd '${sapid}'adm -u 1001 -g 1001 -d /usr/sap/'${sapID}'/home -c "SAP HANA Database System" -s /bin/sh && useradd sapadm -u 1002 -g 1001 -d /home/sapadm -c "SAP Local Administrator" -s /bin/sh && (echo '${PASSWORD}'; echo '${PASSWORD}') | passwd '${sapid}'adm && (echo '${PASSWORD}'; echo '${PASSWORD}') | passwd sapadm'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'groupadd -g 1001 sapsys && useradd '${sapid}'adm -u 1001 -g 1001 -d /usr/sap/'${sapID}'/home -c "SAP HANA Database System" -s /bin/sh && useradd sapadm -u 1002 -g 1001 -d /home/sapadm -c "SAP Local Administrator" -s /bin/sh && (echo '${PASSWORD}'; echo '${PASSWORD}') | passwd '${sapid}'adm && (echo '${PASSWORD}'; echo '${PASSWORD}') | passwd sapadm'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'groupadd -g 1001 sapsys && useradd '${sapid}'adm -u 1001 -g 1001 -d /usr/sap/'${sapID}'/home -c "SAP HANA Database System" -s /bin/sh && useradd sapadm -u 1002 -g 1001 -d /home/sapadm -c "SAP Local Administrator" -s /bin/sh && (echo '${PASSWORD}'; echo '${PASSWORD}') | passwd '${sapid}'adm && (echo '${PASSWORD}'; echo '${PASSWORD}') | passwd sapadm'

###### [A] Mount the shared Azure NetApp Files volumes
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "# Add the following entries\n'${volume_data_vol1IP}':/'${sapID}'-data-mnt00001 /hana/data/'${sapID}'/mnt00001  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_data_vol2IP}':/'${sapID}'-data-mnt00002 /hana/data/'${sapID}'/mnt00002  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_data_vol3IP}':/'${sapID}'-data-mnt00003 /hana/data/'${sapID}'/mnt00003  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol1IP}':/'${sapID}'-log-mnt00001 /hana/log/'${sapID}'/mnt00001  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol2IP}':/'${sapID}'-log-mnt00002 /hana/log/'${sapID}'/mnt00002  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol3IP}':/'${sapID}'-log-mnt00003 /hana/log/'${sapID}'/mnt00003  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_shareIP}':/'${sapID}'-shared /hana/shared  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0" >> /etc/fstab && mount -a'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "# Add the following entries\n'${volume_data_vol1IP}':/'${sapID}'-data-mnt00001 /hana/data/'${sapID}'/mnt00001  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_data_vol2IP}':/'${sapID}'-data-mnt00002 /hana/data/'${sapID}'/mnt00002  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_data_vol3IP}':/'${sapID}'-data-mnt00003 /hana/data/'${sapID}'/mnt00003  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol1IP}':/'${sapID}'-log-mnt00001 /hana/log/'${sapID}'/mnt00001  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol2IP}':/'${sapID}'-log-mnt00002 /hana/log/'${sapID}'/mnt00002  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol3IP}':/'${sapID}'-log-mnt00003 /hana/log/'${sapID}'/mnt00003  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_shareIP}':/'${sapID}'-shared /hana/shared  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0" >> /etc/fstab && mount -a'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo -e "# Add the following entries\n'${volume_data_vol1IP}':/'${sapID}'-data-mnt00001 /hana/data/'${sapID}'/mnt00001  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_data_vol2IP}':/'${sapID}'-data-mnt00002 /hana/data/'${sapID}'/mnt00002  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_data_vol3IP}':/'${sapID}'-data-mnt00003 /hana/data/'${sapID}'/mnt00003  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol1IP}':/'${sapID}'-log-mnt00001 /hana/log/'${sapID}'/mnt00001  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol2IP}':/'${sapID}'-log-mnt00002 /hana/log/'${sapID}'/mnt00002  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_log_vol3IP}':/'${sapID}'-log-mnt00003 /hana/log/'${sapID}'/mnt00003  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0\n'${volume_shareIP}':/'${sapID}'-shared /hana/shared  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0" >> /etc/fstab && mount -a'

###### [1] Mount the node-specific volumes on hanadb1
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "# Add the following entries\n'${volume_usrsap1IP}':/'${volume_usrsap1_path}' /usr/sap/'${sapID}'  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0" >> /etc/fstab && mount -a'

###### [2] Mount the node-specific volumes on hanadb2
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "# Add the following entries\n'${volume_usrsap2IP}':/'${volume_usrsap2_path}'  /usr/sap/'${sapID}'  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0" >> /etc/fstab && mount -a'

###### [3] Mount the node-specific volumes on hanadb3 - POR CORRER!!
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo -e "# Add the following entries\n'${volume_usrsap3IP}':/'${volume_usrsap3_path}'  /usr/sap/'${sapID}'  nfs   rw,vers=4,minorversion=1,hard,timeo=600,rsize=262144,wsize=262144,intr,noatime,lock,_netdev,sec=sys  0  0" >> /etc/fstab && mount -a'

###### [A] Verify that all HANA volumes are mounted 
#az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'nfsstat -m' -o json

################################################################ VM Confiurations ################################################################

###### [A] Before the HANA installation, set the root password
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts '(echo '${PASSWORD}'; echo '${PASSWORD}') | passwd root'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts '(echo '${PASSWORD}'; echo '${PASSWORD}') | passwd root'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts '(echo '${PASSWORD}'; echo '${PASSWORD}') | passwd root'

# https://stackoverflow.com/questions/43235179/how-to-execute-ssh-keygen-without-prompt
###### Create Keys
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts "ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1"

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config && systemctl restart sshd.service";
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config && systemctl restart sshd.service";
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts "sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config && systemctl restart sshd.service";

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'ssh-keyscan -H '${vmsapname2}' >> /root/.ssh/known_hosts'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'ssh-keyscan -H '${vmsapname3}' >> /root/.ssh/known_hosts'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'ssh-keyscan -H '${vmsapname1}' >> /root/.ssh/known_hosts'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'ssh-keyscan -H '${vmsapname3}' >> /root/.ssh/known_hosts'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'ssh-keyscan -H '${vmsapname1}' >> /root/.ssh/known_hosts'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'ssh-keyscan -H '${vmsapname2}' >> /root/.ssh/known_hosts'

# https://www.ibm.com/docs/en/spectrum-scale-bda?topic=STXKQY_BDA_SHR/bl1adv_passwordlessroot.html
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'chmod 700 /root/.ssh/ && chmod 640 /root/.ssh/authorized_keys'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'chmod 700 /root/.ssh/ && chmod 640 /root/.ssh/authorized_keys'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'chmod 700 /root/.ssh/ && chmod 640 /root/.ssh/authorized_keys'

# https://software.opensuse.org/download.html?project=network&package=sshpass

az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "zypper addrepo -G --refresh -C https://download.opensuse.org/repositories/network/SLE_15/network.repo && zypper install -y sshpass" 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts "zypper addrepo -G --refresh -C https://download.opensuse.org/repositories/network/SLE_15/network.repo && zypper install -y sshpass" 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts "zypper addrepo -G --refresh -C https://download.opensuse.org/repositories/network/SLE_15/network.repo && zypper install -y sshpass" 
 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sshpass -p '${PASSWORD}' ssh-copy-id -f -i /root/.ssh/id_rsa.pub root@'${vmsapname2}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'sshpass -p '${PASSWORD}' ssh-copy-id -f -i /root/.ssh/id_rsa.pub root@'${vmsapname3}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sshpass -p '${PASSWORD}' ssh-copy-id -f -i /root/.ssh/id_rsa.pub root@'${vmsapname1}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'sshpass -p '${PASSWORD}' ssh-copy-id -f -i /root/.ssh/id_rsa.pub root@'${vmsapname3}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'sshpass -p '${PASSWORD}' ssh-copy-id -f -i /root/.ssh/id_rsa.pub root@'${vmsapname1}''
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'sshpass -p '${PASSWORD}' ssh-copy-id -f -i /root/.ssh/id_rsa.pub root@'${vmsapname2}''

###### [A] Install additional packages, which are required for HANA 2.0 SP4
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'zypper install -y libgcc_s1 libstdc++6 libatomic1 insserv-compat libtool';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'zypper install -y libgcc_s1 libstdc++6 libatomic1 insserv-compat libtool';
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'zypper install -y libgcc_s1 libstdc++6 libatomic1 insserv-compat libtool';

###### [2], [3] Change ownership of SAP HANA data and log directories to hn1adm
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'chown '${sapid}'adm:sapsys /hana/data/'${sapID}' && chown '${sapid}'adm:sapsys /hana/log/'${sapID}' && chown '${sapid}'adm:sapsys -R /usr/sap/'${sapID}'/'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'chown '${sapid}'adm:sapsys /hana/data/'${sapID}' && chown '${sapid}'adm:sapsys /hana/log/'${sapID}' && chown '${sapid}'adm:sapsys -R /usr/sap/'${sapID}'/'

################################################################ INSTALLATION ################################################################

###### [1] Decompress SAP File + Give Permissons
###### Get AZCopy Tool
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cd /usr/sap/'${sapID}' && wget -O azcopy_v10.tar.gz https://azcopyvnext.azureedge.net/release20230123/azcopy_linux_amd64_10.17.0.tar.gz && tar -xf azcopy_v10.tar.gz && chown root:root -R azcopy_linux_amd64_10.17.0 && export PATH=$PATH:/usr/sap/'${sapID}'/azcopy_linux_amd64_10.17.0'

###### Decompress
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts "cd /usr/sap/'${sapID}'/azcopy_linux_amd64_10.17.0 && ./azcopy copy '${installerZipUrl}' '/hana/shared/'${sapID}'/download' --recursive=TRUE"
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'unzip -d /hana/shared/'${sapID}'/download/hanainstall /hana/shared/'${sapID}'/download/'${storage_container_name}'/'${sapfileNAME}'' 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS && chmod +x HDB_SERVER_LINUX_X86_64 && cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS/HDB_SERVER_LINUX_X86_64;'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'chmod o+rx /hana/shared'

# https://help.sap.com/docs/SAP_HANA_PLATFORM/2c1988d620e04368aa4103bf26f17727/0c328b5e61bc45c181f6082928d3c269.html?version=2.0.01
# https://help.sap.com/docs/SAP_HANA_ONE/1c837b3899834ddcbae140cc3e7c7bdd/b1c5b5be821f4ebba0cdb5b65055158c.html
###### [A] Add Password XML File
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'echo -e "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Passwords>\n<password><![CDATA['${PASSWORD}']]></password>\n<sapadm_password><![CDATA['${PASSWORD}']]></sapadm_password>\n<system_user_password><![CDATA['${PASSWORD}']]></system_user_password>\n<root_password><![CDATA['${PASSWORD}']]></root_password>\n</Passwords>" >> /root/hdb_passwords.xml' 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'echo -e "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Passwords>\n<password><![CDATA['${PASSWORD}']]></password>\n<sapadm_password><![CDATA['${PASSWORD}']]></sapadm_password>\n<system_user_password><![CDATA['${PASSWORD}']]></system_user_password>\n<root_password><![CDATA['${PASSWORD}']]></root_password>\n</Passwords>" >> /root/hdb_passwords.xml' 
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'echo -e "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Passwords>\n<password><![CDATA['${PASSWORD}']]></password>\n<sapadm_password><![CDATA['${PASSWORD}']]></sapadm_password>\n<system_user_password><![CDATA['${PASSWORD}']]></system_user_password>\n<root_password><![CDATA['${PASSWORD}']]></root_password>\n</Passwords>" >> /root/hdb_passwords.xml' 

###### [1] Silent Install
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/download/hanainstall/DATA_UNITS/HDB_SERVER_LINUX_X86_64 && cat ~/hdb_passwords.xml | ./hdblcm --batch --action=install --components=client,server --sid='${sapID}' --number='${instanceID}' --read_password_from_stdin=xml'

###### [1] Configure Internal Network
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/hdblcm/ && cat ~/hdb_passwords.xml | ./hdblcm --batch --action=configure_internal_network --listen_interface=internal --internal_network='${INTERNAL_ADDRESS}' --read_password_from_stdin=xml'

###### [2], [3] Change ownership of SAP HANA data and log directories to hn1adm
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'chown '${sapid}'adm:sapsys /hana/data/'${sapID}' && chown '${sapid}'adm:sapsys /hana/log/'${sapID}' && chown '${sapid}'adm:sapsys -R /usr/sap/'${sapID}'/'
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'chown '${sapid}'adm:sapsys /hana/data/'${sapID}' && chown '${sapid}'adm:sapsys /hana/log/'${sapID}' && chown '${sapid}'adm:sapsys -R /usr/sap/'${sapID}'/'

###### [2] Add Host - as worker
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname2 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/hdblcm/ && cat ~/hdb_passwords.xml | ./hdblcm --batch --action=add_hosts --addhosts='${vmsapname2}':role='${vmsapname2_role}' --read_password_from_stdin=xml'

###### [3] Add Host - as standby
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname3 --command-id RunShellScript --scripts 'cd /hana/shared/'${sapID}'/hdblcm/ && cat ~/hdb_passwords.xml | ./hdblcm --batch --action=add_hosts --addhosts='${vmsapname3}':role='${vmsapname3_role}' --read_password_from_stdin=xml'

###### [A]
# Confirm HA - Two Nodes
az vm run-command invoke -g $RESOURCE_GROUP -n $vmsapname1 --command-id RunShellScript --scripts 'su - '${sapid}'adm -c "python /usr/sap/'${sapID}'/HDB'${instanceID}'/exe/python_support/landscapeHostConfiguration.py"' | grep "message"
