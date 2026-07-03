#!/usr/bin/env python3
"""Structure Discovery Lab — local web console.

Zero-dependency backend (Python stdlib only). Serves the SPA in
webapp/static/ and JSON APIs over the repo's real artifacts:

  GET  /api/state         aggregated lab state (runs, ledger, panel, verdicts,
                          families, approvals, pipeline current/next step)
  GET  /api/kb            theorem arsenal (parsed docs/kb cards, searchable)
  GET  /api/doc?name=     raw markdown of a whitelisted doc
  GET  /api/series?name=  numeric series for the equation lab
  POST /api/try_equation  fit a user harmonic hypothesis to a series
  GET  /api/agents        agent/process status (ps scan + status file + runs)
  GET/POST /api/approvals approval queue (records to results/webapp_approvals.jsonl;
                          fills blank approved_by_human lines when present)
  GET/POST /api/config    admin config (API keys -> webapp/config.local.json,
                          gitignored; values stored locally, served masked)

Start:  python3 webapp/server.py  [port]      (default 8787)
Then open http://localhost:8787

Security model: localhost tool for the lab owner. Binds 127.0.0.1 only.
Approvals recorded here carry channel="webapp" in the audit trail.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STATIC = os.path.join(HERE, "static")
CONFIG = os.path.join(HERE, "config.local.json")
APPROVALS = os.path.join(ROOT, "results", "webapp_approvals.jsonl")
AGENT_STATUS = os.path.join(ROOT, "results", "agent_status.json")

DOC_WHITELIST_DIRS = ("docs", "evals")


def rd(path):
    with open(os.path.join(ROOT, path)) as f:
        return f.read()


def jl(path):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def jd(path, default=None):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return default
    return json.load(open(p))


# ---------------------------------------------------------------- state
def pipeline_state():
    """Derive 'where are we / what's next' from repo artifacts."""
    steps = []

    def step(sid, title, status, detail):
        steps.append({"id": sid, "title": title, "status": status,
                      "detail": detail})

    step("audit", "Correctness audit + remediation", "done",
         "AUDIT_RESOLUTION_2026-07-02.md — all findings closed; "
         "adversarial reviews remediated")
    ratified = "RATIFIED" in rd("docs/RESULTS_EQ_READJUDICATION.md")[:400]
    step("ratify", "Verdict re-adjudication ratified",
         "done" if ratified else "waiting-human",
         "v1-B AT_FLOOR · v2-B FAIL_corrected · confirm1 UNCONFIRMED")
    rerun = jd("results/corrected_rerun_r1.json")
    step("rerun", "Registered corrected-instrument rerun",
         "done" if rerun else "next",
         "corrected_rerun_r1: all NULL, positive control intact"
         if rerun else "REGISTRATION_CORRECTED_RERUN.md")
    blind = jd("results/eq_eval_verdicts.json")
    step("eq_eval", "eq_eval_set_v1 blind run (FRESH session required)",
         "done" if blind else "next",
         "Sealed 12-unit benchmark gates eq v4. Executor must never have "
         "read the answer key — run from a new agent session.")
    v4 = os.path.exists(os.path.join(ROOT, "docs", "REGISTRATION_EQ_TIDAL_V4.md"))
    step("eq_v4", "Equation program v4",
         "done" if v4 else "later",
         "Corrected selection, B>=399, in-run adjudication, calibrated "
         "residual scan of the 36.34 d question, baselines")
    cur = next((s for s in steps if s["status"] in ("next", "waiting-human")),
               None)
    return {"steps": steps, "current": cur["id"] if cur else "eq_v4"}


def candidate_equations():
    """The equation program's claims with ratified statuses."""
    adj = jd("results/eq_readjudication_2026-07-02.json", {})
    v2 = jd("results/eq_tidal_v2.json", {})
    out = []
    for cid, c in (v2.get("claims") or {}).items():
        sel = c.get("selected_family")
        rec = (c.get("family_records") or {}).get(sel, {})
        periods = rec.get("periods_d", [])
        key = ("eq_tidal_v2.claimB_moondist" if "moondist" in cid
               else "eq_tidal_v2.claimA_tidal_phase")
        st = (adj.get("claims") or {}).get(key, {})
        out.append({
            "id": cid, "selected_family": sel,
            "periods_d": [round(p, 3) for p in periods],
            "complexity": rec.get("complexity"),
            "target": c.get("target"),
            "frozen_verdict": c.get("verdict"),
            "corrected_status": st.get("corrected_status"),
            "binding_p": st.get("binding_p"),
            "series": ("moon_distance" if "moondist" in cid else "tidal_accel"),
        })
    return out


