# VM Analyzer

Builds and opens the Azure Managed Grafana **Virtual Machine Analyzer** dashboard
for an Azure VM over a chosen time range, then lets you analyze the panels.

## Usage

```
python vm_analyzer.py --id <VM ARM ID or VM ID> --from <start> --to <end> [--timezone utc] [--no-open]
```

- `--id`   Azure VM ARM ID (`/subscriptions/.../virtualMachines/<name>`) or a VM identifier.
- `--from` / `--to` accept:
  - ISO-8601: `2026-06-01T00:00:00Z`, `2026-06-01`
  - Epoch milliseconds: `1782913111882`
  - Epoch seconds: `1782913111`
  - Grafana relative: `now`, `now-24h`, `now-7d`
- `--no-open` prints the URL without launching the browser.

### Examples

```
python vm_analyzer.py --id "/subscriptions/xxxx/resourcegroups/rg/providers/microsoft.compute/virtualmachines/myvm" \
    --from "2026-06-01T00:00:00Z" --to "2026-06-02T00:00:00Z"

python vm_analyzer.py --id myvm --from now-24h --to now
```

## Authentication

The tool only builds and opens the URL. Your browser handles sign-in to
Azure Managed Grafana with your Azure AD account (e.g. `tiagosimoes@microsoft.com`).

## Analysis workflow

1. Run the tool — it opens the **Virtual Machine Analyzer** dashboard with all panels.
2. Review the panels (CPU, memory, disk, network, availability, etc.).
3. To get an automated analysis, export the panel data (CSV/JSON from a panel's
   *Inspect > Data*, or share screenshots) and provide it back for review.
