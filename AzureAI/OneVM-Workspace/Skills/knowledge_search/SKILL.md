---
name: knowledge_search
description: When analyzing Azure technical issues, retrieve authoritative materials from multiple sources as a supplement to the model’s own knowledge: Internal ADO Wiki (TSGs, troubleshooting guides), Microsoft Learn official documentation, and public technical resources. Trigger when the user asks "how to troubleshoot X issue", "is there a TSG / KB / internal document", "Azure XXX troubleshooting", "check official documentation", "internal wiki", "is there any related material".
---

# Skill: Knowledge_Search
# Creator: Jack DONG

## Core Principles

- **This skill supplements the model’s own knowledge**, proactively querying external sources during technical issue analysis to obtain the most up-to-date and specific guidance
- **All references must include source links** to ensure the information is verifiable

---

## Information Sources (by Priority)

| Priority | Source | Tool | Applicable Scenario |
|---|---|---|---|
| 🥇 P1 | **ADO Internal Wiki** | `mcp_ado_search_wiki` | TSGs, internal troubleshooting guides, design documentation |
| 🥇 P1 | **Microsoft Learn** | `mcp_mslearn_microsoft_docs_search` / `mcp_mslearn_microsoft_code_sample_search` | Official product documentation, API references, code samples |
| 🥈 P2 | **Public Web Resources** | `fetch_webpage` | Used as a supplement when P1 sources are insufficient |

> Both P1 sources must be queried **in parallel**, without order of precedence; P2 should only be used when P1 results are insufficient.

---

## ADO Wiki Query Standards

### Project Priority

**High Priority** (search first):

| Project | Applicable Scenario |
|---|---|
| `AzureIaaSVM` | IaaS VM, Compute, Storage, Networking |
| `AzureLinuxNinjas` | Linux, SAP, Pacemaker, Clustering |
| `AzureNetworking` | Networking, VNet, DNS, Load Balancing |
| `AzureStrategicWorkloads` | SAP, HPC, Critical Workloads |

**Secondary Priority** (search only if no results from high-priority projects): `CSSGuide` and other Supportability projects

### Retrieve Page Content (4 Steps)

1. Use `mcp_ado_search_wiki` to search and record `project.name`, `wiki.id`, `path` (including `.md`)
2. Use `mcp_ado_wiki_list_wikis` to obtain the wiki list for that project, match `wiki.id` → extract **`repositoryId`**
3. Use the Git Items API to retrieve the content (full script available at [references/fetch-wiki-content.md](references/fetch-wiki-content.md)):
   ```
   GET https://dev.azure.com/Supportability/{project}/_apis/git/repositories/{repositoryId}/items?path={filePath}&api-version=7.1
   ```
4. Wiki reference link format:
   `https://supportability.visualstudio.com/{project}/_wiki/wikis/{wikiName}/{pageId}/{pageName}`

> **Note**: Supportability Wikis are Code Wikis. You must use `repositoryId` + Git Items API. Wiki Page API will return 404.

---

## Output Format

```
## [Issue Title]

[Comprehensive analysis based on model knowledge + retrieved results]

### Troubleshooting Steps / Recommended Actions
1. ...
2. ...

### References
- Document Title + Link — Source: ADO Wiki / Microsoft Learn / Public Resource
- ...
```

- If the answer comes from the model’s own knowledge, no references are required
- If the answer references or uses external sources, links must be included and the source type must be specified
- ADO Wiki links must use the `supportability.visualstudio.com` format
- Microsoft Learn links must use the original `learn.microsoft.com` URL