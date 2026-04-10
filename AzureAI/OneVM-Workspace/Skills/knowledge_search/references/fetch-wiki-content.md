# Fetch Wiki Content via Git Items API

Supportability 的 Wiki 均为 **Code Wiki**，必须使用 Git Items API（而非 Wiki Page API）获取内容。

## PowerShell 脚本

```powershell
# 1. 获取 Azure DevOps 访问令牌
$token = az account get-access-token `
  --resource 499b84ac-1321-427f-aa17-267ca6975798 `
  --query accessToken -o tsv

# 2. 构建请求并下载页面
$headers = @{ Authorization = "Bearer $token" }
$org  = "Supportability"
$uri  = "https://dev.azure.com/$org/{project}/_apis/git/repositories/{repositoryId}/items?path={filePath}&api-version=7.1"

Invoke-RestMethod -Uri $uri -Headers $headers -Method Get -OutFile "$env:TEMP\wiki_page.md"
Get-Content "$env:TEMP\wiki_page.md"
```

### 变量说明

| 变量 | 来源 |
|---|---|
| `{project}` | 搜索结果中的 `project.name` |
| `{repositoryId}` | `mcp_ado_wiki_list_wikis` 返回的 `repositoryId`（≠ wiki id） |
| `{filePath}` | 搜索结果中的 `path`，保留 `.md` 扩展名 |

## Wiki 链接格式

```
https://supportability.visualstudio.com/{project}/_wiki/wikis/{wikiName}/{pageId}/{pageName}
```
