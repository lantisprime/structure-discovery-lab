#!/usr/bin/env python3
"""Structure Discovery Lab — guided installer.

One command sets the whole lab up:

    python3 install.py                # interactive wizard (5 short questions)
    python3 install.py --yes          # accept every recommended default
    python3 install.py --dry-run      # show the plan, change nothing
    python3 install.py --verify-only  # re-run the health checks, change nothing

Design rules (they mirror the lab's own constitution):
  * NOTHING IS EVER DELETED. "Clean start" options MOVE files into a
    timestamped archive/ folder (git-ignored) — restore = move them back.
  * The four ledgers (run, multiplicity, commitment, admission) are
    append-only artifacts; this installer never truncates or edits them.
  * FROZEN HISTORICAL RECORD scripts in src/ are never touched.
  * Agent LLM keys are stored the same way the web console stores them:
    webapp/config.local.json (git-ignored, chmod 600), obfuscated at rest
    with the machine-local salt webapp/.keysalt.

Non-interactive flags (for automation; the wizard asks these otherwise):
    --env venv|system      Python environment       (default: venv)
    --ledger keep|clean    lab history/ledgers      (default: keep)
    --datasets keep|clean  onboarded datasets       (default: keep)
    --riemann yes|no       riemann-zero-lab deps    (default: yes)
    --provider <id>        LLM provider for agents (anthropic, openai,
                           openrouter, google, ollama, ...); reads the key
                           from env LAB_LLM_API_KEY so it never appears in
                           shell history. Omit to configure later in the
                           console's Admin page.
"""

import argparse
import base64
import getpass
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(ROOT, "results")
WEBAPP = os.path.join(ROOT, "webapp")
RIEMANN = os.path.join(ROOT, "riemann-zero-lab")
LEDGER_FILES = ["run_ledger.jsonl", "multiplicity_ledger.jsonl",
                "commitment_ledger.txt", "admission_log.txt"]

# Providers the wizard offers directly (a subset of the console's full list —
# any other provider can be added later on the console Admin page).
WIZARD_PROVIDERS = {
    "anthropic": ("Anthropic", "https://console.anthropic.com/settings/keys", False),
    "openai": ("OpenAI", "https://platform.openai.com/api-keys", False),
    "openrouter": ("OpenRouter", "https://openrouter.ai/keys", False),
    "google": ("Google Gemini", "https://aistudio.google.com/apikey", False),
    "ollama": ("Ollama (local, keyless)", "https://ollama.com/download", True),
}
AGENT_ROLES = ("analyst", "executor", "reviewer", "companion")


# --------------------------------------------------------------------- ui
# Windows consoles often default to cp1252, which cannot encode the
# box-drawing/check characters below — degrade to '?' instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


def hr():
    print("─" * 62)


def say(*lines):
    for l in lines:
        print(l)


def read_line(prompt):
    """input() that treats EOF (Ctrl-D / exhausted stdin) as 'accept the
    default' instead of crashing the wizard."""
    try:
        return input(prompt)
    except EOFError:
        print()
        return ""


def ask_choice(step, total, title, intro, options, default=0):
    """One decision per screen; ENTER accepts the recommended default.
    options: list of (label, explanation). Returns the chosen index."""
    print()
    hr()
    print(f" Step {step} of {total} — {title}")
    hr()
    for l in intro:
        print(f" {l}")
    print()
    for i, (label, expl) in enumerate(options, 1):
        mark = "  (recommended)" if i - 1 == default else ""
        print(f"   [{i}] {label}{mark}")
        if expl:
            print(f"       {expl}")
    while True:
        raw = read_line(f"\n Choice [1-{len(options)}] "
                        f"(ENTER = {default + 1}): ").strip()
        if raw == "":
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(" Please type a number from the list (or just press ENTER).")


def confirm(prompt, default_yes=True):
    suffix = "[Y/n]" if default_yes else "[y/N]"
    raw = read_line(f" {prompt} {suffix}: ").strip().lower()
    if raw == "":
        return default_yes
    return raw in ("y", "yes")


