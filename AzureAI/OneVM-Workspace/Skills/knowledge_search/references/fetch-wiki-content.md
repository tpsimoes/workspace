# Fetch Wiki Content via Git Items API

All Supportability Wikis are **Code Wikis**, and their content must be retrieved using the Git Items API (**not** the Wiki Page API).

## PowerShell Script

```powershell
# 1. Get Azure DevOps access token
$token = az account get-access-token `
  --resource 499b84ac-1321-427f-aa17-267ca6975798 `
  --query accessToken -o tsv

# 2. Build request and download the page
$headers = @{ Authorization = "Bearer $token" }
$org  = "Supportability"
$uri  = "https://dev.azure.com/$org/{project}/_apis/git/repositories/{repositoryId}/items?path={filePath}&api-version=7.1"

Invoke-RestMethod -Uri $uri -Headers $headers -Method Get -OutFile "$env:TEMP\wiki_page.md"
Get-Content "$env:TEMP\wiki_page.md"

## Variable Description

| Variable         | Source                                                                                  |
|------------------|-----------------------------------------------------------------------------------------|
| `{project}`      | `project.name` from the search result                                                   |
| `{repositoryId}` | `repositoryId` returned by `mcp_ado_wiki_list_wikis` (not the wiki id)                 |
| `{filePath}`     | `path` from the search result, keep the `.md` extension                                 |

---

## Wiki Link Format

```
https://supportability.visualstudio.com/{project}/_wiki/wikis/{wikiName}/{pageId}/{pageName}
```
