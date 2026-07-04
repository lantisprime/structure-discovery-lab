#!/usr/bin/env python3
"""End-to-end test for the redesigned Help view (/console#help).

Help has no numbered screenshot in the design bundle; it follows the mock's card
theme (dc.html §isHelp + HELP_BLOCKS) but is made DYNAMIC per the lab owner's
direction: a live "Lab at a glance" and a browser for the lab's real Markdown
docs, rather than static prose.

This test proves the dynamism is real, not decorative:
  * Every "Lab at a glance" figure is READ FROM THE LIVE API — the DOM tiles are
    checked against GET /api/state and GET /api/kb (theorem-card count, admitted
    count, experiments run, live ledger tests, instrument families, and the
    honesty meta-p). In particular the honesty p is the live value, never the
    prototype's placeholder 0.385, and a hot panel is never labelled "looks
    honest".
  * "The lab's documents" opens a REAL doc: clicking Open fetches the file
    through /api/doc (whitelisted to docs/) and renders it in the shared reader
    modal — asserted end-to-end (read-only; nothing is written).

Run:  <venv>/bin/python webapp/test_help_e2e.py http://localhost:8799
"""
import json
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_help.png"


def _api(path):
    return json.load(urllib.request.urlopen(f"{BASE}{path}"))


def run():
    st = _api("/api/state")
    kb = _api("/api/kb")
    cards = len(kb)
    admitted = sum(1 for c in kb if c.get("admitted"))
    lg = st.get("ledger", {})
    live = lg.get("live") if lg.get("live") is not None else lg.get("tests", 0)
    runs = len(st.get("runs", []))
    fams = len(st.get("families", {}))
    p = (st.get("meta_panel") or {}).get("p_meta_discrete")
    honesty = f"{float(p):.3f}" if p is not None else "—"

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 1600})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))

        pg.goto(f"{BASE}/console#help", wait_until="networkidle")
        pg.wait_for_selector(".help-stats")

        # --- structure / copy fidelity ---
        assert pg.locator("h1.view-h1", has_text="Help").count() == 1
        assert pg.locator(".guide", has_text="five minutes").count() == 1
        assert pg.locator(".card", has_text="Lab at a glance").count() == 1
        assert pg.locator(".help-grid .card").count() == 6, "six orientation cards"
        assert pg.locator(".card", has_text="The lab's documents").count() == 1

        # --- every stat tile is the LIVE figure, not a hard-coded prototype value ---
        tiles = pg.locator(".help-stat").all_inner_texts()
        blob = "\n".join(tiles)
        assert f"{cards}" in blob and "theorem-instrument cards" in blob, tiles
        assert f"{admitted} admitted" in blob, ("admitted count must be live", tiles)
        assert "experiments run" in blob and f"{runs}" in blob, tiles
        assert "live tests in the ledger" in blob and f"{live}" in blob, tiles
        assert "instrument families" in blob and f"{fams}" in blob, tiles

        # honesty p: live value shown, placeholder never shown, hot never "honest"
        honesty_tile = pg.locator(".help-stat", has_text="honesty p").inner_text()
        assert honesty in honesty_tile, (f"expected live honesty {honesty}", honesty_tile)
        assert "0.385" not in honesty_tile, "must never render the prototype placeholder"
        if p is not None and float(p) < 0.05:
            assert "looks honest" not in honesty_tile, \
                "a hot honesty panel must not be labelled 'looks honest'"

        # --- the documents list is populated and each row is openable ---
        docs = pg.locator(".help-doc")
        assert docs.count() == 10, "ten curated protocol docs"
        assert docs.first.locator(".dp", has_text="docs/").count() == 1

        # --- Open reads a REAL doc through /api/doc into the reader modal ---
        docs.filter(has_text="Runbook").get_by_role("button", name="Open").click()
        pg.wait_for_selector(".overlay .md")
        assert pg.locator(".overlay h3", has_text="Runbook").count() == 1
        body = pg.locator(".overlay .md").inner_text()
        assert len(body.strip()) > 40, "the real doc body must render in the modal"
        pg.keyboard.press("Escape")

        pg.screenshot(path=SHOT, full_page=True)
        assert not errs, f"console/page errors: {errs}"
        b.close()

    print(f"HELP E2E OK — Lab-at-a-glance live from API (cards={cards}, "
          f"admitted={admitted}, runs={runs}, ledger.live={live}, families={fams}, "
          f"honesty p={honesty} — not 0.385); 6 orientation cards; 10 protocol docs; "
          f"Open renders a real doc via /api/doc. Shot: {SHOT}")


if __name__ == "__main__":
    run()
