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
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from server import JOB_DEFS, job_argv, get_api_key, jd  # noqa: E402

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
def call_anthropic(model, messages):
    key = get_api_key("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("No ANTHROPIC_API_KEY configured (Admin page).")
    body = {"model": model or "claude-haiku-4-5-20251001", "max_tokens": 2000,
            "system": SYSTEM, "tools": TOOLS, "messages": messages}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    calls = [{"id": c["id"], "name": c["name"], "args": c["input"]}
             for c in r.get("content", []) if c.get("type") == "tool_use"]
    text = "".join(c.get("text", "") for c in r.get("content", [])
                   if c.get("type") == "text")
    return text, calls, r


def call_openai(model, messages):
    cfg = jd("../webapp/config.local.json", {}) or {}
    st = (jd(os.path.relpath(os.path.join(HERE, "config.local.json"), ROOT),
             {}) or {}).get("settings", {})
    base = st.get("openai_base_url") or "https://api.openai.com/v1"
    key = get_api_key("OPENAI_COMPAT_API_KEY") or "ollama"
    oa_tools = [{"type": "function", "function": {
        "name": t["name"], "description": t["description"],
        "parameters": t["input_schema"]}} for t in TOOLS]
    body = {"model": model or st.get("openai_model") or "gpt-4o-mini",
            "messages": [{"role": "system", "content": SYSTEM}] + messages,
            "tools": oa_tools}
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "content-type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    msg = r["choices"][0]["message"]
    calls = [{"id": c["id"], "name": c["function"]["name"],
              "args": json.loads(c["function"]["arguments"] or "{}")}
             for c in (msg.get("tool_calls") or [])]
    return msg.get("content") or "", calls, msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--provider", choices=["anthropic", "openai"],
                    default="anthropic")
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    cfg_settings = (json.load(open(os.path.join(HERE, "config.local.json")))
                    .get("settings", {})
                    if os.path.exists(os.path.join(HERE, "config.local.json"))
                    else {})
    model = a.model or (cfg_settings.get("anthropic_model")
                        if a.provider == "anthropic"
                        else cfg_settings.get("openai_model"))
    print(f"agent: provider={a.provider} model={model or '(default)'}")
    print(f"task: {a.task}\n")
    messages = [{"role": "user", "content": a.task}]
    final = None
    for turn in range(MAX_TURNS):
        text, calls, raw = (call_anthropic if a.provider == "anthropic"
                            else call_openai)(model, messages)
        if text.strip():
            print(f"--- agent (turn {turn+1}) ---\n{text}\n", flush=True)
        if not calls:
            final = text
            break
        if a.provider == "anthropic":
            messages.append({"role": "assistant", "content": raw["content"]})
            results = []
            for c in calls:
                print(f">>> {c['name']}({json.dumps(c['args'])[:120]})",
                      flush=True)
                out = do_tool(c["name"], c["args"])
                results.append({"type": "tool_result", "tool_use_id": c["id"],
                                "content": out[:12000]})
            messages.append({"role": "user", "content": results})
        else:
            messages.append(raw)
            for c in calls:
                print(f">>> {c['name']}({json.dumps(c['args'])[:120]})",
                      flush=True)
                out = do_tool(c["name"], c["args"])
                messages.append({"role": "tool", "tool_call_id": c["id"],
                                 "content": out[:12000]})
    os.makedirs(os.path.join(ROOT, "results", "agent_runs"), exist_ok=True)
    rp = os.path.join(ROOT, "results", "agent_runs",
                      f"webapp-agent-{time.strftime('%Y%m%d-%H%M%S')}.md")
    with open(rp, "w") as f:
        f.write(f"# Standalone agent report\n\nTask: {a.task}\n"
                f"Provider: {a.provider} · model {model}\n\n"
                f"{final or '(hit turn limit without a final report)'}\n")
    json.dump({"agent": "standalone-runner", "stage": "finished",
               "progress": os.path.relpath(rp, ROOT),
               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(STATUS, "w"), indent=1)
    print(f"\nreport: {os.path.relpath(rp, ROOT)}")
    sys.exit(0 if final else 2)


if __name__ == "__main__":
    main()
