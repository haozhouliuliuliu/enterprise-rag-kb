# 测试

本目录用于存放 RAG 检索与回答的测试问题、预期依据、实际结果与可复现评测脚本。

## 文件

| 文件 | 说明 | 状态 |
| --- | --- | --- |
| [questions.v0.1.md](questions.v0.1.md) | 旧版 14 条 Markdown 问题，保留作资料制作参考 | ✅ 已定义 |
| [questions.v0.2.json](questions.v0.2.json) | 评测脚本读取的 JSON 题集；当前含 1 道 API 连通性占位题 | 🔄 骨架 |
| [eval.py](eval.py) | AnythingLLM Developer API 评测脚本（仅标准库） | ✅ 已就绪 |
| [results/template.md](results/template.md) | 人工测试记录模板（旧版） | ✅ 已定义 |
| `results/eval-*.json/.md` | 脚本生成的结构化结果与可读报告 | ✅ SMOKE-01 已运行 |
| [results/eval-20261018-175648.md](results/eval-20261018-175648.md) | 占位题实测：回答 `EVAL_OK`，判定命中；含 Top-5 检索统计 | ✅ 通过 |
| [questions.spotcheck.json](questions.spotcheck.json) | 22 份资料入库后的 5 类文档抽查题 | ✅ 已定义 |
| [results/eval-20261018-191433.md](results/eval-20261018-191433.md) | 5 类抽查复跑：5/5 命中、Top-5 5/5 | ✅ 通过 |
| [results/table-pdf-quality.md](results/table-pdf-quality.md) | B04 表格 PDF 解析质量结论 | ✅ 完整/结构压平 |
| [questions.full.json](questions.full.json) | 30 题全量集：10 直接 + 5 综合 + 5 易混淆 + 5 版本 + 5 无答案 | ✅ 已定义 |
| [results/full-30-summary.md](results/full-30-summary.md) | 三轮调参对比、最终三项指标、未达标题归因 | ✅ 已完成 |
| [results/eval-20261019-111954.md](results/eval-20261019-111954.md) | 第 3 轮 30 题原始结果（N03 复判前） | ✅ 已记录 |
| [results/eval-20261019-112107.md](results/eval-20261019-112107.md) | N03 拒答复判 | ✅ 拒答 |
| [questions.doc-update-add.json](questions.doc-update-add.json) / [delete](questions.doc-update-delete.json) | P1-05 新增/删除文档测试题 | ✅ 已定义 |
| [results/eval-20261019-114025.md](results/eval-20261019-114025.md) | X-300 新增后 15 W 命中 | ✅ 命中 |
| [results/eval-20261019-114057.md](results/eval-20261019-114057.md) | X-300 删除后资料不足拒答 | ✅ 拒答 |
| [results/doc-update-test.md](results/doc-update-test.md) | P1-05 四项验证完整记录 | ✅ 通过 |
| [results/eval-20261019-114757.md](results/eval-20261019-114757.md) | Top-N 8 实验：22/25 来源支持 | ✅ 保留 8 |

## 评测脚本用法

```powershell
# 1. 只校验题集，不调用 API
python tests/eval.py --validate-only

# 2. 设置 Developer API key（只在本机，不入库）
$env:ANYTHINGLLM_API_KEY = Read-Host "AnythingLLM Developer API Key"

# 3. 运行全部题
python tests/eval.py

# 4. 只跑指定题号
python tests/eval.py --id SMOKE-01
```

脚本读取：

- `ANYTHINGLLM_BASE_URL`，默认 `http://127.0.0.1:3001/api/v1`
- `ANYTHINGLLM_WORKSPACE_SLUG`，默认 `enterprise-rag-kb`
- `ANYTHINGLLM_API_KEY`，必填；也可放在仓库根目录 `.env`（已忽略）

对设置了 `judge.expected_sources` 的题，脚本会先调用
`POST /workspace/{slug}/vector-search`，默认取 **Top-5**，记录检索结果并判断
预期来源是否在前 5 条中；然后再调用 chat 记录回答与引用。可用
`--retrieval-top-n 5` 调整。

## JSON 题目格式

```json
{
  "id": "Q01",
  "question": "NX-200 的扭矩量程和精度是多少？",
  "type": "单文档/表格数值",
  "mode": "query",
  "expected": "2–200 N·m；±2% FS，来源为产品说明书",
  "judge": {
    "must_include_all": ["2", "200", "2%"],
    "expected_sources": ["STAR-NX200"]
  }
}
```

判定规则：

- `must_refuse: true`：无答案题；未出现拒答标记则判“编造”；
- `must_include_all`：回答必须包含全部关键词；
- `must_include_any`：回答至少包含一个关键词；
- `expected_sources`：sources 的标题或片段必须命中至少一个来源标识；
- `expected_sources_all`：sources 必须同时命中全部来源标识（用于跨文档/版本对比题）；
- 其余情况判“未命中”；API/网络异常判“错误”。

## 通过标准（v0.2）

- 可回答问题 ≥ 80% 在检索结果前 5 条中找到相关依据；
- 可回答问题 ≥ 80% 的最终回答提供真实、足以支持回答的来源；
- 5 道无答案问题中 ≥ 4 道正确表明资料不足；
- 每题都有预期结果或明确判定规则，结果可复现；
- 不出现编造数值或虚构来源。
