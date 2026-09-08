#!/usr/bin/env bash
# The closed loop in one scheduled command (constitution A0, Milestone R):
#   observe incl. replay (R0/R4) -> attribute (R1) -> heal + PR (R4) -> gate + merge (R3) -> learn + re-tier (R5)
# then commit the appended ledger/lessons rows to master (append-only, verified).
#
#   ./tools/lab_loop.sh                  run one cycle now
#   ./tools/lab_loop.sh --dry-run        print the steps, run nothing
#   ./tools/lab_loop.sh --install-launchd   schedule every 6 h on this Mac (launchd)
#   ./tools/lab_loop.sh --uninstall-launchd
#   ./tools/lab_loop.sh --print-cron     the equivalent crontab line (Linux)
#
# Needs: gh auth, the repair agent's provider auth (claude), the verifier's
# (pi/LiteLLM or codex). Refuses to run on a dirty tree or off master. One
# instance at a time (LAB_LOOP_LOCK). Logs: ~/Library/Logs/lab-loop/ (or
# $LAB_LOOP_LOG_DIR).
set -u
cd "$(dirname "$0")/.."
REPO=$(pwd)
PY=${PY:-.venv/bin/python}
LOCK=${LAB_LOOP_LOCK:-${TMPDIR:-/tmp}/lab-loop.lock}
LOG_DIR=${LAB_LOOP_LOG_DIR:-$HOME/Library/Logs/lab-loop}
PLIST="$HOME/Library/LaunchAgents/local.lab-loop.plist"
LEDGERS="results/outcome_ledger.jsonl results/lessons.jsonl"
MODE=${1:-run}

case "$MODE" in
  --print-cron)
    echo "0 */6 * * * cd $REPO && PATH=/opt/homebrew/bin:/usr/local/bin:\$PATH ./tools/lab_loop.sh >> $LOG_DIR/cron.log 2>&1"
    exit 0 ;;
  --install-launchd)
    mkdir -p "$(dirname "$PLIST")" "$LOG_DIR"
    cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>local.lab-loop</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$REPO/tools/lab_loop.sh</string></array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>StartInterval</key><integer>21600</integer>
  <key>RunAtLoad</key><false/>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>HOME</key><string>$HOME</string>
  </dict>
  <key>StandardOutPath</key><string>$LOG_DIR/launchd.out.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/launchd.err.log</string>
</dict></plist>
EOF
    launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$PLIST" && echo "installed $PLIST (every 6 h); launchctl list | grep lab-loop"
    exit $? ;;
  --uninstall-launchd)
    launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    rm -f "$PLIST" && echo "removed $PLIST"
    exit 0 ;;
  --dry-run|run) ;;
  *) echo "usage: $0 [--dry-run|--install-launchd|--uninstall-launchd|--print-cron]"; exit 2 ;;
esac

# One instance at a time. A lock left by a killed run (its pid is gone) is stale
# and taken over; a live pid means another cycle is still running.
take_lock() {
  mkdir "$LOCK" 2>/dev/null && { echo $$ > "$LOCK/pid"; return 0; }
  local pid; pid=$(cat "$LOCK/pid" 2>/dev/null || echo "")
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then return 1; fi
  if [ -z "$pid" ] && [ -z "${LAB_LOOP_LOCK_TAKEOVER:-}" ]; then return 1; fi   # foreign lock dir: leave it
  rm -rf "$LOCK" && mkdir "$LOCK" 2>/dev/null && { echo $$ > "$LOCK/pid"; return 0; }
  return 1
}
if ! take_lock; then echo "lab-loop: already running (lock $LOCK)"; exit 3; fi
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT

# step NAME ARGS...: print the step; run it unless --dry-run. Arguments are
# passed as an array, never re-split (review finding 7).
step() {
  echo; echo "step $*"
  [ "$MODE" = "--dry-run" ] && return 0
  "$@" || echo "   ↑ exit $? (recorded in the ledger; the loop continues)"
}

if [ "$MODE" != "--dry-run" ]; then
  mkdir -p "$LOG_DIR"
  LOG="$LOG_DIR/$(date -u +%Y%m%dT%H%M%SZ).log"
  exec > >(tee -a "$LOG") 2>&1
  echo "lab-loop: start $(date -u +%FT%TZ) in $REPO"
  if [ -n "$(git status --porcelain)" ]; then echo "lab-loop: dirty tree, refusing"; exit 4; fi
  if [ "$(git branch --show-current)" != "master" ]; then echo "lab-loop: not on master, refusing"; exit 4; fi
  git fetch -q origin && git pull -q --ff-only origin master || { echo "lab-loop: cannot fast-forward master"; exit 4; }
fi

step "$PY" src/outcome_collect.py --all --gate
step "$PY" src/agent_eval_dispatch.py --stale
step "$PY" src/outcome_attribute.py --new
step "$PY" src/lab_heal.py --new --push
step "$PY" src/lab_gate.py --new
step "$PY" src/lab_learn.py --derive
step "$PY" src/lab_tier.py --recommend

echo; echo "step ledger commit: append-only diff of $LEDGERS + new dispatch records under results/agent_runs -> commit + push origin master"
[ "$MODE" = "--dry-run" ] && exit 0
# New eval/proposal records are new files only (the dispatcher never rewrites a
# record); a modified tracked record is an append-only violation: refuse, exit 5.
NEW_RECORDS=$(git ls-files --others --exclude-standard -- results/agent_runs)
MODIFIED_RECORDS=$(git diff --name-only -- results/agent_runs)
if [ -n "$MODIFIED_RECORDS" ]; then
  echo "lab-loop: historical dispatch record(s) modified (records are append-only); refusing to commit:"
  echo "$MODIFIED_RECORDS"; exit 5
fi
if git diff --quiet -- $LEDGERS && [ -z "$NEW_RECORDS" ]; then
  echo "no new rows"
else
  DEL=$(git diff --numstat -- $LEDGERS | awk '{d+=$2} END {print d+0}')
  if [ "$DEL" != "0" ]; then echo "lab-loop: ledger diff removes $DEL line(s); refusing to commit"; exit 5; fi
  $PY src/outcome_ledger.py --verify || exit 5
  git add $LEDGERS
  [ -n "$NEW_RECORDS" ] && echo "$NEW_RECORDS" | xargs git add --
  git -c user.name=lab-loop -c user.email=loop@structure-discovery.local commit -q -m "loop: ledger rows $(date -u +%FT%TZ)

Appended by tools/lab_loop.sh (observe/evals/attribute/heal/gate/learn cycle)." \
    && git pull -q --rebase origin master && git push -q origin master && echo "pushed ledger rows"
fi
echo "lab-loop: end $(date -u +%FT%TZ)"
