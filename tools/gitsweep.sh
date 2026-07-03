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
#   sh tools/gitsweep.sh
# Safe by construction: only moves files matching *.lock and tmp_obj_*, and
# refuses locks younger than 60 seconds (a live git process may own them).
set -e
cd "$(dirname "$0")/.."
mkdir -p .git/sandbox-trash
now=$(date +%s)
swept=0
for f in $(find .git -name '*.lock' -not -path '*/sandbox-trash/*') \
         $(find .git/objects -name 'tmp_obj_*' 2>/dev/null); do
  age=$(( now - $(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f") ))
  if [ "$age" -lt 60 ]; then
    echo "SKIP (age ${age}s — may be live): $f"
    continue
  fi
  mv "$f" ".git/sandbox-trash/$(basename "$f").$now" && swept=$((swept+1))
done
echo "gitsweep: $swept stale file(s) moved to .git/sandbox-trash/"
echo "(on a machine with full permissions you can empty that folder:"
echo "  rm -rf .git/sandbox-trash)"
