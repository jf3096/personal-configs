#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  init_evolution_cycle.sh --req-id <REQ-ID> --task <task> [options]

Required:
  --req-id <REQ-ID>          Requirement ID, e.g. REQ-101
  --task <task>              Task statement for this cycle

Optional:
  --docs-dir <dir>           Output docs dir (default: docs)
  --source-file <path>       Source file path
  --target-file <path>       Target file path
  --acceptance <text>        Extra acceptance criterion (repeatable)

Example:
  init_evolution_cycle.sh \
    --req-id REQ-101 \
    --task "Convert compliance-review-demo.js to python" \
    --source-file compliance-review-demo.js \
    --target-file compliance-review-demo.py
USAGE
}

REQ_ID=""
TASK=""
DOCS_DIR="docs"
SOURCE_FILE=""
TARGET_FILE=""
ACCEPTANCE_ITEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --req-id)
      REQ_ID="$2"
      shift 2
      ;;
    --task)
      TASK="$2"
      shift 2
      ;;
    --docs-dir)
      DOCS_DIR="$2"
      shift 2
      ;;
    --source-file)
      SOURCE_FILE="$2"
      shift 2
      ;;
    --target-file)
      TARGET_FILE="$2"
      shift 2
      ;;
    --acceptance)
      ACCEPTANCE_ITEMS+=("$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$REQ_ID" || -z "$TASK" ]]; then
  echo "--req-id and --task are required." >&2
  usage
  exit 1
fi

mkdir -p "$DOCS_DIR"

REQ_FILE="$DOCS_DIR/${REQ_ID}.md"
REHEARSAL_FILE="$DOCS_DIR/REHEARSAL-${REQ_ID}.md"
POSTMORTEM_FILE="$DOCS_DIR/POSTMORTEM-${REQ_ID}.md"
R2_FILE="$DOCS_DIR/${REQ_ID}-R2.md"

if [[ ${#ACCEPTANCE_ITEMS[@]} -eq 0 ]]; then
  ACCEPTANCE_ITEMS+=("Run source and target implementations successfully with exit code 0")
  ACCEPTANCE_ITEMS+=("Verify key expected output snippets are present")
  ACCEPTANCE_ITEMS+=("Compare normalized outputs and record diff result")
fi

write_acceptance_list() {
  local i=1
  for item in "${ACCEPTANCE_ITEMS[@]}"; do
    echo "$i. $item"
    i=$((i + 1))
  done
}

cat > "$REQ_FILE" <<EOF_REQ
# ${REQ_ID}

## Objective

${TASK}

## Scope

- Source: ${SOURCE_FILE:-[to be specified]}
- Target: ${TARGET_FILE:-[to be specified]}

## Acceptance Criteria

$(write_acceptance_list)

## Evidence Plan

- Save execution logs for source and target runs.
- Record command exit codes and key output snippets.
- Capture normalized diff results for behavior comparison.
EOF_REQ

cat > "$REHEARSAL_FILE" <<EOF_REHEARSAL
# REHEARSAL ${REQ_ID}

## Predicted Steps

1. Read source implementation and map expected behavior.
2. Implement or update target implementation.
3. Execute source and target commands.
4. Validate key output snippets and diff normalized outputs.
5. Run gate checks (positive/negative/adversarial).

## Risk Matrix

- Risk: behavior drift between source and target
- Risk: false confidence from text-only checks
- Risk: missing adversarial validation

## Validation Matrix

- Positive case: should pass
- Negative case: should block
- Adversarial/boundary case: should expose weak spots
EOF_REHEARSAL

cat > "$POSTMORTEM_FILE" <<EOF_POST
# POSTMORTEM ${REQ_ID}

## What Happened

- [fill after execution]

## Rehearsal vs Actual Delta

- Predicted:
- Actual:
- Delta:

## Improvements

- Rule/prompt improvements:
- Test additions:
- Process updates:
EOF_POST

cat > "$R2_FILE" <<EOF_R2
# ${REQ_ID}-R2

## Objective

Re-run ${REQ_ID} under evolved baseline.

## Tightened Acceptance Criteria

1. Keep original acceptance criteria.
2. Add mandatory positive/negative/adversarial verification.
3. Include gate verbose evidence when relevant.

## Mandatory Rerun Checks

- Source and target execution
- Normalized diff check
- Gate checks and regression tests
EOF_R2

printf 'Created:\n- %s\n- %s\n- %s\n- %s\n' "$REQ_FILE" "$REHEARSAL_FILE" "$POSTMORTEM_FILE" "$R2_FILE"
