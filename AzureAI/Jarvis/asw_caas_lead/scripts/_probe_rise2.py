import json
from collections import Counter
data = json.load(open(r'c:\GitHubCopilot\IronMan\Output\asw_fy26_all_cases.json','r',encoding='utf-8'))

print("=== All cases where Customer_TPID = 603819 (SAP SE) ===")
sap = [r for r in data if str(r.get('Customer_TPID')) == '603819']
print(f"Total: {len(sap)}")
print("Queue distribution:")
for q, n in Counter((r.get('CurrentQueueName') or '') for r in sap).most_common():
    print(f"  {n:5d}  {q}")

print("\n=== All cases where Customer_TPID = 2699441 ===")
alt = [r for r in data if str(r.get('Customer_TPID')) == '2699441']
print(f"Total: {len(alt)}")
for q, n in Counter((r.get('CurrentQueueName') or '') for r in alt).most_common():
    print(f"  {n:5d}  {q}")

print("\n=== All cases where Customer_TPID = 15902931 (SAP) ===")
alt2 = [r for r in data if str(r.get('Customer_TPID')) == '15902931']
print(f"Total: {len(alt2)}")
for q, n in Counter((r.get('CurrentQueueName') or '') for r in alt2).most_common():
    print(f"  {n:5d}  {q}")

print("\n=== ALL distinct queues in FY26 dataset ===")
for q, n in Counter((r.get('CurrentQueueName') or '') for r in data).most_common():
    print(f"  {n:5d}  {q}")
