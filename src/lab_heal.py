#!/usr/bin/env python3
"""Healer (R4, minimal closed loop): take an open defect from the outcome
ledger, dispatch a repair agent in an isolated git worktree, gate the result
with the lab's full check battery plus the defect's own check, and open a pull
request. Merging is R3 and is NOT done here; the PR is the proposal.

    python3 src/lab_heal.py --new [--push] [--model sonnet] [--max-turns 40]
    python3 src/lab_heal.py --defect-key "<source|artifact|signal|hash>" [--push]

Without --push the branch and commit stay local (the worktree path is printed)
so the loop can be exercised offline. LAB_HEAL_AGENT_CMD overrides the agent
command (tests use a fake agent). Each attempt appends one `heal` row
(PROPOSED with the PR url / branch, or REJECTED with the gate's last lines);
the defect row itself is closed only when the collector observes it PASS.

Guardrails given to the agent, verbatim in the brief: preserve A1-A8; never
edit frozen results or existing ledger rows (append only); never touch
docs/THEOREM_GOVERNANCE.md A0 or the owner-reserved decisions; explain the
change in HEAL_NOTES.md at the worktree root.
"""

import argparse
import datetime as _dt
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import outcome_ledger as OL  # noqa: E402
import outcome_collect as OC  # noqa: E402
import outcome_attribute as OA  # noqa: E402
import artifact_registry as AR  # noqa: E402
import lab_learn as LL  # noqa: E402

# The agent may edit files and run the lab's own checks; it may NOT commit,
# push, or run arbitrary shell. The healer commits and gates after it exits.
DEFAULT_AGENT_CMD = (
    "claude -p --model {model} --max-turns {max_turns} --permission-mode acceptEdits "
    "--allowedTools Read Edit Write Grep Glob "
    "Bash(.venv/bin/python:*) Bash(python3:*) Bash(./tools/check.sh:*) "
    "Bash(git diff:*) Bash(git status:*) Bash(git log:*) Bash(git show:*) Bash(git blame:*) "
    "--disallowedTools Bash(git commit:*) Bash(git push:*) Bash(git checkout:*) Bash(git reset:*) "
    "Bash(gh:*) Bash(curl:*) Bash(wget:*) Bash(ssh:*) Bash(scp:*) "
    "--output-format text")
DEFAULT_GATE_CMD = "./tools/check.sh"
AGENT_TIMEOUT = 3600
HEAL_ATTEMPT_CAP = 3   # heal rows per occurrence; beyond it the R3 gate routes the defect to the owner
# Credentials never reach the agent's environment except the one it needs to
# talk to its own model provider (ANTHROPIC_API_KEY, when the CLI relies on it).
CREDENTIAL_ENV_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE_KEY|_KEY$|^AWS_|^GH_|^GITHUB_)", re.I)
CREDENTIAL_ENV_KEEP = {"ANTHROPIC_API_KEY"}
# Anything that lands in a ledger row from agent or gate output is redacted first.
SECRET_RE = re.compile(
    r"(?i)(?:(api[_-]?key|token|secret|password|passwd|authorization|bearer)\s*[:=]\s*)[^\s,;]+"
    r"|sk-[A-Za-z0-9_\-]{8,}|gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,}"
    r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----")


def redact(text):
    return SECRET_RE.sub(lambda m: (m.group(1) + "=<redacted>") if m.group(1) else "<redacted>", text or "")


def agent_env():
    env = {k: v for k, v in os.environ.items()
           if k in CREDENTIAL_ENV_KEEP or not CREDENTIAL_ENV_RE.search(k)}
    env.pop("CLAUDECODE", None)  # allow a nested headless session
    return env


def now_ts():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sh(argv, cwd, timeout=600, env=None, stdin=None):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                       env=env, input=stdin)
    return p.returncode, p.stdout, p.stderr


def slug(defect):
    s = re.sub(r"[^a-z0-9]+", "-", f"{defect['artifact']}-{defect['signal']}".lower()).strip("-")
    return f"heal/{s[:50]}-{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%d%H%M%S%f')[:-3]}"


# ---------------------------------------------------------------- brief ----

