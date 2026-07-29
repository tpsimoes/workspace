import json
from collections import Counter
data = json.load(open(r'c:\GitHubCopilot\IronMan\Output\asw_fy26_all_cases.json','r',encoding='utf-8'))

# Cases in the RISE Escalations queue
rise_rows = [r for r in data if 'RISE' in (r.get('CurrentQueueName') or '')]
print(f"Total cases in RISE queue: {len(rise_rows)}")
print("Queue distribution (RISE-related):")
for q, n in Counter((r.get('CurrentQueueName') or '') for r in rise_rows).most_common():
    print(f"  {n:5d}  {q}")

print("\nTPID distribution within RISE Escalations queue:")
tpid_cnt = Counter((r.get('Customer_TPID'), r.get('Customer_TPName')) for r in rise_rows)
for (tpid, name), n in tpid_cnt.most_common(20):
    print(f"  {n:5d}  {tpid}  {name}")

print("\n--- Check TPID 603819 (SAP SE) full breakdown ---")
sap_rows = [r for r in data if r.get('Customer_TPID') == 603819]
print(f"Total cases for TPID 603819: {len(sap_rows)}")
for q, n in Counter((r.get('CurrentQueueName') or '') for r in sap_rows).most_common(10):
    print(f"  {n:5d}  {q}")

print("\n--- Check TPID 2699441 ---")
alt_rows = [r for r in data if r.get('Customer_TPID') == 2699441]
print(f"Total cases for TPID 2699441: {len(alt_rows)}")
for q, n in Counter((r.get('CurrentQueueName') or '') for r in alt_rows).most_common(10):
    print(f"  {n:5d}  {q}")
