#!/usr/bin/env python3
"""Tier recommendation from repeated eval rolls (R5 full).

    python3 src/lab_tier.py --recommend [--agent lab-proposer] [--dry-run]
    python3 src/lab_tier.py --report   [--agent NAME]

For each agent, every dated eval record under results/agent_runs/ (all rolls,
not only the latest) is read: agent.txt names the tier and the definition
sha256 (only rolls against the agent's current definition count), grade.json
the grade.
Per (eval, tier) the latest <= 5 rolls count. A tier is *proven* for an agent
when every one of its evals has >= 3 rolls at that tier and all of them PASS.
The recommendation (R2 review F19 guard: one roll is not an eval):

  - a cheaper tier than the current one is proven      -> recommend it (cost)
  - the current tier has >= 3 rolls on some eval with a failure
    and a higher tier is proven                        -> recommend it (quality)
  - fewer than 3 rolls at the current tier on any eval -> "insufficient rolls"
  - otherwise                                          -> keep

A recommendation is written as a lesson (kind `tier`, artifact agents/<name>.md)
once per distinct (recommendation, evidence): the frontmatter edit itself stays
a pull request, never an automatic change.
"""

import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import outcome_collect as OC  # noqa: E402
import artifact_registry as AR  # noqa: E402
import lab_learn as LL  # noqa: E402
import grade_agent_eval as G  # noqa: E402

TIERS = ("haiku", "sonnet", "opus")      # cheapest first
ROLLS_WINDOW = 5
ROLLS_MIN = 3
MODEL_RE = re.compile(r"\bmodel: ([A-Za-z0-9._-]+)")


def evals_of(agent):
    prefix = next((p for p, a in OC.AGENT_FOR_PREFIX.items() if a == agent), None)
    return [e for e in G.RECORDS if e.split("-")[0] == prefix] if prefix else []


def definition_sha(root, agent):
    path = os.path.join(root, "agents", f"{agent}.md")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return OC.sha256_bytes(fh.read())


def rolls(root, eval_id, digest=None):
    """[(stamp, tier, grade)] for every dated record of an eval, oldest first.
    With `digest`, only records whose agent.txt names that definition sha256
    count: a roll against an older definition is not evidence about this one
    (review finding 3)."""
    out = []
    for d in sorted(glob.glob(os.path.join(root, "results", "agent_runs", f"eval-{G.record_slug(eval_id)}-*"))):
        m = G.DATED_RE.search(d)
        if not os.path.isdir(d) or not m:
            continue
        try:
            with open(os.path.join(d, "agent.txt"), encoding="utf-8") as fh:
                line = fh.read()
            with open(os.path.join(d, "grade.json"), encoding="utf-8") as fh:
                grade = json.load(fh).get("grade")
        except (OSError, json.JSONDecodeError, AttributeError):
            continue
        tier = MODEL_RE.search(line)
        if tier and grade and (digest is None or digest in line):
            out.append((m.group(1) + (m.group(2) or ""), tier.group(1), grade))
    return out


def tally(root, agent):
    """{eval: {tier: {"n": rolls counted, "pass": passes}}} over the latest <= ROLLS_WINDOW
    per (eval, tier), counting only rolls made against the agent's current definition."""
    t = {}
    digest = definition_sha(root, agent)
    for ev in evals_of(agent):
        per_tier = {}
        for stamp, tier, grade in rolls(root, ev, digest):
            per_tier.setdefault(tier, []).append(grade)
        t[ev] = {tier: {"n": len(g[-ROLLS_WINDOW:]), "pass": sum(1 for x in g[-ROLLS_WINDOW:] if x == "PASS")}
                 for tier, g in per_tier.items()}
    return t


def proven(t, tier):
    return bool(t) and all(c.get(tier, {}).get("n", 0) >= ROLLS_MIN and c[tier]["pass"] == c[tier]["n"]
                           for c in t.values())


