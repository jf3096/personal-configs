#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
WORKSPACE="$ROOT_DIR/temp/ralph-loop-todo-smoke-workspace"
RUN_ROOT="$ROOT_DIR/temp/ralph-loop-runs"
CASES_ROOT="$WORKSPACE/cases"
TODO_FILE="$WORKSPACE/todo.yaml"

mkdir -p "$CASES_ROOT" "$WORKSPACE/evidence"

cat > "$CASES_ROOT/catalog.yaml" <<'EOF'
version: 1
suite_name: smoke
cases:
  - id: case-positive-smoke
    title: positive smoke
    type: positive
    priority: high
    spec_file: case-positive-smoke.md
    enabled: true
EOF

cat > "$CASES_ROOT/case-positive-smoke.md" <<'EOF'
Create a file `evidence/todo-smoke.txt` with exact contents `todo-smoke-ok`.

Then output exactly one final block:
<case_report>
case_id: case-positive-smoke
verdict: pass
expectation_check: met
failure_signal_check: not_hit
evidence_refs: evidence/todo-smoke.txt
confidence: 100
next_action: stop
</case_report>
EOF

cat > "$TODO_FILE" <<'EOF'
todo_id: todo-smoke
loop_rounds: 3
continue_on_failure: true
selection_policy: highest_priority_pending
completion_policy:
  mode: all_enabled_cases_passed
  completion_promise: DONE
items:
  - case_id: case-positive-smoke
    enabled: true
    stability_runs: 3
    stability_pass_threshold: 3
EOF

RUN_DIR="$(
python3 "$ROOT_DIR/.codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py" todo-start \
  --workspace "$WORKSPACE" \
  --cases-root "$CASES_ROOT" \
  --todo-file "$TODO_FILE" \
  --run-root "$RUN_ROOT"
)"

echo "Todo smoke run dir: $RUN_DIR"

python3 "$ROOT_DIR/.codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py" todo-status "$RUN_DIR" --json \
  | jq -e '.status == "completed" and .state.last_stop_reason == "all_cases_passed"' >/dev/null

test -s "$WORKSPACE/evidence/todo-smoke.txt"
echo "todo smoke ok"
