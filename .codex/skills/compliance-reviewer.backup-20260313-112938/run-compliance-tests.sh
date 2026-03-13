#!/usr/bin/env bash
set -euo pipefail

TEST_DIR="/home/jf3096/.codex/skills/compliance-reviewer/tests"

if [ "${1:-}" = "--core-only" ]; then
  python3 -m pytest -q \
    "$TEST_DIR/test_hook_examples.py" \
    "$TEST_DIR/test_hook_rules.py" \
    "$TEST_DIR/test_hook_consistency.py"
  exit 0
fi

python3 -m pytest -q "$TEST_DIR"
