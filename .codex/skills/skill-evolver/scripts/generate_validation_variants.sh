#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  generate_validation_variants.sh --req-id <REQ-ID> [--docs-dir <dir>]

Example:
  generate_validation_variants.sh --req-id REQ-200 --docs-dir docs
USAGE
}

REQ_ID=""
DOCS_DIR="docs"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --req-id)
      REQ_ID="$2"
      shift 2
      ;;
    --docs-dir)
      DOCS_DIR="$2"
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

if [[ -z "$REQ_ID" ]]; then
  echo "--req-id is required" >&2
  usage
  exit 1
fi

mkdir -p "$DOCS_DIR"

BASE="$DOCS_DIR/${REQ_ID}-variants-overview.md"
V1="$DOCS_DIR/${REQ_ID}-V1-baseline-equivalence.md"
V2="$DOCS_DIR/${REQ_ID}-V2-failure-closure.md"
V3="$DOCS_DIR/${REQ_ID}-V3-gate-regression.md"
V4="$DOCS_DIR/${REQ_ID}-V4-adversarial-hardening.md"

cat > "$BASE" <<EOF_BASE
# ${REQ_ID} Variants Overview

Base scenario (5-step loop):

1. Create requirement.
2. Rehearse with AGENTS.md + compliance-reviewer rules.
3. Execute real change.
4. Compare rehearsal vs actual.
5. Evolve and rerun step 1.

Derived variants:

- V1 baseline equivalence
- V2 failure closure
- V3 gate regression
- V4 adversarial hardening
EOF_BASE

cat > "$V1" <<'EOF_V1'
# V1 Baseline Equivalence

## Objective

Prove source and target behavior are equivalent under normalized comparison.

## Required checks

1. Run source implementation and capture output.
2. Run target implementation and capture output.
3. Check key output snippets.
4. Normalize dynamic fields and run diff.
EOF_V1

cat > "$V2" <<'EOF_V2'
# V2 Failure Closure

## Objective

Prove failure-closure evidence chain is complete.

## Required checks

1. Trigger one expected failure (negative case).
2. Apply fix and document changed files/logic.
3. Re-run and prove pass.
4. Report in order: fail -> fix -> pass.
EOF_V2

cat > "$V3" <<'EOF_V3'
# V3 Gate Regression

## Objective

Validate gate/rule changes with strict regression proof.

## Required checks

1. Positive sample (exit 0).
2. Negative sample (exit 1).
3. Adversarial sample.
4. Run core regression suite.
5. Run full regression suite.
EOF_V3

cat > "$V4" <<'EOF_V4'
# V4 Adversarial Hardening

## Objective

Stress-test gate robustness against bypass-like inputs.

## Required checks

1. Mixed-language keywords.
2. Full-width/half-width punctuation variants.
3. Multi-line status confusion.
4. Evidence keyword obfuscation attempts.
EOF_V4

printf 'Created:\n- %s\n- %s\n- %s\n- %s\n- %s\n' "$BASE" "$V1" "$V2" "$V3" "$V4"
