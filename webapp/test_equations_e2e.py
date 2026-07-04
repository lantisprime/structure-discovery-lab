#!/usr/bin/env python3
"""End-to-end test for the redesigned Equations view (/console#equations),
checked against the TARGET DESIGN in
  design_handoff_structure_lab_console/Structure Lab Console.dc.html  (§Equations)

Fidelity assertions use the prototype's exact copy/labels (metric labels
"hold-out RMSE" / "climatology baseline" / "vs baseline", the per-mode chart
captions, the "What this means"-style interpretation, the readjudication
expander, the full-width Fit card below the two columns).

NO number is hard-coded: the expected metrics/gain are derived from a live
/api/try_equation call and then asserted to appear in the rendered card — proving
the UI shows real experiment output, not literals.

Run:  <venv>/bin/python webapp/test_equations_e2e.py http://localhost:8799
"""
import json
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_equations.png"


def _api(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data,
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def _fmt(v):  # mirror the client's toPrecision(4) for the hold-out RMSE (<1e5)
    return "%.4g" % v


def run():
    cands = _api("/api/state")["equations"]
    moon = next(c for c in cands if c["series"] == "moon_distance")
    # live experiment output — the source of truth for every rendered number
    fit = _api("/api/try_equation", {"series": "moon_distance",
                                     "periods_d": moon["periods_d"], "trend": False})
    gain = round((1 - fit["rmse_holdout"] / fit["rmse_climatology_holdout"]) * 100)
    beats = fit["beats_climatology"]

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 1200})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"{BASE}/console#equations", wait_until="networkidle")
        pg.wait_for_selector(".candrow")

        # --- left column: both real candidates render as FAILURES ---
        assert pg.locator(".candrow").count() == len(cands)
        badges = [pg.locator(".candrow .badge").nth(i).inner_text().strip()
                  for i in range(pg.locator(".candrow .badge").count())]
        assert all("FAIL" in bt.upper() for bt in badges), badges
        for i in range(pg.locator(".candrow .badge").count()):
            col = pg.locator(".candrow .badge").nth(i).evaluate(
                "el => getComputedStyle(el).color").replace(" ", "")
            assert "36,138,61" not in col, "a FAIL must never render green"

        # readjudication expander (target design has this) toggles + links the doc
        assert pg.locator(".readjtog").inner_text().strip().endswith("(readjudication)")
        assert "open" not in (pg.locator("#readjbody").get_attribute("class") or "")
        pg.locator(".readjtog").click()
        assert "open" in pg.locator("#readjbody").get_attribute("class")
        assert "FAIL_corrected" in pg.locator("#readjbody").inner_text()

        # --- fit via the candidate button; result is a FULL-WIDTH card below grid ---
        pg.locator(".candrow", has_text="moondist").get_by_role(
            "button", name="Try it").click()
        pg.wait_for_selector(".eqres .bigmetrics")  # settle past the "Fitting…" card
        assert pg.locator(".eqres").count() == 1
        assert pg.locator("#sandbox .eqres").count() == 0, "Fit card is NOT inside the sandbox column"
        assert pg.locator(".eqcol .eqres").count() == 0, "Fit card spans below both columns"

        res = pg.locator(".eqres")
        assert f"Fit — {fit['label']}" in res.inner_text()

        # metric labels + copy, verbatim from the classic app (index.html runEq)
        assert "hold-out RMSE (last 20%)" in res.inner_text()
        assert "climatology baseline RMSE" in res.inner_text()
        assert ("beats" if beats else "loses to") in res.inner_text()
        assert ("skill" if beats else "no skill") in res.inner_text()  # skill badge
        # numbers are the LIVE experiment output, not literals
        assert _fmt(fit["rmse_holdout"]) in res.inner_text(), "hold-out RMSE is the live value"
        # recovered amplitudes row shows real fitted amplitudes
        amps = res.locator(".amps").inner_text()
        assert "recovered amplitudes" in amps
        assert f"{fit['amplitudes'][0]['period_d']}d" in amps
        # "What this means" interpretation quotes the live gain% and residual period
        interp = res.locator(".interp").inner_text()
        assert "What this means" in interp
        assert f"{gain}%" in interp, "interp shows the live gain, not a hard-coded number"
        assert f"~{fit['residual_top_period_d']} days" in interp
        assert ("explains real variation" in interp) if beats else ("publishes nulls" in interp)
        # Export to PDF button is present (classic parity)
        assert pg.get_by_role("button", name="Export to PDF").count() >= 1

        # axis labels present (y min/max + first/last date)
        assert res.locator(".yax span").count() == 2
        assert res.locator(".xax span").count() == 2
        assert fit["plot"]["dates"][0] in res.locator(".xax").inner_text()

        # chart caption is the target copy, per segment
        assert "never used for fitting" in res.locator(".chartcap2").inner_text()
        assert res.locator("svg.chart path.fitline").count() == 1
        res.get_by_role("button", name="Residuals").click()
        assert "leaves unexplained" in res.locator(".chartcap2").inner_text()
        assert res.locator("svg.chart path.resline").count() == 1
        res.get_by_role("button", name="Residual spectrum").click()
        assert "periodogram" in res.locator(".chartcap2").inner_text()
        assert res.locator("svg.chart line.stem, svg.chart line.peak").count() > 0

        # honest, non-dismissible disclaimer
        assert "never citable" in res.locator(".disc").inner_text()
        assert "0 multiplicity" in res.locator(".disc").inner_text()

        pg.screenshot(path=SHOT, full_page=True)
        assert not errs, f"console/page errors: {errs}"
        b.close()
    print(f"EQUATIONS E2E OK — matches target .dc.html (labels/captions/interp/"
          f"readjudication), live gain={gain}% beats={beats}, no hard-coded numbers. Shot: {SHOT}")


if __name__ == "__main__":
    run()
