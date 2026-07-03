#!/bin/sh
# gitsweep — clear stale git locks/temp litter left by sandboxed sessions.
#
# Background: Cowork's sandbox mounts this repo with unlink() denied inside
# .git/, so any git operation that crashes (or hits a pre-existing stale
# lock) leaves 0-byte *.lock files and tmp_obj_* litter it cannot remove.
# rename() IS permitted, so this script sweeps them into .git/sandbox-trash/
# instead of deleting. Two standing mitigations are already in .git/config:
#   core.createObject = rename   (objects land via rename -> no tmp litter)
# Run this any time git complains about an existing lock file:
#   sh tools/gitsweep.sh        (skips locks <60s old — a live git may own them)
#   sh tools/gitsweep.sh -f     (force: sweep regardless of age; use only when
#                                you know no git process is running)
# Prefer tools/git-sandbox.sh for day-to-day git in the sandbox — it sweeps
# before and after every command automatically.
set -e
cd "$(dirname "$0")/.."
mkdir -p .git/sandbox-trash
now=$(date +%s)
swept=0
for f in $(find .git -name '*.lock' -not -path '*/sandbox-trash/*') \
         $(find .git/objects -name 'tmp_obj_*' 2>/dev/null); do
  if [ "$1" != "-f" ]; then
    age=$(( now - $(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f") ))
    if [ "$age" -lt 60 ]; then
      echo "SKIP (age ${age}s — may be live): $f"
      continue
    fi
  fi
  mv "$f" ".git/sandbox-trash/$(basename "$f").$now.$swept" && swept=$((swept+1))
done
echo "gitsweep: $swept stale file(s) moved to .git/sandbox-trash/"
echo "(on a machine with full permissions you can empty that folder:"
echo "  rm -rf .git/sandbox-trash)"
