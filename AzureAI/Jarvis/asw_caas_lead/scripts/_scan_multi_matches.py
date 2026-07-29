"""Scan existing workload_rows.txt files to find customers with multiple
SAP / EPIC workload matches (needing multi-workload capture)."""
import re
from pathlib import Path

ROOT = Path(r"C:\GitHubCopilot\IronMan\Skills\asw_caas_lead\references\acr_capture_2026-07")
SAP  = re.compile(r"(?<![a-zA-Z0-9])(sap|hana|s/?4hana|s/?4|netweaver|bw)(?![a-zA-Z0-9])", re.IGNORECASE)
EPIC = re.compile(r"(?<![a-zA-Z0-9])(epic)(?![a-zA-Z0-9])", re.IGNORECASE)

# From scraper: hint for each customer
HINT = {
    "603819": "RISE", "15902931": "RISE", "2699441": "RISE",
    "636846": "SAP", "1719071": "SAP", "682354": "SAP", "10545209": "SAP",
    "523595": "SAP", "605015": "SAP", "1248703": "SAP", "640443": "SAP",
    "520706": "SAP", "523272": "SAP", "101552": "SAP", "645076": "SAP",
    "643195": "SAP", "940486": "SAP", "639155": "SAP",
    "1283152": "EPIC", "18982817": "EPIC", "1833997": "EPIC", "3841220": "EPIC",
}

results = []
for folder in sorted(ROOT.glob("*_*")):
    if not folder.is_dir():
        continue
    tpid = folder.name.split("_", 1)[0]
    rows_file = folder / "workload_rows.txt"
    if not rows_file.exists():
        continue
    hint = HINT.get(tpid, "SAP")
    pat = EPIC if hint == "EPIC" else SAP
    # Parse "[N] picker=True | ..." blocks
    content = rows_file.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"^\[\d+\]\s+picker=", content, flags=re.MULTILINE)
    matches = []
    for blk in blocks:
        blk = blk.strip()
        if not blk.startswith("True"):
            continue
        # First data line = " | <first line after 'True | ...'>" then next line is workload name
        # Actually format: 'True | X\nWorkload Name\nWorkload Type\n...'
        lines = [ln.strip() for ln in blk.splitlines() if ln.strip()]
        # lines[0] = 'True | X' where X is avatar letter (short) OR workload-name (long)
        # If short avatar → workload name is lines[1]; else lines[0] already stripped from '|'
        # After 'True | ' split
        head = lines[0].split("|", 1)[-1].strip() if lines else ""
        candidate = ""
        if head and (len(head) <= 3 and head.isupper() and len(lines) >= 2):
            candidate = lines[1]
        elif head:
            candidate = head
        if candidate and pat.search(candidate):
            matches.append(candidate[:80])
    results.append((tpid, folder.name, hint, len(matches), matches))

# Print grouped
print("\n=== Customers with MULTIPLE SAP/EPIC workload matches ===")
multi = [r for r in results if r[3] > 1]
for tpid, name, hint, n, ms in multi:
    print(f"  {name} (hint={hint}) — {n} matches:")
    for m in ms:
        print(f"    - {m}")

print("\n=== Customers with EXACTLY 1 match ===")
single = [r for r in results if r[3] == 1]
for tpid, name, hint, n, ms in single:
    print(f"  {name}: {ms[0]}")

print("\n=== Customers with 0 matches (need manual mapping) ===")
zero = [r for r in results if r[3] == 0]
for tpid, name, hint, n, ms in zero:
    print(f"  {name} (hint={hint})")

print(f"\nSummary: {len(multi)} multi / {len(single)} single / {len(zero)} zero, total {len(results)}")
