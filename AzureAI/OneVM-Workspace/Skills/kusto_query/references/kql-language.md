# KQL Language Reference — Azure Infrastructure Investigation

Source: Microsoft Learn official docs + AzureIaaSVM wiki best practices

---

## Core Concepts

- KQL is **read-only**, **case-sensitive** (table names, column names, operators, functions)
- Data flows through **pipe `|`** operators sequentially — order matters for performance
- Three statement types: `let` (bind variable), tabular expression (pipeline), `set` (query options)
- Cross-cluster syntax: `cluster("uri").database("db").TableName`

---

## Operator Quick Reference

### Filtering

| Operator | Purpose | Example |
|----------|---------|---------|
| `where` | Filter rows by predicate | `\| where NodeId == "{NodeId}"` |
| `where` + datetime | Time-window filter | `\| where PreciseTimeStamp between(datetime({Start})..datetime({End}))` |
| `where` + `ago()` | Relative time | `\| where PreciseTimeStamp > ago(2h)` |
| `has` | Token match (fast, indexed) | `\| where Message has "IERR"` |
| `contains` | Substring match (slower) | `\| where Message contains "Fault"` |
| `=~` | Case-insensitive equals | `\| where ServiceName =~ "datapath"` |
| `in` | Membership test | `\| where NodeId in (nodeids)` |
| `!in` | Exclusion test | `\| where EventId !in (504, 505)` |

> **Best practice**: Use `has` over `contains`; use `==` over `=~` when data is consistent case. Place `where` on datetime columns first — Kusto indexes them.

### Column Manipulation

| Operator | Purpose | Example |
|----------|---------|---------|
| `project` | Select/order columns | `\| project PreciseTimeStamp, NodeId, Message` |
| `project-away` | Drop columns | `\| project-away _SomeInternalCol` |
| `project-rename` | Rename column | `\| project-rename NodeId = BladeID` |
| `project-reorder` | Reorder columns | `\| project-reorder PreciseTimeStamp, NodeId` |
| `extend` | Add computed column | `\| extend Duration = EndTime - StartTime` |

### Aggregation

```kusto
// summarize: group + aggregate
T | summarize count() by ServiceVersion
T | summarize arg_max(PreciseTimeStamp, *) by NodeId   // latest record per NodeId
T | summarize min(PreciseTimeStamp), max(PreciseTimeStamp) by NodeId, ContainerId
T | summarize make_set(NodeId) by Tenant               // collect into dynamic array
```

Key aggregation functions: `count()`, `sum()`, `avg()`, `min()`, `max()`, `arg_max()`, `arg_min()`, `make_set()`, `make_list()`, `dcount()`

### Sorting & Limiting

```kusto
T | sort by PreciseTimeStamp desc
T | top 10 by PreciseTimeStamp desc
T | take 100        // same as limit, for quick exploration
T | distinct NodeId, ContainerId
```

### Joining Tables

```kusto
// Standard join — put smaller table on LEFT
LeftTable
| join kind=inner (RightTable | where ...) on $left.NodeId == $right.NodeId

// join kinds: inner, innerunique (default), leftouter, rightouter, 
//             fullouter, leftanti, rightanti, leftsemi

// Cross-cluster join — run on the cluster where MOST data lives
let nodeids = cluster('azcore.centralus.kusto.windows.net').database('AzureCP').SomeTable
    | distinct NodeId;
cluster('azurecm.kusto.windows.net').database('AzureCM').SomeTable
| where NodeId in (nodeids)
```

> **Best practice**: Small table on left. Use `in` instead of `left semi join` for single-column filtering. Use `hint.strategy=broadcast` when left side is small (<100MB).

### Multi-Value & Dynamic

```kusto
T | mv-expand Events                        // expand dynamic array to rows
T | parse Message with "NodeId=" NodeId:string " State=" State:string  // parse fixed format
T | extend props = parse_json(Properties)
    | where props.Category == "Fault"
```

### Variables & Reuse

```kusto
// let: bind scalar or tabular expression
let startTime = datetime(2025-01-01);
let endTime = startTime + 2d;
let nodeids =
    cluster('azurecm.kusto.windows.net').database('AzureCM').LogContainerSnapshot
    | where subscriptionId == "{SubscriptionId}"
    | distinct NodeId;

// Use materialize() when referencing same tabular expression multiple times
let expensive = materialize(T | where ... | summarize ...);
expensive | join (expensive) on NodeId
```

