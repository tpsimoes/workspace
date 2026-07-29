"""Decode SharePoint-downloaded CaaS Lead PPT payload, run markitdown, and build a review JSON.

Input:  Output/caas_lead_reviews_jun2026/_ppt_payload.json
Output:
    - Output/caas_lead_reviews_jun2026/<name>.pptx           (decoded binaries)
    - Output/caas_lead_reviews_jun2026/<name>.md             (markitdown output)
    - Skills/asw_caas_lead/references/caas_lead_reviews_jun2026.json  (structured JSON)

The .json output uses the same by_key indexing as customer_wiki_summaries.json so the
dashboard can render a per-customer modal keyed by TPID.
"""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
ROOT      = Path(__file__).resolve().parents[3]              # c:\GitHubCopilot\IronMan
DOWNLOADS = ROOT / "Output" / "caas_lead_reviews_jun2026"
PAYLOAD   = DOWNLOADS / "_ppt_payload.json"
OUT_JSON  = ROOT / "Skills" / "asw_caas_lead" / "references" / "caas_lead_reviews_jun2026.json"

# Filename → (customer display, tpid) mapping. Matches the FOCUS list in
# generate_dashboard_v1.py (dkey format = "tpid<value>" or "noTPID-<slug>").
FILE_MAP: dict[str, tuple[str, str | None]] = {
    "[Zone 2] Petrobras CaaS Lead Update - June 2026.pptx":            ("Petrobras",         "940486"),
    "[Zone 2] mtsinai.pptx":                                            ("Mt. Sinai",         "1283152"),
    "[Zone 2] PepsiCo 202606.pptx":                                     ("PepsiCo",           "636846"),
    "[Zone 1] Bayer ASW CaaS Lead Status Update - June 26.pptx":        ("Bayer AG",          "520706"),
    "[Zone 2] Shell CaaS Lead Update - June  2026.pptx":                ("Shell",             "10545209"),
    "[Zone 2] Lego_CaaS.pptx":                                          ("Lego",              "605015"),
    "[Zone 2] University of Kentucky CaaS Lead status - 070126.pptx":   ("Univ. Kentucky",    None),
    "[Zone 2] Halliburton June.pptx":                                   ("Halliburton",       "643195"),
    "[Zone 1] Woolworths CaaS Lead update July 2026.pptx":              ("Woolworths",        "1719071"),
    "[Zone 2] TJU CaaS Lead Update - June 2026.pptx":                   ("TJU",               "18982817"),
    "[Zone 2] Michmed.pptx":                                            ("MichMed",           "1833997"),
    "[Zone 2] Ascension Health CaaS Lead status - 070126.pptx":         ("Ascension Health",  "3841220"),
    "[Zone 1] BHP presentation July 1st.pptx":                          ("BHP",               "523272"),
    "[Zone 2] McKesson-CaaS Lead Status July 1st 2026.pptx":            ("McKesson",          "645076"),
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _dkey(customer: str, tpid: str | None) -> str:
    if tpid:
        return f"tpid{tpid}"
    return f"noTPID-{_slug(customer)}"


# ---------------------------------------------------------------------------
# Section extraction heuristics.
# The PPTs use very free-form headings; markitdown collapses them into plain text.
# We tag lines against several buckets and stop when we see a "next-bucket" header.

SECTION_KEYWORDS = {
    "key_updates": [
        r"^\s*key\s+updates?\b",
        r"^\s*monthly\s+(?:key\s+)?updates?\b",
        r"^\s*(?:this\s+)?month(?:'s)?\s+(?:key\s+)?updates?\b",
        r"^\s*highlights?\b",
        r"^\s*(?:key\s+)?activit(?:y|ies)\b",
        r"^\s*progress\b",
        r"^\s*executive\s+summary\b",
        r"^\s*status\s+update\b",
        r"^\s*engagement\s+update\b",
    ],
    "service_delivery": [
        r"^\s*service\s+delivery\b",
        r"^\s*support\s+delivery\b",
        r"^\s*case\s+(?:delivery|status)\b",
        r"^\s*csat\b",
        r"^\s*case\s+volume\b",
        r"^\s*key\s+metrics\b",
        r"^\s*kpis?\b",
        r"^\s*critsit(?:s)?\b",
        r"^\s*escalations?\b",
    ],
    "reminders": [
        r"^\s*(?:asw\s+)?(?:team\s+)?reminders?\b",
        r"^\s*(?:call\s+to\s+)?action(?:s|\s+items)?\b",
        r"^\s*(?:things?\s+to\s+watch|watch\s+list|what\s+to\s+watch)\b",
        r"^\s*asks?\b",
        r"^\s*next\s+steps?\b",
        r"^\s*follow(?:\s|-)?ups?\b",
        r"^\s*ask(?:s|\s+of)\s+asw\b",
        r"^\s*ask\s+of\s+team\b",
    ],
}
ALL_SECTION_RES = {k: [re.compile(p, re.I) for p in v] for k, v in SECTION_KEYWORDS.items()}


def _classify_heading(line: str) -> str | None:
    """Return the section bucket if this line looks like a section heading, else None."""
    stripped = line.strip().lstrip("#").strip()
    if not stripped or len(stripped) > 80:
        return None
    for bucket, regs in ALL_SECTION_RES.items():
        for rx in regs:
            if rx.search(stripped):
                return bucket
    return None


def _extract_sections(md: str) -> dict[str, list[str]]:
    """Walk the markitdown output and route bullets/paragraphs into the three buckets."""
    sections = {"key_updates": [], "service_delivery": [], "reminders": []}
    current: str | None = None
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue

        bucket = _classify_heading(line)
        if bucket is not None:
            current = bucket
            continue

        if current is None:
            # No heading seen yet — treat leading text as key_updates
            current = "key_updates"

        # Clean bullet markers, page markers, meta
        cleaned = re.sub(r"^\s*(?:[-*•●▪◦o]|\d+\.|[a-z]\))\s*", "", line).strip()
        cleaned = re.sub(r"^\s*<!--.*?-->\s*", "", cleaned)
        if not cleaned:
            continue
        # Skip markitdown scaffolding
        if cleaned.startswith("<!-- Slide number:"):
            continue
        if re.fullmatch(r"#+\s*Slide\s*\d+", cleaned, re.I):
            continue
        if re.fullmatch(r"(?:slide\s*)?\d+", cleaned, re.I):
            continue
        if len(cleaned) < 3:
            continue
        # Trim overly long chunks
        if len(cleaned) > 500:
            cleaned = cleaned[:497].rstrip() + "…"
        sections[current].append(cleaned)

    # Deduplicate while preserving order
    for k, v in sections.items():
        seen = set()
        out = []
        for item in v:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        sections[k] = out[:25]  # cap at 25 bullets per bucket
    return sections


def _fallback_lines(md: str, limit: int = 20) -> list[str]:
    """When section detection finds nothing, take the first N meaningful lines."""
    out = []
    for raw in md.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("<!--") or s.startswith("#") or s.startswith("!["):
            continue
        s = re.sub(r"^\s*(?:[-*•●▪◦o]|\d+\.|[a-z]\))\s*", "", s).strip()
        if len(s) < 5:
            continue
        if len(s) > 500:
            s = s[:497].rstrip() + "…"
        out.append(s)
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------

def main() -> int:
    if not PAYLOAD.exists():
        print(f"[FAIL] Payload not found: {PAYLOAD}", file=sys.stderr)
        return 1

    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    files = payload.get("_payload", [])
    print(f"[INFO] {len(files)} files in payload")

    by_key: dict[str, dict] = {}
    unmapped: list[str] = []

    for f in files:
        name = f["name"]
        b64  = f.get("b64")
        if not b64:
            print(f"[SKIP] {name}: no base64 (err={f.get('error')})")
            continue
        if name not in FILE_MAP:
            unmapped.append(name)
            print(f"[WARN] {name}: not in FILE_MAP — skipped")
            continue

        customer, tpid = FILE_MAP[name]
        pptx_path = DOWNLOADS / name
        pptx_path.write_bytes(base64.b64decode(b64))
        print(f"[SAVE] {pptx_path.name} ({pptx_path.stat().st_size:,} bytes)")

        # Run markitdown
        md_path = DOWNLOADS / (pptx_path.stem + ".md")
        try:
            res = subprocess.run(
                [sys.executable, "-m", "markitdown", str(pptx_path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=90,
            )
            if res.returncode != 0:
                print(f"[FAIL] markitdown for {name}: {res.stderr[:200]}")
                continue
            md_path.write_text(res.stdout, encoding="utf-8")
            print(f"       markitdown → {len(res.stdout):,} chars → {md_path.name}")
        except Exception as e:
            print(f"[FAIL] markitdown exception for {name}: {e}")
            continue

        # Extract sections
        sections = _extract_sections(res.stdout)
        has_any = any(sections.values())
        if not has_any:
            # No bucket matched — put everything into key_updates as fallback
            sections["key_updates"] = _fallback_lines(res.stdout)

        key = _dkey(customer, tpid)
        by_key[key] = {
            "customer":         customer,
            "tpid":             tpid,
            "pptx_name":        name,
            "pptx_size_kb":     round(pptx_path.stat().st_size / 1024, 1),
            "key_updates":      sections["key_updates"],
            "service_delivery": sections["service_delivery"],
            "reminders":        sections["reminders"],
            "used_fallback":    not has_any,
        }

    out = {
        "meta": {
            "month":            "Jun 2026",
            "month_label":      "June 2026",
            "sharepoint_folder":"https://microsoft.sharepoint.com/teams/AzureStrategicWorkloads-SAP/Shared%20Documents/Forms/AllItems.aspx?id=%2Fteams%2FAzureStrategicWorkloads%2DSAP%2FShared%20Documents%2FGeneral%2FCxOutreach%2FFY26June%20%2D%20CaaS%20Lead%20Sync",
            "customer_count":   len(by_key),
            "unmapped_files":   unmapped,
        },
        "by_key": by_key,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] {OUT_JSON}  ({len(by_key)} customers)")
    if unmapped:
        print(f"[WARN] {len(unmapped)} unmapped file(s):")
        for u in unmapped:
            print(f"       - {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
