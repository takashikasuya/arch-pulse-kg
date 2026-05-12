#!/usr/bin/env bash
# Run component tests for CS-KG-STORE and generate evidence JSON.
# Usage: ./run_component_tests.sh [--venv <path>]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="${PYTHON:-python3}"
if [[ "${1:-}" == "--venv" && -n "${2:-}" ]]; then
    PYTHON="$2/bin/python"
fi

echo "=== CS-KG-STORE component tests ==="
echo "Python: $PYTHON"

PYTHONPATH="$SCRIPT_DIR/src" "$PYTHON" -m pytest tests/component/ -v \
    --tb=short \
    -p no:cacheprovider

echo ""
echo "Evidence generated at: evidence/TC-COMP-KG-STORE-002.json"
