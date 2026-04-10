---
name: knowledge_search
description: 分析 Azure 技术问题时，作为模型自有知识的补充，从多个来源检索权威资料：内部 ADO Wiki（TSG、排查指南）、Microsoft Learn 官方文档、以及公开技术资料。当用户提问"如何排查 X 问题"、"有没有 TSG / KB / 内部文档"、"Azure XXX troubleshooting"、"查一下官网文档"、"internal wiki"、"有没有相关资料" 时触发。
---

# Skill: Knowledge_Search
# Creator: Jack DONG
## 核心原则

- **本 skill 是模型自有知识的补充**，在分析技术问题时主动查询外部来源，以获取最新、最具体的指导
- **所有引用必须附出处链接**，确保来源真实可查

---

## 信息来源（按优先级）

| 优先级 | 来源 | 工具 | 适用场景 |
|---|---|---|---|
| 🥇 P1 | **ADO Internal Wiki** | `mcp_ado_search_wiki` | TSG、内部排查指南、设计文档 |
| 🥇 P1 | **Microsoft Learn** | `mcp_mslearn_microsoft_docs_search` / `mcp_mslearn_microsoft_code_sample_search` | 官方产品文档、API 参考、代码示例 |
| 🥈 P2 | **公开网络资料** | `fetch_webpage` | 当 P1 来源无法覆盖时补充 |

> P1 两个来源**并行查询**，不分先后；P2 仅在 P1 结果不足时使用。

---

## ADO Wiki 查询规范

### 项目优先级

**高优先级**（优先搜索）：

| 项目 | 适用场景 |
|---|---|
| `AzureIaaSVM` | IaaS VM、Compute、Storage、Networking |
| `AzureLinuxNinjas` | Linux、SAP、Pacemaker、Clustering |
| `AzureNetworking` | 网络、VNet、DNS、负载均衡 |
| `AzureStrategicWorkloads` | SAP、HPC、关键工作负载 |

**次优先级**（高优先级无结果时搜索）：`CSSGuide` 及其他 Supportability 项目

### 获取页面内容（4 步）

1. `mcp_ado_search_wiki` 搜索，记录 `project.name`、`wiki.id`、`path`（含 `.md`）
2. `mcp_ado_wiki_list_wikis` 获取该项目的 wiki 列表，匹配 `wiki.id` → 提取 **`repositoryId`**
3. 调用 Git Items API 拉取内容（完整脚本见 [references/fetch-wiki-content.md](references/fetch-wiki-content.md)）：
   ```
   GET https://dev.azure.com/Supportability/{project}/_apis/git/repositories/{repositoryId}/items?path={filePath}&api-version=7.1
   ```
4. Wiki 引用链接格式：
   `https://supportability.visualstudio.com/{project}/_wiki/wikis/{wikiName}/{pageId}/{pageName}`

> **注意**：Supportability Wiki 均为 Code Wiki，必须使用 `repositoryId` + Git Items API，Wiki Page API 会返回 404。

---

## 输出格式

```
## [问题标题]

[基于模型知识 + 检索结果的综合分析]

### 排查步骤 / 建议操作
1. ...
2. ...

### 参考资料
- 文档标题 + 链接 — 来源：ADO Wiki / Microsoft Learn / 公开资料
- ...
```

- 若回答内容来自模型自有知识，无需附加引用
- 若回答引用或参考了外部来源，必须附上链接并标注来源类型
- ADO Wiki 链接使用 `supportability.visualstudio.com` 格式
- Microsoft Learn 链接使用 `learn.microsoft.com` 原始 URL