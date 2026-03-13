#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import subprocess
import sys


ALLOWED_COMPLIANCE_VERDICTS = {"PASS", "FAIL"}
ALLOWED_DELIVERY_VERDICTS = {"PASS", "PASS_WITH_HIGH_RISK", "BLOCKED"}

HIGH_RISK_KEYWORDS = (
    "新增依赖",
    "dependency addition",
    "dependency added",
    "db migration",
    "database migration",
    "公共 api",
    "public api",
    "protocol change",
    "协议变更",
    "生产配置",
    "permission script",
    "权限脚本",
)

EXECUTABLE_CLAIM_KEYWORDS = (
    "启动",
    "start server",
    "deploy",
    "部署",
    "health check",
    "api 可用",
    "api available",
)

SECTION_HEADER_TDD = "TDD-Strict Revalidation"
RUNTIME_RESULT_PATTERN = re.compile(
    r"(exit\s*code|exit|退出码|返回码)\s*[:=]?\s*[0-9]+",
    re.I,
)


def _extract_field(text: str, label: str) -> str | None:
    pattern = re.compile(rf"^\s*{re.escape(label)}\s*[:：]\s*(.+?)\s*$", re.M)
    matches = pattern.findall(text)
    if not matches:
        return None
    return matches[-1].strip()


def _parse_verdicts(text: str) -> tuple[dict[str, str | None] | None, str | None]:
    compliance = _extract_field(text, "Compliance Verdict")
    if compliance is None:
        return None, "Missing required field: Compliance Verdict"
    compliance = compliance.upper()
    if compliance not in ALLOWED_COMPLIANCE_VERDICTS:
        return None, f"Invalid Compliance Verdict: {compliance}"

    delivery = _extract_field(text, "Delivery Verdict")
    if delivery is None:
        return None, "Missing required field: Delivery Verdict"
    delivery = delivery.upper()
    if delivery not in ALLOWED_DELIVERY_VERDICTS:
        return None, f"Invalid Delivery Verdict: {delivery}"

    release = _extract_field(text, "Release Advice")
    if release is not None:
        release = release.capitalize()
        if release not in {"Ship", "Hold"}:
            return None, f"Invalid Release Advice: {release}"

    return {
        "compliance": compliance,
        "delivery": delivery,
        "release_advice": release,
    }, None


def _parse_int_field(text: str, keys: tuple[str, ...]) -> int | None:
    for key in keys:
        pattern = re.compile(rf"^\s*(?:-+\s*)?{re.escape(key)}\s*[:：]\s*([0-9]+)\s*$", re.M | re.I)
        match = pattern.search(text)
        if match:
            return int(match.group(1))
    return None


def _has_high_risk_signal(text: str) -> bool:
    explicit = re.search(r"^\s*(?:-+\s*)?(high_risk|高风险)\s*[:：]\s*(true|yes|1|是)\s*$", text, re.M | re.I)
    if explicit:
        return True

    lowered = text.lower()
    if any(keyword in lowered for keyword in HIGH_RISK_KEYWORDS):
        return True

    files_changed = _parse_int_field(text, ("files_changed", "files changed", "变更文件数"))
    if files_changed is not None and files_changed > 5:
        return True

    line_delta = _parse_int_field(text, ("line_delta", "line delta", "变更行数"))
    if line_delta is not None and line_delta > 200:
        return True

    return False


def _extract_section(text: str, header: str) -> str:
    pattern = re.compile(
        rf"{re.escape(header)}\n(.*?)(?=\n(?:##+\s+|Compliance Verdict|Delivery Verdict|Release Advice|状态[:：]|$))",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1)


def _extract_tdd_command(text: str) -> str | None:
    section = _extract_section(text, SECTION_HEADER_TDD)
    if not section.strip():
        return None

    patterns = (
        r"^\s*TDD Revalidation Command\s*[:：]\s*(.+?)\s*$",
        r"^\s*-\s*tdd_revalidation_command\s*[:：]\s*(.+?)\s*$",
        r"^\s*-\s*command\s*[:：]\s*(.+?)\s*$",
        r"^\s*-\s*run\s*[:：]\s*(.+?)\s*$",
    )
    for raw in patterns:
        match = re.search(raw, section, re.M | re.I)
        if match:
            return match.group(1).strip()
    return None


def _parse_attempts(text: str) -> int | None:
    return _parse_int_field(
        text,
        (
            "Auto Remediation Attempts",
            "auto_remediation_attempts",
            "自动修复尝试次数",
        ),
    )


def _has_runtime_evidence(text: str) -> bool:
    commands = re.findall(r"^\s*(?:-+\s*)?command\s*[:：]\s*(.+?)\s*$", text, re.M | re.I)
    results = re.findall(r"^\s*(?:-+\s*)?result\s*[:：]\s*(.+?)\s*$", text, re.M | re.I)
    if not commands or not results:
        return False
    return any(RUNTIME_RESULT_PATTERN.search(result) for result in results)


