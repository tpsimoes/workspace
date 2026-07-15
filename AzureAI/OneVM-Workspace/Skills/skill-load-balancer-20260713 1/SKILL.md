---
name: load-balancer
version: 1.0.0
description: >-
  Azure Load Balancer (Layer 4) troubleshooting skill. Combines step-by-step Guided Troubleshooter (GT) decision-tree flows with production B01 Kusto (KQL) queries. Use for backend pool connectivity, health probe failures, SNAT / outbound connectivity, inbound NAT rules, load distribution, Basic-to-Standard SKU upgrade, Gateway Load Balancer, global (cross-region) load balancer, ILB probes, CRUD issues, and SLB/MUX backend data-path RCA.
---

# Azure Load Balancer Troubleshooting Skill

> **Sources:** Azure Networking Guided Troubleshooter (GT) + B01 Dashboard ([aka.ms/b01](https://aka.ms/b01))
> **Coverage:** 15 GT decision-tree guides + 3 B01 Kusto query packs (LB/NAT Gateway, SLB-VIP, SLB deep RCA)
> **Scope:** Layer 4 Load Balancer (Basic/Standard), NAT Gateway, Gateway LB, Global LB, and the SLB/MUX backend

## When to Use This Skill

Use this skill when the user describes a Load Balancer issue, such as:
- **Backend connectivity** — can't connect to backend pool, connection issues between LB and backends
- **Health probes** — ILB probe failures, probe misconfiguration, backend marked down
- **SNAT / outbound** — SNAT port exhaustion, outbound connectivity failures
- **Inbound NAT** — inbound NAT rules, port forwarding
- **Load distribution** — uneven traffic distribution, session persistence, distribution mode
- **SKU / migration** — Basic → Standard SKU upgrade issues
- **Specialized LB** — Gateway Load Balancer, Global (cross-region) load balancer inbound connectivity
- **Lifecycle** — CRUD (create/delete/update) failures, add/remove load-balanced resources
- **Backend infra (deep RCA)** — SLB ring / MUX health, VIP diagnostics, crash/exception analysis

## How to Use

1. Match the user's symptom to a **GT guide** below and follow it as a decision tree (collect scoping info first, then route to the resolution path).
2. For quick, copy-run KQL, start with the **[Cheat-Sheet](references/cheatsheet.md)** (parameterized common queries).
3. For the full query set, use the packs under [references/kusto/](references/kusto/).
4. Always return KQL in fully-qualified form: `cluster("<cluster>").database("<db>").<table>`.

## Key Kusto Data Sources

| Cluster | Database | Used For |
|---------|----------|----------|
| `cluster('Azslb')` | `azslbmds` | LB health probes, DIP endpoint probe history, SNAT, data path |
| `cluster('argwus2nrpone.westus2')` | `AzureResourceGraph` | LB inventory (SKU, tier, ELB/ILB) |
| `cluster('Azslb')` | `azslbmds` | SLB ring health, VIP diagnostics, MUX RCA |

> Query packs:
> - [load-balancer.md](references/kusto/load-balancer.md) — LB & NAT Gateway: health probes, SNAT, data path, NAT rules
> - [slb-vip.md](references/kusto/slb-vip.md) — SLB ring health, Azure VIP diagnostics
> - [slb-deep-rca.md](references/kusto/slb-deep-rca.md) — SLB/MUX deep RCA: crash analysis, SF health, exceptions

## GT Troubleshooting Guides

**Trigger words:** load balancer, LB, ILB, backend pool, health probe, SNAT, outbound connectivity, inbound NAT rule, load distribution, session persistence, uneven traffic, Basic to Standard, SKU upgrade, Gateway Load Balancer, global load balancer, cross-region, CRUD, can't connect, probe failure, SlbV2

### Backend Connectivity & Probes
- [Networking: Load Balancer - Can't connect to Backend Pool](references/gt/454c4292_Networking_Load_Balancer_-_Cant_connect_to_Backend_Pool.md)
- [Troubleshoot connection issues between load balancer and backend pool](references/gt/e3c6812c_Troubleshoot_connection_issues_between_load_balancer_and_backend_pool.md)
- [ILB having issues with probes](references/gt/9cf81f45_ILB_having_issues_with_probes.md)

### Load Distribution & NAT
- [Networking: Load Balancer - Configure load distribution](references/gt/4b9d578a_Networking_Load_Balancer_-_Configure_load_distribution.md)
- [Troubleshoot uneven traffic distribution](references/gt/ca1c2d47_Troubleshoot_Azure_Load_Balancer_uneven_traffic_distribution.md)
- [Inbound NAT rules for Azure load balancers](references/gt/fce11f54_Inbound_NAT_rules_For_Azure_load_balancers.md)

### Gateway LB & Global LB
- [Inbound connectivity through Gateway Load Balancer (a)](references/gt/1921d987_Inbound_connectivity_issue_through_Gateway_Load_balancer.md)
- [Inbound connectivity through Gateway Load Balancer (b)](references/gt/ce0b18c3_Inbound_connectivity_issue_through_Gateway_Load_balancer.md)
- [Inbound connectivity through global load balancer (a)](references/gt/72b02d86_Inbound_connectivity_issue_through_global_load_balancer.md)
- [Inbound connectivity through global load balancer (b)](references/gt/ccaeb9da_Inbound_connectivity_issue_through_global_load_balancer.md)

### SKU Upgrade & Lifecycle (CRUD)
- [Resolve issues upgrading Basic to Standard SKU Load Balancer](references/gt/235ad95c_Resolve_issues_with_upgrading_from_Basic_to_Standard_SKU_Load_Balancer.md)
- [Upgrading from Basic to Standard SKU load balancer](references/gt/bda22259_Upgrading_from_Basic_to_Standard_SKU_load_balancer.md)
- [CRUD Issues with Load Balancer](references/gt/ee87a493_CRUD_Issues_with_Load_Balancer.md)
- [How to add or remove load balanced resources](references/gt/ebeb8e3e_How_to_add_or_remove_load_balanced_resources.md)

### SLB Module
- [Module: Azure Networking SlbV2](references/gt/1b59d1e2_Module_Azure_Networking_SlbV2.md)

## Kusto
- **[cheatsheet.md](references/cheatsheet.md)** — 常用快查表：copy-run 的参数化查询（清单、规则/探针、健康事件、VIP、SLB HP、NAT GW/SNAT）
- [load-balancer.md](references/kusto/load-balancer.md) — LB & NAT Gateway: health probes, SNAT, data path, NAT rules (B01)
- [slb-vip.md](references/kusto/slb-vip.md) — SLB ring health, Azure VIP diagnostics (B01)
- [slb-deep-rca.md](references/kusto/slb-deep-rca.md) — SLB/MUX deep RCA: crash analysis, SF health, exceptions (B01)
