#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from typing import Any


ALLOWED_STATUS = {"pass", "fail", "blocked"}


def _to_list(value: Any) -> list[str]:
    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _normalize_status(payload: dict[str, Any]) -> tuple[str, str]:
    candidates = [
        payload.get("revalidation_status"),
        payload.get("status"),
        payload.get("result"),
        payload.get("outcome"),
    ]

    raw = ""
    for item in candidates:
        if item is not None and str(item).strip():
            raw = str(item).strip().lower()
            break

    if not raw:
        return "blocked", "missing status field"

    mapping = {
        "ok": "pass",
        "passed": "pass",
        "success": "pass",
        "pass": "pass",
        "failed": "fail",
        "failure": "fail",
        "error": "fail",
        "fail": "fail",
        "blocked": "blocked",
    }
    normalized = mapping.get(raw, raw)
    if normalized in ALLOWED_STATUS:
        return normalized, "normalized"
    return "blocked", f"unsupported status value: {raw}"


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    status, status_reason = _normalize_status(payload)

    test_evidence = _to_list(payload.get("test_evidence"))
    run_evidence = _to_list(payload.get("run_evidence"))
    if not test_evidence:
        test_evidence = _to_list(payload.get("tests"))
    if not run_evidence:
        run_evidence = _to_list(payload.get("runs"))

    summary = str(payload.get("regression_summary", "")).strip()
    if not summary:
        summary = str(payload.get("summary", "")).strip()
    if not summary:
        summary = "adapter normalized payload"

    return {
        "revalidation_status": status,
        "test_evidence": test_evidence,
        "run_evidence": run_evidence,
        "regression_summary": summary,
        "adapter_metadata": {
            "adapter_name": "tdd_cli_adapter_template",
            "status_reason": status_reason,
        },
    }


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        normalized = {
            "revalidation_status": "blocked",
            "test_evidence": [],
            "run_evidence": [],
            "regression_summary": "empty stdin payload",
            "adapter_metadata": {
                "adapter_name": "tdd_cli_adapter_template",
                "status_reason": "empty stdin",
            },
        }
        print(json.dumps(normalized, ensure_ascii=False))
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        normalized = {
            "revalidation_status": "blocked",
            "test_evidence": [],
            "run_evidence": [],
            "regression_summary": "invalid JSON payload",
            "adapter_metadata": {
                "adapter_name": "tdd_cli_adapter_template",
                "status_reason": f"json decode error: {exc.msg}",
            },
        }
        print(json.dumps(normalized, ensure_ascii=False))
        return 0

    if not isinstance(payload, dict):
        normalized = {
            "revalidation_status": "blocked",
            "test_evidence": [],
            "run_evidence": [],
            "regression_summary": "payload must be a JSON object",
            "adapter_metadata": {
                "adapter_name": "tdd_cli_adapter_template",
                "status_reason": "non-object payload",
            },
        }
        print(json.dumps(normalized, ensure_ascii=False))
        return 0

    normalized = normalize_payload(payload)
    print(json.dumps(normalized, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
