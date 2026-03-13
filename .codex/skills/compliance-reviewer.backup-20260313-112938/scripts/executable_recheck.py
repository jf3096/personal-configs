#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass


SEVERITIES_REQUIRING_RECHECKS = {"strongly_suggested", "suggest_blocking"}
SECTION_HEADER = "Stage 2 可执行复验命令"


@dataclass(frozen=True)
class RecheckCommand:
    run: str
    expect_exit: int = 0
    expect_stdout: str | None = None
    expect_stderr: str | None = None


def _extract_section(text: str, header: str) -> str:
    pattern = rf"{re.escape(header)}\n(.*?)(?=\n(?:### |Compliance Skill:|状态[:：]|Stage 2 推荐门禁上下文摘要|Stage 2 推荐门禁清单|$))"
    match = re.search(pattern, text, re.S)
    return match.group(1) if match else ""


def _extract_severity(text: str) -> str | None:
    block = _extract_section(text, "Stage 2 推荐门禁清单")
    match = re.search(r"^- severity:\s*(.+?)\s*$", block, re.M)
    if not match:
        return None
    return match.group(1).strip().lower()


def parse_recheck_commands(text: str) -> list[RecheckCommand]:
    block = _extract_section(text, SECTION_HEADER)
    if not block.strip():
        return []

    commands: list[RecheckCommand] = []
    current: dict[str, str] = {}

    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- run:"):
            if current:
                commands.append(_build_command(current))
                current = {}
            current["run"] = line.split(":", 1)[1].strip()
            continue
        if line.startswith("- expect_exit:"):
            current["expect_exit"] = line.split(":", 1)[1].strip()
            continue
        if line.startswith("- expect_stdout:"):
            current["expect_stdout"] = line.split(":", 1)[1].strip()
            continue
        if line.startswith("- expect_stderr:"):
            current["expect_stderr"] = line.split(":", 1)[1].strip()
            continue

    if current:
        commands.append(_build_command(current))

    return commands


def _build_command(payload: dict[str, str]) -> RecheckCommand:
    if "run" not in payload or not payload["run"]:
        raise ValueError("Each Stage 2 recheck entry must contain - run:")

    expect_exit_raw = payload.get("expect_exit", "0")
    try:
        expect_exit = int(expect_exit_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid expect_exit value: {expect_exit_raw}") from exc

    return RecheckCommand(
        run=payload["run"],
        expect_exit=expect_exit,
        expect_stdout=payload.get("expect_stdout"),
        expect_stderr=payload.get("expect_stderr"),
    )


def requires_rechecks(text: str) -> bool:
    severity = _extract_severity(text)
    return severity in SEVERITIES_REQUIRING_RECHECKS


def execute_rechecks(text: str) -> tuple[bool, str]:
    if not requires_rechecks(text):
        return True, ""

    commands = parse_recheck_commands(text)
    if not commands:
        return False, "Missing executable Stage 2 recheck commands."

    timeout_seconds = int(os.environ.get("COMPLIANCE_REVIEW_RECHECK_TIMEOUT_SECONDS", "30"))
    verbose = os.environ.get("COMPLIANCE_REVIEW_VERBOSE", "false").lower() == "true"

    for index, command in enumerate(commands, start=1):
        result = subprocess.run(
            command.run,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        if verbose:
            print(
                f"[compliance-recheck] index={index} exit={result.returncode} command={command.run}",
                file=sys.stderr,
            )

        if result.returncode != command.expect_exit:
            return (
                False,
                f"Executable Stage 2 recheck failed: command #{index} exit "
                f"{result.returncode} != expected {command.expect_exit}",
            )
        if command.expect_stdout is not None and command.expect_stdout not in result.stdout:
            return (
                False,
                f"Executable Stage 2 recheck failed: command #{index} stdout "
                f"missing expected substring {command.expect_stdout!r}",
            )
        if command.expect_stderr is not None and command.expect_stderr not in result.stderr:
            return (
                False,
                f"Executable Stage 2 recheck failed: command #{index} stderr "
                f"missing expected substring {command.expect_stderr!r}",
            )

    return True, ""


def main() -> int:
    text = sys.stdin.read()
    try:
        ok, message = execute_rechecks(text)
    except subprocess.TimeoutExpired as exc:
        print(
            f"Executable Stage 2 recheck failed: command timed out after {exc.timeout}s",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"Executable Stage 2 recheck failed: {exc}", file=sys.stderr)
        return 1

    if not ok:
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
