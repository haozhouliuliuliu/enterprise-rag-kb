#!/usr/bin/env python3
"""Rebuild AnythingLLM workspace embeddings with the current splitter settings.

The script removes selected documents from the workspace (not from disk), then
re-adds them one by one so the current text splitter settings are applied.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:3001/api/v1"
WORKSPACE = "enterprise-rag-kb"
SECRET = pathlib.Path(r"C:\RAG库\secrets\anythingllm_api.key")


def call(method: str, path: str, key: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["delete", "add", "rebuild"], default="rebuild")
    parser.add_argument("--only", default="", help="comma separated manifest ids")
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    key = SECRET.read_text(encoding="utf-8").strip()
    manifest = json.loads((REPO_ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    wanted = {x.strip().upper() for x in args.only.split(",") if x.strip()}
    docs = [d for d in manifest if not wanted or d["id"].upper() in wanted]
    ws = call("GET", f"/workspace/{WORKSPACE}", key)
    workspace = (ws.get("workspace") or [{}])[0]
    existing = workspace.get("documents") or []
    by_name = {}
    for item in existing:
        docpath = str(item.get("docpath", ""))
        by_name[docpath] = item

    selected = []
    for doc in docs:
        name = pathlib.Path(doc["path"]).name
        matches = [p for p in by_name if name in p]
        if not matches:
            print(f"[WARN] {doc['id']} not in workspace: {name}")
            continue
        selected.append((doc, matches[0]))

    print(f"workspace documents={len(existing)} selected={len(selected)}")
    if not selected:
        return 1

    if args.mode in ("delete", "rebuild"):
        deletes = [p for _, p in selected]
        result = call("POST", f"/workspace/{WORKSPACE}/update-embeddings", key, {"deletes": deletes})
        print(f"[DELETE] {len(deletes)} document(s): {result.get('message', 'ok')}")
        time.sleep(1)

    if args.mode in ("add", "rebuild"):
        failures = 0
        for doc, docpath in selected:
            try:
                result = call("POST", f"/workspace/{WORKSPACE}/update-embeddings", key, {"adds": [docpath]})
                print(f"[ADD] {doc['id']} {docpath}")
                if not result.get("workspace"):
                    print(f"[WARN] {doc['id']} response has no workspace")
                time.sleep(args.delay)
            except Exception as exc:
                failures += 1
                print(f"[FAIL] {doc['id']}: {exc}", file=sys.stderr)
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