def _has_executable_claim(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in EXECUTABLE_CLAIM_KEYWORDS)


def _run_tdd_cli(command: str, timeout_seconds: int) -> tuple[int, str, str]:
    result = subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _parse_tdd_output(stdout: str) -> tuple[dict[str, object] | None, str | None]:
    if not stdout:
        return None, "TDD CLI produced empty stdout; expected JSON output."
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return None, f"TDD CLI stdout is not valid JSON: {exc}"
    if not isinstance(parsed, dict):
        return None, "TDD CLI JSON payload must be an object."
    return parsed, None


def _validate_tdd_payload(payload: dict[str, object]) -> tuple[str | None, str | None]:
    status = str(payload.get("revalidation_status", "")).strip().lower()
    if status not in {"pass", "fail", "blocked"}:
        return None, "TDD CLI JSON missing/invalid field: revalidation_status"

    test_evidence = payload.get("test_evidence")
    run_evidence = payload.get("run_evidence")
    if not isinstance(test_evidence, list):
        return None, "TDD CLI JSON missing/invalid field: test_evidence(list)"
    if not isinstance(run_evidence, list):
        return None, "TDD CLI JSON missing/invalid field: run_evidence(list)"

    return status, None


def evaluate_delivery_contract(text: str) -> tuple[bool, str]:
    verdicts, verdict_error = _parse_verdicts(text)
    if verdict_error:
        return False, verdict_error
    assert verdicts is not None

    attempts = _parse_attempts(text)
    if attempts is not None and attempts > 2:
        return False, "Auto remediation attempts exceed maximum allowed (2)."

    high_risk = _has_high_risk_signal(text)
    if high_risk and verdicts["delivery"] == "PASS":
        return False, "High-risk report cannot declare Delivery Verdict PASS."
    if not high_risk and verdicts["delivery"] == "PASS_WITH_HIGH_RISK":
        return False, "Delivery Verdict PASS_WITH_HIGH_RISK requires high-risk signal."

    if verdicts["delivery"] in {"BLOCKED", "PASS_WITH_HIGH_RISK"} and verdicts["release_advice"] not in {"Hold"}:
        return False, "Release Advice must be Hold when Delivery Verdict is BLOCKED or PASS_WITH_HIGH_RISK."

    if verdicts["delivery"] in {"PASS", "PASS_WITH_HIGH_RISK"} and _has_executable_claim(text):
        if not _has_runtime_evidence(text):
            return False, "Executable claim requires runtime evidence (command/result/exit code)."

    if not high_risk:
        return True, ""

    tdd_command = _extract_tdd_command(text)
    if not tdd_command:
        return False, "High-risk report requires TDD-Strict Revalidation command."

    timeout_seconds = int(os.environ.get("COMPLIANCE_REVIEW_TDD_TIMEOUT_SECONDS", "120"))
    exit_code, stdout, stderr = _run_tdd_cli(tdd_command, timeout_seconds)
    verbose = os.environ.get("COMPLIANCE_REVIEW_VERBOSE", "false").lower() == "true"
    if verbose:
        print(
            f"[delivery-gate] high_risk=true command={tdd_command!r} exit={exit_code}",
            file=sys.stderr,
        )

    if exit_code != 0:
        if verdicts["delivery"] == "BLOCKED":
            return True, ""
        return False, f"TDD CLI command failed with exit {exit_code}: {stderr or stdout}"

    payload, parse_error = _parse_tdd_output(stdout)
    if parse_error:
        if verdicts["delivery"] == "BLOCKED":
            return True, ""
        return False, parse_error
    assert payload is not None

    status, payload_error = _validate_tdd_payload(payload)
    if payload_error:
        if verdicts["delivery"] == "BLOCKED":
            return True, ""
        return False, payload_error
    assert status is not None

    if verdicts["delivery"] == "PASS_WITH_HIGH_RISK":
        if status != "pass":
            return False, "PASS_WITH_HIGH_RISK requires TDD revalidation_status=pass."
        if verdicts["release_advice"] != "Hold":
            return False, "PASS_WITH_HIGH_RISK requires Release Advice Hold."
        return True, ""

    if verdicts["delivery"] == "BLOCKED":
        return True, ""

    return False, "High-risk delivery verdict is inconsistent with TDD revalidation outcome."


def main() -> int:
    text = sys.stdin.read()
    try:
        ok, message = evaluate_delivery_contract(text)
    except subprocess.TimeoutExpired as exc:
        print(
            f"TDD CLI command timed out after {exc.timeout}s.",
            file=sys.stderr,
        )
        return 1

    if not ok:
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
