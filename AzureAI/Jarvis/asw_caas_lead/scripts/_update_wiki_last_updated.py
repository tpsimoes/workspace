"""One-shot update: patch last_updated (and small metadata gaps) in customer_wiki_summaries.json.

Dates come from ADO git commit history of the wiki-backing repo
(project: AzureStrategicWorkloads, code wiki 'AzureStrategicWorkloads', repoId 4417da5a-...).
These match the timestamp shown in the wiki UI's <time class="last-updated-date"> element
(verified on Unilever: 2024-10-29T03:21:17Z = "Oct 29, 2024").
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
JSON_PATH = HERE.parent / "references" / "customer_wiki_summaries.json"

# key = customer name in JSON, value = (last_updated_iso_date, git_committer)
# NOTE: for the 2026-07-14 batch, Francisco Paulos ran a bulk PR that touched most
# Know-Me pages to add the tag block asw.Reviewed-07-2026 (many EPIC + SAP stubs).
UPDATES: dict[str, dict] = {
    # SAP with content
    "PepsiCo":      {"last_updated": "2024-10-29", "committer": "Ivan Ayala"},
    "Woolworths":   {"last_updated": "2026-05-27", "committer": "Jake Lin"},
    "Medline":      {"last_updated": "2025-04-17", "committer": "Frank Gong"},
    "Lego":         {"last_updated": "2026-07-14", "committer": "Francisco Paulos"},
    "Nike":         {"last_updated": "2025-01-22", "committer": "Alexander Kassap"},
    "Bayer AG":     {"last_updated": "2025-02-25", "committer": "Dante Stancato"},
    "BHP":          {"last_updated": "2025-06-27", "committer": "Jake Lin"},
    "Unilever":     {"last_updated": "2024-10-29", "committer": "Ivan Ayala"},
    # SAP stubs
    "Shell":        {"last_updated": "2026-07-14", "committer": "Francisco Paulos"},
    "Ferrero":      {"last_updated": "2026-07-14", "committer": "Francisco Paulos"},
    "Beiersdorf":   {"last_updated": "2026-07-14", "committer": "Francisco Paulos"},
    "General Motors":{"last_updated":"2026-07-14", "committer": "Francisco Paulos"},
    "CVS":          {"last_updated": "2026-07-14", "committer": "Francisco Paulos"},
    # Previously flagged "No Know-Me page" but a page DOES exist in the git tree:
    "McKesson":     {"last_updated": "2026-04-10", "committer": "Katherine Martinez Torres",
                     "page_exists": True,
                     "wiki_slug": "McKesson",
                     "note": "Know-Me page exists in SAP/SfMC-Customers wiki tree (last edited 2026-04-10 by Katherine Martinez Torres). Content not yet extracted."},
    "Halliburton":  {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                     "page_exists": True,
                     "wiki_slug": "Halliburton",
                     "note": "Know-Me page exists but page touched only by the 2026-07-14 bulk tag-refresh PR (asw.Reviewed-07-2026)."},
    "Walgreens":    {"last_updated": "2026-04-24", "committer": "Francesca Vargas Martinez",
                     "page_exists": True,
                     "wiki_slug": "WBA-Walgreens-Boots-Alliance",
                     "note": "Know-Me page exists in SAP/SfMC-Customers wiki tree as WBA-Walgreens-Boots-Alliance (last edited 2026-04-24). Content not yet extracted."},
    # EPIC entries
    "TJU":                 {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                            "page_exists": True,
                            "wiki_slug_epic": "Thomas-Jefferson-University"},
    "MichMed":             {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                            "page_exists": True,
                            "wiki_slug_epic": "MichMed"},
    "Ascension Health":    {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                            "page_exists": True,
                            "wiki_slug_epic": "Ascension-Health"},
    "UTMB":                {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                            "page_exists": True,
                            "wiki_slug_epic": "UTMB"},
    "Brown University":    {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                            "page_exists": True,
                            "wiki_slug_epic": "Brown-University"},
    "Cone Health":         {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                            "page_exists": True,
                            "wiki_slug_epic": "Cone-Health"},
    "Univ. Kentucky":      {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                            "page_exists": True,
                            "wiki_slug_epic": "University-of-Kentucky"},
    "Mt. Sinai":           {"last_updated": "2026-07-14", "committer": "Francisco Paulos",
                            "page_exists": True,
                            "wiki_slug_epic": "Mount-Sinai"},
    # Children's Hosp Phila -> no page found in EPIC/SfMC-Customers list
}

SAP_WIKI_PARENT = "https://supportability.visualstudio.com/AzureStrategicWorkloads/_wiki/wikis/AzureStrategicWorkloads/1720255/SfMC-Customers"
EPIC_WIKI_PARENT = "https://supportability.visualstudio.com/AzureStrategicWorkloads/_wiki/wikis/AzureStrategicWorkloads/2849066/SfMC-Customers"

def sap_url(slug: str) -> str:
    return (
        "https://supportability.visualstudio.com/AzureStrategicWorkloads/"
        f"_wiki/wikis/AzureStrategicWorkloads?pagePath=%2FSAP%2FSfMC-Customers%2F{slug}"
    )

def epic_url(slug: str) -> str:
    return (
        "https://supportability.visualstudio.com/AzureStrategicWorkloads/"
        f"_wiki/wikis/AzureStrategicWorkloads?pagePath=%2FEPIC%2FSfMC-Customers%2F{slug}"
    )


def main() -> None:
    doc = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    by_key = doc["by_key"]
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Map customer name -> key (loose match)
    name_to_key: dict[str, str] = {}
    for key, entry in by_key.items():
        name_to_key[entry.get("customer", "").strip()] = key

    changed: list[str] = []
    for cust, upd in UPDATES.items():
        key = name_to_key.get(cust)
        if not key:
            # Try loose match
            candidates = [k for k, e in by_key.items() if cust.lower() in e.get("customer", "").lower()]
            if candidates:
                key = candidates[0]
        if not key:
            print(f"  [skip] no JSON entry for {cust!r}")
            continue
        entry = by_key[key]
        entry["last_updated"] = upd["last_updated"]

        # Attach committer to notes if not already reflected
        committer = upd.get("committer")
        note = entry.get("notes") or ""
        if committer and committer not in note:
            hint = f" Last-modified {upd['last_updated']} by {committer} (from ADO git commit history)."
            entry["notes"] = (note + hint).strip()

        # For entries previously marked "no wiki page" but a page actually exists, promote
        if upd.get("page_exists"):
            slug = upd.get("wiki_slug")
            slug_epic = upd.get("wiki_slug_epic")
            if slug:
                entry["wiki_url_guess"] = sap_url(slug)
                entry["wiki_parent_url"] = SAP_WIKI_PARENT
            elif slug_epic:
                entry["wiki_url_guess"] = epic_url(slug_epic)
                entry["wiki_parent_url"] = EPIC_WIKI_PARENT
            # `has_content` stays as-is for SAP promotions (need manual review); set True where user asked for it
            if entry.get("has_content") is None:
                entry["has_content"] = False  # EPIC stubs — Under Construction placeholders
            if upd.get("note"):
                entry["notes"] = upd["note"] + f" Last-modified {upd['last_updated']} by {committer or 'unknown'}."
            elif not entry.get("notes"):
                entry["notes"] = (
                    f"Page exists at {entry['wiki_url_guess']}. Last-modified {upd['last_updated']} "
                    f"by {committer or 'unknown'}. Content is 'Under Construction' placeholder "
                    f"(tags asw.EPIC, asw.Reviewed-07-2026)."
                )
            entry["fetched_at"] = now_iso

        changed.append(f"{cust} ({key}) -> {upd['last_updated']}")

    # Update meta
    doc["meta"]["last_fetch_run"] = now_iso
    notes = doc["meta"].get("notes", [])
    marker = "last_updated sourced from ADO git commit history"
    if not any(marker in n for n in notes):
        notes.append(
            "last_updated sourced from ADO git commit history "
            "(project AzureStrategicWorkloads, wiki repo 4417da5a-4ba2-4720-8824-897f99d5f29a, "
            "branch main) — matches the timestamp shown in the wiki UI's <time class=\"last-updated-date\">."
        )
    doc["meta"]["notes"] = notes

    JSON_PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {len(changed)} entries:")
    for line in changed:
        print(f"  - {line}")


if __name__ == "__main__":
    main()
