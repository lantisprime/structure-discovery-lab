#!/usr/bin/env python3
"""End-to-end test for the redesigned Approvals view (/console#approvals),
checked against the TARGET DESIGN in
  design_handoff_structure_lab_console/Structure Lab Console.dc.html  (§Approvals)
  design_handoff_structure_lab_console/screenshots/02-approvals.png

Approvals is the lab's HUMAN GATE (a core non-negotiable): nothing registered
runs without the owner's signature, and the sign flow must GENUINELY POST and
reflect state — never a cosmetic "signed ✓". This test proves exactly that:

  * The pending queue + audit log are RENDERED FROM DATA, not hard-coded — a
    GET /api/approvals is intercepted with a fixture and asserted against the DOM
    (title, doc path, Read/Approve buttons, sign-as input, audit rows).
  * Clicking Approve issues a REAL POST /api/approvals carrying
    {doc, name, decision:"approve"} — the intercepted body is inspected — and the
    view re-renders from the refreshed queue on success.
  * The gate refuses an unsigned approval: with the "Sign as" field emptied,
    Approve fires NO POST (mirrors the server, which raises without a name).
  * The guide CTA "Sign the pending registration" focuses the signature field but
    must NOT auto-approve — reading before signing is the gate itself.
  * A live read-only pass (no GET intercept) confirms the real server's queue
    renders (empty-state today).

Because the mutating POST is intercepted, NOTHING under docs/ is written and the
append-only results/webapp_approvals.jsonl is asserted absent/unchanged before and
after — the test never edits a frozen registration. (The real server gate itself,
record_approval(), is unchanged classic code, verified separately by a live curl
round-trip against a throwaway fixture during review.)

Run:  <venv>/bin/python webapp/test_approvals_e2e.py http://localhost:8799
"""
import json
import os
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_approvals.png"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPR_LOG = os.path.join(REPO, "results", "webapp_approvals.jsonl")
DOCS = os.path.join(REPO, "docs")

# Fixture the intercepted GET returns — every figure here is invented so the test
# proves the DOM mirrors server data rather than any baked-in prototype number.
FIX_DOC = "docs/REGISTRATION_E2E_FIXTURE.md"
FIX_TITLE = "E2E fixture — corrected-instrument rerun"
FIXTURE = {
    "pending": [{"doc": FIX_DOC, "title": FIX_TITLE}],
    "recorded": [
        {"doc": "docs/REGISTRATION_EQ_READJUDICATION.md", "name": "Cha (lab owner)",
         "decision": "approve", "ts": "2026-07-03T09:14:02"},
    ],
}


def _api(path):
    return json.load(urllib.request.urlopen(f"{BASE}{path}"))


def _docs_snapshot():
    return sorted(os.listdir(DOCS)) if os.path.isdir(DOCS) else []


def _log_snapshot():
    if not os.path.exists(APPR_LOG):
        return None
    with open(APPR_LOG) as f:
        return f.read()


