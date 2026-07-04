#!/usr/bin/env python3
"""End-to-end test for the redesigned Theorems view (/console#theorems),
checked against the TARGET DESIGN in
  design_handoff_structure_lab_console/Structure Lab Console.dc.html  (§Theorems)

Fidelity: H1 "Theorem arsenal", the guide CTA "Propose a card", search placeholder,
face chips, card -> modal + "Export to PDF", the propose-a-card modal.

NO count is hard-coded: card count, face chips and per-face counts are derived from a
live GET /api/kb and asserted against the rendered DOM — proving the UI shows the real
arsenal, not literals.

The propose flow is exercised WITHOUT touching the frozen docs/kb corpus: POST /api/kb
is intercepted/mocked in the browser, the GET reload passes through to the real server,
and the real docs/kb file list is asserted UNCHANGED before/after.

Run:  <venv>/bin/python webapp/test_theorems_e2e.py http://localhost:8799
"""
import json
import os
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_theorems.png"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(REPO, "docs", "kb")

MOCK_SLUG = "e2e-mock-proposed-card"
MOCK_NEXT = ("Card created as PROPOSED. Next: run 'Re-measure instrument families' "
             "in the Run centre to harmonize it.")


def _api(path):
    return json.load(urllib.request.urlopen(f"{BASE}{path}"))


def _kb_listing():
    return sorted(f for f in os.listdir(KB_DIR)
                  if f.endswith(".md") and f != "INDEX.md")


def run():
    kb = _api("/api/kb")
    total = len(kb)
    faces = sorted({c["face"] for c in kb if c["face"]})
    assert total and faces, "live KB must be non-empty with faces"
    face0 = faces[0]
    face0_count = sum(1 for c in kb if c["face"] == face0)
    # a distinctive word from the first card's title, for the search test
    word = max(kb[0]["title"].replace("—", " ").split(), key=len).lower()

    before = _kb_listing()  # frozen-corpus snapshot

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 1200})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))

        # Intercept ONLY POST /api/kb (propose). GET passes through to the real
        # server so the list renders live data; POST is mocked so no file is written.
        def handle_kb(route, request):
            if request.method == "POST":
                body = json.loads(request.post_data or "{}")
                if len(body.get("title", "")) < 5:
                    route.fulfill(status=200, content_type="application/json",
                                  body=json.dumps({"error": "title: 5-90 characters"}))
                else:
                    route.fulfill(status=200, content_type="application/json",
                                  body=json.dumps({"file": f"docs/kb/{MOCK_SLUG}.md",
                                                   "slug": MOCK_SLUG, "next": MOCK_NEXT}))
            else:
                route.continue_()
        pg.route("**/api/kb", handle_kb)

        pg.goto(f"{BASE}/console#theorems", wait_until="networkidle")
        pg.wait_for_selector(".th-card")

        # --- header / copy fidelity ---
        assert pg.locator("h1.view-h1", has_text="Theorem arsenal").count() == 1
        assert (pg.locator("#th-q").get_attribute("placeholder")
                == "Search theorems, statistics, blind spots…")
        assert pg.get_by_role("link", name="Propose a card").count() == 1

        # --- every live card renders; none is falsely badged PROPOSED ---
        assert pg.locator(".th-card").count() == total, "one card per live KB entry"
        assert pg.locator(".th-card .th-prop").count() == 0, \
            "no established card may show a PROPOSED badge"

        # --- face chips: All + each distinct live face ---
        assert pg.locator(".th-face").count() == len(faces) + 1
        assert pg.locator(".th-faces", has_text="All").count() == 1

        # --- face filter narrows to the live per-face count ---
        pg.locator(".th-face", has_text=face0).first.click()
        assert pg.locator(".th-card").count() == face0_count, \
            f"filtering by {face0} must show exactly its {face0_count} cards"
        pg.locator(".th-face", has_text="All").first.click()
        assert pg.locator(".th-card").count() == total

        # --- search narrows and still shows the matching card ---
        pg.fill("#th-q", word)
        n = pg.locator(".th-card").count()
        assert 1 <= n <= total, f"search '{word}' -> {n} of {total}"
        assert pg.locator(".th-card", has_text=kb[0]["title"][:24]).count() >= 1
        pg.fill("#th-q", "")

        # --- card -> modal with body + Export to PDF, no PROPOSED warning ---
        pg.locator(".th-card").first.click()
        pg.wait_for_selector(".modal")
        assert pg.locator(".modal .md").inner_text().strip(), "modal shows the card body"
        assert pg.get_by_role("button", name="Export to PDF").count() == 1
        assert pg.locator(".modal .th-caution").count() == 0, \
            "an admitted card shows no not-citable warning"
        pg.keyboard.press("Escape")
        assert pg.locator(".modal").count() == 0

        # --- propose modal: validation error path then success path (mocked POST) ---
        pg.get_by_role("link", name="Propose a card").click()
        pg.wait_for_selector("#pp-title")
        pg.fill("#pp-title", "x")  # too short -> mocked server rejects
        pg.fill("#pp-stmt", "Counts of runs are asymptotically normal under H0.")
        pg.fill("#pp-h0", "Expected run count for an iid binary sequence.")
        pg.fill("#pp-det", "Serial clustering and over-alternation.")
        pg.fill("#pp-blind", "Higher-order structure beyond one-step runs.")
        pg.get_by_role("button", name="Create PROPOSED card").click()
        pg.wait_for_selector("#pp-err:visible")
        assert "title" in pg.locator("#pp-err").inner_text().lower()

        # fix the title -> success -> "harmonize" guidance appears
        pg.fill("#pp-title", "Runs test — Wald-Wolfowitz")
        pg.get_by_role("button", name="Create PROPOSED card").click()
        pg.wait_for_selector(".guide", state="attached")
        pg.wait_for_function(
            "() => document.body.innerText.includes('now harmonize it')")
        assert MOCK_NEXT[:32] in pg.locator("#app").inner_text()

        pg.screenshot(path=SHOT, full_page=True)
        assert not errs, f"console/page errors: {errs}"
        b.close()

    after = _kb_listing()
    assert before == after, \
        f"frozen docs/kb changed! before={len(before)} after={len(after)}"
    assert f"{MOCK_SLUG}.md" not in after, "mocked propose must not write a real card"

    print(f"THEOREMS E2E OK — {total} live cards, faces={faces}, face '{face0}'"
          f"={face0_count}; modal+propose(validate+success, mocked); docs/kb "
          f"untouched ({len(after)} cards). Shot: {SHOT}")


if __name__ == "__main__":
    run()
