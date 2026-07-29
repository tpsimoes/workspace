---
Tags:
- asw.Sfmc
- asw.SAP
- asw.PepsiCo
- asw.Know-Me
- asw.Reviewed-01-2024
---

[[_TOC_]]

# Customer Introduction
PepsiCo is an S500 strategic customer with Microsoft. They entered into a strategic partnership with Microsoft in December of 2019.

# Contacts and Plan of Record
To confirm what are the PepsiCo main contacts please check our [Wiki Page](https://supportability.visualstudio.com/AzureStrategicWorkloads/_wiki/wikis/AzureStrategicWorkloads/1290496/Contacts), can also check the [PepsiCo PoR](https://microsoft.sharepoint.com/:p:/t/AzureStrategicWorkloads-SAP/EQna3ifs-eJEmzd6oxxcdhkBnaUAzZiAv7-0H6jd9cC86w?e=oBCuKk)

# Know-Me One Page
PepsiCo is part of the ACE Program - please check the following links:
[PepsiCo Know-Me One Pager](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/195471/PepsiCo-Know-Me-One-Pager) 

# Architectures 
## Documentation
- [PGT - A1P Production environment - (SCUS)](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/622131/PGT-A1P-Production-environment-(SCUS))
- [PGT- GCP | e-HANA system Architecture](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/622132/PGT-e-HANA-system-Architecture)
- [A1P HANA Storage layout Architecture](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/622177/A1P-HANA-Storage-layout-Architecture)
- [GCP HANA Storage layout Architecture](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/622179/GCP-HANA-Storage-layout-Architecture)
- [PGT Networking Architecture (Includes all SAP System](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/622175/PGT-Networking-Architecture-(Includes-all-SAP-Systems-A1P-GCP))
- [PGT SAP Instances, Environments, Landscapes](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/186137/PGT-SAP-Instances-Environments-Landscapes-and-Azure-Regions)

## CSA Brownbag Sessions
[Videos](https://supportability.visualstudio.com/AzureStrategicWorkloads/_wiki/wikis/AzureStrategicWorkloads/1288111/CSA-Architectures-Sessions)

# Customer Hot issues
(from ACE Know-Me Page)
- [**App Servers to DB Timeouts**](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/622134/Troubleshooting-tools-Logs) (Once Azure Platform is ruled out - Inform PepsiCo to open up a OSS ticket to engage SAP Partners)

- [**SAP Latency issues**](https://msazure.visualstudio.com/AdvCloudEngSupport/_wiki/wikis/Azure%20ACE%20Wiki/622134/Troubleshooting-tools-Logs) (Once Azure Platform is ruled out - Inform PepsiCo to open up a OSS ticket to engage SAP Partners)

- **VM Hung issues**: KDump 
  - [RHEL](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/system_design_guide/installing-and-configuring-kdump_system-design-guide#installing-kdump-command-lineinstalling-kdump)
  - [SLES](https://www.suse.com/support/kb/doc/?id=000016171)

- **Capacity Constraints**: Engage both:
  - Joanne Marime, joannemarime@microsoft.com 
  - DL: Capacity Customer Experience Operations PD ccxopspd@microsoft.com for immediate attention. <br>
   Please note this is specific only to **PGT** architecture.

#  Azure Subscription Detail

|Workload  |Subscription  | Customer Friendly Name | Is Critical? (Yes/No) | Subscription Type (Prod/Staging/Dev/Testing etc) |
|--|--|--|--|--|
| SAP |b55e2972-a467-4092-a828-fdb4b15d40f1 | PEP-SAP-01-SUB | Yes |Contains Non-Prod and Prod workloads  |
| SAP |af151909-5f7c-4e1d-8b8f-a970d0960f88 | PEP-SAP-NONPROD-01-SUB | Yes | Contains Non-Prod and Prod workloads |

### Contributors
@<4606601B-1758-6FA1-9127-C3C45B5A4119>
