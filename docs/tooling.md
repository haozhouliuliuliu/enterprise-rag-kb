# 辅助工具使用记录：skill-atlas

本文记录按任务要求对 [skill-atlas](https://github.com/haozhouliuliuliu/skill-atlas) 的调研、安装与实际调用结果。它是**辅助调研工具**，不参与 RAGFlow 运行时，也不是本项目的依赖。

## 1. 结论摘要

- skill-atlas 已成功下载、安装并运行（Python 3.11 虚拟环境，`pip install -e .`）。
- 它实际是一个 **GitHub 项目能力位索引器**：按预设的功能分类检索 GitHub 仓库、计算质量指标、生成 Obsidian 笔记库；**不是**可直接加载的 “RAG 需求 / 代码规范 skill 包”。
- 有用的产出：
  - 列出 54 个能力位，其中与本项目相关的是“文档解析与 RAG 切片”“Agent 记忆与检索”“模型接入与聚合”；
  - `inspect` 对 RAGFlow 与 Dify 做了仓库质量体检，可作为选型的辅助证据。
- 局限：全量 `fetch/enrich` 因网络 `IncompleteRead` 只完成了 10/54 个能力位（见 `known-issues.md` KI-006），因此没有把它的排序结果作为选型依据。
- 代码规范方面采用仓库内置的轻量规范（`.editorconfig`、`.gitattributes`、Conventional Commits、`scripts/check-env.ps1`），没有额外引入 linter；本项目第一步只有文档和 PowerShell 脚本，引入完整 lint 工具链收益有限。

## 2. 安装位置与方式

工具安装在仓库之外，避免污染交付物：

```powershell
New-Item -ItemType Directory -Force C:\RAG库\_tools | Out-Null
git clone --depth 1 https://github.com/haozhouliuliuliu/skill-atlas.git C:\RAG库\_tools\skill-atlas
Set-Location C:\RAG库\_tools\skill-atlas
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\skill-atlas.exe --version
```

- 安装路径：`C:\RAG库\_tools\skill-atlas`
- 运行环境：Python 3.11.9（项目要求 ≥ 3.10）
- 是否入库：否；`C:\RAG库\_tools` 不在 Git 仓库内
- 是否影响 RAGFlow：否

## 3. 实际调用记录

### 3.1 能力位列表（`slots`）

```powershell
skill-atlas slots
```

输出 54 个能力位。与本项目相关的条目：

| 能力位 | 类型 | 与本项目的关系 |
| --- | --- | --- |
| 文档解析与 RAG 切片 | staple / core | 对应 PDF/Word 解析、chunk 与引用 |
| Agent 记忆与检索 | staple / core | 对应检索增强与上下文管理 |
| 模型接入与聚合 | rule / core | 对应在线模型供应商接入 |
| Agent 可观测与调试界面 | rule | 对应日志、引用核验与调试 |

这些能力位帮助确认了需要关注的组件类别，但不直接给出“选 RAGFlow”的结论。

### 3.2 离线演示（`examples/demo.py`）

```powershell
python examples\demo.py
```

运行成功，生成 `examples/out` 下的 Obsidian 笔记库，并用示例需求验证了“需求 → 能力位 → 候选仓库”的检索流程。该演示使用本地样例，不访问网络。

### 3.3 仓库体检（`inspect`）

```powershell
skill-atlas inspect infiniflow/ragflow
skill-atlas inspect langgenius/dify
```

2026-10-17 实测：

| 指标 | RAGFlow | Dify |
| --- | --- | --- |
| Stars | 92,368 | 158,700 |
| Forks | 11,017 | 25,083 |
| License | Apache-2.0 | NOASSERTION |
| 最近推送 | 2026-10-17 | 2026-10-17 |
| 归档 | 否 | 否 |
| 质量分（工具启发式） | 94 / 100 | 97 / 100 |
| 结论 | OK | OK；命中“Agent 编排与 Harness” |

解读：

- 两者都活跃、都满足基本质量门槛；Dify 的 star 更多，但许可证被 GitHub 标记为 `NOASSERTION`，企业使用前需要法务确认。
- RAGFlow 的 Apache-2.0 许可清晰，且工具给出的质量分（94）与活跃度满足演示要求。
- 质量分是启发式指标，不能替代对 chunk 引用能力、文档解析效果的实际验证；最终选型仍以官方能力说明和验收要求为准。

### 3.4 数据抓取（`update` / `fetch` / `enrich`）

```powershell
$env:GITHUB_TOKEN = gh auth token
skill-atlas update
```

结果：

- `fetch` 成功抓取 day/week 榜单，month 榜单因网络中断失败；
- `enrich` 断点续跑，截至本文记录完成 10/54 个能力位（`data/raw/enriched.json`）；
- 失败原因：GitHub 搜索大响应读取不完整，抛出 `http.client.IncompleteRead`。

本地规避：在 `_tools` 副本的 `src/skill_atlas/api.py` 中，把 `http.client.HTTPException` 加入重试异常（不修改上游仓库）。该问题记录为 KI-006。

由于索引不完整，`query` 未能给出可信的完整排序结果；本文不引用其排序结论。

## 4. 对项目决策的实际影响

| 用途 | 是否采用 | 说明 |
| --- | --- | --- |
| 发现候选组件类别 | ✅ | 确认“文档解析与 RAG 切片”是关键能力位 |
| RAGFlow vs Dify 质量对比 | ✅（辅助） | 两者均活跃；RAGFlow 许可证更清晰 |
| 直接决定技术选型 | ❌ | 选型主依据仍是 chunk 级引用与 DeepDoc 解析能力 |
| 提供现成 RAG 需求/代码规范 skill | ❌ | 该仓库不提供此类可直接加载的 skill |
| 运行时代码依赖 | ❌ | 工具不进入 RAGFlow 部署链路 |

## 5. 复现与清理

复现：

```powershell
Set-Location C:\RAG库\_tools\skill-atlas
$env:PYTHONIOENCODING = "utf-8"
$env:GITHUB_TOKEN = gh auth token
.\.venv\Scripts\skill-atlas.exe slots
.\.venv\Scripts\skill-atlas.exe inspect infiniflow/ragflow
```

清理（不影响仓库与 RAGFlow）：

```powershell
Remove-Item -Recurse -Force C:\RAG库\_tools\skill-atlas
```

## 6. 备注

- 工具抓取的是公开 GitHub 元数据，不涉及企业内部资料。
- `inspect` 的 star/fork/质量分是动态数据，本文记录的是 2026-10-17 的快照。
- 如果后续需要完整的 54 个能力位索引，建议在稳定网络下重跑 `fetch` + `enrich`，或向上游反馈 `IncompleteRead` 重试问题。
