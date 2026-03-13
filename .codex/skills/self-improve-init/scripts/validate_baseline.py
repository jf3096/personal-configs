#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PLACEHOLDERS = {"待确认", "tbd", "todo", "pending"}
PRD_GOAL_META_PHRASES = [
    "作为后续 self-improve",
    "供后续 self-improve",
    "用于后续 self-improve",
    "self-improve loop",
    "后续 self-improve",
    "后续 loop",
    "初始基线",
    "baseline 文档",
]
PRD_GOAL_META_COMPOUNDS = [
    ("baseline", "loop"),
    ("baseline", "self-improve"),
    ("baseline", "初始"),
]
LOW_LEVEL_EXECUTION_HINTS = [
    "selector",
    "locator",
    "xpath",
    "css",
    "waitfor",
    "wait for",
    "fallback",
    "retry",
    "regex",
    "endpoint",
    "header",
    "json path",
    "page.locator",
]
PLAYBOOK_RUNTIME_SECTIONS = ["输入", "输出", "当前执行方案"]
PLAYBOOK_HISTORY_HINTS = ["来自真实 run 观察", "真实 run 复核记录"]

REQUIRED = {
    "prd.md": ["业务目标", "执行路径", "预期结果", "边界与约束"],
    "execution-playbook.md": [
        "执行目标与职责",
        "输入",
        "输出",
        "当前执行方案",
        "候选降级路径与待验证项",
        "后续优化方向",
    ],
    "benchmark.md": ["任务背景", "任务输入", "期望输出", "评分维度", "通过标准"],
}

BLOCKING = {
    "prd.md": ["业务目标"],
    "execution-playbook.md": ["执行目标与职责", "当前执行方案"],
    "benchmark.md": ["期望输出", "评分维度"],
}


def parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def strip_html_comments(value: str) -> str:
    return re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL).strip()


def is_missing(value: str) -> bool:
    cleaned = strip_html_comments(value)
    if not cleaned.strip():
        return True
    normalized = cleaned.strip().lower()
    if normalized in PLACEHOLDERS:
        return True
    if normalized == "- 待确认":
        return True
    return False


def find_prd_goal_meta_issue(value: str) -> str | None:
    normalized = strip_html_comments(value).strip().lower()
    for phrase in PRD_GOAL_META_PHRASES:
        if phrase.lower() in normalized:
            return phrase
    for left, right in PRD_GOAL_META_COMPOUNDS:
        if left in normalized and right in normalized:
            return f"{left}+{right}"
    return None


def find_low_level_execution_issue(value: str) -> list[str]:
    normalized = strip_html_comments(value).strip().lower()
    hits: list[str] = []
    for hint in LOW_LEVEL_EXECUTION_HINTS:
        if hint in normalized:
            hits.append(hint)
    return hits


def find_placeholder_fragments(value: str) -> list[str]:
    cleaned = strip_html_comments(value)
    hits: list[str] = []
    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if "待确认" in line or re.search(r"\b(tbd|todo|pending)\b", lower):
            hits.append(line)
    return hits


