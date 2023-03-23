############################# Account #############################

export subscriptionId=b7b83ce4-d953-4285-b8f4-d791ed252e4a;

############################# RESOURCE_GROUP #############################

export LOCATION=eastus;
export RESOURCE_GROUP=hana-script;

############################# RESOURCE_GROUP > Network #############################

export sapvnet=vnet-sap;
export sapvnetaddress="10.23.0.0/22"
export clientsubnet=client;
export hanasubnet=hana;
export storagesubnet=storage;
export netappsubnet=anf;
export clientsubnetaddress="10.23.0.0/24"
export hanasubnetaddress="10.23.3.0/24"
export storagesubnetaddress="10.23.2.0/24"
export netappsubnetaddress="10.23.1.0/26"
export avsetname="sap-avb-set"

netappIP=${netappsubnetaddress:0:8}4

export myIP=$(curl http://ifconfig.co)
export myIPnsgRULEname=AllowMyIP
export vnetNSGname=$sapvnet-$hanasubnet-nsg-$LOCATION

######################### VMs Configs Image + Names + NICs
# Create Extra NICs
export vmsapname1=hanadb1
export vmsapname2=hanadb2
export vmsapname3=hanadb3

export vmsap1nic_client=$vmsapname1-client
export vmsap1nic_hana=$vmsapname1-hana
export vmsap1nic_storage=$vmsapname1-storage

export vmsap2nic_client=$vmsapname2-client
export vmsap2nic_hana=$vmsapname2-hana
export vmsap2nic_storage=$vmsapname2-storage

export vmsap3nic_client=$vmsapname3-client
export vmsap3nic_hana=$vmsapname3-hana
export vmsap3nic_storage=$vmsapname3-storage

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

###### Size + Image
export hanadb_size=Standard_E8ds_v5
export suseimage="SUSE:sles-sap-15-sp4:gen2:2023.02.05";

############################# RESOURCE_GROUP > ANF Account + Volumes #############################

###### Capacity Pool & Volumes
export VNET_ID=$(az network vnet show --resource-group $RESOURCE_GROUP --name $sapvnet --query "id" -o tsv)
export SUBNET_ID=$(az network vnet subnet show --resource-group $RESOURCE_GROUP --vnet-name $sapvnet --name $netappsubnet --query "id" -o tsv)
export VOLUME_SIZE_GiB=200 # 200 GiB

export ANF_ACCOUNT_NAME=mynetappsap
export ANF_IP=10.23.1.4

export POOL_NAME="sappool"
export POOL_SIZE_TiB=4 # Size in Azure CLI needs to be in TiB unit (minimum 4 TiB)
export SERVICE_LEVEL="Ultra" # Valid values are Standard, Premium and Ultra

export volume_data_vol1=$sapID-data-mnt00001
export volume_data_vol1_path=$sapID-data-mnt00001
export volume_data_vol2=$sapID-data-mnt00002
export volume_data_vol2_path=$sapID-data-mnt00002
export volume_log_vol1=$sapID-log-mnt00001
export volume_log_vol1_path=$sapID-log-mnt00001
export volume_log_vol2=$sapID-log-mnt00002
export volume_log_vol2_path=$sapID-log-mnt00002
export volume_shared=$sapID-shared
export volume_shared_path=$sapID-shared
export volume_data_vol1=$sapID-data-mnt00001
export volume_data_vol2=$sapID-data-mnt00002
export volume_log_vol1=$sapID-log-mnt00001
export volume_log_vol2=$sapID-log-mnt00002
export volume_shared_vm1=$sapID-shared
export volume_usrsap1=$sapID-usrsap-${vmsapname1}
export volume_usrsap1_path=$sapID-usrsap-${vmsapname1}
export volume_usrsap2=$sapID-usrsap-${vmsapname2}
export volume_usrsap2_path=$sapID-usrsap-${vmsapname2}
export volume_usrsap3=$sapID-usrsap-${vmsapname3}
export volume_usrsap3_path=$sapID-usrsap-${vmsapname3}
export ALLOWED_CLIENTS=0.0.0.0/0

############################# RESOURCE_GROUP > Storage Account

export storage_sku=Standard_RAGRS
export storage_name=sap2023stg
export storage_container_name=sapsoftwarerepro

############################# SAP Variables #############################

export sapID=HN1
export sapid=hn1
export instanceID=00

# Role Profile for Nodes
export vmsapname2_role=worker

# Internal Address
export INTERNAL_ADDRESS=${hanasubnetaddress:0:7}/24