#!/usr/bin/env python3
"""Artifact registry (R1-S1). Derived from the repository, never hand-kept:

    agents/<name>.md                      -> agent (model tier from frontmatter)
    */results/agent_runs/<record>         -> agent (eval record standing in for a definition)
    src/<script>.py exposing --verify     -> instrument
    docs/kb/<card>.md (not INDEX.md)      -> theorem_card
    datasets/<set>/provenance/<m>.json    -> adapter_manifest
    results/multiplicity_ledger.jsonl     -> design
    results/run_ledger.jsonl              -> ledger
    pytest suites named by the collector  -> suite
    src/outcome_collect.py                -> collector

    python3 src/artifact_registry.py                 # print the registry
    python3 src/artifact_registry.py --check-ledger  # exit 1 if a ledger artifact is unregistered
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import outcome_ledger as OL  # noqa: E402

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)


def _frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        m = FRONTMATTER_RE.match(fh.read())
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta


def _rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def build_registry(root=ROOT):
    reg = {}
    for p in sorted(glob.glob(os.path.join(root, "agents", "*.md"))):
        meta = _frontmatter(p)
        reg[_rel(root, p)] = {"class": "agent", "tier": meta.get("model"), "name": meta.get("name")}
    for p in sorted(glob.glob(os.path.join(root, "src", "*.py"))):
        with open(p, encoding="utf-8") as fh:
            src = fh.read()
        if "--verify" in src and "add_argument" in src or "--verify" in src and "sys.argv" in src:
            reg[_rel(root, p)] = {"class": "instrument"}
    for p in sorted(glob.glob(os.path.join(root, "docs", "kb", "*.md"))):
        if os.path.basename(p) != "INDEX.md":
            reg[_rel(root, p)] = {"class": "theorem_card"}
    for p in sorted(glob.glob(os.path.join(root, "datasets", "*", "provenance", "*.json"))):
        reg[_rel(root, p)] = {"class": "adapter_manifest"}
    reg["results/multiplicity_ledger.jsonl"] = {"class": "design"}
    reg["results/run_ledger.jsonl"] = {"class": "ledger"}
    reg["src/outcome_collect.py"] = {"class": "collector"}
    try:
        import outcome_collect as OC
        for name, _paths in OC.PYTEST_SUITES:
            reg[name] = {"class": "suite"}
    except Exception:  # registry must still build without the collector
        pass
    return reg


def classify(artifact, registry):
    """Registry entry for a ledger artifact, or None when unregistered."""
    if artifact in registry:
        return registry[artifact]
    if "/results/agent_runs/" in "/" + artifact:
        return {"class": "agent", "tier": None, "name": None, "record": True}
    return None


def unregistered(rows, registry):
    return sorted({r["artifact"] for r in rows if classify(r["artifact"], registry) is None})


def main(argv):
    reg = build_registry()
    if "--check-ledger" in argv:
        rows = OL.read_rows(OL.ledger_path())
        missing = unregistered(rows, reg)
        for a in missing:
            print("  UNREGISTERED", a)
        print(f"ARTIFACT REGISTRY: {'FAIL' if missing else 'OK'} ({len(reg)} entries, "
              f"{len({r['artifact'] for r in rows})} ledger artifacts, {len(missing)} unregistered)")
        return 1 if missing else 0
    print(json.dumps(reg, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
