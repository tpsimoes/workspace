import json
from collections import Counter
data = json.load(open(r'c:\GitHubCopilot\IronMan\Output\asw_fy26_all_cases.json','r',encoding='utf-8'))
cnt = Counter((r['Customer_TPID'], r['Customer_TPName']) for r in data)
for (tpid, name), n in cnt.most_common():
    print(f'  {n:5d}  {tpid}  {name}')
