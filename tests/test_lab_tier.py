#!/usr/bin/env python3
"""R5 full: tier recommendation from repeated eval rolls. Records are fixtures
(agent.txt + grade.json); no LLM, no dispatch.

Run: python3 -m pytest tests/test_lab_tier.py -q
"""
import importlib.util
import json
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, "src", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LT = load("lab_tier")
LL = LT.LL


def plant(root, eval_id, stamp, tier, grade):
    d = root / "results" / "agent_runs" / f"eval-{LT.G.record_slug(eval_id)}-{stamp}"
    d.mkdir(parents=True)
    (d / "agent.txt").write_text(f"agent: lab-proposer | model: {tier} | definition sha256: {'ab' * 32} | eval: {eval_id}\n")
    (d / "grade.json").write_text(json.dumps({"eval": eval_id, "grade": grade}))


def lab(tmp_path, tier="sonnet"):
    root = tmp_path / "lab"
    (root / "agents").mkdir(parents=True)
    (root / "agents" / "lab-proposer.md").write_text(f"---\nname: lab-proposer\nmodel: {tier}\n---\nbody\n")
    return root


def test_tier_recommendation_rules(tmp_path):
    root = lab(tmp_path)
    lessons = str(tmp_path / "lessons.jsonl")
    quiet = open(os.devnull, "w")
    assert LT.evals_of("lab-proposer") == ["P-1", "P-2"] and LT.evals_of("nobody") == []
    # (1) one roll is not an eval: insufficient rolls, no lesson
    plant(root, "P-1", "20260907T100000", "sonnet", "PASS"), plant(root, "P-2", "20260907T100001", "sonnet", "PASS")
    plant(root, "P-2", "20260907T090000", "haiku", "PASS")
    r = LT.report(str(root), "lab-proposer")
    assert r["current"] == "sonnet" and r["recommendation"] is None and "insufficient rolls" in r["reason"]
    assert LT.run(str(root), lessons, out=quiet) == [] and not os.path.exists(lessons)
    # (2) the current tier proven 3/3 on both evals, nothing cheaper proven: keep
    for i in (1, 2):
        plant(root, "P-1", f"20260907T10000{i + 1}", "sonnet", "PASS"), plant(root, "P-2", f"20260907T10001{i}", "sonnet", "PASS")
    r = LT.report(str(root), "lab-proposer")
    assert r["recommendation"] is None and "proven" in r["reason"]
    assert r["tally"]["P-1"]["sonnet"] == {"n": 3, "pass": 3}
    # (3) haiku 3/3 on P-2 only is not proven for the agent; 3/3 on P-1 too -> recommend the cheaper tier, once
    plant(root, "P-2", "20260907T090001", "haiku", "PASS"), plant(root, "P-2", "20260907T090002", "haiku", "PASS")
    assert LT.report(str(root), "lab-proposer")["recommendation"] is None
    for i in range(3):
        plant(root, "P-1", f"20260907T09000{i}", "haiku", "PASS")
    r = LT.report(str(root), "lab-proposer")
    assert r["recommendation"] == "haiku"
    new = LT.run(str(root), lessons, out=quiet)
    assert len(new) == 1 and new[0]["kind"] == "tier" and new[0]["recommended_tier"] == "haiku"
    assert new[0]["artifact"] == "agents/lab-proposer.md" and "propose the frontmatter change as a PR" in new[0]["lesson"]
    assert LT.run(str(root), lessons, out=quiet) == []                       # same evidence: not repeated
    assert (root / "agents" / "lab-proposer.md").read_text().count("model: sonnet") == 1   # never edited
    # (4) the window is the latest 5 per (eval, tier): an old haiku failure pushed out of the window does not
    #     count, a new one inside it does
    plant(root, "P-1", "20260907T090003", "haiku", "PASS"), plant(root, "P-1", "20260907T090004", "haiku", "PASS")
    plant(root, "P-1", "20260901T000000", "haiku", "FAIL")
    assert LT.report(str(root), "lab-proposer")["tally"]["P-1"]["haiku"] == {"n": 5, "pass": 5}
    plant(root, "P-1", "20260908T000000", "haiku", "FAIL")
    assert LT.report(str(root), "lab-proposer")["recommendation"] is None
    # (5) the current tier failing with a higher tier proven -> recommend the higher tier
    root2 = lab(tmp_path / "2", tier="haiku")
    for i in range(3):
        plant(root2, "P-1", f"20260907T00000{i}", "haiku", "PASS" if i else "FAIL")
        plant(root2, "P-2", f"20260907T00000{i}", "haiku", "PASS")
        plant(root2, "P-1", f"20260907T01000{i}", "sonnet", "PASS"), plant(root2, "P-2", f"20260907T01000{i}", "sonnet", "PASS")
    r = LT.report(str(root2), "lab-proposer")
    assert r["recommendation"] == "sonnet" and "haiku fails on P-1" in r["reason"]
    lessons2 = str(tmp_path / "lessons2.jsonl")
    assert LT.run(str(root2), lessons2, dry_run=True, out=quiet)[0]["recommended_tier"] == "sonnet"
    assert not os.path.exists(lessons2)                                       # dry-run appends nothing
    # (6) a record without a grade or tier is ignored, not fatal
    bad = root2 / "results" / "agent_runs" / "eval-p1-20260907T020000"
    bad.mkdir(), (bad / "agent.txt").write_text("agent: lab-proposer | eval: P-1\n")
    assert LT.report(str(root2), "lab-proposer")["recommendation"] == "sonnet"


def test_tier_cli_on_the_lab():
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "lab_tier.py"), "--recommend", "--dry-run"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "agents/lab-proposer.md: tier sonnet" in r.stdout and "tier:" in r.stdout
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "lab_tier.py"), "--report", "--agent", "lab-proposer"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0 and json.loads(r.stdout)["agent"] == "lab-proposer"
