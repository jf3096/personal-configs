# TDD CLI Adapter Template

## Goal

Provide a replaceable adapter contract for third-party TDD/revalidation tools.
The adapter reads JSON from `stdin` and prints normalized JSON to `stdout`.

Path:

- `/home/jf3096/.codex/skills/compliance-reviewer/scripts/tdd_cli_adapter_template.py`

## I/O Contract

Input (`stdin`, flexible source schema):

```json
{
  "status": "pass|fail|blocked",
  "test_evidence": ["..."],
  "run_evidence": ["..."],
  "summary": "..."
}
```

Output (`stdout`, strict contract for `delivery_gate.py`):

```json
{
  "revalidation_status": "pass|fail|blocked",
  "test_evidence": ["..."],
  "run_evidence": ["..."],
  "regression_summary": "...",
  "adapter_metadata": {
    "adapter_name": "tdd_cli_adapter_template",
    "status_reason": "..."
  }
}
```

## Usage

Pass-through / normalization example:

```bash
cat /tmp/tdd-request.json | python3 /home/jf3096/.codex/skills/compliance-reviewer/scripts/tdd_cli_adapter_template.py
```

Integration example in report:

```text
TDD-Strict Revalidation
TDD Revalidation Command: cat /tmp/tdd-request.json | python3 /home/jf3096/.codex/skills/compliance-reviewer/scripts/tdd_cli_adapter_template.py
```

## Fail-Closed Behavior

When input is empty, invalid JSON, or unsupported status, the adapter returns:

- `revalidation_status: "blocked"`
- with non-empty `adapter_metadata.status_reason`

This keeps the gate deterministic and compatible with `Delivery Verdict: BLOCKED`.
