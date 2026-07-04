#!/usr/bin/env python3
"""End-to-end test for the redesigned Ledger view (/console#ledger),
checked against the TARGET DESIGN in
  design_handoff_structure_lab_console/Structure Lab Console.dc.html  (§Ledger)
  design_handoff_structure_lab_console/screenshots/06-ledger.png

Fidelity: H1 "Ledger", the "Why this page exists" guide, the "Explore the
p-values" card with a Histogram / By family / In sequence segmented control and
a chart, three KPI tiles, an honesty-meter card, the recent-test-rows table, and
the instrument-families accordion.

NO number is hard-coded. The three tiles, the global-m label, the honesty meter
(discrete meta p, share ≤ .05, panel sha), the recent-rows count and the
family-legend chips are all derived from a live GET /api/state and asserted
against the rendered DOM — proving the UI shows the real multiplicity ledger, NOT
the mock's placeholders (173/126/47, honesty 0.385, fake rows).

The Ledger view is read-only (no POST), so nothing is mocked and no artefact is
touched.

Run:  <venv>/bin/python webapp/test_ledger_e2e.py http://localhost:8799
"""
import json
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_ledger.png"


def _api(path):
    return json.load(urllib.request.urlopen(f"{BASE}{path}"))


def _fmtp(p):
    if p is None:
        return "—"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def run():
    st = _api("/api/state")
    L = st.get("ledger", {})
    M = st.get("meta_panel", {})
    fams = st.get("families", {})
    recent = L.get("recent", [])
    # Live population that feeds the charts (parity with the view + classic app).
    live = [t for t in recent if t.get("raw_p") is not None and not t.get("exploratory")]
    live_families = sorted({(t.get("family_id") or "—") for t in live})
    assert L and recent, "live ledger must be non-empty"
    assert M.get("p_meta_discrete") is not None, "meta panel must be populated"

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 1400})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))

        pg.goto(f"{BASE}/console#ledger", wait_until="networkidle")
        pg.wait_for_selector("#lg-chart svg.lgchart")

        # --- header / copy fidelity ---
        assert pg.locator("h1.view-h1", has_text="Ledger").count() == 1
        assert pg.locator(".guide", has_text="The lab's accounting").count() == 1

        # --- segmented control: 3 modes, Histogram active by default ---
        seg = pg.locator("#lg-seg button")
        assert seg.count() == 3
        assert [seg.nth(i).inner_text() for i in range(3)] == \
            ["Histogram", "By family", "In sequence"]
        assert pg.locator("#lg-seg button.on").inner_text() == "Histogram"

        # --- three KPI tiles = live ledger counts (NOT the mock's 173/126/47) ---
        vals = pg.locator(".tiles .tile .val")
        assert vals.count() == 3
        assert vals.nth(0).inner_text().strip() == str(L["tests"]), "tile: test rows"
        assert vals.nth(1).inner_text().strip() == str(L["live"]), "tile: live"
        assert vals.nth(2).inner_text().strip() == str(L["exploratory"]), "tile: exploratory"
        assert f"global m = {L['global_m']}" in \
            pg.locator(".tiles .tile").nth(1).inner_text(), "tile shows live global m"

        # --- honesty meter reads live meta-panel figures (real ~0.03, not 0.385) ---
        honesty = pg.locator(".card", has_text="Honesty meter")
        htext = honesty.inner_text()
        assert _fmtp(M["p_meta_discrete"]) in htext, "live discrete meta p"
        assert f"{M['frac_le_05'] * 100:.1f}%" in htext, "live share ≤ .05"
        assert str(M["panel_sha"]) in htext, "live panel sha"
        assert "0.385" not in htext, "must not show the mock's placeholder honesty p"

        # --- recent test rows: one row per live ledger entry, real data shown ---
        rows = pg.locator(".ptable tbody tr")
        assert rows.count() == len(recent), \
            f"one row per recent ledger entry ({len(recent)})"
        assert pg.locator(".ptable tbody tr", has_text=recent[0]["dataset"]).count() >= 1
        assert pg.get_by_role("button", name="Export to PDF").count() == 1

        # --- instrument families accordion = live families ---
        assert pg.locator(".lg-fam").count() == len(fams), \
            f"one accordion per live family ({len(fams)})"

        # --- By family: legend chips = distinct live families; chart re-renders ---
        pg.locator("#lg-seg button", has_text="By family").click()
        pg.wait_for_selector("#lg-legend .lg-chip")
        assert pg.locator("#lg-legend .lg-chip").count() == len(live_families), \
            "one legend chip per distinct live family"
        assert pg.locator("#lg-chart svg.lgchart rect").count() == len(live_families)

        # --- In sequence: sparkline polyline over the live p-values ---
        pg.locator("#lg-seg button", has_text="In sequence").click()
        pg.wait_for_selector("#lg-chart svg.lgchart polyline")
        assert pg.locator("#lg-chart svg.lgchart polyline").count() == 1

        pg.screenshot(path=SHOT, full_page=True)
        assert not errs, f"console/page errors: {errs}"
        b.close()

    print(f"LEDGER E2E OK — tiles {L['tests']}/{L['live']}/{L['exploratory']} "
          f"(global m={L['global_m']}), honesty p={_fmtp(M['p_meta_discrete'])}, "
          f"{len(recent)} rows, {len(fams)} families, {len(live_families)} live "
          f"family chips. Shot: {SHOT}")


if __name__ == "__main__":
    run()