# --------------------------------------------------------------- preflight
def count_jsonl(path):
    if not os.path.exists(path):
        return None
    n = 0
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#"):
            n += 1
    return n


def frozen_scripts():
    out = []
    for name in sorted(os.listdir(os.path.join(ROOT, "src"))):
        p = os.path.join(ROOT, "src", name)
        if not name.endswith(".py") or not os.path.isfile(p):
            continue
        try:
            head = "".join(open(p, errors="replace").readlines()[:4])
        except OSError:
            continue
        if "FROZEN HISTORICAL RECORD" in head:
            out.append(name)
    return out


def dataset_dirs():
    base = os.path.join(ROOT, "datasets")
    return sorted(d for d in os.listdir(base)
                  if os.path.isdir(os.path.join(base, d)) and d != "_TEMPLATE")


def read_requirements(path):
    pkgs = []
    if os.path.exists(path):
        for line in open(path):
            line = line.split("#")[0].strip()
            if line:
                pkgs.append(line)
    return pkgs


def preflight():
    if not os.path.exists(os.path.join(ROOT, "src", "lint_frozen_imports.py")):
        sys.exit("install.py must live at (and be run from) the lab repo root.")
    if sys.version_info < (3, 10):
        sys.exit(f"Python 3.10+ required — you are on "
                 f"{sys.version.split()[0]}. Install a newer Python and rerun.")
    state = {
        "python": sys.version.split()[0],
        "runs": count_jsonl(os.path.join(RESULTS, "run_ledger.jsonl")),
        "tests": count_jsonl(os.path.join(RESULTS, "multiplicity_ledger.jsonl")),
        "ledgers_present": [f for f in LEDGER_FILES
                            if os.path.exists(os.path.join(RESULTS, f))],
        "datasets": dataset_dirs(),
        "frozen": frozen_scripts(),
    }
    print()
    hr()
    say(" Structure Discovery Lab — installer",
        " 5 short questions; ENTER on each one gives a good install.",
        " Nothing is ever deleted: clean-start options move files to",
        " archive/ (git-ignored). Frozen scripts and append-only ledgers",
        " are never modified.")
    hr()
    say(f"  • Python {state['python']} ✓ (needs 3.10+)",
        f"  • run ledger: {state['runs'] if state['runs'] is not None else '—'} runs"
        f" · multiplicity ledger: {state['tests'] if state['tests'] is not None else '—'} test rows",
        f"  • ledgers present: {len(state['ledgers_present'])}/4 (append-only)",
        f"  • datasets onboarded: {len(state['datasets'])} (+ _TEMPLATE)",
        f"  • frozen historical scripts: {len(state['frozen'])} (left untouched)")
    return state


