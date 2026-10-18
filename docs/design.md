# 方案设计说明（v0.2）

> 更新时间：2026-10-18
> 当前底座：AnythingLLM Desktop v1.18.0
> 说明：v0.1 的 RAGFlow/Docker 设计已废弃；完整架构见 [architecture.md](architecture.md)，底座决策见 [README.md](../README.md) 的 ADR-001。

## 1. 当前方案一句话

单台 Windows 电脑运行 AnythingLLM Desktop；文档在本机解析、切片并写入本地 LanceDB，chunk 与问题通过阿里云百炼做向量化和回答生成，回答下方展示 chunk 级 sources。不使用 Docker、WSL2、RAGFlow 或 Dify。

## 2. 关键决策

### ADR-001：废弃 RAGFlow，改用 AnythingLLM

- **决策**：只部署 AnythingLLM Desktop v1.18.0。
- **原因**：目标机无 Docker/WSL2，16 GB 内存与旧 CPU 难以承担 RAGFlow 多容器底座；AnythingLLM 原生应用更轻，仍满足 workspace、PDF/Word、检索与引用验收。
- **代价**：数据会发送到百炼；解析/切片可控性弱于 RAGFlow；桌面版单用户。
- **详细记录**：见 [README.md](../README.md) 第 2 节。

### ADR-002：本地向量库 + 本地元数据

- **决策**：使用 AnythingLLM 内置 LanceDB（向量）与 SQLite（元数据），不单独部署向量数据库。
- **理由**：单机演示、数据量小；少一套服务就少一份资源与运维负担。
- **代价**：不适合大规模并发；需要随应用数据目录一起备份。

### ADR-003：在线模型只用百炼一家

- **决策**：`qwen-plus` + `text-embedding-v4`，共用一把 `DASHSCOPE_API_KEY`，OpenAI 兼容 base URL。
- **理由**：中文效果、国内网络、按量计费、RAGFlow/AnythingLLM 均可接入。
- **代价**：依赖公网与供应商；数据出境到阿里云；只允许虚构资料。

### ADR-004：第一版不做 rerank / 查询改写

- **决策**：先用 AnythingLLM 默认检索参数跑通引用闭环。
- **复审条件**：测试集出现召回不足或引用不相关时，再评估 rerank、调整 chunk 或 Top-N。

## 3. 与 v0.1 的差异

| 项目 | v0.1（已废弃） | v0.2（当前） |
| --- | --- | --- |
| RAG 应用 | RAGFlow v0.27.2 | AnythingLLM Desktop v1.18.0 |
| 运行方式 | Docker Desktop + WSL2 + 多容器 | 原生 Windows 应用 |
| 向量库 | Elasticsearch 8.11.3 | 内置 LanceDB |
| 元数据 | MySQL 8.0.40 | 内置 SQLite |
| 对象存储 | MinIO/SILO | 本机文件系统 |
| 缓存 | Valkey 8 | 无独立缓存 |
| 评测 | 手工 + RAGFlow API | Developer API + `tests/eval.py` |
| 数据边界 | 文档与问答在本机容器 | chunk/问题发送到阿里云百炼 |

## 4. 引用验收口径

1. 回答中的事实性结论至少能展开 1 条 source；
2. source 必须能定位到具体文档与 chunk 片段，而不是只有文件名；
3. 引用片段必须真的包含回答中的关键数值/结论；
4. 无答案问题必须明确表示资料不足，不得编造；
5. 评测脚本只做规则初筛，最终以人工核对引用片段为准。

## 5. 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| 百炼 key 缺失/欠费/限流 | 无法 embedding 或问答 | 演示前检查额度；key 只放本机 |
| 数据发送到阿里云 | 合规风险 | 只用虚构资料；架构/安全文档明示 |
| 文档解析质量差 | 引用缺失或数值错误 | 使用文本型 PDF/真实 Word 表格；人工检查 chunk |
| 内存 15.96 GB | 大文档解析卡顿 | 关闭无关应用；单次处理一份大文档 |
| 桌面版单用户 | 无企业权限/审计 | 定位为演示，不作为生产 |
