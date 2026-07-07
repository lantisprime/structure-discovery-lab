#!/usr/bin/env python3
"""End-to-end browser test for the redesigned Experiments view (/console#results).

Asserts the run ledger renders newest-first from live data, grade badges parse
the first Gn token (with neutral fallback for grade-less runs), the guide banner
+ CTA are present, inline detail expands with real provenance, and the
registration doc opens in the modal.

Run:  <venv>/bin/python webapp/test_experiments_e2e.py http://localhost:8799
"""
import json
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_experiments.png"


def run():
    _state = json.load(urllib.request.urlopen(f"{BASE}/api/state"))
    runs = _state["runs"]
    st_ledger_recent = _state.get("ledger", {}).get("recent", [])
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 950})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"{BASE}/console#results", wait_until="networkidle")
        pg.wait_for_selector(".exprow")

        # guide banner + CTA + H1
        assert "Why this page exists" in pg.locator(".guide").inner_text()
        assert "newest first" in pg.locator(".guide").inner_text()
        assert pg.get_by_role("link", name="New experiment").get_attribute("href") == "#new"
        assert pg.locator(".view-h1").inner_text() == "Experiments"

        # one row per run, newest first
        assert pg.locator(".exprow").count() == len(runs), "row per run"
        first = pg.locator(".exprow").first
        assert runs[0]["run_id"] in first.inner_text()

        # grade badges parse the first Gn token; grade-less runs fall back to
        # "—". The newest row changes as the append-only ledger grows, so
        # derive the expectation from the run's ledgered grade, never a pin.
        badges = [pg.locator(".exprow .badge").nth(i).inner_text().strip()
                  for i in range(pg.locator(".exprow .badge").count())]
        newest_grade = runs[0].get("grade") or ""
        assert badges[0] and (badges[0] == "—" or
                              badges[0].split()[0] in newest_grade), \
            f"newest badge {badges[0]!r} should derive from {newest_grade!r}"
        # Gn grades parse to G0-G6; non-Gn/absent show a neutral fallback token
        assert all(bt in ("G0", "G1", "G2", "G3", "G4", "G5", "G6")
                   or not bt.startswith("G") for bt in badges), badges
        assert "—" in badges, "grade-less runs show neutral '—' fallback"
        assert "eval" in badges, "non-Gn grade ('eval V-1 PASS') falls back to its token"

        # inline detail expands with real provenance
        first.click()
        pg.wait_for_selector(".expdetail")
        det = pg.locator(".expdetail").first.inner_text()
        assert "positive control" in det.lower() or runs[0]["status"][:20] in det
        assert "datasets" in det.lower() or "verifiers" in det.lower()
        # plain-language interpretation the guide promises (ported from classic interpretRun)
        interp = pg.locator(".expdetail .interp").first.inner_text()
        assert "What this experiment means" in interp
        assert len(interp) > 60, "interpretation should be a real narrative, not empty"
        # per-run ledgered p-values chart + table (restored from classic detail page)
        detail = pg.locator(".expdetail").first
        run_tests = [t for t in st_ledger_recent if t.get("run_id") == runs[0]["run_id"]]
        if run_tests:
            assert detail.locator(".pvsec svg.pvbars rect").count() == len(run_tests), \
                "one p-value bar per ledgered test for this run"
            assert detail.locator(".ptable tbody tr").count() == len(run_tests), \
                "one table row per ledgered test"
        # per-run Export to PDF (classic parity)
        assert detail.get_by_role("button", name="Export to PDF").count() == 1

        # registration doc opens in the modal, then closes
        pg.get_by_role("link", name="Read the registration").click()
        pg.wait_for_selector(".overlay .modal")
        assert "Registration" in pg.locator(".modal").inner_text()
        pg.locator(".modal .mx").click()
        assert pg.locator(".overlay").count() == 0, "modal closes"

        # collapse
        first.click()
        assert pg.locator(".expdetail").count() == 0, "detail collapses"

        pg.screenshot(path=SHOT, full_page=True)
        assert not errs, f"console/page errors: {errs}"
        b.close()
    print(f"EXPERIMENTS E2E OK — {len(runs)} runs newest-first, grade parsing + "
          f"fallback, inline detail + registration modal. Shot: {SHOT}")


if __name__ == "__main__":
    run()
