import json, sys
sys.path.insert(0, r'c:\GitHubCopilot\IronMan\Skills\asw_caas_lead\scripts')
from generate_dashboard_v1 import FOCUS, compute_panel_a, rollup, DATA_JSON

cases = json.loads(DATA_JSON.read_text(encoding='utf-8'))
print(f'{"Customer":<32} {"TPID/Queue":<45} {"Vol":>6} {"Closed":>7} {"DTC":>6} {"%<7":>6}')
print('-' * 108)
for f in FOCUS:
    pa = compute_panel_a(cases, f['tpid'], f.get('queue'))
    key = f"{f['tpid']}"
    if f.get('queue'):
        key = f"{f['tpid']} | q={f['queue'][:22]}"
    label = f"[{f['section']}] {f['customer']}"
    print(f"{label:<32} {key:<45} {pa['vol']:>6} {pa['closed']:>7} {str(pa['avg_dtc']):>6} {str(pa['pct_close_7']):>6}")
print('-' * 108)
pas = [compute_panel_a(cases, f['tpid'], f.get('queue')) for f in FOCUS]
r = rollup(pas)
print(f'{"PROGRAM TOTAL":<32} {"":<45} {r["vol"]:>6} {r["closed"]:>7} {str(r["avg_dtc"]):>6} {str(r["pct_close_7"]):>6}')
