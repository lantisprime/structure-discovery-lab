#!/bin/bash
# Stable runner for the Unified Theorem Engine feasibility probe (scratch only).
S="$(dirname "$0")"
V="$S/euclid-venv/bin/python"
export EUCLID_BACKEND=native
if [ "${1:-}" = "introspect" ]; then
  $V -c "import euclid_mcp, inspect; import euclid_mcp.server as s; print(euclid_mcp.__file__); print([n for n in dir(s) if not n.startswith('_')]); print('reason', inspect.signature(s.reason)); print('diagnose', inspect.signature(s.diagnose)); print('what_if', inspect.signature(s.what_if)); print('check_kb', inspect.signature(s.check_kb)); print('explain', inspect.signature(s.explain)); print('register_kb', inspect.signature(s.register_kb))"
  exit 0
fi
if [ "${1:-}" = "eq" ]; then
  $V "$S/eq_poc.py"; echo "=== second run"; $V "$S/eq_poc.py" | tail -1
  exit 0
fi
$V "$S/ute_poc.py"
