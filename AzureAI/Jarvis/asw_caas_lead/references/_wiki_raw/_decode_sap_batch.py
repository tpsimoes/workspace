"""Decode the batched SAP customer wiki content from chat-session-resources into per-customer .md files."""
import json, pathlib, re

BATCH_FILE = pathlib.Path(r'c:\Users\jacobw.FAREAST\AppData\Roaming\Code\User\workspaceStorage\2f685bee3848df999d730f8ddd5268d8\GitHub.copilot-chat\chat-session-resources\91e46d34-7589-49d4-ae0b-bc263e414af0\toolu_bdrk_01Vcqijrw3ywvNu5zwuYVEh4__vscode-1784510629366\content.txt')
OUT_DIR = pathlib.Path(r'c:\GitHubCopilot\IronMan\Skills\asw_caas_lead\references\_wiki_raw')
OUT_DIR.mkdir(parents=True, exist_ok=True)

raw = BATCH_FILE.read_text(encoding='utf-8')
m = re.search(r'### Result\s*\n(.*?)\n### Ran Playwright', raw, re.S)
if not m:
    raise SystemExit('Could not find Result block')
js_str = m.group(1).strip()
data = json.loads(js_str)
print(f'Parsed {len(data)} entries')

for entry in data:
    name = entry['name']
    slug = name.replace(' ', '_')
    key = entry['key']
    pid = entry['pageId']
    content = entry.get('content') or ''
    length = len(content)
    print(f'  {name:20s} key={key:25s} pageId={pid}  len={length}')
    out = OUT_DIR / f'{slug}.md'
    out.write_text(content, encoding='utf-8')

# Also keep a small manifest
manifest = {
    e['name']: {
        'key': e['key'],
        'pageId': e['pageId'],
        'path': e['path'],
        'contentLen': len(e.get('content') or ''),
    } for e in data
}
(OUT_DIR / '_manifest_sap.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(f'Wrote {len(data)} .md files to {OUT_DIR}')
