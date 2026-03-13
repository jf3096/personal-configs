#!/usr/bin/env python3

from __future__ import annotations

from typing import Any


SENSITIVE_TYPES = {
    "hook",
    "rule",
    "skill",
    "validator_script",
    "template",
}

ALLOWED_IMPACT_SCOPES = {
    "local",
    "cross-task",
    "global-verdict-changing",
}

ALLOWED_RECOMMENDED_CHECKS = (
    "positive_case",
    "negative_case",
    "adversarial_case",
)


def _normalize_change_type(change_objects: list[str]) -> str:
    normalized = {
        item.strip().lower()
        for item in change_objects
        if isinstance(item, str) and item.strip()
    }

    for preferred in ("hook", "rule", "skill", "validator_script", "template"):
        if preferred in normalized:
            return preferred
    return "other"


def _normalize_impact_scope(raw_scope: str) -> str:
    scope = raw_scope.strip().lower()
    if scope in ALLOWED_IMPACT_SCOPES:
        return scope
    return "local"


def _determine_severity(change_type: str, impact_scope: str) -> str:
    if change_type not in SENSITIVE_TYPES:
        return "suggested"
    if impact_scope in {"cross-task", "global-verdict-changing"}:
        return "suggest_blocking"
    return "strongly_suggested"


def _recommended_checks(change_type: str, severity: str) -> list[str]:
    if severity == "suggest_blocking":
        return list(ALLOWED_RECOMMENDED_CHECKS)
    if change_type in SENSITIVE_TYPES:
        return ["positive_case", "negative_case"]
    return ["positive_case"]


def recommend_gate(context: dict[str, Any]) -> dict[str, Any]:
    change_objects = context.get("change_objects", [])
    if not isinstance(change_objects, list):
        change_objects = []

    raw_scope = context.get("impact_scope", "local")
    if not isinstance(raw_scope, str):
        raw_scope = "local"

    change_type = _normalize_change_type(change_objects)
    impact_scope = _normalize_impact_scope(raw_scope)
    severity = _determine_severity(change_type, impact_scope)

    return {
        "change_type": change_type,
        "change_summary": str(context.get("change_summary", "")).strip(),
        "impact_scope": impact_scope,
        "recommended_checks": _recommended_checks(change_type, severity),
        "reason": (
            f"change_type={change_type}, impact_scope={impact_scope}, "
            f"severity={severity}"
        ),
        "severity": severity,
        "requires_user_confirmation": True,
    }
