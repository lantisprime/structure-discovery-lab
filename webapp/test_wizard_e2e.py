#!/usr/bin/env python3
"""End-to-end browser test for the redesigned wizard (/console#new).

Deliberately does NOT create a draft registration (no docs/ write): it drives
steps 1-4, checks the governance bar matches the server's /api/governance_preview
live (single source of truth), verifies validation, and confirms the honest
steps 5-6 render with NO fabricated run/verdict/honesty number (Recon B / Codex
F2) by injecting a mock result and rendering — zero side effects.

Run:  <venv>/bin/python webapp/test_wizard_e2e.py http://localhost:8799
"""
import json
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_wizard.png"


def gov_api(instruments):
    req = urllib.request.Request(f"{BASE}/api/governance_preview",
                                 data=json.dumps({"instruments": instruments}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def run():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 950})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"{BASE}/console#new", wait_until="networkidle")

        # Step 1 — dataset cards carry real rows/span/sparkline previews.
        pg.wait_for_selector(".dscard")
        assert pg.locator(".dscard").count() >= 9, "all datasets offered"
        superc = pg.locator(".dscard", has_text="Super Lotto")
        assert "rows" in superc.locator(".meta").inner_text()
        assert superc.locator("svg.spark").count() == 1, "sparkline drawn"
        superc.click()
        assert "on" in (superc.get_attribute("class") or "")
        pg.get_by_role("button", name="Continue").click()

        # Step 2 — id sanitises, question required.
        pg.fill("#w-runid", "Wiz Test!!42")          # illegal chars stripped
        assert pg.input_value("#w-runid") == "wiztest42"
        pg.fill("#w-hyp", "Do the 6/49 draw sums share distributional structure "
                          "across quarters of the year?")
        pg.get_by_role("button", name="Continue").click()

        # Step 3 — toggle two instruments from two families; the dark governance
        # bar must match the server live.
        pg.wait_for_selector(".govbar")
        pg.locator(".ichip", has_text="mmd").first.click()
        pg.locator(".ichip", has_text="lambda-max").first.click()
        pg.wait_for_timeout(400)                     # debounced server round-trip
        cells = pg.locator(".govbar .g .v")
        ui_fams = cells.nth(1).inner_text().strip()
        ui_alpha = cells.nth(2).inner_text().strip()
        ui_mmin = cells.nth(3).inner_text().strip()
        g = gov_api(["mmd", "lambda-max"])
        assert cells.nth(0).inner_text().strip() == "2", "2 claims"
        assert ui_fams == str(g["n_families"]) == "2", ui_fams
        assert ui_alpha == f"{g['alpha_corrected']:.4f}", (ui_alpha, g)
        assert ui_mmin == str(g["m_min"]), (ui_mmin, g)
        pg.screenshot(path=SHOT.replace(".png", "_gov.png"))
        pg.get_by_role("button", name="Continue").click()

        # Step 4 — review shows the SERVER-authoritative alpha'/min m; accept gate.
        pg.wait_for_selector(".rev")
        rev = pg.locator(".wiz-body").inner_text()
        assert f"{g['alpha_corrected']:.4f}" in rev, "server alpha' shown on review"
        assert str(g["m_min"]) in rev, "server min m shown on review"
        seed = pg.locator(".field input.mono").first.input_value()
        assert seed.isdigit() and len(seed) >= 8, f"fresh seed prefilled: {seed}"
        # accept box required before it will draft
        pg.get_by_role("button", name="Create draft registration").click()
        assert "accepting both outcome branches" in pg.locator(".wiz-err").inner_text()

        # Steps 5-6 — inject a mock result and render; assert HONEST copy only.
        pg.evaluate("""() => {
          WIZ.result = {doc:'docs/REGISTRATION_DEMO.md',
            families_engaged:['two-sample','hit-count-cooc'],
            alpha_corrected:0.0253, m_min:78};
          WIZ.step = 5; renderWizard();
        }""")
        s5 = pg.locator(".wiz-body").inner_text()
        assert "Nothing has run yet" in s5, "step 5 states nothing executed"
        assert "docs/REGISTRATION_DEMO.md" in s5
        assert "role-separated agents will" in s5, "future-tense pipeline"
        assert pg.get_by_role("link", name="Review & sign in Approvals").count() >= 1
        assert "%" not in s5 and "Running" not in s5, "no fake run progress"
        assert "Verdict" not in s5 and "0.385" not in s5, "no fabricated result"
        pg.screenshot(path=SHOT)

        pg.evaluate("() => { WIZ.step = 6; renderWizard(); }")
        s6 = pg.locator(".wiz-body").inner_text()
        assert "Approve" in s6 and "Interpret" in s6, "the honest loop is shown"
        assert "publishable result" in s6, "null-is-a-result value stated"
        assert "0.385" not in s6, "no fabricated honesty number"

        assert not errs, f"console/page errors: {errs}"
        b.close()
    print(f"WIZARD E2E OK — governance matches server live; validation + honest "
          f"steps 5-6 (no fabricated run/verdict). Shots: {SHOT}")


if __name__ == "__main__":
    run()
