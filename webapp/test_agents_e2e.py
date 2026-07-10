#!/usr/bin/env python3
"""End-to-end test for the redesigned Agents / Run centre view (/console#agents),
checked against the TARGET DESIGN in
  design_handoff_structure_lab_console/Structure Lab Console.dc.html  (§Run centre)
  design_handoff_structure_lab_console/screenshots/07-agents.png

Fidelity: H1 "Run centre", the guide + "Run the three gates" CTA, job-group cards
(Gates & health / Registered executors / Analysis / Maintenance) each with Run
buttons, the "Launch a standalone agent" card, and the "Running now" panel.

NO count is hard-coded: the job groups and their Run buttons are derived from a
live GET /api/jobs and asserted against the DOM. The launch/run/cancel POSTs are
INTERCEPTED so no real job or agent process is ever spawned; the webapp/joblogs
directory is asserted UNCHANGED before/after. The intercepted POST body is
checked to prove the standalone launcher sends {task, role} (the classic app sent
a non-existent provider field and no role).

Run:  <venv>/bin/python webapp/test_agents_e2e.py http://localhost:8799
"""
import json
import os
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BREAK_PCSO_UI = "--break-pcso-ui" in sys.argv
ARGS = [arg for arg in sys.argv[1:] if arg != "--break-pcso-ui"]
BASE = ARGS[0] if ARGS else "http://localhost:8799"
SHOT = ARGS[1] if len(ARGS) > 1 else "/tmp/console_agents.png"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBLOGS = os.path.join(REPO, "webapp", "joblogs")


def _api(path):
    return json.load(urllib.request.urlopen(f"{BASE}{path}"))


def _joblogs():
    return sorted(os.listdir(JOBLOGS)) if os.path.isdir(JOBLOGS) else []


def run():
    jobs = _api("/api/jobs")
    defs = jobs["defs"]
    if BREAK_PCSO_UI:
        defs["gates"] = [
            item for item in defs.get("gates", [])
            if item.get("name") != "pcso_weekly_verify"
        ]
    # runnable (Run-button) defs per category = everything except the task-need
    # standalone-agent def, which the mock routes to its own launcher card.
    runnable = {cat: [d for d in ds if "task" not in (d.get("needs") or [])]
                for cat, ds in defs.items()}
    total_run = sum(len(v) for v in runnable.values())
    assert total_run, "server must declare runnable jobs"
    cat_titles = {"gates": "Gates & health", "executors": "Registered executors",
                  "analysis": "Analysis tools", "maintenance": "Maintenance"}

    before = _joblogs()
    posted = []  # captured intercepted POST bodies

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 1500})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))

        # Intercept job-control POSTs so nothing actually executes. GET /api/jobs
        # passes through to the live server.
        def handle_jobs(route, request):
            if request.method == "POST":
                body = json.loads(request.post_data or "{}")
                posted.append(body)
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps({"id": "e2e-mock-job", "job": body.get("job"),
                                               "label": "E2E mock job", "status": "running",
                                               "started": "00:00:00"}))
            else:
                if BREAK_PCSO_UI:
                    response = route.fetch()
                    value = response.json()
                    value["defs"]["gates"] = [
                        item for item in value["defs"].get("gates", [])
                        if item.get("name") != "pcso_weekly_verify"
                    ]
                    route.fulfill(response=response, body=json.dumps(value))
                else:
                    route.continue_()

        def handle_cancel(route, request):
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"id": "e2e-mock-job", "status": "cancelled"}))
        pg.route("**/api/jobs", handle_jobs)
        pg.route("**/api/jobs/cancel", handle_cancel)

        pg.goto(f"{BASE}/console#agents", wait_until="networkidle")
        pg.wait_for_selector("#ag-groups .card")

        # --- header / copy fidelity ---
        assert pg.locator("h1.view-h1", has_text="Run centre").count() == 1
        assert pg.locator(".guide", has_text="cockpit").count() == 1
        assert pg.get_by_role("link", name="Run the three gates").count() == 1

        # --- job-group cards + Run buttons match the live whitelist ---
        for cat, title in cat_titles.items():
            if runnable.get(cat):
                assert pg.locator("#ag-groups .card", has_text=title).count() == 1, \
                    f"missing group card: {title}"
        assert pg.locator("#ag-groups .ag-item button", has_text="Run").count() == total_run, \
            f"one Run button per runnable job ({total_run})"
        pcso_row = pg.locator(".ag-item", has_text="Verify PCSO weekly batch")
        assert pcso_row.count() == 1, "PCSO byte verifier must be visible"

        # --- standalone launcher: textarea + role select (3 roles) + Launch ---
        assert pg.locator("#ag-task").count() == 1
        assert pg.locator("#ag-role option").count() == 3
        assert pg.get_by_role("button", name="Launch agent").count() == 1
        assert pg.locator("#ag-running .card", has_text="Running now").count() == 1

        # --- Run a gate (mocked POST): opens the log panel, no real job runs ---
        design_row = pg.locator(".ag-item", has_text="Design verifier")
        design_row.get_by_role("button", name="Run").click()
        pg.wait_for_selector("#ag-log .ag-logcard")
        assert posted and posted[-1]["job"] == "design_verifier", \
            "Run posts the whitelisted job name"
        pcso_row.get_by_role("button", name="Run").click()
        for _ in range(40):
            if posted and posted[-1].get("job") == "pcso_weekly_verify":
                break
            pg.wait_for_timeout(50)
        assert posted[-1]["job"] == "pcso_weekly_verify", \
            "PCSO Run posts the non-mutating verifier job"

        # --- launch validation: <10 chars rejected, no POST ---
        n_before = len(posted)
        pg.fill("#ag-task", "too short")
        pg.get_by_role("button", name="Launch agent").click()
        pg.wait_for_selector("#toast.on")
        assert len(posted) == n_before, "short task must not POST"

        # --- launch success: sends {task, role}, NOT a provider field ---
        pg.fill("#ag-task", "Run all three gates then rebuild the honesty meter")
        pg.select_option("#ag-role", "reviewer")
        pg.get_by_role("button", name="Launch agent").click()
        # the intercepted POST resolves synchronously; give the async handler a beat
        for _ in range(40):
            if len(posted) > n_before:
                break
            pg.wait_for_timeout(50)
        assert len(posted) > n_before, "launch must POST"
        launch = posted[-1]
        assert launch["job"] == "agent_task"
        assert launch["params"].get("task", "").startswith("Run all three gates")
        assert launch["params"].get("role") == "reviewer", "role must be sent"
        assert "provider" not in launch["params"], \
            "must not resend the classic app's phantom provider field"

        pg.screenshot(path=SHOT, full_page=True)
        assert not errs, f"console/page errors: {errs}"
        b.close()

    after = _joblogs()
    assert before == after, \
        f"joblogs changed! a real job ran despite mocking: {set(after) - set(before)}"

    print(f"AGENTS E2E OK — {len(runnable)} groups, {total_run} runnable jobs, "
          f"3 roles; Run+launch POSTs intercepted (job='{posted[0]['job']}' … "
          f"launch role='{posted[-1]['params'].get('role')}', no provider); "
          f"joblogs untouched ({len(after)}). Shot: {SHOT}")


if __name__ == "__main__":
    run()
