#!/usr/bin/env bash
# check-skills.sh - Every skill gate, in the order CI runs them. Needs a built CLI (pnpm -C cli build).
# Run: bash scripts/check-skills.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="node $REPO_ROOT/cli/dist/index.js"
# Lowest audit score a skill may have; raise it as skills improve, never lower it to pass.
MIN_SCORE=80

cd "$REPO_ROOT"

echo "=== Validate skills: structure, strict YAML, security patterns, audit floor $MIN_SCORE, marketplace cross-check ==="
$CLI validate --all --source skills --cross --min-score "$MIN_SCORE"

echo "=== Skill script tests (Python) ==="
# On Windows "python3" is often the Microsoft Store stub that exits 49 without running anything.
PYTHON=python3
python3 -c "" 2>/dev/null || PYTHON=python
for test_file in skills/*/scripts/test_*.py; do
  [ -f "$test_file" ] || continue
  echo "--- $test_file"
  (cd "$(dirname "$test_file")" && "$PYTHON" -B "$(basename "$test_file")" -v)
done

echo "=== Skill script tests (Node) ==="
shopt -s nullglob
node_tests=(skills/*/scripts/*.test.mjs)
if [ ${#node_tests[@]} -gt 0 ]; then
  node --test "${node_tests[@]}"
fi

echo "PASSED: all skill gates"