def state():
    runs = jl("results/run_ledger.jsonl")
    ml = jl("results/multiplicity_ledger.jsonl")
    tests = [r for r in ml if r.get("row_type") == "test"]
    live = [r for r in tests if "superseded_by" not in r
            and not r.get("exploratory")]
    meta = jd("results/meta_uniformity.json", {})
    fams = jd("results/families.json", {})
    return {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pipeline": pipeline_state(),
        "runs": list(reversed(runs)),
        "ledger": {
            "rows": len(ml), "tests": len(tests), "live": len(live),
            "charges": len(ml) - len(tests),
            "exploratory": sum(1 for r in tests if r.get("exploratory")),
            "global_m": (live[0].get("global_m") if live else None),
            "frac_le_05": round(sum(1 for r in live
                                    if (r.get("raw_p") or 1) <= .05)
                                / max(len(live), 1), 4),
            "recent": list(reversed(tests[-40:])),
        },
        "meta_panel": {k: meta.get(k) for k in
                       ("panel_version", "panel_sha", "n_tests",
                        "p_meta_discrete", "frac_le_05",
                        "sim_frac_le_05_q05_q95", "composition_sensitivity")},
        "families": fams.get("families", {}),
        "family_couplings": fams.get("reported_couplings", []),
        "equations": candidate_equations(),
        "readjudication": jd("results/eq_readjudication_2026-07-02.json", {}),
        "readmission": {k: v.get("verdict") for k, v in
                        (jd("results/readmission_v2.json", {}) or {}).items()
                        if isinstance(v, dict) and "verdict" in v},
        "approvals": approvals_list(),
    }


# ---------------------------------------------------------------- kb
KB_FACE_RE = re.compile(r"\*\*Face\*\*[:\s]*([^\n]*)", re.I)


def kb_cards():
    out = []
    kb = os.path.join(ROOT, "docs", "kb")
    for f in sorted(os.listdir(kb)):
        if not f.endswith(".md") or f == "INDEX.md":
            continue
        txt = open(os.path.join(kb, f)).read()
        title = next((l.lstrip("# ").strip() for l in txt.splitlines()
                      if l.startswith("#")), f)
        face = (KB_FACE_RE.search(txt).group(1).strip()
                if KB_FACE_RE.search(txt) else "")
        out.append({"slug": f[:-3], "file": f"docs/kb/{f}", "title": title,
                    "face": face,
                    "preview": " ".join(txt.split())[:400],
                    "body": txt})
    return out


# ---------------------------------------------------------------- series
def load_csv_col(path, col, date_col="Date"):
    import csv as _csv
    xs, ds = [], []
    with open(os.path.join(ROOT, path)) as f:
        for row in _csv.DictReader(f):
            try:
                xs.append(float(row[col]))
                ds.append(row.get(date_col) or row.get("date"))
            except (ValueError, TypeError, KeyError):
                pass
    return ds, xs


SERIES = {
    "moon_distance": ("datasets/jpl-horizons-sun-moon/sun_moon_daily.csv",
                      "Moon Dist (km)", "Moon distance (km)"),
    "tidal_accel": ("datasets/tidal-manila/tidal_derived.csv",
                    "Total tidal accel (g)", "Total tidal acceleration (g)"),
    "pressure": ("datasets/openmeteo-pressure-manila/pressure_daily.csv",
                 "P_msl_mean_hPa", "Manila MSL pressure (hPa)"),
    "kp_index": ("datasets/gfz-kp-geomagnetic/kp_daily.csv",
                 "Kp_daily_mean", "Kp geomagnetic daily mean"),
}
for i in range(1, 13):
    SERIES[f"eval_unit_{i:02d}"] = (
        f"evals/eq_eval_set_v1/blind/datasets/unit_{i:02d}.csv",
        "value", f"eq-eval blind unit {i:02d}")


def get_series(name):
    path, col, label = SERIES[name]
    ds, xs = load_csv_col(path, col)
    return {"name": name, "label": label, "dates": ds, "values": xs}


