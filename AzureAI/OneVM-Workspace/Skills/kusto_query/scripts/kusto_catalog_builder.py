#!/usr/bin/env python3
"""
kusto_catalog_builder.py — Build/refresh Kusto cluster+table catalog from ADO wiki.

Usage:
    python kusto_catalog_builder.py --wiki-project AzureIaaSVM
    python kusto_catalog_builder.py --wiki-project AzureIaaSVM --output-dir ../references

Requirements:
    pip install azure-devops msrest requests

Authentication:
    Uses personal access token (PAT) or interactive browser auth via azure-identity.
    Set environment variable ADO_PAT=<your-pat> for non-interactive use.

Output:
    references/catalog-<wiki-project>.md
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone

# ── Optional: use requests if azure-devops SDK not installed ──────────────────
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


ADO_ORG = "Supportability"
ADO_BASE = f"https://dev.azure.com/{ADO_ORG}"

# Wiki pages known to contain Kusto cluster/table information
KUSTO_WIKI_PATHS = [
    "/Tools/Kusto/Kusto Tables_Tool",
    "/Tools/Kusto/Kusto Endpoints_Tool",
    "/Tools/Kusto/Kusto Tables Control Plane_Tool",
]

# Search terms to discover additional Kusto wiki pages
SEARCH_TERMS = [
    "kusto cluster database table investigation",
    "kusto endpoint AzureCM vmadb",
    "kusto queries RCA investigation",
]


def get_pat() -> str:
    """Get ADO PAT from environment or prompt user."""
    pat = os.environ.get("ADO_PAT", "")
    if not pat:
        print("ADO_PAT environment variable not set.")
        print("Set it with:  $env:ADO_PAT = '<your-personal-access-token>'")
        print("Or get a PAT at: https://dev.azure.com/Supportability/_usersSettings/tokens")
        sys.exit(1)
    return pat


def ado_headers(pat: str) -> dict:
    """Return Basic auth headers for ADO REST API."""
    import base64
    token = base64.b64encode(f":{pat}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def get_wiki_page_content(project: str, wiki_id: str, path: str, headers: dict) -> str:
    """Fetch raw markdown content of a wiki page via ADO REST API."""
    encoded_path = requests.utils.quote(path, safe="")
    url = (
        f"{ADO_BASE}/{project}/_apis/wiki/wikis/{wiki_id}/pages"
        f"?path={encoded_path}&includeContent=true&api-version=7.1"
    )
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("content", "")
    else:
        print(f"  [WARN] Page not found: {path} (HTTP {resp.status_code})")
        return ""


def search_wiki(project: str, search_text: str, headers: dict, top: int = 10) -> list[dict]:
    """Search ADO wiki for pages matching search_text."""
    url = f"https://almsearch.dev.azure.com/{ADO_ORG}/_apis/search/wikisearchresults?api-version=7.1"
    body = {
        "searchText": search_text,
        "filters": {"Project": [project]},
        "$top": top,
        "$skip": 0,
        "includeFacets": False,
    }
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        return [
            {"path": r["path"].replace(".md", ""), "wiki_id": r["wiki"]["id"]}
            for r in results
        ]
    return []


def get_wiki_info(project: str, headers: dict) -> dict:
    """Get wiki metadata (id) for the project wiki."""
    url = f"{ADO_BASE}/{project}/_apis/wiki/wikis?api-version=7.1"
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        wikis = resp.json().get("value", [])
        for wiki in wikis:
            if wiki.get("name") == project:
                return wiki
        if wikis:
            return wikis[0]
    print(f"[ERROR] Could not get wiki info for project {project}")
    sys.exit(1)


def extract_kusto_tables_from_markdown(content: str) -> list[dict]:
    """
    Parse wiki markdown to extract cluster/database/table info.
    Handles the table format used in Kusto-Tables_Tool and Kusto-Endpoints_Tool.
    Returns list of dicts: {cluster_uri, database, table, description}
    """
    entries = []
    # Match lines like: `cluster('x').database('y').TableName` | description |
    pattern = re.compile(
        r"`cluster\(['\"]([^'\"]+)['\"]\)\.database\(['\"]([^'\"]+)['\"]\)\.([^`\s|]+)`"
        r"[^|]*\|([^|]+)\|",
        re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        cluster_uri, database, table, description = match.groups()
        entries.append({
            "cluster_uri": cluster_uri.strip(),
            "database": database.strip(),
            "table": table.strip(),
            "description": description.strip(),
        })

    # Match standalone cluster+database section headers like:
    # `cluster('x').database('y')`
    cluster_db_pattern = re.compile(
        r"`cluster\(['\"]([^'\"]+)['\"]\)\.database\(['\"]([^'\"]+)['\"]\)`",
        re.IGNORECASE,
    )
    current_cluster = current_db = None
    for line in content.splitlines():
        m = cluster_db_pattern.search(line)
        if m:
            current_cluster, current_db = m.group(1).strip(), m.group(2).strip()

        # Table row: `{ClusterDB}.TableName` | description |
        table_match = re.search(
            r"`\{[A-Za-z0-9]+\}\.([A-Za-z0-9_]+)`[^|]*\|([^|]+)\|", line
        )
        if table_match and current_cluster and current_db:
            entries.append({
                "cluster_uri": current_cluster,
                "database": current_db,
                "table": table_match.group(1).strip(),
                "description": table_match.group(2).strip(),
            })

    return entries


def group_entries(entries: list[dict]) -> dict:
    """Group entries by (cluster_uri, database)."""
    grouped: dict[tuple, list] = {}
    for e in entries:
        key = (e["cluster_uri"], e["database"])
        grouped.setdefault(key, [])
        # Deduplicate by table name
        existing_tables = {t["table"] for t in grouped[key]}
        if e["table"] not in existing_tables:
            grouped[key].append(e)
    return grouped


def render_markdown(grouped: dict, project: str, search_results: list[dict]) -> str:
    """Render grouped entries as markdown catalog."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Kusto Catalog — {project} Wiki",
        "",
        f"Source: {project} ADO Wiki (auto-generated)",
        f"Last synced: {now}",
        "",
        "> Use `scripts/kusto_catalog_builder.py --wiki-project {project}` to refresh this file.",
        "",
        "---",
        "",
    ]

    if search_results:
        lines += [
            "## Discovered Wiki Pages",
            "",
            "The following Kusto-related wiki pages were found during this build:",
            "",
        ]
        for r in search_results:
            lines.append(f"- `{r['path']}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    if not grouped:
        lines.append(
            "_No cluster/table entries were automatically extracted. "
            "Check the wiki pages listed above for manual reference._"
        )
    else:
        for (cluster_uri, database), tables in sorted(grouped.items()):
            alias = cluster_uri.split(".")[0].replace("'", "")
            lines += [
                f"## {alias} → {database}",
                f"**URI**: `https://{cluster_uri}` (if not already a full URL)",
                f"**Database**: `{database}`",
                "",
                "| Table | Description |",
                "|-------|-------------|",
            ]
            for t in tables:
                desc = t["description"].replace("|", "\\|")
                lines.append(f"| `{t['table']}` | {desc} |")
            lines.append("")

    return "\n".join(lines)


def build_catalog(project: str, output_dir: str) -> None:
    """Main entry point: fetch wiki pages, extract tables, write catalog."""
    if not HAS_REQUESTS:
        print("[ERROR] 'requests' package is required. Install with: pip install requests")
        sys.exit(1)

    pat = get_pat()
    headers = ado_headers(pat)

    print(f"[1/4] Getting wiki info for project: {project}")
    wiki = get_wiki_info(project, headers)
    wiki_id = wiki["id"]
    print(f"      Wiki ID: {wiki_id}")

    all_content = []
    all_search_results = []

    print(f"[2/4] Fetching known Kusto wiki pages...")
    for path in KUSTO_WIKI_PATHS:
        print(f"      GET {path}")
        content = get_wiki_page_content(project, wiki_id, path, headers)
        if content:
            all_content.append(content)
            print(f"      ✓ {len(content)} chars")

    print(f"[3/4] Searching wiki for additional Kusto pages...")
    seen_paths = set(KUSTO_WIKI_PATHS)
    for term in SEARCH_TERMS:
        results = search_wiki(project, term, headers, top=5)
        for r in results:
            if r["path"] not in seen_paths:
                seen_paths.add(r["path"])
                all_search_results.append(r)
                print(f"      Found: {r['path']}")
                content = get_wiki_page_content(project, wiki_id, r["path"], headers)
                if content:
                    all_content.append(content)

    print(f"[4/4] Extracting cluster/table entries and writing catalog...")
    all_entries = []
    for content in all_content:
        all_entries.extend(extract_kusto_tables_from_markdown(content))

    grouped = group_entries(all_entries)
    print(f"      Extracted {len(all_entries)} entries across {len(grouped)} cluster/db pairs")

    markdown = render_markdown(grouped, project, all_search_results)
    output_path = os.path.join(output_dir, f"catalog-{project}.md")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\n✅ Catalog written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Build Kusto cluster/table catalog from ADO wiki"
    )
    parser.add_argument(
        "--wiki-project",
        required=True,
        help="ADO wiki project name (e.g. AzureIaaSVM)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "references"),
        help="Directory to write the catalog markdown file (default: ../references)",
    )
    args = parser.parse_args()
    build_catalog(args.wiki_project, os.path.abspath(args.output_dir))


if __name__ == "__main__":
    main()