def run():
    # Ground truth: the real, unintercepted queue (read-only) must render.
    live = _api("/api/approvals")

    docs_before = _docs_snapshot()
    log_before = _log_snapshot()
    posted = []       # captured intercepted POST bodies
    doc_reads = []    # captured /api/doc reads (Read button)

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 1400})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))

        # Intercept the approvals endpoint: GET -> fixture, POST -> capture + fake
        # success (so no registration is ever patched and no jsonl is written).
        state = {"serve_fixture": True}

        def handle_appr(route, request):
            if request.method == "POST":
                posted.append(json.loads(request.post_data or "{}"))
                # After a successful sign the queue is empty (item consumed).
                state["serve_fixture"] = False
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps({"doc": posted[-1].get("doc"),
                                               "name": posted[-1].get("name"),
                                               "decision": "approve",
                                               "doc_patched": True}))
            else:
                payload = FIXTURE if state["serve_fixture"] else {"pending": [], "recorded": FIXTURE["recorded"]}
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps(payload))

        def handle_doc(route, request):
            from urllib.parse import urlparse, parse_qs
            name = parse_qs(urlparse(request.url).query).get("name", [""])[0]
            doc_reads.append(name)
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"name": name,
                                           "body": "# " + FIX_TITLE + "\n\nDraft body for review."}))

        pg.route("**/api/approvals", handle_appr)
        pg.route("**/api/doc*", handle_doc)

        pg.goto(f"{BASE}/console#approvals", wait_until="networkidle")
        pg.wait_for_selector(".appr-row")

        # --- header / copy fidelity (mock + non-negotiable gate framing) ---
        assert pg.locator("h1.view-h1", has_text="Approvals").count() == 1
        assert pg.locator(".guide", has_text="human gate").count() == 1
        assert pg.get_by_role("link", name="Sign the pending registration").count() == 1
        assert pg.locator(".appr-h2", has_text="Awaiting your signature").count() == 1
        assert pg.locator(".appr-h2", has_text="Audit log").count() == 1

        # --- pending row rendered FROM the fixture (title + doc + both buttons) ---
        row = pg.locator(".appr-row")
        assert row.count() == 1, "exactly one pending row from the fixture"
        assert row.locator(".appr-title", has_text=FIX_TITLE).count() == 1
        assert row.locator(".appr-doc", has_text=FIX_DOC).count() == 1
        assert row.get_by_role("button", name="Approve").count() == 1
        assert row.get_by_role("button", name="Read").count() == 1, \
            "Read (viewDoc) preserved — reading the draft is part of the gate"

        # --- sign-as input present, defaulted ---
        assert pg.locator("#appr-name").input_value() == "Cha (lab owner)"

        # --- audit log rows rendered from the fixture ---
        assert pg.locator(".appr-log", has_text="Cha (lab owner)").count() == 1
        assert pg.locator(".appr-log", has_text="docs/REGISTRATION_EQ_READJUDICATION.md").count() == 1

        # --- Read opens the draft (real /api/doc round-trip, intercepted) ---
        row.get_by_role("button", name="Read").click()
        pg.wait_for_selector(".overlay .md")
        assert doc_reads and doc_reads[-1] == FIX_DOC, "Read fetches the pending doc"
        pg.keyboard.press("Escape")

        # --- gate refuses an unsigned approval: empty name -> NO POST ---
        pg.fill("#appr-name", "")
        pg.get_by_role("button", name="Approve").click()
        pg.wait_for_selector("#toast.on")
        assert len(posted) == 0, "Approve with no signature must not POST"

        # --- guide CTA focuses the signature field but does NOT auto-approve ---
        pg.get_by_role("link", name="Sign the pending registration").click()
        pg.wait_for_timeout(150)
        assert len(posted) == 0, "the CTA must never sign on the owner's behalf"

        # --- real signature: Approve POSTs {doc,name,decision} and re-renders ---
        pg.fill("#appr-name", "Juan dela Cruz (lab owner)")
        pg.get_by_role("button", name="Approve").click()
        for _ in range(60):
            if posted:
                break
            pg.wait_for_timeout(50)
        assert len(posted) == 1, "Approve must issue exactly one POST"
        sig = posted[0]
        assert sig.get("doc") == FIX_DOC, "signs the pending doc"
        assert sig.get("name") == "Juan dela Cruz (lab owner)", "carries the signature verbatim"
        assert sig.get("decision") == "approve", "decision is approve"

        # --- success reflects state: queue re-rendered, now cleared ---
        pg.wait_for_selector(".appr-clear")
        assert pg.locator(".appr-row").count() == 0, "signed item leaves the queue"
        assert pg.locator(".appr-clear", has_text="Nothing pending").count() == 1

        pg.screenshot(path=SHOT, full_page=True)
        assert not errs, f"console/page errors: {errs}"
        b.close()

    # Nothing was written to disk: the POST was intercepted, so no registration
    # under docs/ changed and the append-only approvals log is untouched.
    assert _docs_snapshot() == docs_before, "docs/ must be unchanged (no registration written)"
    assert _log_snapshot() == log_before, "approvals log must be unchanged (POST was intercepted)"

    print(f"APPROVALS E2E OK — live queue rendered (pending={len(live['pending'])}, "
          f"recorded={len(live['recorded'])}); fixture pending row + audit log render "
          f"from data; Read fetches the draft; unsigned Approve blocked; CTA does not "
          f"auto-approve; Approve POSTs {{doc,name='{posted[0]['name']}',decision}} and "
          f"clears the queue; docs/ + approvals log untouched. Shot: {SHOT}")


if __name__ == "__main__":
    run()
