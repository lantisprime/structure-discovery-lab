#!/usr/bin/env python3
"""End-to-end browser test for the redesigned console (/console), driven with
Playwright against a live server. Asserts the Overview renders REAL lab data
(not the prototype placeholders), that the honesty meter never mislabels a
mildly-hot panel as "looks honest", nav/companion/responsive behavior, and that
unbuilt views degrade honestly.

Run:  python3 webapp/server.py 8799 &   then
      <venv>/bin/python webapp/test_console_e2e.py http://localhost:8799
"""
import re
import sys
from playwright.sync_api import sync_playwright, expect

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_overview.png"


def run():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))

        # Source of truth: the page must mirror the SAME live state the API
        # serves — never pinned snapshots, which rot on the next legitimate
        # ledger append, and never the prototype's placeholders.
        state = pg.request.get(f"{BASE}/api/state").json()
        n_runs = len(state["runs"])
        live_m = state["ledger"]["live"]
        panel = state["meta_panel"]
        p_live = panel["p_meta_discrete"]
        band_hi = panel["sim_frac_le_05_q05_q95"][1]
        panel_hot = panel["frac_le_05"] > band_hi

        pg.goto(f"{BASE}/console", wait_until="networkidle")
        pg.wait_for_selector(".greet", timeout=5000)

        body = pg.inner_text("body")

        # 1. Run-ledger tile mirrors the live ledger, not the prototype's "10".
        rtile_val = pg.locator(".tile", has_text="experiments in the run ledger"
                               ).locator(".val").inner_text().strip()
        assert rtile_val == str(n_runs), \
            f"run count should be live ({n_runs}), got {rtile_val}"

        # 2. Honesty meter: live p AND an honest label — NEVER "looks honest"
        #    while the panel is actually hot (frac_le_05 above the sim band).
        htile = pg.locator(".tile", has_text="honesty-meter p")
        hval = htile.locator(".val").inner_text().strip()
        assert hval.startswith(f"{p_live:.3f}"[:5]), \
            f"honesty p should be live ~{p_live:.3f}, got {hval}"
        hlab = htile.inner_text()
        if panel_hot:
            assert "looks honest" not in hlab, \
                "must not mislabel a hot panel as honest"
            assert "excess" in hlab, "hot panel should surface the excess caveat"
        assert "0.385" not in body, "prototype placeholder 0.385 must not appear"
        # panel provenance restored from the classic app (version + n_tests)
        assert f"v{panel['panel_version']}" in hlab and "tests" in hlab, \
            "honesty tile shows panel version + n_tests"

        # 3. Live-tests tile mirrors the ledger + the frac_le_05 figure.
        ltile = pg.locator(".tile", has_text="live tests toward global m")
        assert ltile.locator(".val").inner_text().strip() == str(live_m)
        assert "≤ .05" in ltile.inner_text(), "restore the % ≤ .05 figure from index.html"

        # 4. Next-action reflects live pipeline (no pending approval => eval step).
        nexttitle = pg.locator(".next h2").inner_text().lower()
        assert "eval" in nexttitle or "experiment" in nexttitle, nexttitle
        assert pg.locator(".next .eyebrow").inner_text().lower() == \
            "right now, the lab needs one thing"   # CSS uppercases it

        # 5. Latest result shows the real newest run + a parsed grade badge,
        #    plus the classic provenance (script + registration) and nav to agents.
        newest_run = state["runs"][0]["run_id"]
        rc = pg.locator(".rightcol").inner_text()
        assert newest_run in rc, \
            f"latest card should show the ledger's newest run ({newest_run})"
        badge = pg.locator(".rightcol .badge").first.inner_text().strip()
        assert re.fullmatch(r"G\d\S*", badge), \
            f"latest card shows a parsed grade badge, got {badge!r}"
        assert ".py" in rc, "latest card shows the run's script (classic parity)"
        assert "REGISTRATION" in rc.upper(), "latest card shows the registration doc"
        assert pg.locator(".rightcol a", has_text="Agent status").count() == 1

        # 6. No pending approvals right now => no pending badge anywhere.
        assert pg.locator(".penddot").count() == 0, "no pending dot when queue empty"

        # 7. Help cards present (3) and open the companion.
        assert pg.locator(".help").count() == 3
        pg.locator(".help", has_text="The honesty meter").click()
        pg.wait_for_selector(".comp.open", timeout=3000)
        assert pg.locator(".comp .chip").count() == 3, "quick-ask chips present"
        pg.locator(".comp .x").click()
        pg.wait_for_selector(".comp.open", state="detached", timeout=3000) \
            if pg.locator(".comp.open").count() == 0 else None

        # 8. Companion button toggles the drawer.
        pg.locator(".compbtn").click()
        pg.wait_for_selector(".comp.open", timeout=3000)
        pg.locator(".comp .x").click()

        # 9. Responsive: <=720px hides inline pills, shows the hamburger.
        pg.set_viewport_size({"width": 700, "height": 900})
        pg.wait_for_timeout(200)
        assert not pg.locator("nav.pills").is_visible(), "pills hide on phone"
        assert pg.locator(".morebtn").is_visible(), "hamburger shows on phone"
        pg.set_viewport_size({"width": 1280, "height": 900})

        # 10. Unknown view degrades honestly (fallback card, no crash). Every real
        #     view is built post-cut-over, so hit a bogus hash to reach notBuilt.
        pg.goto(f"{BASE}/console#nonexistent", wait_until="networkidle")
        pg.wait_for_selector(".view", timeout=3000)
        body = pg.inner_text("body")
        assert "isn't part of the console" in body, "unknown-view fallback text"
        assert "/classic" in pg.content(), "fallback points to the classic app at /classic"

        # 11. Screenshot the Overview for the human review.
        pg.goto(f"{BASE}/console", wait_until="networkidle")
        pg.wait_for_selector(".greet")
        pg.screenshot(path=SHOT, full_page=True)

        assert not errs, f"console/page errors: {errs}"
        b.close()
    print("E2E OK — Overview renders live data; honesty label honest; "
          f"nav/companion/responsive/unbuilt all pass. Shot: {SHOT}")


if __name__ == "__main__":
    run()
