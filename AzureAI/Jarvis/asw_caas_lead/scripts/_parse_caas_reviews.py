"""Extract Key Updates / Service Delivery / Reminders from CaaS Lead .md files.

Handles TWO output formats from the earlier extraction step:

  (a) markitdown-generated markdown (real .pptx)  -> 3-column markdown tables
      with canonical anchor headers in the header row.
  (b) PowerPoint COM-generated flat text (legacy .ppt) -> linear shape-order
      dump with anchors interleaved with content (often triplicated).

For (a) we walk the table cell-by-cell using a column->section map; the header
row establishes the map, each data row's cells are routed to the section that
its column is currently tagged with. A second sub-header (Service Delivery /
Feedback) simply re-tags columns 1 and 2 to new sections.

For (b) we cannot rely on column boundaries, so we walk anchor-to-anchor and
route everything after an anchor into that bucket, deduplicating aggressively
because the COM dump often emits each column's text 2-3x per slide.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT      = Path(__file__).resolve().parents[3]

# ---------------------------------------------------------------------------
# Month configuration.
# Change MONTH_TAG when running for a new month; all other paths derive from it.
# Override at runtime with:   python _parse_caas_reviews.py --month=jul2026
# ---------------------------------------------------------------------------
MONTH_TAG   = "jun2026"                       # <-- update per month
MONTH_LABEL = "June 2026"                     # <-- update per month
MONTH_SHORT = "Jun 2026"                      # <-- update per month
SP_FOLDER   = "FY26June - CaaS Lead Sync"     # <-- update per month (SharePoint folder name)

if len(sys.argv) > 1 and sys.argv[1].startswith("--month="):
    MONTH_TAG = sys.argv[1].split("=", 1)[1].strip()

DOWNLOADS = ROOT / "Output" / f"caas_lead_reviews_{MONTH_TAG}"
# NOTE: parser writes the *raw* stage output. The curated file (consumed by the
# dashboard) is produced by _curate_caas_reviews.py from this raw file + a
# hand-authored curation dict — see SKILL.md §14.6.
OUT_JSON  = ROOT / "Skills" / "asw_caas_lead" / "references" / f"caas_lead_reviews_{MONTH_TAG}_raw.json"

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

# --- anchors ---------------------------------------------------------------

ANCHOR_PATTERNS = [
    ("key_updates",      re.compile(r"key\s+update.*?sync\s+up",           re.I)),
    ("reminders",        re.compile(r"reminders?\s+to\s+asw\s+support",    re.I)),
    ("service_delivery", re.compile(r"service\s+delivery.*items.*actions", re.I)),
    ("feedback",         re.compile(r"feedback\s*/\s*support\s+need",      re.I)),
]


def _match_anchor(text: str) -> str | None:
    s = text.strip()
    if not s or len(s) > 80:
        return None
    for section, rx in ANCHOR_PATTERNS:
        if rx.search(s):
            return section
    return None


# --- boilerplate -----------------------------------------------------------

DROP_PATTERNS = [
    r"^customername\s*:",
    r"^support\s+offering\s*:",
    r"^outreach\s+stage\s*:",
    r"^deliverables?\s+completed?\s*$",
    r"^contacts?\s*(?:person)?\s*$",
    r"^(?:ace|csam|csa|im\+|sfmc|tpm|acm)\s*:",
    r"^\S+@\S+$",
    r"^items?\s*$", r"^status\s*$", r"^notes?\s*$",
    r"^subscriptions?/?\s*tag\s*$",
    r"^plan\s+of\s+record\s*$",
    r"^wiki\s+page\s*$",
    r"^dashboard\s*$",
    r"^join\s+cx\s+call\s*$",
    r"^caas\s+lead\s*:",
    r"^date\s*:",
    r"^see\s+details\s+in\s+por\s*$",
    r"^see\s+wiki\s+page.*download.*$",
    r"^weekly\s+meeting.*$",
    r"^(?:bi-?)?weekly.*sync.*$",
    r"^completed\s*$", r"^wip\s*$", r"^done\s*$", r"^building\s*$",
    r"^as\s+needed\s*$", r"^yes\s*$", r"^no\s*$",
    r"^about\s+customer\s+name\s*$",
    r"^\d+\s*$",
    r"^slide\s+number\s*:",
    r"^asw\s+caas\s+lead\s+status\s+update\s*$",
    r"^ongoing\s*[:\uff1a]?\s*$",
    r"^cx\s+adv\s+ee\s*:",
    r"^tp[mn]\s*:",
    r"^#+\s*notes\s*:\s*$",
]
DROP_RES = [re.compile(p, re.I) for p in DROP_PATTERNS]


def _is_boilerplate(line: str) -> bool:
    s = line.strip()
    if not s or len(s) < 4:
        return True
    return any(rx.match(s) for rx in DROP_RES)


def _clean(text: str) -> str:
    s = text.strip()
    s = re.sub(r"^\s*(?:[-*\u2022\u25cf\u25aa\u25e6\u25b6\u25ba]|\d+[.)]|[a-z][.)]|\[\d+\])\s*", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.strip("| ")
    return s


def _split_sentences(text: str) -> list[str]:
    text = text.replace("\r", "\n")
    parts: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # split "1. foo 2. bar" into separate items
        subs = re.split(r"(?<=\.)\s+(?=\d+\.\s+[A-Z])", line)
        # then further sentence split (after period/exclaim/question) when the
        # next token starts with a capital letter, digit or [ tag
        buf: list[str] = []
        for sub in subs:
            for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\[\d\u2022])", sub):
                buf.append(s)
        for sub in buf:
            for s in re.split(r"\s+(?=\[\d+\])", sub):
                s = s.strip()
                if s:
                    parts.append(s)
    return parts


# --- markdown table walker -------------------------------------------------

TABLE_ROW_RX = re.compile(r"^\s*\|(.+)\|\s*$", re.DOTALL)


def _row_cells(row_text: str) -> list[str] | None:
    """Split an accumulated (possibly multi-line) markdown row into cells.
    Returns None for divider rows (---)."""
    m = TABLE_ROW_RX.match(row_text)
    if not m:
        return None
    cells = [c.strip() for c in m.group(1).split("|")]
    if all(re.fullmatch(r":?-{2,}:?", (c or "").strip()) for c in cells if c is not None):
        return None
    return cells


def _iter_table_rows(md: str):
    """Yield markdown table rows, joining lines that continue a multi-line cell.
    A row starts on a line beginning with '|'. It ends on a line ending with '|'
    (possibly the same line). Intermediate lines are treated as continuations
    of the last cell."""
    buf: str | None = None
    for raw in md.splitlines():
        stripped = raw.rstrip()
        starts = stripped.lstrip().startswith("|")
        ends   = stripped.endswith("|") and stripped.lstrip().startswith("|") is False or (
                 stripped.endswith("|") and (starts and len(stripped.rstrip("|").rstrip()) > 0))
        # simpler: a row is closed when the current line ends with '|' (any line)
        if buf is None:
            if not starts:
                continue
            if stripped.endswith("|"):
                yield stripped
            else:
                buf = stripped
        else:
            buf += "\n" + stripped
            if stripped.endswith("|"):
                yield buf
                buf = None
    if buf is not None:
        yield buf


def parse_tabular(md: str) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {"key_updates": [], "service_delivery": [], "reminders": [], "feedback": []}
    col_section: dict[int, str] = {}
    for row_text in _iter_table_rows(md):
        cells = _row_cells(row_text)
        if cells is None:
            continue
        anchor_in_row = False
        for i, cell in enumerate(cells):
            sec = _match_anchor(cell)
            if sec is not None:
                col_section[i] = sec
                anchor_in_row = True
        if anchor_in_row:
            continue
        for i, cell in enumerate(cells):
            section = col_section.get(i)
            if not section:
                continue
            for piece in _split_sentences(cell):
                if _is_boilerplate(piece):
                    continue
                cleaned = _clean(piece)
                if len(cleaned) < 5:
                    continue
                if len(cleaned) > 500:
                    cleaned = cleaned[:497].rstrip() + "\u2026"
                buckets[section].append(cleaned)
    return buckets


# --- linear walker ---------------------------------------------------------
# The 6 legacy .ppt files all use the same template with a repeating structure:
#
#   Top half:
#     "Key update since last sync up (Accomplishment)"     [visual header]
#     "Reminder to ASW Support"                            [visual header]
#     ("CustomerName: ..." + "Support Offering: ..." + "Outreach Stage: ...")  [About col, skip]
#     "Deliverables Completed"                            -> col2 = key_updates
#     numbered / free-text lines                          -> key_updates
#     "[N] Title" bracketed items                         -> col3 = reminders
#
#   Bottom half:
#     "Service Delivery (Items/actions for future)"       -> col2 = service_delivery
#     "Feedback/Support Need"                             -> col3 = feedback
#     "Ongoing:" numbered items                           -> service_delivery
#     "For follow-the-sun ..." style prose                -> service_delivery/feedback
#
# The slide often contains 3-4 duplicate shapes (visual placeholders that got
# copied at authoring time), so we rely on dedupe at the end.

COL_MARKER_RX  = re.compile(r"^<!--\s*COL\s*:\s*(\d+)\s*-->\s*$", re.I)
SLIDE_MARKER_RX = re.compile(r"^<!--\s*Slide\s+number\s*:", re.I)
BRACKET_ITEM_RX = re.compile(r"^\[(\d+)\]\s")
DELIV_RX        = re.compile(r"^deliverables?\s+completed\s*$", re.I)
ONGOING_RX      = re.compile(r"^ongoing[\s:\uff1a]*$", re.I)
ABOUT_RX        = re.compile(r"^about\s+customer\s+name\s*$", re.I)
CONTACTS_RX     = re.compile(r"^contacts?\s+person\s*$", re.I)


def parse_linear(md: str) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {"key_updates": [], "service_delivery": [], "reminders": [], "feedback": []}
    in_second_half   = False   # True after "Service Delivery (Items/actions for future)" anchor
    in_right_col     = False   # True while inside col3 (Reminder / Feedback)
    routing_disabled = False   # True when in About col or after Contacts Person

    for raw in md.splitlines():
        line = raw.replace("\u200b", "").strip()
        if not line:
            continue
        if COL_MARKER_RX.match(line):
            continue
        if SLIDE_MARKER_RX.match(line):
            continue

        # visual headers / state changers
        low = line.lower()

        if ABOUT_RX.match(line):
            routing_disabled = True   # About column content follows
            in_right_col     = False
            continue
        if re.search(r"key\s+update.*sync\s+up", low):
            # visual header only, do not change routing state
            continue
        if re.search(r"reminders?\s+to\s+asw\s+support", low):
            # visual header for col3
            routing_disabled = False
            in_right_col     = True
            continue
        if re.search(r"service\s+delivery.*items.*actions", low):
            in_second_half   = True
            in_right_col     = False
            routing_disabled = False
            continue
        if re.search(r"feedback\s*/\s*support\s+need", low):
            in_right_col     = True
            routing_disabled = False
            continue
        if DELIV_RX.match(line):
            # col2 header (Key Updates / Service Delivery)
            in_right_col     = False
            routing_disabled = False
            continue
        if ONGOING_RX.match(line):
            in_right_col     = False
            routing_disabled = False
            continue
        if CONTACTS_RX.match(line):
            routing_disabled = True
            continue

        # bracketed items -> col3
        if BRACKET_ITEM_RX.match(line):
            in_right_col     = True
            routing_disabled = False
            # fall through to route this line

        if routing_disabled:
            continue
        if _is_boilerplate(line):
            continue

        if in_second_half:
            section = "feedback" if in_right_col else "service_delivery"
        else:
            section = "reminders" if in_right_col else "key_updates"

        for piece in _split_sentences(line):
            if _is_boilerplate(piece):
                continue
            cleaned = _clean(piece)
            if len(cleaned) < 5:
                continue
            if len(cleaned) > 500:
                cleaned = cleaned[:497].rstrip() + "\u2026"
            buckets[section].append(cleaned)
    return buckets


# --- post-process ----------------------------------------------------------

def _dedupe(items: list[str], limit: int = 12) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        key = re.sub(r"\W+", "", it.lower())[:100]
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
        if len(out) >= limit:
            break
    return out


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _dkey(customer: str, tpid: str | None) -> str:
    """Match the dashboard's `_tpid_key(f)` format: bare TPID string, or
    `noTPID-{slug}` for customers without a TPID."""
    return str(tpid) if tpid else f"noTPID-{_slug(customer)}"


# --- main ------------------------------------------------------------------

def main() -> int:
    by_key: dict[str, dict] = {}
    for name, (customer, tpid) in FILE_MAP.items():
        md_path = DOWNLOADS / (name.rsplit(".", 1)[0] + ".md")
        if not md_path.exists():
            print(f"[MISS] {md_path.name}")
            continue
        raw = md_path.read_text(encoding="utf-8")
        has_table = any(TABLE_ROW_RX.match(l) for l in raw.splitlines())
        if has_table:
            buckets = parse_tabular(raw)
            fmt = "table"
        else:
            buckets = parse_linear(raw)
            fmt = "linear"

        merged_reminders = buckets["reminders"] + buckets["feedback"]

        key_updates      = _dedupe(buckets["key_updates"],      limit=12)
        service_delivery = _dedupe(buckets["service_delivery"], limit=10)
        reminders        = _dedupe(merged_reminders,            limit=10)

        by_key[_dkey(customer, tpid)] = {
            "customer":         customer,
            "tpid":             tpid,
            "pptx_name":        name,
            "source_format":    fmt,
            "key_updates":      key_updates,
            "service_delivery": service_delivery,
            "reminders":        reminders,
        }
        print(f"[OK] {customer:20} [{fmt:6}]  key={len(key_updates):>2}  svc={len(service_delivery):>2}  rem={len(reminders):>2}")

    out = {
        "meta": {
            "month":            MONTH_SHORT,
            "month_label":      MONTH_LABEL,
            "sharepoint_folder":f"https://microsoft.sharepoint.com/teams/AzureStrategicWorkloads-SAP/Shared%20Documents/Forms/AllItems.aspx?id=%2Fteams%2FAzureStrategicWorkloads%2DSAP%2FShared%20Documents%2FGeneral%2FCxOutreach%2F{SP_FOLDER.replace(' ', '%20').replace('-', '%2D')}",
            "customer_count":   len(by_key),
            "stage":            "raw",
        },
        "by_key": by_key,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] {OUT_JSON} ({len(by_key)} customers, {OUT_JSON.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
