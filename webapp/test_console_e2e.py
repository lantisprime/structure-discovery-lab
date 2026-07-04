#!/usr/bin/env python3
"""End-to-end browser test for the redesigned console (/console), driven with
Playwright against a live server. Asserts the Overview renders REAL lab data
(not the prototype placeholders), that the honesty meter never mislabels a
mildly-hot panel as "looks honest", nav/companion/responsive behavior, and that
unbuilt views degrade honestly.

Run:  python3 webapp/server.py 8799 &   then
      <venv>/bin/python webapp/test_console_e2e.py http://localhost:8799
"""
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

        pg.goto(f"{BASE}/console", wait_until="networkidle")
        pg.wait_for_selector(".greet", timeout=5000)

        body = pg.inner_text("body")

        # 1. Real ledger count (22 runs), not the prototype's "10".
        assert pg.locator(".tile", has_text="experiments in the run ledger").locator(
            ".val").inner_text().strip() == "22", "run count should be live (22)"

        # 2. Honesty meter: live 0.032 AND honest label — NEVER "looks honest"
        #    while the panel is mildly hot (frac_le_05 above the sim band).
        htile = pg.locator(".tile", has_text="honesty-meter p")
        hval = htile.locator(".val").inner_text().strip()
        assert hval.startswith("0.032"), f"honesty p should be live ~0.032, got {hval}"
        hlab = htile.inner_text()
        assert "looks honest" not in hlab, "must not mislabel a hot panel as honest"
        assert "excess" in hlab, "hot panel should surface the #45 excess caveat"
        assert "0.385" not in body, "prototype placeholder 0.385 must not appear"

        # 3. Priced-into-correction tile is the live live-test count (195).
        assert pg.locator(".tile", has_text="priced into the global correction"
                          ).locator(".val").inner_text().strip() == "195"

        # 4. Next-action reflects live pipeline (no pending approval => eval step).
        nexttitle = pg.locator(".next h2").inner_text().lower()
        assert "eval" in nexttitle or "experiment" in nexttitle, nexttitle
        assert pg.locator(".next .eyebrow").inner_text().lower() == \
            "right now, the lab needs one thing"   # CSS uppercases it

        # 5. Latest result shows the real newest run + a parsed grade badge.
        assert "corrected_rerun_r1" in pg.locator(".rightcol").inner_text()
        assert pg.locator(".rightcol .badge").first.inner_text().strip() == "G2"

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

        # 10. Unbuilt view degrades honestly (placeholder, no crash).
        pg.goto(f"{BASE}/console#ledger", wait_until="networkidle")
        pg.wait_for_selector(".view", timeout=3000)
        assert "being rebuilt" in pg.inner_text("body"), "unbuilt view placeholder"

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
