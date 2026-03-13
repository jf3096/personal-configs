#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
    yaml = None


DEFAULT_RUN_ROOT = "temp/ralph-loop-runs"
ITERATION_REPORT_OPEN = "<iteration_report>"
ITERATION_REPORT_CLOSE = "</iteration_report>"
CASE_REPORT_OPEN = "<case_report>"
CASE_REPORT_CLOSE = "</case_report>"
ITERATION_REPORT_REQUIRED_KEYS: tuple[str, ...] = (
    "changes_before",
    "changes_after",
    "optimization_strategy",
    "score_before",
    "score_after",
    "score_delta",
    "next_iteration_plan",
)
SCORE_VALUE_PATTERN = re.compile(r"^\s*\d+\s*/\s*100\s*$")
CASE_TYPES = {"positive", "negative"}


def load_yaml_file(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required for todo mode; install pyyaml first")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"yaml root must be mapping: {path}")
    return payload


def _ensure_case_fields(case: dict[str, Any], index: int) -> None:
    for field in ("id", "title", "type", "spec_file"):
        if not case.get(field):
            raise ValueError(f"missing required field: {field} (case #{index})")
    case_type = str(case["type"]).strip().lower()
    if case_type not in CASE_TYPES:
        raise ValueError(f"invalid case type for {case['id']}: {case_type}")


def load_catalog(cases_root: Path) -> dict[str, Any]:
    catalog_path = cases_root / "catalog.yaml"
    payload = load_yaml_file(catalog_path)
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("catalog cases must be a non-empty list")

    normalized_cases: list[dict[str, Any]] = []
    cases_by_id: dict[str, dict[str, Any]] = {}
    for index, raw_case in enumerate(cases, start=1):
        if not isinstance(raw_case, dict):
            raise ValueError(f"case entry must be mapping (case #{index})")
        _ensure_case_fields(raw_case, index)

        case_id = str(raw_case["id"]).strip()
        if case_id in cases_by_id:
            raise ValueError(f"duplicate case id: {case_id}")
        spec_file = Path(str(raw_case["spec_file"]).strip())
        spec_path = (cases_root / spec_file).resolve()
        if not spec_path.exists():
            raise ValueError(f"spec_file not found for case {case_id}: {spec_path}")

        case_type = str(raw_case["type"]).strip().lower()
        priority = str(raw_case.get("priority", "medium")).strip().lower()
        enabled = bool(raw_case.get("enabled", True))
        quality_checks = raw_case.get("quality_checks") or []
        if quality_checks and not isinstance(quality_checks, list):
            raise ValueError(f"quality_checks must be list for case {case_id}")
        role = str(raw_case.get("role", "optimize")).strip().lower()
        if role not in {"optimize", "holdout"}:
            raise ValueError(f"invalid role for case {case_id}: {role}")

        normalized = {
            "id": case_id,
            "title": str(raw_case["title"]).strip(),
            "type": case_type,
            "priority": priority,
            "tags": raw_case.get("tags") or [],
            "spec_file": str(spec_file),
            "spec_path": str(spec_path),
            "enabled": enabled,
            "quality_checks": [str(item) for item in quality_checks],
            "role": role,
        }
        normalized_cases.append(normalized)
        cases_by_id[case_id] = normalized

    return {
        "path": str(catalog_path.resolve()),
        "version": payload.get("version", 1),
        "suite_name": payload.get("suite_name", "default"),
        "cases": normalized_cases,
        "cases_by_id": cases_by_id,
    }


def _coerce_int(value: Any, default: int) -> int:
    if value is None:
        return default
    return int(value)


def _default_completion_policy(payload: dict[str, Any]) -> dict[str, Any]:
    completion = payload.get("completion_policy") or {}
    if not isinstance(completion, dict):
        raise ValueError("completion_policy must be a mapping")
    return {
        "mode": completion.get("mode") or "all_enabled_cases_passed",
        "completion_promise": completion.get("completion_promise"),
    }


def load_todo_plan(todo_file: Path, catalog: dict[str, Any]) -> dict[str, Any]:
    payload = load_yaml_file(todo_file)
    todo_id = str(payload.get("todo_id") or "").strip()
    if not todo_id:
        raise ValueError("todo_id is required")
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")

    loop_rounds = _coerce_int(payload.get("loop_rounds"), 1)
    continue_on_failure = bool(payload.get("continue_on_failure", True))
    selection_policy = str(payload.get("selection_policy", "highest_priority_pending")).strip()
    if selection_policy not in {"highest_priority_pending", "explicit_order"}:
        raise ValueError(f"invalid selection_policy: {selection_policy}")
    completion_policy = _default_completion_policy(payload)
    progress_log = str(payload.get("progress_log") or "todo/progress.txt")

    normalized_items: list[dict[str, Any]] = []
    for index, raw_item in enumerate(items, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"todo item must be mapping (item #{index})")
        case_id = str(raw_item.get("case_id") or "").strip()
        if not case_id:
            raise ValueError(f"todo item missing case_id (item #{index})")
        case_meta = catalog["cases_by_id"].get(case_id)
        if case_meta is None:
            raise ValueError(f"unknown case_id: {case_id}")

        case_type = case_meta["type"]
        default_stability = 3 if case_type == "positive" else 1
        normalized_items.append(
            {
                "case_id": case_id,
                "enabled": bool(raw_item.get("enabled", True)),
                "rounds": _coerce_int(raw_item.get("rounds"), loop_rounds),
                "stability_runs": _coerce_int(raw_item.get("stability_runs"), default_stability),
                "stability_pass_threshold": _coerce_int(
                    raw_item.get("stability_pass_threshold"), default_stability
                ),
                "max_attempts": _coerce_int(raw_item.get("max_attempts"), 0),
                "priority": case_meta.get("priority", "medium"),
                "type": case_type,
                "role": case_meta.get("role", "optimize"),
                "spec_path": case_meta.get("spec_path"),
                "quality_checks": list(case_meta.get("quality_checks", [])),
            }
        )

    return {
        "path": str(todo_file.resolve()),
        "todo_id": todo_id,
        "loop_rounds": loop_rounds,
        "continue_on_failure": continue_on_failure,
        "selection_policy": selection_policy,
        "completion_policy": completion_policy,
        "progress_log": progress_log,
        "items": normalized_items,
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sanitize_slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "run"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def detect_completion(last_message: str, promise: str | None) -> bool:
    if not promise:
        return False
    stripped = last_message.strip()
    if stripped == promise:
        return True
    pattern = re.compile(r"<promise>\s*" + re.escape(promise) + r"\s*</promise>", re.DOTALL)
    return bool(pattern.search(last_message))


def build_iteration_prompt(
    *,
    base_prompt: str,
    iteration: int,
    completion_promise: str | None,
    require_iteration_report: bool,
) -> str:
    if not require_iteration_report:
        return base_prompt

    promise_hint = (
        f"If and only if completion is truly satisfied, output exactly `<promise>{completion_promise}</promise>` "
        "after the report block."
        if completion_promise
        else "If completion condition is satisfied, output the completion promise after the report block."
    )
    contract = f"""
---
Iteration Reporting Contract (required for every iteration):
- You MUST include exactly one `{ITERATION_REPORT_OPEN}...{ITERATION_REPORT_CLOSE}` block in your final message.
- Use the exact keys below (key: value format), and keep scores on a 0-100 scale:

{ITERATION_REPORT_OPEN}
iteration: {iteration}
changes_before: <what the workspace looked like before this iteration>
changes_after: <what changed after this iteration>
optimization_strategy: <why this iteration improves outcomes>
score_before: <number>/100
score_after: <number>/100
score_delta: <after-before, include sign>
next_iteration_plan: <next focus or reason to stop>
{ITERATION_REPORT_CLOSE}

{promise_hint}
- If this report contract is missing or malformed, do NOT output completion promise.
""".strip()
    return f"{base_prompt.rstrip()}\n\n{contract}\n"


def extract_iteration_report(last_message: str) -> str:
    pattern = re.compile(
        re.escape(ITERATION_REPORT_OPEN) + r"\s*(.*?)\s*" + re.escape(ITERATION_REPORT_CLOSE),
        re.DOTALL,
    )
    matches = list(pattern.finditer(last_message))
    if not matches:
        return ""
    return matches[-1].group(1).strip()


def extract_case_report(last_message: str) -> str:
    pattern = re.compile(
        re.escape(CASE_REPORT_OPEN) + r"\s*(.*?)\s*" + re.escape(CASE_REPORT_CLOSE),
        re.DOTALL,
    )
    matches = list(pattern.finditer(last_message))
    if not matches:
        return ""
    return matches[-1].group(1).strip()


def extract_report_key_value(report_text: str, key: str) -> str | None:
    match = re.search(rf"(?mi)^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", report_text)
    if not match:
        return None
    return match.group(1).strip()


def parse_case_report(last_message: str) -> dict[str, Any]:
    report_text = extract_case_report(last_message)
    if not report_text:
        raise ValueError("missing case_report block")

    required_keys = (
        "case_id",
        "verdict",
        "expectation_check",
        "failure_signal_check",
        "evidence_refs",
        "confidence",
        "next_action",
    )
    parsed: dict[str, Any] = {}
    missing: list[str] = []
    for key in required_keys:
        value = extract_report_key_value(report_text, key)
        if value is None:
            missing.append(key)
            continue
        parsed[key] = value
    if missing:
        raise ValueError(f"missing case_report keys: {','.join(missing)}")

    evidence_raw = str(parsed["evidence_refs"])
    parsed["evidence_refs"] = [item.strip() for item in evidence_raw.split(",") if item.strip()]
    parsed["verdict"] = str(parsed["verdict"]).strip().lower()
    return parsed


def _parse_signal_token(value: str) -> str:
    token = str(value).strip().lower().split()[0]
    if token in {"met", "pass", "passed", "satisfied", "yes", "true"}:
        return "met"
    if token in {"not_met", "failed", "no", "false"}:
        return "not_met"
    if token in {"hit", "triggered", "matched"}:
        return "hit"
    if token in {"not_hit", "none", "missed"}:
        return "not_hit"
    return token


def check_evidence_refs(evidence_refs: list[str], workspace: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    root = workspace.resolve()
    if not evidence_refs:
        return False, ["evidence_missing"]

    for ref in evidence_refs:
        path = Path(ref).expanduser()
        if not path.is_absolute():
            path = (root / path).resolve()
        else:
            path = path.resolve()
        try:
            path.relative_to(root)
        except ValueError:
            issues.append("evidence_outside_workspace")
            continue
        if not path.exists():
            issues.append("evidence_missing")
            continue
        if path.is_file() and path.stat().st_size == 0:
            issues.append("evidence_empty")
    return len(issues) == 0, sorted(set(issues))


def validate_case_result(report: dict[str, Any], case_type: str, workspace: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    normalized_case_type = case_type.strip().lower()
    verdict = str(report.get("verdict", "")).strip().lower()
    expectation_token = _parse_signal_token(str(report.get("expectation_check", "")))
    failure_token = _parse_signal_token(str(report.get("failure_signal_check", "")))

    if normalized_case_type == "positive":
        if verdict != "pass":
            issues.append("positive_case_requires_verdict_pass")
        if expectation_token != "met":
            issues.append("positive_case_expectation_not_met")
        if failure_token != "not_hit":
            issues.append("positive_case_failure_signal_must_be_not_hit")
    elif normalized_case_type == "negative":
        if verdict != "pass":
            issues.append("negative_case_requires_verdict_pass")
        if failure_token != "hit":
            issues.append("negative_case_requires_failure_hit")
    else:
        issues.append("unsupported_case_type")

    evidence_ok, evidence_issues = check_evidence_refs(list(report.get("evidence_refs", [])), workspace)
    if not evidence_ok:
        issues.extend(evidence_issues)

    return len(issues) == 0, sorted(set(issues))


def validate_iteration_report(report_text: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not report_text.strip():
        return False, ["missing_iteration_report_block"]

    for key in ITERATION_REPORT_REQUIRED_KEYS:
        if extract_report_key_value(report_text, key) is None:
            issues.append(f"missing_key:{key}")

    for score_key in ("score_before", "score_after"):
        value = extract_report_key_value(report_text, score_key)
        if value is None:
            continue
        if not SCORE_VALUE_PATTERN.match(value):
            issues.append(f"invalid_score_format:{score_key}")

    score_delta = extract_report_key_value(report_text, "score_delta")
    if score_delta is not None and not re.search(r"[+-]?\d+", score_delta):
        issues.append("invalid_score_delta")

    return len(issues) == 0, issues


def parse_extra_args(values: list[str]) -> list[str]:
    parsed: list[str] = []
    for value in values:
        parsed.extend(shlex.split(value))
    return parsed


def resolve_workspace(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def resolve_run_root(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def find_git_dir(path: Path) -> bool:
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists():
            return True
    return False


@dataclass
class RunFiles:
    run_dir: Path
    iterations_dir: Path
    state_file: Path
    prompt_file: Path
    summary_file: Path
    cancel_file: Path


@dataclass
class TodoRunFiles:
    run_dir: Path
    items_dir: Path
    state_file: Path
    summary_file: Path
    scoreboard_file: Path
    snapshot_file: Path
    progress_file: Path
    cancel_file: Path


def build_run_files(run_dir: Path) -> RunFiles:
    return RunFiles(
        run_dir=run_dir,
        iterations_dir=run_dir / "iterations",
        state_file=run_dir / "state.json",
        prompt_file=run_dir / "prompt.md",
        summary_file=run_dir / "summary.md",
        cancel_file=run_dir / "cancel.request",
    )


def build_todo_run_files(run_dir: Path) -> TodoRunFiles:
    return TodoRunFiles(
        run_dir=run_dir,
        items_dir=run_dir / "items",
        state_file=run_dir / "state.json",
        summary_file=run_dir / "summary.md",
        scoreboard_file=run_dir / "scoreboard.json",
        snapshot_file=run_dir / "todo.snapshot.yaml",
        progress_file=run_dir / "progress.txt",
        cancel_file=run_dir / "cancel.request",
    )


def initialize_state(args: argparse.Namespace, prompt_text: str, run_dir: Path, workspace: Path) -> dict[str, Any]:
    extra_args = parse_extra_args(args.codex_arg or [])
    model = getattr(args, "model", None)
    max_iterations = int(args.max_iterations)
    state = {
        "version": 1,
        "status": "running",
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "workspace": str(workspace),
        "run_dir": str(run_dir),
        "prompt_file": "prompt.md",
        "iteration": 0,
        "max_iterations": max_iterations,
        "completion_promise": args.completion_promise,
        "require_iteration_report": not bool(args.disable_iteration_report),
        "iteration_report_required_keys": list(ITERATION_REPORT_REQUIRED_KEYS),
        "model": model,
        "sandbox": args.sandbox,
        "skip_git_repo_check": bool(args.skip_git_repo_check),
        "codex_args": extra_args,
        "history": [],
        "last_message_file": None,
        "last_stdout_file": None,
        "last_stderr_file": None,
        "last_exit_code": None,
        "last_stop_reason": None,
        "prompt_preview": prompt_text[:160],
    }
    return state


def initialize_todo_scoreboard(plan: dict[str, Any]) -> dict[str, Any]:
    cases: dict[str, Any] = {}
    for item in plan["items"]:
        case_id = item["case_id"]
        cases[case_id] = {
            "case_id": case_id,
            "type": item["type"],
            "priority": item.get("priority"),
            "enabled": item["enabled"],
            "status": "pending",
            "attempts": 0,
            "passes": 0,
            "fails": 0,
            "stability_runs": item["stability_runs"],
            "stability_pass_threshold": item["stability_pass_threshold"],
            "last_issues": [],
            "history": [],
        }
    return {"version": 1, "cases": cases}


def initialize_todo_state(
    args: argparse.Namespace,
    run_dir: Path,
    workspace: Path,
    plan: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    return {
        "version": 1,
        "mode": "todo",
        "status": "running",
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "workspace": str(workspace),
        "run_dir": str(run_dir),
        "todo_file": str(Path(args.todo_file).expanduser().resolve()),
        "cases_root": str(Path(args.cases_root).expanduser().resolve()),
        "catalog_file": catalog["path"],
        "todo_id": plan["todo_id"],
        "loop_rounds": int(plan["loop_rounds"]),
        "current_round": 0,
        "continue_on_failure": bool(plan["continue_on_failure"]),
        "selection_policy": plan["selection_policy"],
        "completion_policy": plan["completion_policy"],
        "items": plan["items"],
        "model": getattr(args, "model", None),
        "sandbox": getattr(args, "sandbox", "workspace-write"),
        "skip_git_repo_check": bool(getattr(args, "skip_git_repo_check", False)),
        "codex_args": parse_extra_args(getattr(args, "codex_arg", []) or []),
        "dry_run": bool(getattr(args, "dry_run", False)),
        "last_stop_reason": None,
        "exit_reason": None,
    }


def write_summary(files: RunFiles, state: dict[str, Any]) -> None:
    lines = [
        "# Ralph Loop Run Summary",
        "",
        f"- status: {state['status']}",
        f"- workspace: {state['workspace']}",
        f"- run_dir: {state['run_dir']}",
        f"- iteration: {state['iteration']}",
        f"- max_iterations: {state['max_iterations']}",
        f"- completion_promise: {state['completion_promise'] or 'none'}",
        f"- require_iteration_report: {state.get('require_iteration_report', False)}",
        f"- started_at: {state['started_at']}",
        f"- updated_at: {state['updated_at']}",
        f"- last_exit_code: {state['last_exit_code']}",
        f"- last_stop_reason: {state['last_stop_reason']}",
        "",
        "## Artifacts",
        "",
        f"- prompt: {files.prompt_file}",
        f"- state: {files.state_file}",
        f"- iterations: {files.iterations_dir}",
    ]
    if state["history"]:
        lines.extend(["", "## Iterations", ""])
        for item in state["history"]:
            lines.append(
                f"- iteration {item['iteration']}: exit={item['exit_code']} promise={item.get('promise_detected')} completion={item['completion_detected']} report_valid={item.get('report_valid')} stdout={item['stdout_file']} stderr={item['stderr_file']} report={item.get('report_file')}"
            )
            if item.get("report_issues"):
                lines.append(f"  report_issues={','.join(item['report_issues'])}")
    files.summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_todo_summary(files: TodoRunFiles, state: dict[str, Any], scoreboard: dict[str, Any]) -> None:
    lines = [
        "# Ralph Todo Run Summary",
        "",
        f"- status: {state['status']}",
        f"- workspace: {state['workspace']}",
        f"- run_dir: {state['run_dir']}",
        f"- todo_id: {state['todo_id']}",
        f"- loop_rounds: {state['loop_rounds']}",
        f"- current_round: {state['current_round']}",
        f"- continue_on_failure: {state['continue_on_failure']}",
        f"- selection_policy: {state['selection_policy']}",
        f"- completion_policy_mode: {state['completion_policy']['mode']}",
        f"- completion_promise: {state['completion_policy'].get('completion_promise') or 'none'}",
        f"- started_at: {state['started_at']}",
        f"- updated_at: {state['updated_at']}",
        f"- last_stop_reason: {state.get('last_stop_reason')}",
        f"- exit_reason: {state.get('exit_reason')}",
        "",
        "## Artifacts",
        "",
        f"- state: {files.state_file}",
        f"- scoreboard: {files.scoreboard_file}",
        f"- progress: {files.progress_file}",
        f"- items: {files.items_dir}",
        "",
        "## Cases",
        "",
    ]
    for case in scoreboard.get("cases", {}).values():
        lines.append(
            f"- {case['case_id']}: status={case['status']} attempts={case['attempts']} passes={case['passes']} fails={case['fails']}"
        )
    files.summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_state(files: RunFiles, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    dump_json(files.state_file, state)
    write_summary(files, state)


def save_todo_state(files: TodoRunFiles, state: dict[str, Any], scoreboard: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    dump_json(files.state_file, state)
    dump_json(files.scoreboard_file, scoreboard)
    write_todo_summary(files, state, scoreboard)


def load_state(run_dir: Path) -> tuple[RunFiles, dict[str, Any], str]:
    files = build_run_files(run_dir)
    if not files.state_file.exists():
        raise FileNotFoundError(f"state file not found: {files.state_file}")
    state = json.loads(load_text(files.state_file))
    prompt_text = load_text(files.prompt_file)
    return files, state, prompt_text


def load_todo_state(run_dir: Path) -> tuple[TodoRunFiles, dict[str, Any], dict[str, Any]]:
    files = build_todo_run_files(run_dir)
    if not files.state_file.exists():
        raise FileNotFoundError(f"todo state file not found: {files.state_file}")
    state = json.loads(load_text(files.state_file))
    scoreboard = json.loads(load_text(files.scoreboard_file)) if files.scoreboard_file.exists() else {"cases": {}}
    return files, state, scoreboard


def build_codex_command(
    *,
    workspace: Path,
    last_message_file: Path,
    sandbox: str,
    model: str | None,
    skip_git_repo_check: bool,
    codex_args: list[str],
) -> list[str]:
    cmd = [
        "codex",
        "exec",
        "--cd",
        str(workspace),
        "--output-last-message",
        str(last_message_file),
        "--color",
        "never",
        "--sandbox",
        sandbox,
    ]
    if model:
        cmd.extend(["--model", model])
    if skip_git_repo_check or not find_git_dir(workspace):
        cmd.append("--skip-git-repo-check")
    cmd.extend(codex_args)
    cmd.append("-")
    return cmd


def append_progress(progress_file: Path, message: str) -> None:
    ensure_dir(progress_file.parent)
    with progress_file.open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip() + "\n")


def todo_completion_reached(state: dict[str, Any], scoreboard: dict[str, Any]) -> bool:
    mode = state["completion_policy"].get("mode", "all_enabled_cases_passed")
    if mode != "all_enabled_cases_passed":
        return False
    for item in state["items"]:
        if not item["enabled"]:
            continue
        case = scoreboard["cases"].get(item["case_id"])
        if not case:
            return False
        if case["status"] != "passed":
            return False
    return True


def _priority_value(value: str | None) -> int:
    normalized = (value or "medium").strip().lower()
    return {"high": 0, "medium": 1, "low": 2}.get(normalized, 1)


def select_next_case(
    items: list[dict[str, Any]], scoreboard: dict[str, Any], selection_policy: str
) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for item in items:
        if not item.get("enabled", True):
            continue
        case = scoreboard["cases"].get(item["case_id"])
        if not case:
            continue
        if case.get("status") in {"passed", "failed"}:
            continue
        candidates.append(item)

    if not candidates:
        return None
    if selection_policy == "explicit_order":
        return candidates[0]
    return sorted(candidates, key=lambda item: (_priority_value(item.get("priority")), item["case_id"]))[0]


def compute_stability_status(
    *,
    case_type: str,
    recent_results: list[bool],
    stability_runs: int,
    stability_pass_threshold: int,
) -> str:
    _ = case_type
    if stability_runs <= 0:
        stability_runs = 1
    window = recent_results[-stability_runs:]
    if len(window) < stability_runs:
        return "pending"
    pass_count = sum(1 for result in window if result)
    if pass_count >= stability_pass_threshold:
        return "passed"
    return "pending"


def run_quality_checks(
    *, commands: list[str], workspace: Path, logs_dir: Path
) -> tuple[bool, list[dict[str, Any]]]:
    ensure_dir(logs_dir)
    results: list[dict[str, Any]] = []
    overall_ok = True
    for index, command in enumerate(commands, start=1):
        stdout_file = logs_dir / f"quality-check-{index:03d}.stdout.log"
        stderr_file = logs_dir / f"quality-check-{index:03d}.stderr.log"
        with stdout_file.open("w", encoding="utf-8") as stdout_handle, stderr_file.open(
            "w", encoding="utf-8"
        ) as stderr_handle:
            proc = subprocess.run(
                ["bash", "-lc", command],
                cwd=str(workspace),
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                check=False,
            )
        result_item = {
            "command": command,
            "exit_code": proc.returncode,
            "stdout_file": str(stdout_file),
            "stderr_file": str(stderr_file),
        }
        if proc.returncode != 0:
            overall_ok = False
        results.append(result_item)
    return overall_ok, results


def build_case_prompt(case_spec: str, case_id: str, case_type: str) -> str:
    contract = f"""
---
Case Reporting Contract (required):
- You MUST include exactly one `{CASE_REPORT_OPEN}...{CASE_REPORT_CLOSE}` block in your final message.
- Use strict keys and token values for machine validation:
  - `verdict`: pass|fail
  - `expectation_check`: met|not_met
  - `failure_signal_check`: hit|not_hit
  - `evidence_refs`: comma-separated file paths inside workspace

{CASE_REPORT_OPEN}
case_id: {case_id}
verdict: <pass|fail>
expectation_check: <met|not_met>
failure_signal_check: <hit|not_hit>
evidence_refs: <path1,path2>
confidence: <0-100>
next_action: <continue|stop|retry>
{CASE_REPORT_CLOSE}

Case type: {case_type}
""".strip()
    return f"{case_spec.rstrip()}\n\n{contract}\n"


def run_case_attempt(
    *,
    case_id: str,
    case_type: str,
    case_spec_path: Path,
    attempt_dir: Path,
    workspace: Path,
    sandbox: str,
    model: str | None,
    skip_git_repo_check: bool,
    codex_args: list[str],
    quality_checks: list[str],
) -> dict[str, Any]:
    ensure_dir(attempt_dir)
    prompt_snapshot = attempt_dir / "prompt.md"
    stdout_file = attempt_dir / "stdout.log"
    stderr_file = attempt_dir / "stderr.log"
    message_file = attempt_dir / "last-message.txt"
    report_file = attempt_dir / "report.md"
    quality_logs_dir = attempt_dir / "quality"

    case_spec = load_text(case_spec_path)
    prompt = build_case_prompt(case_spec, case_id, case_type)
    prompt_snapshot.write_text(prompt, encoding="utf-8")

    cmd = build_codex_command(
        workspace=workspace,
        last_message_file=message_file,
        sandbox=sandbox,
        model=model,
        skip_git_repo_check=skip_git_repo_check,
        codex_args=codex_args,
    )
    with stdout_file.open("w", encoding="utf-8") as stdout_handle, stderr_file.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            stdout=stdout_handle,
            stderr=stderr_handle,
            cwd=str(workspace),
            check=False,
        )

    issues: list[str] = []
    report: dict[str, Any] | None = None
    last_message = message_file.read_text(encoding="utf-8") if message_file.exists() else ""
    try:
        report = parse_case_report(last_message)
    except ValueError as error:
        issues.append(str(error))
    if report is not None:
        report_file.write_text(extract_case_report(last_message) + "\n", encoding="utf-8")
        semantic_ok, semantic_issues = validate_case_result(report, case_type, workspace)
        if not semantic_ok:
            issues.extend(semantic_issues)
    else:
        report_file.write_text("# missing case_report block\n", encoding="utf-8")

    quality_results: list[dict[str, Any]] = []
    quality_ok = True
    if quality_checks:
        quality_ok, quality_results = run_quality_checks(commands=quality_checks, workspace=workspace, logs_dir=quality_logs_dir)
        if not quality_ok:
            issues.append("quality_checks_failed")

    passed = result.returncode == 0 and report is not None and len(issues) == 0 and quality_ok
    return {
        "passed": passed,
        "issues": sorted(set(issues)),
        "exit_code": result.returncode,
        "stdout_file": str(stdout_file),
        "stderr_file": str(stderr_file),
        "last_message_file": str(message_file),
        "report_file": str(report_file),
        "quality_results": quality_results,
    }


def run_todo_loop(
    files: TodoRunFiles,
    state: dict[str, Any],
    scoreboard: dict[str, Any],
    *,
    dry_run: bool = False,
) -> int:
    ensure_dir(files.items_dir)
    ensure_dir(files.run_dir)
    ensure_dir(files.progress_file.parent)
    if not files.progress_file.exists():
        files.progress_file.write_text("# Ralph Todo Progress Log\n", encoding="utf-8")

    if dry_run:
        state["status"] = "completed"
        state["current_round"] = 0
        state["last_stop_reason"] = "dry_run"
        state["exit_reason"] = "dry_run"
        append_progress(files.progress_file, f"## {utc_now()} - dry run initialized")
        save_todo_state(files, state, scoreboard)
        return 0

    workspace = Path(state["workspace"])
    while True:
        if files.cancel_file.exists():
            state["status"] = "cancelled"
            state["last_stop_reason"] = "cancel_requested"
            state["exit_reason"] = "cancel_requested"
            save_todo_state(files, state, scoreboard)
            return 0

        if todo_completion_reached(state, scoreboard):
            state["status"] = "completed"
            state["last_stop_reason"] = "all_cases_passed"
            state["exit_reason"] = "all_cases_passed"
            save_todo_state(files, state, scoreboard)
            return 0

        if state["loop_rounds"] > 0 and state["current_round"] >= state["loop_rounds"]:
            state["status"] = "max_rounds_reached"
            state["last_stop_reason"] = "max_rounds_reached"
            state["exit_reason"] = "max_rounds_reached"
            save_todo_state(files, state, scoreboard)
            return 0

        state["current_round"] = int(state["current_round"]) + 1
        append_progress(files.progress_file, f"## {utc_now()} - round {state['current_round']}")

        pending_items = [
            item
            for item in state["items"]
            if item.get("enabled", True) and scoreboard["cases"][item["case_id"]]["status"] not in {"passed", "failed"}
        ]
        if state["selection_policy"] == "highest_priority_pending":
            pending_items = sorted(pending_items, key=lambda item: (_priority_value(item.get("priority")), item["case_id"]))

        for item in pending_items:
            selected = select_next_case([item], scoreboard, "explicit_order")
            if selected is None:
                continue
            case_id = selected["case_id"]
            case_score = scoreboard["cases"][case_id]
            case_score["attempts"] += 1
            attempt_dir = files.items_dir / case_id / f"attempt-{case_score['attempts']:03d}"
            case_spec_path = Path(str(selected.get("spec_path", ""))).expanduser()
            if not case_spec_path.is_absolute():
                case_spec_path = (workspace / case_spec_path).resolve()
            if not case_spec_path.exists():
                attempt_result = {
                    "passed": False,
                    "issues": [f"missing_spec_file:{case_spec_path}"],
                    "exit_code": 1,
                    "report_file": str((attempt_dir / "report.md")),
                    "stdout_file": str((attempt_dir / "stdout.log")),
                    "stderr_file": str((attempt_dir / "stderr.log")),
                }
                ensure_dir(attempt_dir)
                (attempt_dir / "report.md").write_text("# missing case spec file\n", encoding="utf-8")
                (attempt_dir / "stdout.log").write_text("", encoding="utf-8")
                (attempt_dir / "stderr.log").write_text("", encoding="utf-8")
            else:
                attempt_result = run_case_attempt(
                    case_id=case_id,
                    case_type=selected["type"],
                    case_spec_path=case_spec_path,
                    attempt_dir=attempt_dir,
                    workspace=workspace,
                    sandbox=state["sandbox"],
                    model=state["model"],
                    skip_git_repo_check=state["skip_git_repo_check"],
                    codex_args=state["codex_args"],
                    quality_checks=list(selected.get("quality_checks", [])),
                )

            if attempt_result["passed"]:
                case_score["passes"] += 1
            else:
                case_score["fails"] += 1
            case_score["last_issues"] = attempt_result["issues"]
            case_score["history"].append(
                {
                    "attempt": case_score["attempts"],
                    "passed": attempt_result["passed"],
                    "issues": attempt_result["issues"],
                    "exit_code": attempt_result["exit_code"],
                    "report_file": str(Path(attempt_result["report_file"]).relative_to(files.run_dir)),
                    "stdout_file": str(Path(attempt_result["stdout_file"]).relative_to(files.run_dir)),
                    "stderr_file": str(Path(attempt_result["stderr_file"]).relative_to(files.run_dir)),
                    "ran_at": utc_now(),
                }
            )
            recent_results = [entry["passed"] for entry in case_score["history"]]
            case_score["status"] = compute_stability_status(
                case_type=selected["type"],
                recent_results=recent_results,
                stability_runs=int(selected["stability_runs"]),
                stability_pass_threshold=int(selected["stability_pass_threshold"]),
            )

            append_progress(
                files.progress_file,
                f"- case={case_id} attempt={case_score['attempts']} passed={attempt_result['passed']} status={case_score['status']} issues={','.join(attempt_result['issues']) or 'none'}",
            )

            max_attempts = int(selected.get("max_attempts", 0))
            if max_attempts > 0 and case_score["attempts"] >= max_attempts and case_score["status"] != "passed":
                case_score["status"] = "failed"
                case_score["last_issues"] = sorted(set(case_score["last_issues"] + ["max_attempts_exhausted"]))

            save_todo_state(files, state, scoreboard)
            if not attempt_result["passed"] and not state["continue_on_failure"]:
                state["status"] = "failed"
                state["last_stop_reason"] = "case_failed_stop_on_failure"
                state["exit_reason"] = "case_failed_stop_on_failure"
                save_todo_state(files, state, scoreboard)
                return 1


def run_loop(files: RunFiles, state: dict[str, Any], prompt_text: str) -> int:
    ensure_dir(files.iterations_dir)
    while True:
        if files.cancel_file.exists():
            state["status"] = "cancelled"
            state["last_stop_reason"] = "cancel_requested"
            save_state(files, state)
            return 0

        if state["max_iterations"] > 0 and state["iteration"] >= state["max_iterations"]:
            state["status"] = "max_iterations_reached"
            state["last_stop_reason"] = "max_iterations_reached"
            save_state(files, state)
            return 0

        iteration = int(state["iteration"]) + 1
        stdout_file = files.iterations_dir / f"iteration-{iteration:03d}.stdout.log"
        stderr_file = files.iterations_dir / f"iteration-{iteration:03d}.stderr.log"
        message_file = files.iterations_dir / f"iteration-{iteration:03d}.last-message.txt"
        report_file = files.iterations_dir / f"iteration-{iteration:03d}.report.md"
        prompt_snapshot = files.iterations_dir / f"iteration-{iteration:03d}.prompt.md"
        require_iteration_report = bool(state.get("require_iteration_report", False))
        iteration_prompt = build_iteration_prompt(
            base_prompt=prompt_text,
            iteration=iteration,
            completion_promise=state.get("completion_promise"),
            require_iteration_report=require_iteration_report,
        )
        prompt_snapshot.write_text(iteration_prompt, encoding="utf-8")

        cmd = build_codex_command(
            workspace=Path(state["workspace"]),
            last_message_file=message_file,
            sandbox=state["sandbox"],
            model=state["model"],
            skip_git_repo_check=state["skip_git_repo_check"],
            codex_args=state["codex_args"],
        )

        with stdout_file.open("w", encoding="utf-8") as stdout_handle, stderr_file.open(
            "w", encoding="utf-8"
        ) as stderr_handle:
            result = subprocess.run(
                cmd,
                input=iteration_prompt,
                text=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
                cwd=state["workspace"],
                check=False,
            )

        last_message = message_file.read_text(encoding="utf-8") if message_file.exists() else ""
        promise_detected = detect_completion(last_message, state["completion_promise"])
        report_text = extract_iteration_report(last_message)
        report_valid, report_issues = validate_iteration_report(report_text)
        if not require_iteration_report:
            report_valid = True
            report_issues = []

        if report_text:
            report_file.write_text(report_text + "\n", encoding="utf-8")
        else:
            report_file.write_text("# missing iteration report block\n", encoding="utf-8")

        completion_detected = promise_detected and report_valid

        history_item = {
            "iteration": iteration,
            "ran_at": utc_now(),
            "exit_code": result.returncode,
            "stdout_file": str(stdout_file.relative_to(files.run_dir)),
            "stderr_file": str(stderr_file.relative_to(files.run_dir)),
            "last_message_file": str(message_file.relative_to(files.run_dir)),
            "prompt_file": str(prompt_snapshot.relative_to(files.run_dir)),
            "report_file": str(report_file.relative_to(files.run_dir)),
            "promise_detected": promise_detected,
            "report_valid": report_valid,
            "report_issues": report_issues,
            "completion_detected": completion_detected,
        }
        state["history"].append(history_item)
        state["iteration"] = iteration
        state["last_stdout_file"] = history_item["stdout_file"]
        state["last_stderr_file"] = history_item["stderr_file"]
        state["last_message_file"] = history_item["last_message_file"]
        state["last_exit_code"] = result.returncode

        if completion_detected:
            state["status"] = "completed"
            state["last_stop_reason"] = "completion_promise_detected"
            save_state(files, state)
            return 0

        save_state(files, state)


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_text:
        return args.prompt_text
    if args.prompt_file:
        return load_text(Path(args.prompt_file).expanduser())
    raise ValueError("one of --prompt-file or --prompt-text is required")


def command_start(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(args.workspace)
    run_root = resolve_run_root(args.run_root)
    ensure_dir(workspace)
    ensure_dir(run_root)

    prompt_text = read_prompt(args)
    slug_source = args.run_name or prompt_text.splitlines()[0][:60]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = run_root / f"{timestamp}-{sanitize_slug(slug_source)}"
    files = build_run_files(run_dir)
    ensure_dir(files.run_dir)
    ensure_dir(files.iterations_dir)
    files.prompt_file.write_text(prompt_text, encoding="utf-8")

    state = initialize_state(args, prompt_text, run_dir, workspace)
    save_state(files, state)

    exit_code = run_loop(files, state, prompt_text)
    print(files.run_dir)
    return exit_code


def command_resume(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    files, state, prompt_text = load_state(run_dir)
    if state["status"] in {"completed", "cancelled", "max_iterations_reached"} and not args.force:
        print(f"run already finished with status={state['status']}", file=sys.stderr)
        return 1
    state["status"] = "running"
    save_state(files, state)
    return run_loop(files, state, prompt_text)


def command_status(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    _, state, _ = load_state(run_dir)
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        print(f"run_dir: {state['run_dir']}")
        print(f"status: {state['status']}")
        print(f"iteration: {state['iteration']}")
        print(f"max_iterations: {state['max_iterations']}")
        print(f"completion_promise: {state['completion_promise'] or 'none'}")
        print(f"require_iteration_report: {state.get('require_iteration_report', False)}")
        print(f"last_exit_code: {state['last_exit_code']}")
        print(f"last_stop_reason: {state['last_stop_reason']}")
    return 0


def command_cancel(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    files, state, _ = load_state(run_dir)
    files.cancel_file.write_text("cancel requested\n", encoding="utf-8")
    if state["status"] == "running":
        state["status"] = "cancel_requested"
        state["last_stop_reason"] = "cancel_requested"
        save_state(files, state)
    print(f"cancel requested: {files.cancel_file}")
    return 0


def command_todo_start(args: argparse.Namespace) -> int:
    workspace = resolve_workspace(args.workspace)
    run_root = resolve_run_root(args.run_root)
    cases_root = Path(args.cases_root).expanduser().resolve()
    todo_file = Path(args.todo_file).expanduser().resolve()
    ensure_dir(workspace)
    ensure_dir(run_root)

    catalog = load_catalog(cases_root)
    plan = load_todo_plan(todo_file, catalog)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = run_root / f"{timestamp}-{sanitize_slug(plan['todo_id'])}"
    files = build_todo_run_files(run_dir)
    ensure_dir(files.run_dir)
    ensure_dir(files.items_dir)

    state = initialize_todo_state(args, run_dir, workspace, plan, catalog)
    scoreboard = initialize_todo_scoreboard(plan)
    files.snapshot_file.write_text(todo_file.read_text(encoding="utf-8"), encoding="utf-8")
    save_todo_state(files, state, scoreboard)

    exit_code = run_todo_loop(files, state, scoreboard, dry_run=bool(args.dry_run))
    print(files.run_dir)
    return exit_code


def command_todo_resume(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    files, state, scoreboard = load_todo_state(run_dir)
    if state["status"] in {"completed", "cancelled", "max_rounds_reached"} and not args.force:
        print(f"todo run already finished with status={state['status']}", file=sys.stderr)
        return 1
    state["status"] = "running"
    save_todo_state(files, state, scoreboard)
    return run_todo_loop(files, state, scoreboard, dry_run=bool(args.dry_run))


def command_todo_status(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    _, state, scoreboard = load_todo_state(run_dir)
    if args.json:
        payload = {"state": state, "scoreboard": scoreboard}
        payload.update(
            {
                "todo_id": state["todo_id"],
                "status": state["status"],
                "run_dir": state["run_dir"],
            }
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"run_dir: {state['run_dir']}")
        print(f"todo_id: {state['todo_id']}")
        print(f"status: {state['status']}")
        print(f"current_round: {state['current_round']}")
        print(f"loop_rounds: {state['loop_rounds']}")
        print(f"last_stop_reason: {state['last_stop_reason']}")
        print(f"exit_reason: {state.get('exit_reason')}")
    return 0


def command_todo_cancel(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    files, state, scoreboard = load_todo_state(run_dir)
    files.cancel_file.write_text("cancel requested\n", encoding="utf-8")
    if state["status"] == "running":
        state["status"] = "cancel_requested"
        state["last_stop_reason"] = "cancel_requested"
        state["exit_reason"] = "cancel_requested"
        save_todo_state(files, state, scoreboard)
    print(f"cancel requested: {files.cancel_file}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex-native Ralph loop runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="start a new Ralph loop run")
    prompt_group = start.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt-file", help="path to a prompt file")
    prompt_group.add_argument("--prompt-text", help="inline prompt text")
    start.add_argument("--workspace", required=True, help="workspace to run Codex inside")
    start.add_argument("--run-root", default=DEFAULT_RUN_ROOT, help="root directory for loop run artifacts")
    start.add_argument("--run-name", help="human-readable run name")
    start.add_argument("--completion-promise", help="promise text that signals completion")
    start.add_argument("--max-iterations", type=int, default=0, help="maximum iterations; 0 means unlimited")
    start.add_argument("--model", help="Codex model override")
    start.add_argument("--sandbox", default="workspace-write", help="Codex sandbox mode")
    start.add_argument(
        "--disable-iteration-report",
        action="store_true",
        help="disable auto-appended iteration report contract and validation",
    )
    start.add_argument("--skip-git-repo-check", action="store_true", help="forward skip git repo check to codex exec")
    start.add_argument("--codex-arg", action="append", default=[], help="extra argument string forwarded to codex exec")
    start.set_defaults(func=command_start)

    resume = subparsers.add_parser("resume", help="resume an existing Ralph loop run")
    resume.add_argument("run_dir", help="existing run directory")
    resume.add_argument("--force", action="store_true", help="resume even if state is terminal")
    resume.set_defaults(func=command_resume)

    status = subparsers.add_parser("status", help="show run status")
    status.add_argument("run_dir", help="existing run directory")
    status.add_argument("--json", action="store_true", help="print state as JSON")
    status.set_defaults(func=command_status)

    cancel = subparsers.add_parser("cancel", help="request cancellation for a run")
    cancel.add_argument("run_dir", help="existing run directory")
    cancel.set_defaults(func=command_cancel)

    todo_start = subparsers.add_parser("todo-start", help="start a todo-driven Ralph loop run")
    todo_start.add_argument("--workspace", required=True, help="workspace to run Codex inside")
    todo_start.add_argument("--cases-root", required=True, help="root directory containing catalog.yaml")
    todo_start.add_argument("--todo-file", required=True, help="todo yaml path")
    todo_start.add_argument("--run-root", default=DEFAULT_RUN_ROOT, help="root directory for loop run artifacts")
    todo_start.add_argument("--model", help="Codex model override")
    todo_start.add_argument("--sandbox", default="workspace-write", help="Codex sandbox mode")
    todo_start.add_argument(
        "--skip-git-repo-check", action="store_true", help="forward skip git repo check to codex exec"
    )
    todo_start.add_argument("--codex-arg", action="append", default=[], help="extra argument string for codex exec")
    todo_start.add_argument("--dry-run", action="store_true", help="initialize todo artifacts without executing Codex")
    todo_start.set_defaults(func=command_todo_start)

    todo_resume = subparsers.add_parser("todo-resume", help="resume an existing todo run")
    todo_resume.add_argument("run_dir", help="existing todo run directory")
    todo_resume.add_argument("--force", action="store_true", help="resume even if state is terminal")
    todo_resume.add_argument("--dry-run", action="store_true", help="resume in dry-run mode")
    todo_resume.set_defaults(func=command_todo_resume)

    todo_status = subparsers.add_parser("todo-status", help="show todo run status")
    todo_status.add_argument("run_dir", help="existing todo run directory")
    todo_status.add_argument("--json", action="store_true", help="print todo state and scoreboard as JSON")
    todo_status.set_defaults(func=command_todo_status)

    todo_cancel = subparsers.add_parser("todo-cancel", help="request cancellation for a todo run")
    todo_cancel.add_argument("run_dir", help="existing todo run directory")
    todo_cancel.set_defaults(func=command_todo_cancel)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
