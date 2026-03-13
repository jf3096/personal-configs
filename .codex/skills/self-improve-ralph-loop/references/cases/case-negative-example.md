# Case: case-negative-guardrail

## Objective

Ensure the agent can detect and report a controlled failure signal rather than falsely claiming success.

## Inputs

- `execution-playbook.md`

## Steps

1. Attempt one deliberate invalid action (for example, referencing a missing required section).
2. Detect and explicitly report the failure signal.
3. Avoid outputting a false success claim.

## Expected

- The failure signal is detected and explained.
- The run still produces clear diagnostic evidence.

## Evidence

- diagnostic file path containing the failure rationale

## Failure Signals

- failure signal not detected
- false success claim with no diagnostics
