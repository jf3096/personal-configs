#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
WORKSPACE="$ROOT_DIR/temp/ralph-loop-smoke-workspace"
RUN_ROOT="$ROOT_DIR/temp/ralph-loop-runs"
PROMPT_FILE="$WORKSPACE/smoke-prompt.md"

mkdir -p "$WORKSPACE"
cat > "$PROMPT_FILE" <<'EOF'
Create a file named `smoke-success.txt` in the current workspace with the exact contents `smoke-ok`.

In your final message, include:
<iteration_report>
iteration: 1
changes_before: smoke-success.txt did not exist
changes_after: smoke-success.txt exists with smoke-ok
optimization_strategy: perform minimal deterministic file write
score_before: 0/100
score_after: 100/100
score_delta: +100
next_iteration_plan: stop because smoke goal is satisfied
</iteration_report>

When and only when that file exists with the correct contents, output exactly this promise after the report:
<promise>DONE</promise>
EOF

python3 "$ROOT_DIR/.codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py" start \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --run-root "$RUN_ROOT" \
  --run-name "smoke" \
  --completion-promise "DONE" \
  --max-iterations 2
