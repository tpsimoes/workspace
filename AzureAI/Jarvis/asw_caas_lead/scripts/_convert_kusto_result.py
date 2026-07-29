"""Convert Kusto MCP result (columnar) -> flat list of dicts for dashboard generator."""
import json
from pathlib import Path
from datetime import datetime

SRC = Path(r'c:\Users\tiagosimoes\AppData\Roaming\Code\User\workspaceStorage\6b8b2e6838ef67bd2677eb6d2e3b2640\GitHub.copilot-chat\chat-session-resources\ee17a14e-1b06-4a05-8875-73e947509f3e\toolu_bdrk_01RcQs5MQVVgp8CWRoYE2L1H__vscode-1785233636465\content.json')
OUT = Path(__file__).parent.parent / "Output" / "asw_fy27_all_cases.json"

data = json.loads(SRC.read_text(encoding='utf-8'))
items = data['results']['items']
col_names = list(items[0].keys())   # first item is {col: type} map
records = []
for row in items[1:]:
    if not isinstance(row, list):
        continue
    rec = dict(zip(col_names, row))
    # Customer_TPID must be string
    rec['Customer_TPID'] = str(rec.get('Customer_TPID') or '')
    # IsCritSit / IsResolved: normalize to string "True"/"False"
    for field in ('IsCritSit', 'IsResolved'):
        v = rec.get(field)
        rec[field] = str(v) if isinstance(v, bool) else ('False' if v is None else str(v))
    records.append(rec)

OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"Saved {len(records)} records -> {OUT}")

# Sanity check
closed = [r for r in records if r.get('ClosedDateTime')]
dtcs = []
for r in closed:
    try:
        c = datetime.fromisoformat(r['ClosedDateTime'].replace('Z', ''))
        cr = datetime.fromisoformat(r['CreatedDateTime'].replace('Z', ''))
        dtcs.append((c - cr).total_seconds() / 86400)
    except Exception:
        pass
if dtcs:
    avg = sum(dtcs) / len(dtcs)
    pct7 = 100 * sum(1 for d in dtcs if d < 7) / len(dtcs)
    print(f"Closed: {len(closed)}, AvgDTC: {avg:.2f}d, %<7d: {pct7:.1f}%")
else:
    print("No closed cases with valid datetimes.")

tpids = set(r['Customer_TPID'] for r in records)
critsit = sum(1 for r in records if str(r.get('IsCritSit', '')).lower() == 'true')
print(f"Distinct TPIDs: {len(tpids)}, CritSit: {critsit}")
