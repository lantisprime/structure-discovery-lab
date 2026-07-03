#!/bin/sh
# git-sandbox — run any git command safely from Cowork's sandbox.
#
# The sandbox mount denies unlink() inside .git/, so git's rollback paths
# (reflog HEAD.lock, opportunistic index refresh, maintenance.lock) leave
# stale 0-byte locks that block the NEXT git command. This wrapper:
#   1. sweeps stale locks/litter into .git/sandbox-trash/ (rename is allowed)
#   2. runs   git --no-optional-locks <your args>   (skips the opportunistic
#      index-refresh lock that read-only commands would leak)
#   3. sweeps again, so nothing this command leaked blocks the next one
#
# Usage:  sh tools/git-sandbox.sh status
#         sh tools/git-sandbox.sh add -A
#         sh tools/git-sandbox.sh commit -m "message"
# On a normal machine plain git works fine; this wrapper is sandbox-only.
set -e
cd "$(dirname "$0")/.."
sh tools/gitsweep.sh -f >/dev/null
git --no-optional-locks "$@"
rc=$?
sh tools/gitsweep.sh -f >/dev/null
exit $rc