# ---------------------------------------------------------------- try equation
def try_equation(payload):
    """Fit y ~ intercept + trend? + sum_j a_j cos + b_j sin at USER periods.
    Honest framing: this is an in-sample descriptive fit plus a held-out
    check — not a registered discovery test (0 multiplicity; sandbox only)."""
    import numpy as np
    name = payload.get("series", "moon_distance")
    periods = [float(p) for p in payload.get("periods_d", []) if float(p) > 0]
    use_trend = bool(payload.get("trend", False))
    if not (1 <= len(periods) <= 5):
        raise ValueError("give 1-5 positive periods (days)")
    s = get_series(name)
    y = np.asarray(s["values"], float)
    t = np.arange(len(y), dtype=float)
    ntr = int(0.8 * len(y))                     # chronological 80/20
    cols = [np.ones_like(t)] + ([t] if use_trend else [])
    for p in periods:
        cols += [np.cos(2 * np.pi * t / p), np.sin(2 * np.pi * t / p)]
    X = np.stack(cols, 1)
    beta, *_ = np.linalg.lstsq(X[:ntr], y[:ntr], rcond=None)
    fit = X @ beta
    resid = y - fit

    def rmse(a):
        return float(np.sqrt(np.mean(np.asarray(a) ** 2)))
    out = {
        "series": name, "label": s["label"], "n": len(y),
        "train_n": ntr, "periods_d": periods, "trend": use_trend,
        "rmse_train": rmse(resid[:ntr]),
        "rmse_holdout": rmse(resid[ntr:]),
        "rmse_climatology_holdout": rmse(y[ntr:] - y[:ntr].mean()),
        "amplitudes": [
            {"period_d": p,
             "amp": float(np.hypot(beta[(1 + int(use_trend)) + 2 * j],
                                   beta[(1 + int(use_trend)) + 2 * j + 1]))}
            for j, p in enumerate(periods)],
        "beats_climatology": None,
        "residual_top_period_d": None,
        "disclaimer": ("Sandbox fit: descriptive, 0 multiplicity charged, "
                       "never citable. A real claim needs a registration "
                       "and the v4 null-equation generator."),
    }
    out["beats_climatology"] = bool(out["rmse_holdout"]
                                    < out["rmse_climatology_holdout"])
    f = np.abs(np.fft.rfft(resid - resid.mean())[1:]) ** 2
    out["residual_top_period_d"] = round(float(len(y) / (int(np.argmax(f)) + 1)), 2)
    out["residual_top_share"] = round(float(f.max() / f.sum()), 4)
    step = max(1, len(y) // 400)
    out["plot"] = {"dates": s["dates"][::step], "y": list(map(float, y[::step])),
                   "fit": list(map(float, fit[::step])),
                   "train_end_index": ntr // step}
    return out


# ---------------------------------------------------------------- approvals
BLANK_APPROVAL = re.compile(r"approved_by_human:\s*(?:_{4,}|\(name, date\).*)?$")


def approvals_list():
    recorded = jl(os.path.relpath(APPROVALS, ROOT)) if \
        os.path.exists(APPROVALS) else []
    pending = []
    docs_dir = os.path.join(ROOT, "docs")
    for f in sorted(os.listdir(docs_dir)):
        if not f.startswith("REGISTRATION") or not f.endswith(".md"):
            continue
        txt = open(os.path.join(docs_dir, f)).read()
        line = next((l for l in txt.splitlines()
                     if "approved_by_human" in l), None)
        if line is None:
            continue
        val = line.split(":", 1)[1].strip().strip("_ ")
        if not val or val.startswith("(name"):
            pending.append({"doc": f"docs/{f}",
                            "title": txt.splitlines()[0].lstrip("# ")})
    return {"pending": pending, "recorded": list(reversed(recorded))[:20]}


def record_approval(payload):
    doc = payload["doc"]
    name = payload.get("name", "").strip()
    decision = payload.get("decision", "approve")
    if not name:
        raise ValueError("approver name required")
    if not doc.startswith("docs/") or ".." in doc:
        raise ValueError("doc must live in docs/")
    entry = {"doc": doc, "name": name, "decision": decision,
             "channel": "webapp", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "sha_before": hashlib.sha256(
                 open(os.path.join(ROOT, doc), "rb").read()).hexdigest()[:16]}
    with open(APPROVALS, "a") as f:
        f.write(json.dumps(entry) + "\n")
    patched = False
    if decision == "approve":
        p = os.path.join(ROOT, doc)
        txt = open(p).read()
        for pat in ("- approved_by_human: ____________  date: ____________",
                    "- approved_by_human: (name, date) — required before execution."):
            if pat in txt:
                txt = txt.replace(pat, f"- approved_by_human: {name} "
                                       f"(via webapp)  date: "
                                       f"{time.strftime('%Y-%m-%d')}", 1)
                open(p, "w").write(txt)
                patched = True
                break
    entry["doc_patched"] = patched
    return entry


# ---------------------------------------------------------------- agents
LAB_SCRIPTS = ("readmit_r1_r7", "corrected_rerun", "run_blind_eval",
               "eq_tidal", "relational_", "remediation", "measure_",
               "meta_uniformity", "design_verifier", "rerun_batch")


def agent_status():
    procs = []
    try:
        out = subprocess.run(["ps", "-eo", "pid,etime,args"],
                             capture_output=True, text=True, timeout=5).stdout
        for line in out.splitlines()[1:]:
            if "python" in line and any(s in line for s in LAB_SCRIPTS):
                parts = line.split(None, 2)
                procs.append({"pid": parts[0], "elapsed": parts[1],
                              "cmd": parts[2][-120:]})
    except Exception:
        pass
    status_file = jd(os.path.relpath(AGENT_STATUS, ROOT), None) or {}
    runs = jl("results/run_ledger.jsonl")
    return {"running_processes": procs,
            "declared_status": status_file,
            "last_runs": list(reversed(runs))[:5],
            "note": ("Long-running lab scripts appear here while executing. "
                     "Agents may also write results/agent_status.json "
                     "({agent, stage, progress, ts}) for richer status.")}


# ---------------------------------------------------------------- config
def config_get():
    cfg = {}
    if os.path.exists(CONFIG):
        cfg = json.load(open(CONFIG))
    masked = {}
    for k, v in cfg.get("api_keys", {}).items():
        masked[k] = (v[:4] + "…" + v[-4:]) if len(v) > 8 else "set"
    return {"api_keys": masked,
            "settings": cfg.get("settings", {}),
            "config_path": "webapp/config.local.json (gitignored)"}


def config_set(payload):
    cfg = json.load(open(CONFIG)) if os.path.exists(CONFIG) else {}
    cfg.setdefault("api_keys", {})
    cfg.setdefault("settings", {})
    for k, v in (payload.get("api_keys") or {}).items():
        if v == "__delete__":
            cfg["api_keys"].pop(k, None)
        elif v and "…" not in v:
            cfg["api_keys"][k] = v
    cfg["settings"].update(payload.get("settings") or {})
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG, 0o600)
    return config_get()


# ---------------------------------------------------------------- http
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, ctype):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        try:
            if u.path in ("/", "/index.html"):
                return self.send_file(os.path.join(STATIC, "index.html"),
                                      "text/html; charset=utf-8")
            if u.path == "/api/state":
                return self.send_json(state())
            if u.path == "/api/kb":
                return self.send_json(kb_cards())
            if u.path == "/api/series":
                return self.send_json(get_series(q["name"]))
            if u.path == "/api/agents":
                return self.send_json(agent_status())
            if u.path == "/api/approvals":
                return self.send_json(approvals_list())
            if u.path == "/api/config":
                return self.send_json(config_get())
            if u.path == "/api/doc":
                name = q.get("name", "")
                if ".." in name or not name.startswith(DOC_WHITELIST_DIRS):
                    return self.send_json({"error": "not whitelisted"}, 403)
                return self.send_json({"name": name, "body": rd(name)})
            return self.send_json({"error": "not found"}, 404)
        except Exception as e:
            return self.send_json({"error": str(e)}, 500)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        payload = json.loads(self.rfile.read(n) or b"{}")
        try:
            if self.path == "/api/try_equation":
                return self.send_json(try_equation(payload))
            if self.path == "/api/approvals":
                return self.send_json(record_approval(payload))
            if self.path == "/api/config":
                return self.send_json(config_set(payload))
            return self.send_json({"error": "not found"}, 404)
        except Exception as e:
            return self.send_json({"error": str(e)}, 400)


def main():
    args = [a for a in sys.argv[1:]]
    lan = "--lan" in args
    ports = [a for a in args if a.isdigit()]
    port = int(ports[0]) if ports else 8787
    host = "0.0.0.0" if lan else "127.0.0.1"
    srv = ThreadingHTTPServer((host, port), H)
    print(f"Structure Discovery Lab console: http://localhost:{port}")
    if lan:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            print(f"LAN mode: on your phone open http://{ip}:{port} "
                  f"(same Wi-Fi). Approvals/admin are exposed to your "
                  f"network — use only on networks you trust.")
        except OSError:
            print("LAN mode: bound to 0.0.0.0 (could not detect LAN IP)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
