#!/usr/bin/python3

import os
from azure.common.credentials import ServicePrincipalCredentials
from azure.common.credentials import UserPassCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

########## Client Creation Functions ###############
#                                                  #
#   Use these functions to establish connections   #
#   to the respective clients of which there are   #
#   four; Resource, Compute, Storage, or Network   #
#   These connections are required to make any     #
#   azure requests.                                #
#                                                  #
####################################################

def CreateResourceClient(username, password, subscription_id):
    #Create azure credential object
    credentials = UserPassCredentials(username,password,)
    #Pass credential object to resource client
    resource_client = ResourceManagementClient(credentials, subscription_id)
    return resource_client

def CreateComputeClient(username, password, subscription_id):
    #Create azure credential object
    credentials = UserPassCredentials(username,password,)
    #Pass credential object to resource client
    compute_client = ComputeManagementClient(credentials, subscription_id)
    return compute_client

def CreateStorageClient(username, password, subscription_id):
    #Create azure credential object
    credentials = UserPassCredentials(username,password,)
    #Pass credential object to resource client
    storage_client = StorageManagementClient(credentials, subscription_id)
    return storage_client

def CreateNetworkClient(username, password, subscription_id):
    #Create azure credential object
    credentials = UserPassCredentials(username,password,)
    #Pass credential object to resource client
    network_client = NetworkManagementClient(credentials, subscription_id)
    return network_client

################# Group Functions ###################
#                                                   #
#   Use these functions to create either Resource   #
#   or Storage groups, note that Storage Groups     #
#   must be assigned to a previously created        #
#   Resource Group.                                 #           
#                                                   #
#####################################################

def NewResourceGroup(username, password, subscription_id, group_name, location):
    resource_client = CreateResourceClient(username, password, subscription_id)
    #Create Resource Group
    resource_client.resource_groups.create_or_update(group_name, {'location':location})

def GetResourceGroup(username, password, subscription_id, group_name):
    resource_client = CreateResourceClient(username, password, subscription_id)
    #Create Resource Group
    resource_group_info = resource_client.resource_groups.get(group_name)
    return resource_group_info

def NewStorageGroup(username, password, subscription_id, group_name, location, storage_account_name):
    storage_client = CreateStorageClient(username, password, subscription_id)
    storage_operation = storage_client.storage_accounts.create(group_name, storage_account_name,
        {
            'sku': {'name': 'standard_lrs'},
            'kind': 'storage',
            'location': location
        }
    )
    storage_operation.wait()

def GetStorageGroup(username, password, subscription_id, group_name, storage_account_name):
    storage_client = CreateStorageClient(username, password, subscription_id)
    storage_group_info = storage_client.storage_accounts.get_properties(group_name, storage_account_name)
    return storage_group_info

################ Network Functions #################
#                                                  #
#   Use these functions to create/lookop Virtual   # 
#   Networks or Subnets both assigned to a         #
#   resource group and provide a network in CIDR   #
#   notation.  Also note that the subnet range     # 
#   must fall within the virtual network range.    #                
#                                                  #
####################################################

def NewVirtualNetwork(username, password, subscription_id, group_name, location, vnet_name, cidr_network):
    network_client = CreateNetworkClient(username, password, subscription_id)
    async_vnet_creation = network_client.virtual_networks.create_or_update(group_name, vnet_name,
        {
            'location': location,
            'address_space': {
                'address_prefixes': [cidr_network]
            }
        }
    )
    async_vnet_creation.wait()

def GetVirtualNetwork(username, password, subscription_id, group_name, vnet_name):
    network_client = CreateNetworkClient(username, password, subscription_id)
    vnet_info = network_client.virtual_networks.get(group_name, vnet_name)
    return vnet_info

def NewSubnet(username, password, subscription_id, group_name, vnet_name, subnet_name, cidr_network):
    network_client = CreateNetworkClient(username, password, subscription_id)
    
    async_subnet_creation = network_client.subnets.create_or_update(group_name, vnet_name, subnet_name,
        {'address_prefix': cidr_network}
    )
    subnet_info = async_subnet_creation.result()

def GetSubnet(username, password, subscription_id, group_name, vnet_name, subnet_name):
    #returns the subnet object requested
    network_client = CreateNetworkClient(username, password, subscription_id)
    subnet_info = network_client.subnets.get(
        group_name,
        vnet_name,
        subnet_name
    )
    return subnet_info

################## Nic Functions ###################
#                                                  #
#   Use these functions to create/lookop Virtual   # 
#   Nics which are then attached to a virtual      #
#   machine in order to establish connectivity.    #               
#                                                  #
####################################################

def NewNic(username, password, subscription_id, group_name, location, vnet_name, subnet_name, nic_name, ip_configuration_name):
    network_client = CreateNetworkClient(username, password, subscription_id)
    subnet_info = GetSubnet(username, password, subscription_id, group_name, vnet_name, subnet_name)
    async_nic_creation = network_client.network_interfaces.create_or_update(group_name, nic_name,
        {
            'location': location,
            'ip_configurations': [{
                'name': ip_configuration_name,
                'subnet': {
                    'id': subnet_info.id
                }
            }]
        }
    )
    result = async_nic_creation.result()

def GetNic(username, password, subscription_id, group_name, nic_name):
    network_client = CreateNetworkClient(username, password, subscription_id)
    nic_info = network_client.network_interfaces.get(group_name, nic_name)
    return nic_info

##################### VM Reference ####################
#                                                     #
#   This section is used to keep an updated section   #
#   of available VMs to deploy in Azure with vars     #               
#                                                     #
#######################################################

VM_REFERENCE = {
    'linux': {
        'publisher': 'Canonical',
        'offer': 'UbuntuServer',
        'sku': '16.04.0-LTS',
        'version': 'latest'
    },
    'windows': {
        'publisher': 'MicrosoftWindowsServerEssentials',
        'offer': 'WindowsServerEssentials',
        'sku': 'WindowsServerEssentials',
        'version': 'latest'
    }
}

def GenerateParameters(location, vm_name, vm_username, vm_password, os_disk_name, storage_account_name, nic_id, vm_reference):
    #Based on VM Reference and Id of Nic returns azure formatted parameter file
    return {
        'location': location,
        'os_profile': {
            'computer_name': vm_name,
            'admin_username': vm_username,
            'admin_password': vm_password
        },
        'hardware_profile': {
            'vm_size': 'Standard_DS1'
        },
        'storage_profile': {
            'image_reference': {
                'publisher': vm_reference['publisher'],
                'offer': vm_reference['offer'],
                'sku': vm_reference['sku'],
                'version': vm_reference['version']
            },
            'os_disk': {
                'name': os_disk_name,
                'caching': 'None',
                'create_option': 'fromImage',
                'vhd': {
                    'uri': 'https://{}.blob.core.windows.net/vhds/{}.vhd'.format(
                        storage_account_name, vm_name)
                }
            },
        },
        'network_profile': {
            'network_interfaces': [{
                'id': nic_id,
            }]
        },
    }
