---
Tags:
- asw.Sfmc
- asw.SAP
- asw.Lego
- asw.Know-Me
- asw.Reviewed-11-2024
---

[[_TOC_]]


# Customer Introduction
<Lego_Group> is an S500 strategic customer with Microsoft.
The LEGO Group is a global consumer products company best known for designing, manufacturing, and selling LEGO®‑branded construction toys and related experiences. Founded in 1932 and headquartered in Billund, Denmark, LEGO operates worldwide, serving consumers across retail, digital, and entertainment channels. The company places a strong emphasis on innovation, global reach, and data‑driven decision‑making to support its product development, supply chain, and customer engagement activities.


# Contacts and Plan of Record
<Lego_Group>>'s main contacts are [here](https://microsoft.sharepoint.com/:b:/t/AzureStrategicWorkloads-SAP/IQDBygExB-kaRr9HhMMbeyLAAd7tWUMff0cFjBhITgLGwoc?e=lnAIep)
<Lego_Group>>'s Plan of Record is [here](https://microsoft.sharepoint.com/:f:/t/AzureStrategicWorkloads-SAP/IgAUnwOeBDpKSLCsGzdnGhweAW7ZZfhZwPNG_k4kYdGV1w8?e=vwlAm2)



# Know-Me One Pager from ACE Program <Lego_Group>> is part of the ACE Program, their One Pager is [here](https://sfmc.crm4.dynamics.com/main.aspx?navbar=off&recordSetQueryKey=cr508_know_me_documents-e011a098-9caa-419c-a0ad-64ade817e606%253A%2520%253A%2520%253A%2520%253A%2520%253A%2520%253A%2520false%253A%2520%253A%2520%253A%252050&pagetype=entityrecord&etn=cr508_know_me_documents&id=9743add3-c9f4-f011-8406-000d3ab57180&formid=e6c3190a-6554-ed11-bba2-0022489c4051&originalAppId=50fe4413-1e55-ed11-bba2-0022489ca164&forceUCI=1).


# Architecture


All of Lego's Infrastructure is based on North Europe datacenter, they have a DR solution going to On-premises.
They have no Production workloads yet.
Currently they have a single Tenant with several subscriptions but currently Lego just wants the focus on Prod and Pre-Prod subscriptions.

**Next Milestone**


QA System 1 (single‑VM)	March	Provision first QA; single instance (not HA). Seek guidance on architecture, storage choice, and best practices.	Perform architecture review; advise on storage (Azure NetApp Files vs. Premium SSD, or mix‑and‑match per workload); capture recommendations into a prioritized backlog.
QA System 2 (single‑VM)	June	Provision second QA; also single instance, used for iterative data‑migration testing.	Continue recommendation reviews and track progress; prepare for HA design in the next QA.
QA System 3 (HA, multi‑zone)	August	Provision third QA that stays; make it highly available, multi‑zone; use it for infra patching/DR rehearsal before production.	Design & validate Pacemaker‑based HA; run resiliency/chaos testing and performance testing on QA; ensure monitoring/observability (e.g., Azure Monitor for SAP) is in place.
Pre‑Production (HA)	Post‑QA (late Q3/Q4)	Build pre‑prod similarly to QA with HA parity for change validation and pre‑go‑live testing.	Keep QA↔Pre‑prod parity to enable apples‑to‑apples configuration checks; finalize proactive recommendations ahead of production.
Production build & migration	After Aug 26 / around summer	Begin production build after summer; ensure capacity and performance readiness; manage 4,000+ interfaces across on‑prem/AWS/hyperscaler mix.	Capacity planning (region: North Europe/Dublin, BOM sizing, storage profile); coordinate with engineering experts (e.g., Jitendra) and plan interface resiliency across hybrid topology.



## Documentation
TBD

# Customer Hot issues


**DR to on-premises** - how to get the necessary data to on-premises in terms of DR (deciding tooling for backups)

**Networking** - Because Lego did a lift-shift from on-premises to cloud, they require a thorough review on the networking security to make sure the right rules are in place and remove any legacy and unnecessary allowed traffic. 
All traffic is routed to on-premises, except traffic for application gateway

**Monitoring** - customer is looking for a solution that can bring together all resources to a single dashboard for monitoring and log aggregation - on-premises, AWS and Azure.

**Most Critical Point of the Solution/ Dependency Mapping:**
	- 2 Virtual machines with Standard_M416ds_8_v3 SKU, in North Europe



#  Azure Subscription Detail
<Lego_Group>>'s Azure subscriptions are documented [here](https://microsoft.sharepoint.com/:f:/t/AzureStrategicWorkloads-SAP/EqTlgnmBEM1Gv44zTV7SdDoBWAXq8bdhEZ5IUlF73bSTRQ?e=lqnbfN)


### Contributors
[pedmarqu](https://teams.microsoft.com/l/chat/0/0?users=pedmarqu@microsoft.com)
