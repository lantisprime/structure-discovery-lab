#!/usr/bin/env python3
"""Lessons ledger (R5, minimal): what the lab learned from every defect it closed.

    python3 src/lab_learn.py --derive          # append a lesson for each closed defect not yet recorded
    python3 src/lab_learn.py --for ARTIFACT    # print lessons relevant to an artifact (used by the healer)
    python3 src/lab_learn.py --add "text" --artifact PATH [--class CLASS]   # record a lesson by hand

A closed defect is a ledger slot whose history holds a defect row followed by
a PASS row. The lesson carries the defect's evidence, the introducing commit
(from the R1 attribution row when one exists), the commit at which it passed
again, the platform, and a one-line statement. `results/lessons.jsonl` is
append-only; `--derive` is idempotent (dedup by defect_key).
"""

import argparse
import datetime as _dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import outcome_ledger as OL  # noqa: E402

DEFAULT_LESSONS = os.path.join("results", "lessons.jsonl")
SCHEMA_VERSION = 1


def lessons_path(explicit=None):
    p = explicit or os.environ.get("LAB_LESSONS") or DEFAULT_LESSONS
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def now_ts():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_lessons(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def append_lessons(path, lessons):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for l in lessons:
            fh.write(json.dumps(l, sort_keys=True, ensure_ascii=True) + "\n")
    return lessons


def closed_defects(rows):
    """(defect_row, pass_row) pairs: a defect followed later by a PASS in the same slot."""
    by_slot = {}
    for r in rows:
        if r["source"] in ("attribution", "heal"):
            continue
        by_slot.setdefault(OL.slot(r), []).append(r)
    out = []
    for hist in by_slot.values():
        open_defect = None
        for r in hist:
            if r["severity"] == "defect":
                open_defect = open_defect or r
            elif r["signal"] == "PASS" and open_defect is not None:
                out.append((open_defect, r))
                open_defect = None
    return out


def attributions(rows):
    """Keyed per occurrence (defect_key, defect_commit), like R1 itself."""
    return {(r["detail"].get("defect_key"), r["detail"].get("defect_commit")): r
            for r in rows if r["source"] == "attribution"}


def derive(rows, existing):
    known = {(l.get("defect_key"), l.get("defect_commit")) for l in existing}
    attr = attributions(rows)
    lessons = []
    for defect, fixed in closed_defects(rows):
        key = "|".join(OL.state_key(defect))
        if (key, defect["commit"]) in known:
            continue
        a = attr.get((key, defect["commit"]), {}).get("detail", {})
        intro = a.get("introduced_by")
        text = (f"{defect['artifact']} {defect['signal']} ({defect['evidence'][:120]}); "
                f"introduced by {intro or 'unknown'}"
                + (f" via merge {a['merged_by']}" if a.get("merged_by") else "")
                + f"; passing again at {fixed['commit']} on {defect['detail'].get('subject') or 'n/a'}")
        lessons.append({"schema_version": SCHEMA_VERSION, "ts": now_ts(), "kind": "closed_defect",
                        "artifact": defect["artifact"], "artifact_class": defect["artifact_class"],
                        "defect_key": key, "defect_commit": defect["commit"],
                        "signal": defect["signal"], "evidence": defect["evidence"],
                        "introduced_by": intro, "merged_by": a.get("merged_by"),
                        "attribution_method": a.get("method"), "fixed_at": fixed["commit"],
                        "platform": defect["detail"].get("subject"), "lesson": text})
    return lessons


def relevant(lessons, artifact, artifact_class=None):
    same = [l for l in lessons if l.get("artifact") == artifact]
    cls = [l for l in lessons if artifact_class and l.get("artifact_class") == artifact_class
           and l.get("artifact") != artifact]
    return same + cls


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--derive", action="store_true")
    ap.add_argument("--for", dest="for_artifact")
    ap.add_argument("--add")
    ap.add_argument("--artifact")
    ap.add_argument("--class", dest="cls")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--lessons", default=None)
    a = ap.parse_args(argv)
    path = lessons_path(a.lessons)
    existing = read_lessons(path)
    if a.derive:
        rows = OL.read_rows(OL.ledger_path(a.ledger))
        new = derive(rows, existing)
        append_lessons(path, new)
        for l in new:
            print("lesson:", l["lesson"])
        print(f"lessons: {len(new)} new, {len(existing) + len(new)} total in {path}")
        return 0
    if a.add:
        if not a.artifact:
            print("--add needs --artifact")
            return 2
        l = {"schema_version": SCHEMA_VERSION, "ts": now_ts(), "kind": "manual", "artifact": a.artifact,
             "artifact_class": a.cls, "defect_key": None, "lesson": a.add}
        append_lessons(path, [l])
        print("lesson:", a.add)
        return 0
    if a.for_artifact:
        for l in relevant(existing, a.for_artifact, a.cls):
            print("-", l["lesson"])
        return 0
    ap.print_usage()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