def brief_for(defect, rows, root):
    key = "|".join(OL.state_key(defect))
    attr = next((r for r in reversed(rows) if r["source"] == "attribution"
                 and r["detail"].get("defect_key") == key), None)
    reg = AR.classify(defect["artifact"], AR.build_registry(root)) or {"class": defect["artifact_class"]}
    lessons = LL.relevant(LL.read_lessons(LL.lessons_path()), defect["artifact"], reg["class"])
    check = OA.check_command(defect)
    lines = [
        "# Repair brief (autonomous healer, constitution A0 / Milestone R4)",
        "",
        "You are repairing ONE defect that the lab's outcome ledger observed. Work only in this",
        "checkout (a git worktree on its own branch). Do not run git commit or git push; the",
        "healer commits and gates your change after you finish.",
        "",
        "## Defect (ledger row)",
        "```json", json.dumps({k: defect[k] for k in ("source", "artifact", "artifact_class", "signal",
                                                      "evidence", "detail", "commit")}, indent=1), "```",
        f"Artifact class (registry): {reg['class']}" + (f", tier {reg.get('tier')}" if reg.get("tier") else ""),
    ]
    if check:
        lines += ["", "## The check that must pass when you are done", "```",
                  " ".join(shlex.quote(c) for c in check).replace(shlex.quote(sys.executable), ".venv/bin/python"),
                  "```"]
    if attr:
        lines += ["", "## Attribution (R1)", "```json", json.dumps(attr["detail"], indent=1), "```"]
    if lessons:
        lines += ["", "## Lessons already learned about this artifact or class"]
        lines += [f"- {l['lesson']}" for l in lessons[:8]]
    lines += [
        "",
        "## Guardrails (non-negotiable)",
        "- Preserve constitution articles A1-A8 (docs/THEOREM_GOVERNANCE.md Part 2). Never edit A0.",
        "- Frozen results, registrations and existing ledger rows are immutable: append, never rewrite.",
        "  If a result must change, it becomes a new version with its provenance recorded in the run",
        "  ledger row the way r3/r4 did (superseded_output_sha256_*, r*_note).",
        "- Owner-reserved decisions are not yours: amending A0, ratifying constitution entries,",
        "  unsealing holdout data, promoting an evidence grade to G3+. If the fix needs one, stop",
        "  and say so in HEAL_NOTES.md instead of doing it.",
        "- Smallest change that makes the check pass for the right reason. Do not weaken a test,",
        "  a verifier, or the check itself. Do not delete ledger rows.",
        "- `./tools/check.sh` must pass afterwards (the healer runs it as the gate).",
        "",
        "## Deliverable",
        "Edit the files needed, then write HEAL_NOTES.md at the checkout root: root cause (one",
        "paragraph), what you changed and why, how you verified it, and any follow-up you did not do.",
    ]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------- worktree ----

class HealWorktree:
    def __init__(self, root, branch, base="HEAD"):
        self.root, self.branch, self.base = root, branch, base
        self.path = tempfile.mkdtemp(prefix="lab-heal-")

    def __enter__(self):
        os.rmdir(self.path)
        rc, out, err = sh(["git", "worktree", "add", "--quiet", "-b", self.branch, self.path, self.base], self.root)
        if rc != 0:
            raise RuntimeError(f"worktree add failed: {err.strip()}")
        # The lab's interpreter lives in the main checkout's .venv (ignored by git);
        # link it so the brief's check command and ./tools/check.sh run with the
        # right dependencies instead of the agent hunting for one (live run 2026-09-07).
        venv = os.path.join(self.root, ".venv")
        if os.path.isdir(venv) and not os.path.lexists(os.path.join(self.path, ".venv")):
            os.symlink(venv, os.path.join(self.path, ".venv"))
        return self.path

    def __exit__(self, *exc):
        return False  # kept for inspection; remove() is explicit

    def remove(self):
        sh(["git", "worktree", "remove", "--force", self.path], self.root)
        sh(["git", "worktree", "prune"], self.root)


# ---------------------------------------------------------------- steps ----

def dispatch_agent(wt, brief, model, max_turns, agent_cmd=None):
    cmd = (agent_cmd or os.environ.get("LAB_HEAL_AGENT_CMD") or DEFAULT_AGENT_CMD).format(
        model=model, max_turns=max_turns)
    argv = shlex.split(cmd, posix=(os.name != "nt"))  # keep Windows backslash paths intact
    with open(os.path.join(wt, "HEAL_BRIEF.md"), "w", encoding="utf-8") as fh:
        fh.write(brief)
    try:
        rc, out, err = sh(argv, wt, timeout=AGENT_TIMEOUT, env=agent_env(), stdin=brief)
    except subprocess.TimeoutExpired:
        return 124, "", "agent timed out"
    except OSError as e:
        return 127, "", f"agent command failed to start: {e}"
    return rc, out, err


