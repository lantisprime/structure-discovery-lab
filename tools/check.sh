#!/usr/bin/env bash
# One-command health check for the whole lab (macOS + Linux).
# Runs every verifier and every non-browser test suite; add --e2e to also
# drive the browser suite (needs: pip install -r requirements-dev.txt &&
# python -m playwright install chromium).
#
#   ./tools/check.sh          # verifiers + tests
#   ./tools/check.sh --e2e    # + browser e2e against a throwaway server
set -u
cd "$(dirname "$0")/.."

PY=${PY:-}
if [ -z "$PY" ]; then
  if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi
fi
echo "interpreter: $PY"

fails=0
run() {
  echo
  echo "── $1"
  shift
  "$@" || { echo "   ↑ FAILED"; fails=$((fails+1)); }
}

run "runtime dependencies"        "$PY" webapp/test_lab_deps.py
run "ledger integrity"            "$PY" src/verify_ledger_integrity.py --quiet
run "frozen-artifact convention"  "$PY" src/lint_frozen_imports.py
run "domain neutrality"           "$PY" src/lint_domain_neutrality.py
run "design verifier"             "$PY" src/design_verifier.py
run "relational docs verifier"    "$PY" src/verify_relational_docs.py
run "repo tests (installer/ledger/webapp)" "$PY" -m pytest tests/ -q
run "webapp unit tests"           "$PY" -m pytest webapp/test_server.py webapp/test_routing.py -q
run "riemann regression tests"    "$PY" -m pytest riemann-zero-lab/tests -q

if [ "${1:-}" = "--e2e" ]; then
  PORT=8798
  "$PY" webapp/server.py $PORT >/dev/null 2>&1 &
  SRV=$!
  trap 'kill $SRV 2>/dev/null' EXIT
  sleep 2
  for t in console ledger admin agents approvals equations experiments help theorems wizard; do
    run "e2e: $t" "$PY" webapp/test_${t}_e2e.py "http://localhost:$PORT"
  done
fi

echo
if [ $fails -eq 0 ]; then
  echo "ALL CHECKS PASSED"
else
  echo "$fails CHECK(S) FAILED"
  exit 1
fi