### Time Functions

```kusto
ago(1h)                      // 1 hour before query time
datetime(2025-03-01 10:00)   // literal datetime
now()                        // current UTC time
bin(PreciseTimeStamp, 5m)    // floor to 5-minute buckets
format_datetime(ts, "yyyy-MM-dd HH:mm")
startofday(PreciseTimeStamp)
```

### String Functions

```kusto
split(MyResourceID, "/")[2]   // extract substring by delimiter
toupper(s) / tolower(s)
strlen(s)
indexof(s, "Seconds")
substring(s, start, length)
trim_end("}", s)
strcat("prefix", col)
```

---

## Azure Infrastructure Investigation Patterns

### Pattern 1: VM Identification (always start here)

```kusto
cluster("Azcsupfollower").database("AzureCM").LogContainerSnapshot
| where subscriptionId == "{SubscriptionId}" and roleInstanceName has "{VMName}"
| summarize min(PreciseTimeStamp), max(PreciseTimeStamp) 
    by containerId, nodeId, tenantName, virtualMachineUniqueId
| order by min_PreciseTimeStamp asc
```

### Pattern 2: Time-Window Node Investigation

```kusto
let StartTime = datetime({BeginTime});
let EndTime   = datetime({EndTime});
let NodeId    = "{NodeId}";
cluster("AzureCM").database("AzureCM").TMMgmtNodeStateChangedEtwTable
| where PreciseTimeStamp between(StartTime..EndTime)
| where BladeID == NodeId
| project PreciseTimeStamp, BladeID, OldState, NewState
```

### Pattern 3: Cross-Cluster Lookup (filter by subscription's nodes)

```kusto
let nodeids =
    cluster('azcore.centralus.kusto.windows.net').database('AzureCP').SomeTable
    | where PreciseTimeStamp > ago(1d)
    | where SubscriptionId == "{SubscriptionId}"
    | distinct NodeId;
cluster("azurecm.kusto.windows.net").database("AzureCM").OtherTable
| where NodeId in (nodeids)
| where PreciseTimeStamp > ago(2h)
| summarize count() by ServiceVersion
```

### Pattern 4: Latest State (arg_max)

```kusto
T | summarize arg_max(PreciseTimeStamp, *) by NodeId
```

### Pattern 5: Resource ID Decomposition

```kusto
let MyResourceID = "{Resource_id}";
let SubID        = tostring(split(MyResourceID, "/")[2]);
let ResourceGrp  = tostring(split(MyResourceID, "/")[4]);
let VMName       = tostring(split(MyResourceID, "/")[-1]);
```

### Pattern 6: Check Table Latency

```kusto
cluster('Azcsupfollower').database('AzureCM').LogContainerHealthSnapshot
| summarize max(PreciseTimeStamp)
| extend latency = now() - max_PreciseTimeStamp
| project latency
```

### Pattern 7: Check Table Retention

```
// Run in Kusto Explorer (management command)
.show database AzureCM policy retention
```

---

## Best Practices (from Microsoft Learn)

| Rule | Do | Don't |
|------|----|-------|
| String search | `has` (token-level, indexed) | `contains` (unindexed) |
| Case comparison | `==` (exact) | `=~` (case-insensitive) unless needed |
| Filter order | datetime first, then string, then numeric | Computed columns first |
| Join table size | Smallest table on left | Large fact table on left |
| Named expressions reuse | `materialize()` | Reference same tabular `let` multiple times |
| Cross-cluster join | Run on cluster with most data | Don't run on the small cluster side |
| New query exploration | Add `\| take 100` while developing | Run unbounded queries on unknown data |
| Local table reference | Use unqualified name | `cluster("local").database("db").T` if same context |

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Summarize group key is of 'dynamic' type` | Grouping by dynamic column | Add `tostring()` or `toint()` cast |
| `Unknown column 'X'` | Column dropped by earlier `summarize` | Add missing column to `by` clause |
| `Cross-cluster queries not supported` | Wrong cluster for join | Move heavy query to the remote cluster side |
| Query times out | No time filter on large table | Always filter by `PreciseTimeStamp` first |