def gate(wt, defect, gate_cmd=None):
    """(ok, summary). ok iff the gate command exits 0 AND the defect's own check passes."""
    cmd = gate_cmd or os.environ.get("LAB_HEAL_GATE_CMD") or DEFAULT_GATE_CMD
    rc, out, err = sh(shlex.split(cmd, posix=(os.name != "nt")), wt, timeout=1800)
    tail = "\n".join((out + err).strip().splitlines()[-6:])
    if rc != 0:
        return False, f"gate exit {rc}: {tail}"
    check = OA.check_command(defect)
    if check:
        rc2, out2, err2 = sh(check, wt, timeout=900)
        if rc2 != 0:
            return False, f"gate green but the defect's check still exits {rc2}: " + \
                          "\n".join((out2 + err2).strip().splitlines()[-3:])
    return True, tail


def commit_all(wt, message):
    sh(["git", "add", "-A", "--", ".", ":(exclude).venv"], wt)
    rc, out, err = sh(["git", "-c", "user.name=lab-healer", "-c", "user.email=healer@structure-discovery.local",
                       "commit", "-q", "-m", message], wt)
    if rc != 0:
        return None
    rc, out, err = sh(["git", "rev-parse", "--short", "HEAD"], wt)
    return out.strip()


def changed_files(wt):
    rc, out, err = sh(["git", "status", "--porcelain", "--", ".", ":(exclude).venv"], wt)
    return [l[3:] for l in out.splitlines() if l.strip()]


def open_pr(wt, branch, title, body, base="master"):
    rc, out, err = sh(["git", "push", "-q", "-u", "origin", branch], wt, timeout=300)
    if rc != 0:
        return None, f"push failed: {err.strip()[-300:]}"
    rc, out, err = sh(["gh", "pr", "create", "--base", base, "--head", branch, "--title", title,
                       "--body", body], wt, timeout=300)
    return (out.strip() if rc == 0 else None), (err.strip()[-300:] if rc != 0 else "")


# --------------------------------------------------------------- driver ----

def heal_one(defect, rows, root, ledger, model="sonnet", max_turns=40, push=False,
             agent_cmd=None, gate_cmd=None, keep_worktree=False, base="master", out=sys.stdout):
    brief = brief_for(defect, rows, root)
    branch = slug(defect)
    ctx = OC.Ctx(root, rows)
    key = "|".join(OL.state_key(defect))
    base_detail = {"subject": defect["detail"].get("subject", ""), "defect_key": key,
                   "defect_commit": defect["commit"], "branch": branch, "model": model, "base": base}

    def reject(stage, why, extra=None, keep=False):
        row = ctx.row("heal", defect["artifact"], defect["artifact_class"], "REJECTED",
                      redact(why)[:OL.EVIDENCE_MAX], {**base_detail, "stage": stage, **(extra or {})})
        OL.append_rows(ledger, [row])
        print(f"REJECTED ({stage}): {redact(why)}", file=out)
        if keep:
            print(f"worktree kept for inspection: {wt}", file=out)
        return row

    hw = HealWorktree(root, branch)
    wt = hw.__enter__()
    print(f"heal: {defect['artifact']} {defect['signal']} -> worktree {wt} on {branch}", file=out)
    keep = False
    try:
        rc, aout, aerr = dispatch_agent(wt, brief, model, max_turns, agent_cmd)
        files = [f for f in changed_files(wt) if f not in ("HEAL_BRIEF.md",)]
        notes_path = os.path.join(wt, "HEAL_NOTES.md")
        notes = redact(open(notes_path, encoding="utf-8").read()) if os.path.exists(notes_path) else ""
        # A non-zero exit (e.g. "Reached max turns") with files changed is still a
        # candidate: the gate decides, not the exit code (live run 2026-09-07: the
        # agent had made the exact fix and written its notes before the turn cap).
        base_detail.update({"agent_exit": rc, "files_changed": files,
                            "agent_tail": redact((aout.strip() or aerr.strip())[-300:])})
        if not files:
            why = f"agent exit {rc}, no file changed" + (f": {(aout.strip() or aerr.strip())[-200:]}" if (aout + aerr).strip() else "")
            return reject("agent", why)
        os.remove(os.path.join(wt, "HEAL_BRIEF.md"))
        ok, summary = gate(wt, defect, gate_cmd)
        summary = redact(summary)
        if not ok:
            keep = True
            return reject("gate", summary, {"gate_tail": summary[-1500:]}, keep=True)
        title = f"heal: {defect['artifact']} {defect['signal']} ({defect['detail'].get('subject', '')})"
        sha = commit_all(wt, title + "\n\nAutonomous repair (R4 healer). Brief and notes in HEAL_NOTES.md.\n\n"
                         f"Defect key: {key}\n\nCo-Authored-By: lab-healer <healer@structure-discovery.local>")
        if not sha:
            return reject("commit", "git commit failed in the heal worktree")
        pr_url, pr_err = (None, "")
        if push:
            body = (f"Autonomous repair proposed by `src/lab_heal.py` (Milestone R4, constitution A0) for the "
                    f"outcome-ledger defect `{key}`.\n\n## Agent notes\n\n{notes or '(no HEAL_NOTES.md written)'}\n\n"
                    f"## Gate\n\n```\n{summary}\n```\n\nMerging is R3: `src/lab_gate.py` merges this when the required "
                    "CI checks are green, the defect's check passes at this head, the scope is clean and an "
                    "independent verifier of a different model family agrees; otherwise it closes or routes it.")
            pr_url, pr_err = open_pr(wt, branch, title, body, base=base)
        ev = f"PROPOSED {pr_url or branch} commit {sha}; gate green" + (f"; {redact(pr_err)}" if pr_err else "")
        row = ctx.row("heal", defect["artifact"], defect["artifact_class"], "PROPOSED", ev[:OL.EVIDENCE_MAX],
                      {**base_detail, "stage": "proposed", "commit": sha, "pr": pr_url, "notes": notes[:2000],
                       "gate_tail": summary[-600:]})
        OL.append_rows(ledger, [row])
        print(ev, file=out)
        keep = keep_worktree or not pr_url
        if not pr_url:
            print(f"branch {branch} committed locally at {sha}; worktree kept: {wt}", file=out)
        return row
    except Exception as e:  # never leak a worktree or lose the signal
        return reject("exception", f"{type(e).__name__}: {e}")
    finally:
        if not keep and not keep_worktree:
            hw.remove()


