#!/usr/bin/env python3
"""Standalone lab agent — runs INDEPENDENTLY of Claude Desktop/CLI.

Talks directly to an LLM API (Anthropic, or any OpenAI-compatible endpoint)
using the keys/models configured in the web console's Admin page, and
operates the lab through a deliberately narrow tool belt:

  run_job(name)        execute a WHITELISTED lab job (same registry as the
                       Run centre: gates, registered executors, analysis,
                       maintenance) and return its output
  read_file(path)      read files under docs/ results/ src/ evals/ tools/
  list_dir(path)       list those directories
  set_status(...)      publish progress to results/agent_status.json
                       (visible live in the Run centre)

It cannot run arbitrary shell, cannot write lab files (only jobs can, and
each registered executor is self-gated on human approval), and it writes a
final report to results/agent_runs/.

Usage:
  python3 webapp/agent_runner.py --task "Run all three gates and summarize"
  python3 webapp/agent_runner.py --provider openai --task "..."
Stdlib only. Exit 0 on completed report.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from server import JOB_DEFS, job_argv, get_api_key, jd, cli_argv  # noqa: E402

STATUS = os.path.join(ROOT, "results", "agent_status.json")
READ_PREFIXES = ("docs/", "results/", "src/", "evals/", "tools/", "README")
MAX_TURNS = 24
JOB_TIMEOUT = 1800

TOOLS = [
    {"name": "run_job",
     "description": "Execute a whitelisted lab job and get its full output. "
                    "Jobs: " + ", ".join(f"{k} ({v['desc']})"
                                         for k, v in JOB_DEFS.items()
                                         if k != "git_commit"),
     "input_schema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]}},
    {"name": "read_file",
     "description": "Read a repo file (docs/, results/, src/, evals/, tools/).",
     "input_schema": {"type": "object", "properties": {
         "path": {"type": "string"}}, "required": ["path"]}},
    {"name": "list_dir",
     "description": "List a repo directory (same prefixes as read_file).",
     "input_schema": {"type": "object", "properties": {
         "path": {"type": "string"}}, "required": ["path"]}},
    {"name": "set_status",
     "description": "Publish live progress (shown in the web console).",
     "input_schema": {"type": "object", "properties": {
         "stage": {"type": "string"}, "progress": {"type": "string"}},
         "required": ["stage"]}},
]

SYSTEM = """You are the Structure Discovery Lab's standalone operator agent.
Governance is absolute: nothing counts unless registered before it ran; the
registered executors refuse to run unapproved registrations (that gate is in
code, not your judgment); exploratory numbers are never citable. Prefer
running the three gates (design_verifier, verify_docs, lint_frozen) before
and after anything that changes artifacts. Be concise. When the task is
done, reply with a plain-text final report (no tool call)."""


def safe_path(p):
    p = p.lstrip("/")
    if ".." in p or not p.startswith(READ_PREFIXES):
        raise ValueError(f"path not allowed: {p}")
    return os.path.join(ROOT, p)


def do_tool(name, args):
    if name == "run_job":
        job = args["name"]
        if job not in JOB_DEFS or job == "git_commit":
            return f"ERROR: job '{job}' not in whitelist"
        r = subprocess.run(job_argv(job, {}), cwd=ROOT, timeout=JOB_TIMEOUT,
                           capture_output=True, text=True)
        out = (r.stdout + r.stderr)[-8000:]
        return f"[exit {r.returncode}]\n{out}"
    if name == "read_file":
        return open(safe_path(args["path"]), errors="replace").read()[:20000]
    if name == "list_dir":
        return "\n".join(sorted(os.listdir(safe_path(args["path"]))))
    if name == "set_status":
        json.dump({"agent": "standalone-runner", "stage": args.get("stage"),
                   "progress": args.get("progress", ""),
                   "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
                  open(STATUS, "w"), indent=1)
        return "status published"
    return f"ERROR: unknown tool {name}"


# ---------------------------------------------------------------- providers
def _post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers)
    return json.load(urllib.request.urlopen(req, timeout=180))


def call_anthropic(prov, messages):
    if not prov["key"]:
        raise SystemExit(f"No API key for provider '{prov['id']}' — set it "
                         f"on the Admin page.")
    body = {"model": prov["model"] or "claude-haiku-4-5-20251001",
            "max_tokens": 4000, "system": SYSTEM, "tools": TOOLS,
            "messages": messages}
    # effort mapping (Admin roles): deep/balanced enable extended thinking
    budget = {"deep": 8000, "balanced": 2048}.get(prov.get("effort"))
    if budget:
        body["thinking"] = {"type": "enabled", "budget_tokens": budget}
        body["max_tokens"] = budget + 4000
    try:
        r = _post(prov["base"].rstrip("/") + "/v1/messages", body,
                  {"x-api-key": prov["key"],
                   "anthropic-version": "2023-06-01",
                   "content-type": "application/json"})
    except urllib.error.HTTPError as e:
        if budget and e.code == 400:      # model without extended thinking
            body.pop("thinking"); body["max_tokens"] = 4000
            r = _post(prov["base"].rstrip("/") + "/v1/messages", body,
                      {"x-api-key": prov["key"],
                       "anthropic-version": "2023-06-01",
                       "content-type": "application/json"})
        else:
            raise
    calls = [{"id": c["id"], "name": c["name"], "args": c["input"]}
             for c in r.get("content", []) if c.get("type") == "tool_use"]
    text = "".join(c.get("text", "") for c in r.get("content", [])
                   if c.get("type") == "text")
    return text, calls, r


def call_openai(prov, messages):
    if not prov["key"]:
        raise SystemExit(f"No API key for provider '{prov['id']}' — set it "
                         f"on the Admin page.")
    oa_tools = [{"type": "function", "function": {
        "name": t["name"], "description": t["description"],
        "parameters": t["input_schema"]}} for t in TOOLS]
    body = {"model": prov["model"] or "gpt-4o-mini",
            "messages": [{"role": "system", "content": SYSTEM}] + messages,
            "tools": oa_tools}
    eff = {"fast": "low", "balanced": "medium", "deep": "high"}.get(
        prov.get("effort"))
    if eff:
        body["reasoning_effort"] = eff
    hdr = {"Authorization": f"Bearer {prov['key']}",
           "content-type": "application/json"}
    url = prov["base"].rstrip("/") + "/chat/completions"
    try:
        r = _post(url, body, hdr)
    except urllib.error.HTTPError as e:
        if eff and e.code in (400, 422):  # provider without reasoning_effort
            body.pop("reasoning_effort")
            r = _post(url, body, hdr)
        else:
            raise
    msg = r["choices"][0]["message"]
    calls = [{"id": c["id"], "name": c["function"]["name"],
              "args": json.loads(c["function"]["arguments"] or "{}")}
             for c in (msg.get("tool_calls") or [])]
    return msg.get("content") or "", calls, msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--provider", default=None,
                    help="provider id from the Admin registry")
    ap.add_argument("--role", default=None,
                    choices=["analyst", "executor", "reviewer"],
                    help="use this role's provider/model/effort from Admin")
    ap.add_argument("--model", default=None)
    ap.add_argument("--resume", default=None,
                    help="path to a previous run's transcript.json")
    ap.add_argument("--reply", default=None,
                    help="audit question/instruction appended to the resumed "
                         "conversation")
    a = ap.parse_args()
    from server import resolve_provider
    prov = resolve_provider(a.provider, role=a.role)
    if a.model:
        prov["model"] = a.model
    print(f"agent: role={a.role or '(none)'} provider={prov['id']} "
          f"model={prov['model'] or '(default)'} effort={prov.get('effort')}")
    print(f"task: {a.task}\n")
    prior = None
    if a.resume:
        tpath = a.resume if os.path.isabs(a.resume) else \
            os.path.join(ROOT, a.resume)
        prior = json.load(open(tpath))
    final = None
    if prov["protocol"] == "cli":
        # Subscription CLIs are complete agents themselves — run the task
        # through the signed-in CLI with a restricted tool surface and the
        # lab's governance preamble. Output streams into this job's log.
        if not prov.get("key"):
            raise SystemExit(f"The {prov['cli']} CLI is not installed or not "
                             f"signed in — see Admin > subscriptions.")
        preamble = (SYSTEM + "\n\nWork from the repo root. Prefer running "
                    "the gate scripts via python3. TASK:\n")
        if prior:
            prev = "\n".join(f"{m['role'].upper()}: {str(m['content'])[:2000]}"
                             for m in prior["messages"][-6:])
            preamble += ("(AUDIT FOLLOW-UP; previous run transcript "
                         "below)\n" + prev + "\n\nOWNER ASKS: ")
        argv = cli_argv(prov, preamble + a.task)
        print(f">>> {' '.join(argv[:4])} …", flush=True)
        r = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True,
                           timeout=3600)
        print(r.stdout[-12000:], flush=True)
        if r.stderr.strip():
            print("[stderr]", r.stderr[-2000:], flush=True)
        final = r.stdout.strip()[-8000:] or None
        new_msgs = [{"role": "user", "content": a.task},
                    {"role": "assistant", "content": final or ""}]
        messages = (prior["messages"] + new_msgs) if prior else new_msgs
    else:
        if prior:
            messages = prior["messages"]
            messages.append({"role": "user", "content":
                             "AUDIT FOLLOW-UP from the lab owner: " + a.task})
            print("(resuming transcript for audit — prior turns:",
                  len(messages), ")\n")
        else:
            messages = [{"role": "user", "content": a.task}]
        for turn in range(MAX_TURNS):
            try:
                text, calls, raw = (call_anthropic
                                    if prov["protocol"] == "anthropic"
                                    else call_openai)(prov, messages)
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:400]
                raise SystemExit(
                    f"Provider '{prov['id']}' rejected the request "
                    f"(HTTP {e.code}). Check the API key and model on the "
                    f"Admin page.\n{detail}")
            except urllib.error.URLError as e:
                raise SystemExit(
                    f"Could not reach provider '{prov['id']}' at "
                    f"{prov['base']} ({e.reason}). Check your network, or "
                    f"the base URL on the Admin page.")
            if text.strip():
                print(f"--- agent (turn {turn+1}) ---\n{text}\n", flush=True)
            if not calls:
                final = text
                break
            if prov["protocol"] == "anthropic":
                messages.append({"role": "assistant",
                                 "content": raw["content"]})
                results = []
                for c in calls:
                    print(f">>> {c['name']}({json.dumps(c['args'])[:120]})",
                          flush=True)
                    out = do_tool(c["name"], c["args"])
                    results.append({"type": "tool_result",
                                    "tool_use_id": c["id"],
                                    "content": out[:12000]})
                messages.append({"role": "user", "content": results})
            else:
                messages.append(raw)
                for c in calls:
                    print(f">>> {c['name']}({json.dumps(c['args'])[:120]})",
                          flush=True)
                    out = do_tool(c["name"], c["args"])
                    messages.append({"role": "tool",
                                     "tool_call_id": c["id"],
                                     "content": out[:12000]})
    os.makedirs(os.path.join(ROOT, "results", "agent_runs"), exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    if a.resume:
        tpath2 = tpath                       # append to the same transcript
        rp = tpath.replace(".transcript.json", ".md")
    else:
        base = os.path.join(ROOT, "results", "agent_runs",
                            f"webapp-agent-{stamp}")
        tpath2, rp = base + ".transcript.json", base + ".md"
    try:
        json.dump({"task": a.task, "role": a.role, "provider": prov["id"],
                   "messages": messages, "ts": stamp}, open(tpath2, "w"))
        print(f"transcript: {os.path.relpath(tpath2, ROOT)}")
    except TypeError:
        pass                                 # non-serializable provider blobs
    with open(rp, "a" if a.resume else "w") as f:
        if a.resume:
            f.write(f"\n\n---\n## Audit follow-up ({stamp})\n\n"
                    f"**Owner asked:** {a.task}\n\n**Agent:**\n\n"
                    f"{final or '(no final reply)'}\n")
            print(f"report appended: {os.path.relpath(rp, ROOT)}")
            sys.exit(0 if final else 2)
        f.write(f"# Standalone agent report\n\nTask: {a.task}\n"
                f"Role: {a.role} · provider {prov['id']} · model "
                f"{prov['model']} · effort {prov.get('effort')}\n\n"
                f"{final or '(hit turn limit without a final report)'}\n")
    json.dump({"agent": "standalone-runner", "stage": "finished",
               "progress": os.path.relpath(rp, ROOT),
               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(STATUS, "w"), indent=1)
    print(f"\nreport: {os.path.relpath(rp, ROOT)}")
    sys.exit(0 if final else 2)


if __name__ == "__main__":
    main()
