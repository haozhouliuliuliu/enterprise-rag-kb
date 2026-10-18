#!/usr/bin/env python3
"""AnythingLLM RAG 评测通道（v0.2）。

读取 tests/questions.v0.2.json，逐题调用 AnythingLLM Developer API：
  POST {base_url}/workspace/{workspace}/vector-search   # 有 expected_sources 时
  POST {base_url}/workspace/{workspace}/chat
  Authorization: Bearer <ANYTHINGLLM_API_KEY>

记录 Top-5 检索结果、回答、引用来源与片段，并按题目的 judge 规则输出
命中 / 未命中 / 拒答 / 编造 / 错误 的汇总表，同时统计前 5 条检索命中。

安全约束：
  - API key 只从环境变量或仓库根目录的 .env 读取；
  - 不打印 key，不把 key 写入结果文件；
  - 结果文件只包含问题、回答、引用与判定。

依赖：仅 Python 3.9+ 标准库。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUESTIONS = Path(__file__).with_name("questions.v0.2.json")
DEFAULT_BASE_URL = "http://127.0.0.1:3001/api/v1"
DEFAULT_WORKSPACE = "enterprise-rag-kb"
DEFAULT_RESULT_DIR = Path(__file__).with_name("results")
DEFAULT_RETRIEVAL_TOP_N = 5

REFUSAL_MARKERS = (
    "资料中未找到",
    "资料未找到",
    "未找到相关资料",
    "没有找到相关",
    "未提及",
    "资料不足",
    "无法从资料",
    "无法回答",
    "没有相关信息",
    "不包含该信息",
    "not found",
    "insufficient information",
    "no relevant information",
)

VERDICT_HIT = "命中"
VERDICT_MISS = "未命中"
VERDICT_REFUSAL = "拒答"
VERDICT_FABRICATION = "编造"
VERDICT_ERROR = "错误"


class EvalError(RuntimeError):
    """评测过程中的可预期错误。"""


def load_dotenv(path: Path) -> dict[str, str]:
    """读取简单 KEY=VALUE 格式的 .env；不覆盖已有环境变量。"""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def config_value(name: str, dotenv: dict[str, str], default: str = "") -> str:
    return os.environ.get(name) or dotenv.get(name) or default


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def is_refusal(text: str) -> bool:
    normalized = normalize(text)
    return any(marker.lower() in normalized for marker in REFUSAL_MARKERS)


def source_title(source: dict[str, Any]) -> str:
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    for key in ("title", "docSource", "chunkSource", "source", "url"):
        value = source.get(key)
        if value:
            return str(value)
        value = metadata.get(key)
        if value:
            return str(value)
    return "(未命名来源)"


def source_snippet(source: dict[str, Any], limit: int = 240) -> str:
    for key in ("chunk", "text", "snippet", "content"):
        value = source.get(key)
        if value:
            return re.sub(r"\s+", " ", str(value)).strip()[:limit]
    return ""


def source_blob(sources: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for source in sources:
        parts.append(source_title(source))
        parts.append(source_snippet(source, limit=2000))
    return normalize(" ".join(parts))


def post_json(url: str, api_key: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise EvalError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise EvalError(f"无法连接 AnythingLLM API：{exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise EvalError("AnythingLLM 返回了非 JSON 响应") from exc


def judge(question: dict[str, Any], answer: str, sources: list[dict[str, Any]]) -> tuple[str, str]:
    """按题目 judge 规则返回 (判定, 说明)。"""
    rule = question.get("judge") or {}
    normalized_answer = normalize(answer)

    if rule.get("must_refuse"):
        if is_refusal(normalized_answer):
            return VERDICT_REFUSAL, "无答案题检测到拒答标记"
        return VERDICT_FABRICATION, "无答案题未表明资料不足"

    if is_refusal(normalized_answer):
        return VERDICT_REFUSAL, "可回答题意外触发拒答"

    must_all = [str(x) for x in (rule.get("must_include_all") or [])]
    if must_all:
        missing = [x for x in must_all if normalize(x) not in normalized_answer]
        if missing:
            return VERDICT_MISS, "缺少关键词：" + "、".join(missing)

    must_any = [str(x) for x in (rule.get("must_include_any") or [])]
    if must_any and not any(normalize(x) in normalized_answer for x in must_any):
        return VERDICT_MISS, "未出现任一预期关键词：" + "、".join(must_any)

    expected_sources = [str(x) for x in (rule.get("expected_sources") or [])]
    if expected_sources:
        blob = source_blob(sources)
        matched = [x for x in expected_sources if normalize(x) in blob]
        if not matched:
            return VERDICT_MISS, "引用来源未匹配：" + "、".join(expected_sources)
        return VERDICT_HIT, "关键词与引用来源匹配：" + "、".join(matched)

    return VERDICT_HIT, "满足判定规则"


def load_questions(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise EvalError(f"问题清单不存在：{path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    questions = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(questions, list) or not questions:
        raise EvalError("问题清单必须是非空数组，或包含 questions 数组")
    required = {"id", "question", "type", "judge"}
    for index, question in enumerate(questions, start=1):
        missing = required - set(question)
        if missing:
            raise EvalError(f"第 {index} 题缺少字段：{', '.join(sorted(missing))}")
        if not isinstance(question["judge"], dict):
            raise EvalError(f"第 {index} 题的 judge 必须是对象")
    return questions


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# AnythingLLM 评测结果")
    lines.append("")
    lines.append(f"- 生成时间：{report['generated_at']}")
    lines.append(f"- API：{report['base_url']}")
    lines.append(f"- Workspace：`{report['workspace']}`")
    lines.append("- 模型：qwen-plus / text-embedding-v4（阿里云百炼）")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("| --- | --- |")
    for key in (VERDICT_HIT, VERDICT_MISS, VERDICT_REFUSAL, VERDICT_FABRICATION, VERDICT_ERROR):
        lines.append(f"| {key} | {report['summary'].get(key, 0)} |")
    lines.append(f"| 总题数 | {report['summary'].get('total', 0)} |")
    lines.append(f"| 前 5 条检索可评估 | {report['summary'].get('retrieval_evaluable', 0)} |")
    lines.append(f"| 前 5 条检索命中 | {report['summary'].get('retrieval_hits', 0)} |")
    lines.append("")
    lines.append("## 逐题记录")
    lines.append("")
    lines.append("| ID | 类型 | 判定 | 前5检索 | 回答摘要 | 引用来源 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for item in report["results"]:
        answer = item["answer"].replace("|", "\\|").replace("\n", " ")[:300]
        sources = "<br>".join(
            f"{source_title(src)}" for src in item["sources"][:3]
        ) or "（无）"
        sources = sources.replace("|", "\\|")
        retrieval_hit = item.get("retrieval_hit")
        retrieval_label = "—" if retrieval_hit is None else ("✅" if retrieval_hit else "❌")
        lines.append(
            f"| {item['id']} | {item['type']} | {item['verdict']} | {retrieval_label} | {answer} | {sources} |"
        )
    lines.append("")
    lines.append("## 判定说明")
    lines.append("")
    for item in report["results"]:
        lines.append(f"### {item['id']}：{item['verdict']}")
        lines.append("")
        lines.append(f"- 规则：{item['reason']}")
        lines.append(f"- 问题：{item['question']}")
        lines.append(f"- 回答：{item['answer'] or '（空）'}")
        if item["sources"]:
            for source in item["sources"]:
                snippet = source_snippet(source, limit=300)
                lines.append(f"- 来源：{source_title(source)}；片段：{snippet or '（空）'}")
        else:
            lines.append("- 来源：（无）")
        if item.get("retrieval_hit") is None:
            lines.append("- 前 5 条检索：（本题未设置 expected_sources，未评估）")
        else:
            lines.append(f"- 前 5 条检索命中：{'是' if item['retrieval_hit'] else '否'}")
            for source in item.get("retrieval", [])[:5]:
                snippet = source_snippet(source, limit=180)
                lines.append(f"  - {source_title(source)}；片段：{snippet or '（空）'}")
        if item.get("retrieval_error"):
            lines.append(f"- 检索错误：{item['retrieval_error']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AnythingLLM RAG 评测通道")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retrieval-top-n", type=int, default=DEFAULT_RETRIEVAL_TOP_N)
    parser.add_argument("--id", action="append", dest="ids", help="只运行指定题号，可重复")
    parser.add_argument("--result-dir", type=Path, default=DEFAULT_RESULT_DIR)
    parser.add_argument("--validate-only", action="store_true", help="只校验题集，不调用 API")
    args = parser.parse_args(argv)

    try:
        questions = load_questions(args.questions)
    except (EvalError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    if args.ids:
        wanted = set(args.ids)
        questions = [q for q in questions if q["id"] in wanted]
        if not questions:
            print("[FAIL] 没有匹配的题号", file=sys.stderr)
            return 2

    print(f"[OK] 已加载 {len(questions)} 道题：{args.questions}")
    if args.validate_only:
        for question in questions:
            print(f"  - {question['id']} [{question['type']}] {question['question'][:80]}")
        return 0

    dotenv = load_dotenv(REPO_ROOT / ".env")
    api_key = config_value("ANYTHINGLLM_API_KEY", dotenv)
    base_url = (args.base_url or config_value("ANYTHINGLLM_BASE_URL", dotenv, DEFAULT_BASE_URL)).rstrip("/")
    workspace = args.workspace or config_value("ANYTHINGLLM_WORKSPACE_SLUG", dotenv, DEFAULT_WORKSPACE)

    if not api_key:
        print("[FAIL] 未找到 ANYTHINGLLM_API_KEY。请设置环境变量或在仓库根目录 .env 中配置。", file=sys.stderr)
        return 2

    chat_url = f"{base_url}/workspace/{workspace}/chat"
    search_url = f"{base_url}/workspace/{workspace}/vector-search"
    results: list[dict[str, Any]] = []
    for question in questions:
        expected_sources = [str(x) for x in (question.get("judge", {}).get("expected_sources") or [])]
        retrieval: list[dict[str, Any]] = []
        retrieval_hit: bool | None = None
        retrieval_error: str | None = None
        print(f"[RUN] {question['id']} ...", flush=True)

        if expected_sources:
            try:
                search = post_json(
                    search_url,
                    api_key,
                    {"query": question["question"], "topN": args.retrieval_top_n},
                    args.timeout,
                )
                retrieval = search.get("results") or []
                if not isinstance(retrieval, list):
                    retrieval = []
                retrieval_hit = any(normalize(x) in source_blob(retrieval) for x in expected_sources)
            except EvalError as exc:
                retrieval_error = str(exc)

        payload = {
            "message": question["question"],
            "mode": question.get("mode", "query"),
            "sessionId": question.get("sessionId"),
        }
        try:
            response = post_json(chat_url, api_key, payload, args.timeout)
            if response.get("error"):
                raise EvalError(str(response["error"]))
            answer = str(response.get("textResponse") or "")
            sources = response.get("sources") or []
            if not isinstance(sources, list):
                sources = []
            verdict, reason = judge(question, answer, sources)
        except EvalError as exc:
            answer, sources = "", []
            verdict, reason = VERDICT_ERROR, str(exc)

        results.append(
            {
                "id": question["id"],
                "type": question["type"],
                "question": question["question"],
                "expected": question.get("expected", ""),
                "answer": answer,
                "sources": sources,
                "retrieval": retrieval,
                "retrieval_hit": retrieval_hit,
                "retrieval_error": retrieval_error,
                "verdict": verdict,
                "reason": reason,
            }
        )
        print(f"[{verdict}] {question['id']}：{reason}")
        if retrieval_hit is not None:
            print(f"      前5检索：{'命中' if retrieval_hit else '未命中'}（{len(retrieval)} 条）")
        if retrieval_error:
            print(f"      检索错误：{retrieval_error}")
        for source in sources[:3]:
            print(f"      来源：{source_title(source)}")

    summary = Counter(item["verdict"] for item in results)
    summary["total"] = len(results)
    summary["retrieval_evaluable"] = sum(
        1 for item in results if item.get("retrieval_hit") is not None
    )
    summary["retrieval_hits"] = sum(
        1 for item in results if item.get("retrieval_hit") is True
    )
    generated_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    report = {
        "generated_at": generated_at,
        "base_url": base_url,
        "workspace": workspace,
        "summary": dict(summary),
        "results": results,
    }

    args.result_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = args.result_dir / f"eval-{stamp}.json"
    md_path = args.result_dir / f"eval-{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, report)

    print("\n| 判定 | 数量 |")
    print("| --- | --- |")
    for key in (VERDICT_HIT, VERDICT_MISS, VERDICT_REFUSAL, VERDICT_FABRICATION, VERDICT_ERROR):
        print(f"| {key} | {summary.get(key, 0)} |")
    print(f"| 总题数 | {summary['total']} |")
    print(f"| 前 5 条检索可评估 | {summary['retrieval_evaluable']} |")
    print(f"| 前 5 条检索命中 | {summary['retrieval_hits']} |")
    print(f"\n结果已写入：{json_path}")
    print(f"可读报告：{md_path}")
    return 0 if summary.get(VERDICT_ERROR, 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