# ------------------------------------------------------------------ wizard
def run_wizard(args, state, interactive):
    total = 5
    choices = {}

    if args.env:
        choices["env"] = args.env
    elif not interactive:
        choices["env"] = "venv"
    else:
        i = ask_choice(1, total, "Python environment",
                       ["The lab needs numpy/scipy/pandas/matplotlib/ripser/"
                        "ephem/openpyxl.",
                        "A private virtual environment (.venv/) avoids the "
                        "PEP-668 'externally",
                        "managed environment' error on Homebrew/Debian Python."],
                       [("Create a virtual environment at .venv/ and install there",
                         "Safe and self-contained; the wizard prints how to activate it."),
                        ("Install into the current Python interpreter",
                         "Use this if you already manage your own environment.")])
        choices["env"] = "venv" if i == 0 else "system"

    if args.ledger:
        choices["ledger"] = args.ledger
    elif not interactive:
        choices["ledger"] = "keep"
    else:
        i = ask_choice(2, total, "Lab history (the ledgers)",
                       ["The repo ships with the lab's verified history: the run "
                        "ledger, the",
                        "multiplicity ledger, the commitment (hash) ledger and "
                        "the admission log,",
                        "plus every registered result under results/."],
                       [("Keep the existing ledgers and results",
                         "You continue the lab exactly where the repo left off."),
                        ("Start with a clean ledger",
                         "Moves results/ (and riemann-zero-lab/results/) to archive/, "
                         "then creates fresh empty ledgers with a new commitment "
                         "snapshot. Restore any time by moving the archive back.")])
        choices["ledger"] = "keep" if i == 0 else "clean"

    if args.datasets:
        choices["datasets"] = args.datasets
    elif not interactive:
        choices["datasets"] = "keep"
    else:
        i = ask_choice(3, total, "Datasets",
                       [f"The repo ships {len(state['datasets'])} onboarded "
                        f"datasets ({', '.join(state['datasets'])}).",
                        "Each has a completed DATASET.md card — the governance "
                        "prerequisite for",
                        "running any instrument on it."],
                       [("Keep the repo's datasets",
                         "Recommended — instruments and the existing ledger "
                         "reference them."),
                        ("Start with clean datasets",
                         "Moves every dataset except _TEMPLATE to archive/. "
                         "Onboard your own via datasets/_TEMPLATE/DATASET.md.")])
        choices["datasets"] = "keep" if i == 0 else "clean"

    if choices["ledger"] == "keep" and choices["datasets"] == "clean":
        print()
        say(" ⚠  You chose to KEEP the ledgers but ARCHIVE the datasets.",
            "    Existing ledger rows reference those datasets, so their runs",
            "    cannot be reproduced until the archive is restored.")
        if interactive and not confirm("Continue with this combination?",
                                       default_yes=False):
            say("    Switching datasets back to 'keep'.")
            choices["datasets"] = "keep"

    if args.riemann:
        choices["riemann"] = args.riemann
    elif not interactive:
        choices["riemann"] = "yes"
    else:
        i = ask_choice(4, total, "riemann-zero-lab module",
                       ["The deterministic-mathematics module (Riemann ζ zeros) "
                        "additionally",
                        "needs mpmath."],
                       [("Install its dependency too", ""),
                        ("Skip it", "You can `pip install mpmath` later.")])
        choices["riemann"] = "yes" if i == 0 else "no"

    if args.provider:
        choices["provider"] = args.provider
        choices["key"] = ("" if WIZARD_PROVIDERS.get(args.provider, ("", "", False))[2]
                          else os.environ.get("LAB_LLM_API_KEY", ""))
        if not choices["key"] and not WIZARD_PROVIDERS.get(args.provider, ("", "", True))[2]:
            say(f" ⚠  --provider {args.provider} given but LAB_LLM_API_KEY is "
                "not set; the provider will be selected without a key.")
    elif not interactive:
        choices["provider"] = None
    else:
        opts = [(f"{label} — key from {url}" if not keyless else label, "")
                for label, url, keyless in WIZARD_PROVIDERS.values()]
        opts.append(("Skip — configure later in the console (Admin page)",
                     "The console at http://localhost:8787 has the full "
                     "provider list, including Claude/ChatGPT subscription CLIs."))
        i = ask_choice(5, total, "LLM provider for the lab's agents",
                       ["The lab's agents (analyst / executor / reviewer / "
                        "companion) call an LLM",
                        "API. The key is stored git-ignored and obfuscated in "
                        "webapp/config.local.json,",
                        "never in the repo. You can skip this and add it in the "
                        "web console later."],
                       opts, default=len(opts) - 1)
        pids = list(WIZARD_PROVIDERS)
        if i < len(pids):
            pid = pids[i]
            choices["provider"] = pid
            if WIZARD_PROVIDERS[pid][2]:  # keyless (local)
                choices["key"] = ""
            else:
                try:
                    choices["key"] = getpass.getpass(
                        f" Paste your {WIZARD_PROVIDERS[pid][0]} API key "
                        "(hidden, ENTER to skip): ").strip()
                except EOFError:
                    print()
                    choices["key"] = ""
        else:
            choices["provider"] = None
    return choices


