"""Sanity-check the FY26 ASW case snapshot."""
import json, statistics as st, sys
from datetime import datetime
sys.path.insert(0, r'c:\GitHubCopilot\IronMan\Output')
from _asw_list import ASW_ALIASES

cases = json.load(open(r'c:\GitHubCopilot\IronMan\Output\asw_fy26_all_cases.json', encoding='utf-8'))
print(f'Rows: {len(cases)}')
print(f'Distinct customers: {len({c["Customer_TPID"] for c in cases})}')
print(f'Distinct engineers: {len({c["AgentAlias"] for c in cases})}')

closed = [c for c in cases if c.get('ClosedDateTime')]
print(f'Closed rows: {len(closed)}  ({100*len(closed)/len(cases):.1f}%)')

dtcs = []
for c in closed:
    try:
        cd = datetime.fromisoformat(c['CreatedDateTime'].replace('Z',''))
        cl = datetime.fromisoformat(c['ClosedDateTime'].replace('Z',''))
        d = (cl - cd).total_seconds() / 86400
        if d >= 0:
            dtcs.append(d)
    except Exception:
        pass
print(f'Valid DTCs: {len(dtcs)}  AvgDTC: {st.mean(dtcs):.2f}d  MedianDTC: {st.median(dtcs):.2f}d  %<7d: {100*sum(1 for d in dtcs if d < 7)/len(dtcs):.1f}%')

crit = sum(1 for c in cases if str(c.get("IsCritSit") or "").lower() == "true")
print(f'CritSit: {crit}  ({100*crit/len(cases):.2f}%)')

roster = set(ASW_ALIASES)
seen = {c['AgentAlias'] for c in cases}
print(f'Roster: {len(roster)}  Seen in data: {len(seen)}')
print(f'Engineers in data not in roster: {len(seen - roster)}  Sample: {sorted(seen - roster)[:5]}')
print(f'Roster members with 0 cases: {sorted(roster - seen)}')
