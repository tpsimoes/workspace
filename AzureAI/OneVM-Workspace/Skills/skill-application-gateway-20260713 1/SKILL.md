---
name: application-gateway
version: 1.0.0
description: >-
  Azure Application Gateway (Layer 7) troubleshooting skill. Combines step-by-step Guided Troubleshooter (GT) decision-tree flows with production B01 Kusto (KQL) queries. Use for backend connectivity, 4xx/5xx/502/504 errors, WAF (Web Application Firewall) rule tuning and exclusions, SSL/TLS, listener/routing, multi-site hosting, IPv6, deployment/failed-state, connection timeouts, App Service integration, health probes, access logs, and config-change analysis.
---

# Azure Application Gateway Troubleshooting Skill

> **Sources:** Azure Networking Guided Troubleshooter (GT) + B01 Dashboard ([aka.ms/b01](https://aka.ms/b01))
> **Coverage:** 24 GT decision-tree guides + 1 B01 Kusto query pack
> **Scope:** Layer 7 Application Gateway (v1/v2) and WAF

## When to Use This Skill

Use this skill when the user describes an Application Gateway or WAF issue, such as:
- **Errors** — 4xx, 5xx, 502 (backend unreachable/unhealthy), 504 (backend timeout)
- **Backend connectivity** — backend pool unhealthy, health probe failures, App Service backend
- **WAF** — false positives / blocked legitimate traffic, exclusions & exceptions, per-site policy, global parameters, OWASP rule tuning, traffic analysis
- **TLS/SSL** — certificate config, end-to-end TLS, SNI
- **Routing** — listeners, routing rules, multi-site hosting, custom error pages, default route next-hop
- **Lifecycle** — deployment failures, Failed state, IPv6 configuration
- **Connectivity** — connection timeouts between client and Application Gateway

## How to Use

1. Match the user's symptom to a **GT guide** below and follow it as a decision tree (collect scoping info first, then route to the resolution path).
2. For quick, copy-run KQL, start with the **[Cheat-Sheet](references/cheatsheet.md)** (parameterized common queries).
3. For the full query set, use [references/kusto/application-gateway.md](references/kusto/application-gateway.md).
4. Always return KQL in fully-qualified form: `cluster("<cluster>").database("<db>").<table>`.

## Key Kusto Data Sources

| Cluster | Database | Used For |
|---------|----------|----------|
| `cluster('Hybridnetworking')` | `GatewayManager` | App Gateway inventory, instances, GatewayId mapping |
| `cluster('hybridnetworking')` | `aznwmds` | AppGw → container/instance, backend health, access/WAF logs |
| `cluster('AzureCM')` | `AzureCM` | Region → ShoeBox MDM account mapping |

> Full query pack (health probes, backend status, WAF, access logs, config changes): [references/kusto/application-gateway.md](references/kusto/application-gateway.md)

## GT Troubleshooting Guides

**Trigger words:** application gateway, appgw, WAF, web application firewall, backend pool, health probe, 4xx, 5xx, 502, 504, backend connectivity, backend unhealthy, listener, routing rule, multi-site, custom error page, SSL, TLS, certificate, IPv6, deployment failure, failed state, connection timeout, App Service backend, exclusion, per-site policy

### Errors (4xx / 5xx / 502 / 504)
- [ANP Application Gateway 5xx errors](references/gt/2fe5cb93_ANP_Application_Gateway_5xx_errors.md)
- [Automated: Troubleshoot Application Gateway 4xx errors](references/gt/2ff0a630_Automated_Troubleshoot_Application_Gateway_4xx_errors.md)
- [Networking: Application Gateway - 4xx Errors](references/gt/3c547893_Networking_Application_Gateway_-_4xx_Errors.md)
- [Networking: Application Gateway - 502 Errors](references/gt/d88f3f43_Networking_Application_Gateway_-_502_Errors.md)
- [Layer 7: Application Gateway 504 Errors](references/gt/cc7f0d61_Azure_NetworkingLayer_7_Application_Gateway_504_Errors_.md)

### Backend Connectivity & App Service
- [Application Gateway - Backend Connectivity](references/gt/9b713eb1_Application_Gateway_-_Backend_Connectivity.md)
- [Automated: Application Gateway - Backend Connectivity](references/gt/afda377f_Automated_Application_Gateway_-_Backend_Connectivity.md)
- [Automated: Application Gateway - Configure App Service (a)](references/gt/aa7e0587_Automated_Application_Gateway_-_Configure_App_Service.md)
- [Automated: Application Gateway - Configure App Service (b)](references/gt/e7c87348_Automated_Application_Gateway_-_Configure_App_Service.md)

### WAF (Web Application Firewall)
- [Application Gateway WAF: Traffic Analysis](references/gt/47a18936_Application_Gateway_WAF_Traffic_Analysis.md)
- [WAF / WAF Per-Site Policy](references/gt/09cf2a5a_Application_Gateway_Web_Application_Firewall_WAFWAF_Per-Site_Policy.md)
- [Configure Web Application Firewall](references/gt/d7506ec4_Configure_Web_Application_Firewall.md)
- [Debugging Web Application Firewall](references/gt/5bfa47ab_Debugging_Web_Application_Firewall.md)
- [Networking: Application Gateway - Issues configuring WAF](references/gt/82e4249f_Networking_Application_Gateway_-_Issues_configuring_WAF.md)
- [Troubleshoot WAF exclusions and exceptions](references/gt/2b055389_Troubleshoot_Application_Gateway_WAF_exclusions_and_exceptions.md)
- [Troubleshoot WAF Global Parameters issues](references/gt/26547dd9_Troubleshoot_WAF_Global_Parameters_issues_for_Application_Gateway.md)

### Routing, Listeners & Config
- [GT Module: Get Default Route Next Hop Type](references/gt/481e497b_GT_Module_Application_Gateway_Get_Default_Route_Next_Hop_Type.md)
- [Troubleshoot multi-site hosting issues](references/gt/96d4bfc0_Troubleshoot_Application_Gateway_multi-site_hosting_issues.md)
- [Custom Error Page Configuration](references/gt/a6ab7bc9_Custom_Error_Page_Configuration_Application_Gateway.md)
- [Troubleshoot IPv6 configuration](references/gt/6072a4d4_Troubleshoot_Application_Gateway_IPv6_configuration.md)

### Lifecycle & Connectivity
- [Application Gateway - Failed State](references/gt/80ff301f__Application_Gateway_-_Failed_State.md)
- [Troubleshoot deployment failures](references/gt/420e09bc_Troubleshoot_Application_Gateway_deployment_failures.md)
- [Connection timeout between client and Application Gateway (a)](references/gt/c5fba1a1_Troubleshoot_connection_timeout_issues_between_client_and_Application_Gateway.md)
- [Connection timeout between client and Application Gateway (b)](references/gt/221e9c24_Troubleshoot_connection_timeout_issues_between_the_client_and_the_Application_Ga.md)

## Kusto
- **[cheatsheet.md](references/cheatsheet.md)** — 常用快查表：copy-run 的参数化查询（清单、配置、变更历史、实例映射、控制面、VIP、NSG）
- [application-gateway.md](references/kusto/application-gateway.md) — full query pack: health probes, backend status, WAF, access logs, config changes (B01)
