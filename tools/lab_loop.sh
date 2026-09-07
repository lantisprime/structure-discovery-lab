#!/usr/bin/env bash
# The closed loop in one scheduled command (constitution A0, Milestone R):
#   observe (R0) -> attribute (R1) -> heal + PR (R4) -> gate + merge (R3) -> learn (R5)
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

if ! mkdir "$LOCK" 2>/dev/null; then
  echo "lab-loop: already running (lock $LOCK)"; exit 3
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

STEPS=(
  "$PY src/outcome_collect.py --all --gate"
  "$PY src/outcome_attribute.py --new"
  "$PY src/lab_heal.py --new --push"
  "$PY src/lab_gate.py --new"
  "$PY src/lab_learn.py --derive"
  "ledger commit: append-only diff of $LEDGERS -> commit + push origin master"
)
if [ "$MODE" = "--dry-run" ]; then
  for s in "${STEPS[@]}"; do echo "step $s"; done
  exit 0
fi

mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$LOG") 2>&1
echo "lab-loop: start $(date -u +%FT%TZ) in $REPO"

if [ -n "$(git status --porcelain)" ]; then echo "lab-loop: dirty tree, refusing"; exit 4; fi
if [ "$(git branch --show-current)" != "master" ]; then echo "lab-loop: not on master, refusing"; exit 4; fi
git fetch -q origin && git pull -q --ff-only origin master || { echo "lab-loop: cannot fast-forward master"; exit 4; }

for s in "${STEPS[@]:0:5}"; do
  echo; echo "── $s"
  $s || echo "   ↑ exit $? (recorded in the ledger; the loop continues)"
done

echo; echo "── ${STEPS[5]}"
if git diff --quiet -- $LEDGERS; then
  echo "no new rows"
else
  DEL=$(git diff --numstat -- $LEDGERS | awk '{d+=$2} END {print d+0}')
  if [ "$DEL" != "0" ]; then echo "lab-loop: ledger diff removes $DEL line(s); refusing to commit"; exit 5; fi
  $PY src/outcome_ledger.py --verify || exit 5
  git add $LEDGERS
  git -c user.name=lab-loop -c user.email=loop@structure-discovery.local commit -q -m "loop: ledger rows $(date -u +%FT%TZ)

Appended by tools/lab_loop.sh (observe/attribute/heal/gate/learn cycle)." \
    && git pull -q --rebase origin master && git push -q origin master && echo "pushed ledger rows"
fi
echo "lab-loop: end $(date -u +%FT%TZ)"