def recommend(t, current):
    """(recommendation tier or None, reason). A proven cheaper tier wins even
    when the current tier fails: proven is proven, and cost is the point
    (review finding 6, a deliberate tie-break)."""
    rank = {tier: i for i, tier in enumerate(TIERS)}
    if current not in rank:
        return None, f"current tier {current!r} is not a known tier {TIERS}"
    cheaper = [x for x in TIERS if rank[x] < rank[current] and proven(t, x)]
    if cheaper:
        return cheaper[0], f"{cheaper[0]} is proven on every eval ({ROLLS_MIN}+ rolls, all PASS); cheaper than {current}"
    short = [ev for ev, c in t.items() if c.get(current, {}).get("n", 0) < ROLLS_MIN]
    if short or not t:
        return None, f"insufficient rolls at {current} (< {ROLLS_MIN}) on {', '.join(short) or 'every eval'}"
    failing = [ev for ev, c in t.items() if c[current]["pass"] < c[current]["n"]]
    if failing:
        higher = [x for x in TIERS if rank[x] > rank[current] and proven(t, x)]
        if higher:
            return higher[0], f"{current} fails on {', '.join(failing)}; {higher[0]} is proven on every eval"
        return None, f"{current} fails on {', '.join(failing)} and no higher tier is proven yet"
    return None, f"{current} is proven on every eval; no cheaper tier is"


def report(root, agent):
    reg = AR.build_registry(root)
    current = (reg.get(f"agents/{agent}.md") or {}).get("tier")
    t = tally(root, agent)
    rec, why = recommend(t, current)
    return {"agent": agent, "artifact": f"agents/{agent}.md", "current": current, "tally": t,
            "recommendation": rec, "reason": why}


def agents_with_evals(root):
    return sorted({a for a in OC.AGENT_FOR_PREFIX.values() if evals_of(a)
                   and os.path.exists(os.path.join(root, "agents", f"{a}.md"))})


def tier_lesson(r):
    return {"schema_version": LL.SCHEMA_VERSION, "ts": LL.now_ts(), "kind": "tier", "artifact": r["artifact"],
            "artifact_class": "agent", "defect_key": None, "current_tier": r["current"],
            "recommended_tier": r["recommendation"], "tally": r["tally"],
            "lesson": f"{r['artifact']}: re-tier {r['current']} -> {r['recommendation']} ({r['reason']}); "
                      f"propose the frontmatter change as a PR"}


def run(root, lessons_path, agents=None, dry_run=False, out=sys.stdout):
    existing = LL.read_lessons(lessons_path)
    new = []
    for agent in agents or agents_with_evals(root):
        r = report(root, agent)
        print(f"{r['artifact']}: tier {r['current']}; " + (f"recommend {r['recommendation']}" if r["recommendation"]
                                                          else "keep") + f" -- {r['reason']}", file=out)
        if not r["recommendation"]:
            continue
        l = tier_lesson(r)
        last = next((x for x in reversed(existing) if x.get("kind") == "tier" and x.get("artifact") == r["artifact"]), None)
        if last and (last.get("recommended_tier"), last.get("current_tier"), last.get("tally")) == \
                (l["recommended_tier"], l["current_tier"], l["tally"]):
            continue                                        # already on record for this evidence
        new.append(l)
    if new and not dry_run:
        LL.append_lessons(lessons_path, new)
    print(f"tier: {len(new)} recommendation(s) {'(dry-run)' if dry_run else 'recorded'}", file=out)
    return new


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--recommend", action="store_true")
    g.add_argument("--report", action="store_true")
    ap.add_argument("--agent", action="append", default=None)
    ap.add_argument("--lessons", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.report:
        for agent in a.agent or agents_with_evals(ROOT):
            print(json.dumps(report(ROOT, agent), indent=1))
        return 0
    run(ROOT, LL.lessons_path(a.lessons), a.agent, a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