def run(ledger, root=ROOT, defect_key=None, **kw):
    rows = OL.read_rows(ledger)
    # Open defects without a pending proposal for this same occurrence. A proposal is
    # pending until the R3 gate has decided it (a `gate` row for the same branch);
    # a rejected one is retried, up to HEAL_ATTEMPT_CAP attempts per occurrence.
    gated = {(r["detail"].get("defect_key"), r["detail"].get("defect_commit"), r["detail"].get("branch"))
             for r in rows if r["source"] == "gate"}
    pending = {(r["detail"].get("defect_key"), r["detail"].get("defect_commit"))
               for r in rows if r["source"] == "heal" and r["signal"] == "PROPOSED"
               and (r["detail"].get("defect_key"), r["detail"].get("defect_commit"), r["detail"].get("branch")) not in gated}
    attempts = {}
    for r in rows:
        if r["source"] == "heal":
            k = (r["detail"].get("defect_key"), r["detail"].get("defect_commit"))
            attempts[k] = attempts.get(k, 0) + 1
    todo = [d for d in OA.open_defects(rows)
            if ("|".join(OL.state_key(d)), d["commit"]) not in pending
            and attempts.get(("|".join(OL.state_key(d)), d["commit"]), 0) < HEAL_ATTEMPT_CAP]
    if defect_key:
        todo = [r for r in rows if "|".join(OL.state_key(r)) == defect_key and r["severity"] == "defect"][-1:]
    if not todo:
        print("heal: no open defects", file=kw.get("out", sys.stdout))
        return []
    return [heal_one(d, rows, root, ledger, **kw) for d in todo]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new", action="store_true")
    g.add_argument("--defect-key")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--keep-worktree", action="store_true")
    ap.add_argument("--base", default="master", help="PR base branch (default master)")
    a = ap.parse_args(argv)
    ledger = OL.ledger_path(a.ledger)
    if OL.verify_ledger(ledger):
        print("refusing to work from an invalid ledger")
        return 2
    rows = run(ledger, defect_key=a.defect_key, model=a.model, max_turns=a.max_turns, push=a.push,
               keep_worktree=a.keep_worktree, base=a.base)
    return 0 if all(r["signal"] == "PROPOSED" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