def find_history_layer_hints(value: str) -> list[str]:
    cleaned = strip_html_comments(value)
    hits: list[str] = []
    for hint in PLAYBOOK_HISTORY_HINTS:
        if hint in cleaned:
            hits.append(hint)
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    report: dict[str, object] = {
        "workspace": str(workspace),
        "files_exist": {},
        "missing_sections": [],
        "blocking_missing": [],
        "semantic_issues": [],
        "baseline_usable": False,
        "next_question_hint": None,
    }
    evidence_dir = workspace / "evidence"
    evidence_exists = evidence_dir.exists() and any(path.is_file() for path in evidence_dir.rglob("*"))
    report["real_run_evidence_exists"] = evidence_exists

    for file_name, sections in REQUIRED.items():
        file_path = workspace / file_name
        report["files_exist"][file_name] = file_path.exists()
        if not file_path.exists():
            report["missing_sections"].append({"file": file_name, "section": "__file__"})
            for blocking_section in BLOCKING.get(file_name, []):
                report["blocking_missing"].append({"file": file_name, "section": blocking_section})
            continue

        parsed = parse_sections(file_path.read_text(encoding="utf-8"))
        for section in sections:
            value = parsed.get(section, "")
            if is_missing(value):
                item = {"file": file_name, "section": section}
                report["missing_sections"].append(item)
                if section in BLOCKING.get(file_name, []):
                    report["blocking_missing"].append(item)

        if file_name == "prd.md":
            goal_value = parsed.get("业务目标", "")
            meta_issue = find_prd_goal_meta_issue(goal_value)
            if meta_issue is not None:
                item = {
                    "file": "prd.md",
                    "section": "业务目标",
                    "issue": "meta_goal",
                    "matched": meta_issue,
                    "message": "业务目标应描述用户任务本身，不应写 baseline / loop / self-improve 的系统用途",
                }
                report["semantic_issues"].append(item)
                report["blocking_missing"].append(item)

            path_value = parsed.get("执行路径", "")
            low_level_hits = find_low_level_execution_issue(path_value)
            if low_level_hits:
                item = {
                    "file": "prd.md",
                    "section": "执行路径",
                    "issue": "execution_path_too_low_level",
                    "matched": low_level_hits,
                    "message": "执行路径应保持高层骨架，低层执行策略应写入 execution-playbook.md",
                }
                report["semantic_issues"].append(item)
                report["blocking_missing"].append(item)

        if file_name == "execution-playbook.md" and evidence_exists:
            for section in PLAYBOOK_RUNTIME_SECTIONS:
                value = parsed.get(section, "")
                placeholder_hits = find_placeholder_fragments(value)
                if placeholder_hits:
                    item = {
                        "file": "execution-playbook.md",
                        "section": section,
                        "issue": "playbook_section_has_placeholder_after_run",
                        "matched": placeholder_hits,
                        "message": "真实 run 之后，execution-playbook.md 的 输入/输出/运行方式 不应继续保留待确认占位；未确认内容应移到候选策略与降级路径或优化方向",
                    }
                    report["semantic_issues"].append(item)
                    report["blocking_missing"].append(item)
            history_hits = find_history_layer_hints(file_path.read_text(encoding="utf-8"))
            if history_hits:
                item = {
                    "file": "execution-playbook.md",
                    "section": "__document__",
                    "issue": "playbook_has_history_layers_after_run",
                    "matched": history_hits,
                    "message": "真实 run 之后，execution-playbook.md 应收敛为当前执行真相，不应继续保留历史观察附加层；历史过程应写入 evidence/",
                }
                report["semantic_issues"].append(item)
                report["blocking_missing"].append(item)

    report["baseline_usable"] = len(report["blocking_missing"]) == 0
    if report["blocking_missing"]:
        first = report["blocking_missing"][0]
        if first.get("issue") == "meta_goal":
            report["next_question_hint"] = (
                "请改写 prd.md 的 `业务目标`：只写用户要完成的业务任务，"
                "不要写 baseline / loop / self-improve 的系统用途"
            )
        elif first.get("issue") == "execution_path_too_low_level":
            report["next_question_hint"] = (
                "请改写 prd.md 的 `执行路径`：只保留高层执行骨架，"
                "把低层执行细节移到 execution-playbook.md"
            )
        elif first.get("issue") == "playbook_section_has_placeholder_after_run":
            report["next_question_hint"] = (
                f"请改写 execution-playbook.md 的 `{first['section']}`：真实 run 之后不要保留待确认占位，"
                "未确认内容应移到候选策略与降级路径或优化方向"
            )
        elif first.get("issue") == "playbook_has_history_layers_after_run":
            report["next_question_hint"] = (
                "请改写 execution-playbook.md：真实 run 之后应把观察折叠进正文，"
                "不要继续保留历史观察附加层；详细过程移到 evidence/"
            )
        else:
            report["next_question_hint"] = f"请补充 {first['file']} 的 `{first['section']}`"
    elif report["missing_sections"]:
        first = report["missing_sections"][0]
        report["next_question_hint"] = f"请补充 {first['file']} 的 `{first['section']}`"
    else:
        report["next_question_hint"] = "baseline 已可用，可继续进入后续 self-improve 流程"

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
