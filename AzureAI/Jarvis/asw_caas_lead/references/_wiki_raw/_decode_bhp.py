import json, pathlib, re, sys

# The BHP.txt file contains a JSON-encoded string (with the "### Result" header wrapper).
# We want just the raw content.
p = pathlib.Path(r'c:\GitHubCopilot\IronMan\Skills\asw_caas_lead\references\_wiki_raw\BHP.txt')
raw = p.read_text(encoding='utf-8')
# Strip the leading "### Result\n" and any trailing fence-like blocks
m = re.search(r'### Result\s*\n(.*?)\n### Ran Playwright', raw, re.S)
if m:
    js_str = m.group(1).strip()
    # js_str is a JSON string literal (starts with " and ends with ")
    try:
        content = json.loads(js_str)
    except Exception as e:
        print('parse error:', e)
        print('js_str head:', js_str[:200])
        sys.exit(1)
    outp = p.with_name('BHP.md')
    outp.write_text(content, encoding='utf-8')
    print(f'Wrote {outp} ({len(content)} chars)')
else:
    print('Could not find Result section in file')