# ----------------------------------------------------------------- actions
def archive_dir():
    """A guaranteed-fresh archive dir. Timestamps are second-granular, so two
    operations in the same second (clean install then --restore on a fast
    machine) MUST NOT share a dir — --restore would otherwise displace state
    into the very archive it is restoring from."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    base = os.path.join(ROOT, "archive", f"preinstall-{stamp}")
    d, n = base, 1
    while os.path.exists(d):
        n += 1
        d = f"{base}-{n}"
    os.makedirs(d)
    return d


def snapshot_hashes(out):
    """Fresh commitment-ledger snapshot: sha256 (16-hex prefix) of every doc,
    script and dataset file — same format as the shipped ledger. results/ is
    excluded (it is empty on a fresh ledger)."""
    skip_dirs = {".git", ".venv", "archive", "__pycache__", ".pytest_cache",
                 ".episodic-memory", "results", "joblogs"}
    skip_files = {".keysalt", "config.local.json", ".DS_Store"}
    rows = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in skip_dirs)
        for f in sorted(files):
            if f in skip_files:
                continue
            p = os.path.join(base, f)
            rel = "./" + os.path.relpath(p, ROOT).replace(os.sep, "/")
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
            rows.append(f"{h}  {rel}")
    out.write("\n".join(rows) + "\n")


def do_clean_ledger(arch):
    dest = os.path.join(arch, "results")
    shutil.move(RESULTS, dest)
    r_res = os.path.join(RIEMANN, "results")
    if os.path.isdir(r_res):
        shutil.move(r_res, os.path.join(arch, "riemann-results"))
        os.makedirs(os.path.join(r_res, "agent_runs"), exist_ok=True)
        open(os.path.join(r_res, "run_ledger.jsonl"), "w").close()
    for sub in ("figures", "agent_runs", "blind"):
        os.makedirs(os.path.join(RESULTS, sub), exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    with open(os.path.join(RESULTS, "commitment_ledger.txt"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write(
            "# Commitment ledger — append-only. SHA-256 of every doc/script/result.\n"
            f"# Fresh ledger initialized by install.py at {now}.\n"
            f"# Prior history archived at {os.path.relpath(arch, ROOT)}/ "
            "(moved, not deleted).\n"
            "# Future registrations are hashed here BEFORE their run scripts "
            "execute.\n")
        snapshot_hashes(f)
    for name in ("run_ledger.jsonl", "multiplicity_ledger.jsonl",
                 "admission_log.txt"):
        open(os.path.join(RESULTS, name), "w").close()
    say(f"  ✓ history archived to {os.path.relpath(arch, ROOT)}/",
        "  ✓ fresh ledgers created (commitment snapshot of "
        "docs/scripts/datasets taken)",
        "  ⚠ note: src/build_run_ledger.py and src/build_multiplicity_ledger.py",
        "    BACKFILL the repo's historical runs — on a clean ledger, append new",
        "    runs via the console/agents instead of running those builders.")


def do_clean_datasets(arch):
    dest = os.path.join(arch, "datasets")
    os.makedirs(dest, exist_ok=True)
    for d in dataset_dirs():
        shutil.move(os.path.join(ROOT, "datasets", d), os.path.join(dest, d))
    say(f"  ✓ datasets archived to {os.path.relpath(dest, ROOT)}/ "
        "(_TEMPLATE kept)",
        "  → onboard new data by copying datasets/_TEMPLATE/DATASET.md — a "
        "completed",
        "    card is required before any instrument may run (governance Part 4).")


def target_python(env_mode):
    if env_mode == "system":
        return sys.executable
    vdir = os.path.join(ROOT, ".venv")
    py = os.path.join(vdir, "Scripts" if os.name == "nt" else "bin",
                      "python.exe" if os.name == "nt" else "python")
    if not os.path.exists(py):
        say("  creating virtual environment .venv/ …")
        r = subprocess.run([sys.executable, "-m", "venv", vdir])
        if r.returncode != 0:
            sys.exit("venv creation failed. On Debian/Ubuntu: "
                     "sudo apt install python3-venv — or rerun with "
                     "`--env system`.")
    return py


def pip_install(py, pkgs, extra_flags=()):
    """Install pkgs; on bulk failure retry one-by-one so the report names
    exactly what is missing. Returns the list of packages that failed."""
    if not pkgs:
        return []
    base = [py, "-m", "pip", "install", "--disable-pip-version-check",
            *extra_flags]
    r = subprocess.run(base + pkgs)
    if r.returncode == 0:
        return []
    say("  bulk install failed — retrying packages one at a time …")
    failed = []
    for p in pkgs:
        if subprocess.run(base + [p]).returncode != 0:
            failed.append(p)
    return failed


def do_deps(env_mode, with_riemann, locked=False):
    py = target_python(env_mode)
    subprocess.run([py, "-m", "pip", "install", "--quiet", "--upgrade",
                    "pip"], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)  # best-effort only
    pkgs = read_requirements(os.path.join(ROOT, "requirements.txt"))
    if with_riemann:
        pkgs += [p for p in read_requirements(
            os.path.join(RIEMANN, "requirements.txt")) if p not in pkgs]
    constraints = os.path.join(ROOT, "constraints-recorded.txt")
    flags = ()
    if locked and os.path.exists(constraints):
        flags = ("-c", constraints)
        say("  --locked: pinning to the recorded environment "
            "(constraints-recorded.txt)")
    say(f"  installing {len(pkgs)} packages into "
        f"{'.venv/' if env_mode == 'venv' else py} …")
    failed = pip_install(py, pkgs, flags)
    if failed:
        say("", "  ⚠ these packages did not install:")
        for p in failed:
            say(f"      {p}")
        say("    Remedies: PEP-668 error → rerun and choose the .venv option;",
            "    build error (ripser) → ensure a C++ compiler, or "
            "`pip install Cython` first.")
    return py, failed


def obfuscate_key(plaintext):
    """Same at-rest scheme as webapp/server.py: XOR with the machine-local
    webapp/.keysalt, base64, 'enc1:' prefix. The console reads it natively."""
    salt_file = os.path.join(WEBAPP, ".keysalt")
    if not os.path.exists(salt_file):
        with open(salt_file, "wb") as f:
            f.write(os.urandom(64))
        os.chmod(salt_file, 0o600)
    salt = open(salt_file, "rb").read()
    raw = plaintext.encode()
    return "enc1:" + base64.b64encode(
        bytes(b ^ salt[i % len(salt)] for i, b in enumerate(raw))).decode()


def do_agent_config(pid, key):
    cfg_path = os.path.join(WEBAPP, "config.local.json")
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
    cfg.setdefault("api_keys", {})
    st = cfg.setdefault("settings", {})
    if key:
        cfg["api_keys"][f"PROVIDER_{pid.upper()}_KEY"] = obfuscate_key(key)
    st["auth_method"] = "api_key"
    st["active_provider"] = pid
    roles = st.setdefault("agent_roles", {})
    for r in AGENT_ROLES:
        roles.setdefault(r, {})
        if not roles[r].get("provider"):
            roles[r]["provider"] = pid
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(cfg_path, 0o600)
    say(f"  ✓ agents configured to use {pid} "
        f"({'key stored obfuscated, git-ignored' if key else 'keyless/local'})",
        "    All four roles (analyst/executor/reviewer/companion) default to "
        "it; fine-tune",
        "    per-role models and effort on the console's Admin page.")


def verify(py, with_riemann):
    say("", " Verifying the install …")
    checks = []
    r = subprocess.run([py, os.path.join(WEBAPP, "test_lab_deps.py")],
                       capture_output=True, text=True)
    checks.append(("runtime dependencies (webapp/test_lab_deps.py)",
                   r.returncode == 0))
    if r.returncode != 0:
        print((r.stderr or r.stdout).strip()[-800:])
    if with_riemann:
        r = subprocess.run([py, "-c", "import mpmath"], capture_output=True)
        checks.append(("riemann-zero-lab dependency (mpmath)",
                       r.returncode == 0))
    r = subprocess.run([py, os.path.join(ROOT, "src",
                                         "lint_frozen_imports.py")],
                       capture_output=True, text=True)
    checks.append(("frozen-artifact convention (src/lint_frozen_imports.py)",
                   r.returncode == 0))
    if r.returncode != 0:
        print((r.stdout or r.stderr).strip()[-800:])
    ledgers_ok = all(os.path.exists(os.path.join(RESULTS, f))
                     for f in LEDGER_FILES)
    checks.append(("ledger files present (append-only)", ledgers_ok))
    integ = os.path.join(ROOT, "src", "verify_ledger_integrity.py")
    if ledgers_ok and os.path.exists(integ):
        r = subprocess.run([py, integ, "--quiet"],
                           capture_output=True, text=True)
        checks.append(("ledger integrity "
                       "(src/verify_ledger_integrity.py)", r.returncode == 0))
        if r.returncode != 0:
            print((r.stdout or r.stderr).strip()[-800:])
    ok = True
    for label, passed in checks:
        say(f"   {'✓ PASS' if passed else '✗ FAIL'}  {label}")
        ok = ok and passed
    return ok


def do_restore(archive_rel):
    """Mechanically undo a clean start: swap the named archive back in.
    The CURRENT state is archived first — restore never deletes either."""
    arch = archive_rel if os.path.isabs(archive_rel) \
        else os.path.join(ROOT, archive_rel)
    if not os.path.isdir(arch):
        sys.exit(f"archive not found: {archive_rel}")
    has = {n: os.path.isdir(os.path.join(arch, n))
           for n in ("results", "riemann-results", "datasets")}
    if not any(has.values()):
        sys.exit(f"{archive_rel} contains no results/, riemann-results/ or "
                 "datasets/ to restore")
    displaced = archive_dir()
    if has["results"]:
        if os.path.isdir(RESULTS):
            shutil.move(RESULTS, os.path.join(displaced, "results"))
        shutil.move(os.path.join(arch, "results"), RESULTS)
        say("  ✓ results/ restored from the archive")
    if has["riemann-results"]:
        r_res = os.path.join(RIEMANN, "results")
        if os.path.isdir(r_res):
            shutil.move(r_res, os.path.join(displaced, "riemann-results"))
        shutil.move(os.path.join(arch, "riemann-results"), r_res)
        say("  ✓ riemann-zero-lab/results/ restored")
    if has["datasets"]:
        dst = os.path.join(displaced, "datasets")
        os.makedirs(dst, exist_ok=True)
        for d in sorted(os.listdir(os.path.join(arch, "datasets"))):
            cur = os.path.join(ROOT, "datasets", d)
            if os.path.isdir(cur):
                shutil.move(cur, os.path.join(dst, d))
            shutil.move(os.path.join(arch, "datasets", d), cur)
        say("  ✓ datasets restored")
    say(f"  the state that was in place is preserved at "
        f"{os.path.relpath(displaced, ROOT)}/ (nothing deleted)")


def ensure_gitignore():
    gi = os.path.join(ROOT, ".gitignore")
    text = open(gi).read() if os.path.exists(gi) else ""
    add = [e for e in (".venv/", "archive/") if e not in text.splitlines()]
    if add:
        with open(gi, "a") as f:
            if text and not text.endswith("\n"):
                f.write("\n")
            f.write("\n".join(add) + "\n")


# -------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(
        description="Structure Discovery Lab installer (wizard-driven).")
    ap.add_argument("--yes", action="store_true",
                    help="accept every recommended default, no questions")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and exit without changing anything")
    ap.add_argument("--verify-only", action="store_true",
                    help="re-run the post-install checks (deps, frozen "
                         "convention, ledgers) and exit; changes nothing — "
                         "handy after moving the lab to a new machine")
    ap.add_argument("--env", choices=["venv", "system"])
    ap.add_argument("--ledger", choices=["keep", "clean"])
    ap.add_argument("--datasets", choices=["keep", "clean"])
    ap.add_argument("--riemann", choices=["yes", "no"])
    ap.add_argument("--provider", choices=list(WIZARD_PROVIDERS),
                    help="agent LLM provider; key read from env "
                         "LAB_LLM_API_KEY")
    ap.add_argument("--locked", action="store_true",
                    help="pin installs to the recorded environment "
                         "(constraints-recorded.txt) for closest "
                         "reproduction of ledgered results")
    ap.add_argument("--restore", metavar="ARCHIVE_DIR",
                    help="undo a clean start: swap the named archive/"
                         "preinstall-* folder back in (current state is "
                         "archived first, nothing deleted) and exit")
    args = ap.parse_args()

    state = preflight()
    if args.restore:
        do_restore(args.restore)
        return
    if args.verify_only:
        vdir = os.path.join(ROOT, ".venv", "Scripts" if os.name == "nt"
                            else "bin")
        py = os.path.join(vdir, "python.exe" if os.name == "nt" else "python")
        if not os.path.exists(py):
            py = sys.executable
        ok = verify(py, os.path.isdir(RIEMANN))
        sys.exit(0 if ok else 1)
    interactive = sys.stdin.isatty() and not args.yes and not args.dry_run
    if not interactive and not args.yes and not args.dry_run:
        say("", " (no terminal attached — using the recommended defaults;",
            "  pass --env/--ledger/--datasets/--riemann/--provider to override)")
    choices = run_wizard(args, state, interactive)

    # ----- plan summary
    print()
    hr()
    say(" Plan")
    hr()
    say(f"  environment : "
        f"{'.venv/ virtual environment' if choices['env'] == 'venv' else 'current interpreter'}",
        f"  ledger      : "
        f"{'keep existing history' if choices['ledger'] == 'keep' else 'clean start (history moved to archive/)'}",
        f"  datasets    : "
        f"{'keep the repo datasets' if choices['datasets'] == 'keep' else 'clean start (moved to archive/, _TEMPLATE kept)'}",
        f"  riemann lab : "
        f"{'install mpmath' if choices['riemann'] == 'yes' else 'skip'}",
        f"  agents      : "
        f"{choices['provider'] + ' provider' if choices.get('provider') else 'configure later in the console Admin page'}")
    if args.dry_run:
        say("", " --dry-run: nothing was changed.")
        return
    if interactive and not confirm("Proceed?"):
        say(" Aborted — nothing was changed.")
        return

    print()
    hr()
    say(" Installing")
    hr()
    ensure_gitignore()
    arch = None
    if choices["ledger"] == "clean" or choices["datasets"] == "clean":
        arch = archive_dir()
    # datasets first: the fresh commitment snapshot must reflect the tree
    # as it will actually exist after the clean start
    if choices["datasets"] == "clean":
        do_clean_datasets(arch)
    if choices["ledger"] == "clean":
        do_clean_ledger(arch)
    py, failed = do_deps(choices["env"], choices["riemann"] == "yes",
                         locked=args.locked)
    if choices.get("provider"):
        do_agent_config(choices["provider"], choices.get("key", ""))
    ok = verify(py, choices["riemann"] == "yes")

    # ----- next steps
    print()
    hr()
    say(" Done" + ("" if ok and not failed else " (with warnings — see above)"))
    hr()
    n = 1
    if choices["env"] == "venv":
        act = (".venv\\Scripts\\activate" if os.name == "nt"
               else "source .venv/bin/activate")
        say(f"  {n}. Activate the environment:   {act}")
        n += 1
    say(f"  {n}. Start the web console:      python3 webapp/server.py 8787",
        "     (or double-click 'Start Lab Console.command' on macOS)",
        "     → http://localhost:8787 — the Overview page always shows the",
        "       single next action; the Admin page manages agent LLM keys.",
        f"  {n + 1}. Read the map:               README.md → docs/RUNBOOK.md",
        "     Agent workflow:             docs/AGENT_WORKFLOW.md")
    if arch:
        say(f"  Archived (not deleted):        {os.path.relpath(arch, ROOT)}/")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n Aborted — nothing further was changed.")
        sys.exit(130)
