# 测试

本目录用于存放 RAG 检索与回答的测试问题、预期依据、实际结果与可复现评测脚本。

## 文件

| 文件 | 说明 | 状态 |
| --- | --- | --- |
| [questions.v0.1.md](questions.v0.1.md) | 旧版 14 条 Markdown 问题，保留作资料制作参考 | ✅ 已定义 |
| [questions.v0.2.json](questions.v0.2.json) | 评测脚本读取的 JSON 题集；当前含 1 道 API 连通性占位题 | 🔄 骨架 |
| [eval.py](eval.py) | AnythingLLM Developer API 评测脚本（仅标准库） | ✅ 已就绪 |
| [results/template.md](results/template.md) | 人工测试记录模板（旧版） | ✅ 已定义 |
| `results/eval-*.json/.md` | 脚本生成的结构化结果与可读报告 | 🔄 运行后生成 |

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
- 其余情况判“未命中”；API/网络异常判“错误”。

## 通过标准（v0.2）

- 可回答问题 ≥ 80% 在检索结果前 5 条中找到相关依据；
- 可回答问题 ≥ 80% 的最终回答提供真实、足以支持回答的来源；
- 5 道无答案问题中 ≥ 4 道正确表明资料不足；
- 每题都有预期结果或明确判定规则，结果可复现；
- 不出现编造数值或虚构来源。
