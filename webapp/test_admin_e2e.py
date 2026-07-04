#!/usr/bin/env python3
"""End-to-end test for the redesigned Admin view (/console#admin), checked against
the TARGET DESIGN in
  design_handoff_structure_lab_console/Structure Lab Console.dc.html  (§Admin)
  design_handoff_structure_lab_console/screenshots/08-admin.png

Admin migrates the classic app's FULL admin functionality (index.html ROUTES.admin
+ setAuth/saveProv/saveRole/testRole/addDataset/saveSettings) into the mock's skin:
an auth-method toggle, a searchable provider list with per-provider key/model/base
save, subscription-CLI status, one role card per agent role (provider pills, model
select, effort seg, live Test), validated dataset onboarding, and lab settings.

Determinism + safety: GET /api/providers and /api/config are served from a STATEFUL
fixture whose POSTs mutate it (so auth toggles, provider saves and role changes
round-trip through the real client code without depending on — or writing —
webapp/config.local.json). POST /api/datasets and POST /api/test_role are
intercepted so no dataset is written to datasets/user/ and no real LLM call is made.
The datasets/user dir and config.local.json are asserted unchanged before/after.

Run:  <venv>/bin/python webapp/test_admin_e2e.py http://localhost:8799
"""
import copy
import json
import os
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/console_admin.png"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DS = os.path.join(REPO, "datasets", "user")
CFG = os.path.join(REPO, "webapp", "config.local.json")

FIXTURE_PROV = {
    "active": "anthropic", "auth_method": "api_key",
    "providers": [
        {"id": "anthropic", "label": "Anthropic", "protocol": "anthropic",
         "base": "https://api.anthropic.com", "get": "https://console.anthropic.com/",
         "models": ["claude-fable-5", "claude-haiku-4-5"], "keyless": False,
         "model": "", "configured": True, "key_masked": "sk-…ab"},
        {"id": "openai", "label": "OpenAI", "protocol": "openai",
         "base": "https://api.openai.com/v1", "get": "https://platform.openai.com/",
         "models": ["gpt-5.5"], "keyless": False, "model": "", "configured": False,
         "key_masked": None},
        {"id": "ollama", "label": "Ollama (local)", "protocol": "openai",
         "base": "http://localhost:11434/v1", "get": "", "models": ["llama3"],
         "keyless": True, "model": "", "configured": True, "key_masked": None},
        {"id": "claude_cli", "label": "Claude subscription", "protocol": "cli",
         "base": "", "get": "", "models": ["claude-default"], "keyless": True,
         "role_only": True, "model": "", "configured": True, "key_masked": None},
    ],
    "roles": {
        "analyst": {"label": "Analyst", "icon": "🔬", "desc": "designs registrations",
                    "provider": "anthropic", "model": "", "effort": "deep"},
        "executor": {"label": "Executor", "icon": "⚙", "desc": "runs to the letter",
                     "provider": "anthropic", "model": "", "effort": "balanced"},
        "reviewer": {"label": "Reviewer", "icon": "🛡", "desc": "adversarial check",
                     "provider": "anthropic", "model": "", "effort": "deep"},
        "companion": {"label": "Companion", "icon": "💬", "desc": "the in-console guide",
                      "provider": "anthropic", "model": "", "effort": "balanced"},
    },
    "subscriptions": [
        {"id": "claude", "label": "Claude Pro/Max (Claude Code CLI)",
         "get": "https://claude.com/", "cmd": "claude", "flow": "Follow the prompts.",
         "relogin": "claude /logout", "installed": True, "signed_in": False},
    ],
}
FIXTURE_CFG = {"api_keys": {"PROVIDER_ANTHROPIC_KEY": "sk-…ab"},
               "settings": {"default_m": 399, "owner": "Cha (lab owner)"},
               "config_path": "webapp/config.local.json (fixture)"}


def _snapshot(d):
    return sorted(os.listdir(d)) if os.path.isdir(d) else None


def run():
    prov = copy.deepcopy(FIXTURE_PROV)
    cfg = copy.deepcopy(FIXTURE_CFG)
    posts = {"providers": [], "config": [], "datasets": [], "test_role": []}
    ds_before = _snapshot(USER_DS)
    cfg_before = os.path.exists(CFG) and open(CFG, "rb").read()

    def handle_providers(route, request):
        if request.method == "POST":
            body = json.loads(request.post_data or "{}")
            posts["providers"].append(body)
            if body.get("auth_method"):
                prov["auth_method"] = body["auth_method"]
            if body.get("role"):
                rc = body.get("config") or {}
                r = prov["roles"][body["role"]]
                # mirror the server: changing provider without a model drops the old
                if rc.get("provider") and rc["provider"] != r.get("provider") \
                        and "model" not in rc:
                    r["model"] = ""
                r.update({k: v for k, v in rc.items() if k in ("provider", "model", "effort")})
            if body.get("id"):
                p = next(x for x in prov["providers"] if x["id"] == body["id"])
                if body.get("key"):
                    p["configured"] = True
                    p["key_masked"] = "sk-…zz"
                if body.get("model"):
                    p["model"] = body["model"]
                if body.get("base"):
                    p["base"] = body["base"]
                if body.get("active"):
                    prov["active"] = body["id"]
            route.fulfill(status=200, content_type="application/json", body=json.dumps(prov))
        else:
            route.fulfill(status=200, content_type="application/json", body=json.dumps(prov))

    def handle_config(route, request):
        if request.method == "POST":
            body = json.loads(request.post_data or "{}")
            posts["config"].append(body)
            cfg["settings"].update(body.get("settings") or {})
            route.fulfill(status=200, content_type="application/json", body=json.dumps(cfg))
        else:
            route.fulfill(status=200, content_type="application/json", body=json.dumps(cfg))

    def handle_datasets(route, request):
        posts["datasets"].append(json.loads(request.post_data or "{}"))
        route.fulfill(status=200, content_type="application/json", body=json.dumps({
            "slug": "e2e_fixture", "validation": {
                "rows": 128, "date_range": ["2025-01-01", "2025-05-08"],
                "duplicate_dates": 0, "value_column": "value",
                "numeric_columns": ["value"], "missing_frac": 0.0,
                "mean": 12.3, "min": 1.0, "max": 20.0},
            "next": "Dataset validated and saved."}))

    def handle_test_role(route, request):
        posts["test_role"].append(json.loads(request.post_data or "{}"))
        route.fulfill(status=200, content_type="application/json", body=json.dumps({
            "ok": True, "provider": "anthropic", "model": "claude-fable-5",
            "latency_ms": 412}))

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 1700})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/api/providers", handle_providers)
        pg.route("**/api/config", handle_config)
        pg.route("**/api/datasets", handle_datasets)
        pg.route("**/api/test_role", handle_test_role)

        pg.goto(f"{BASE}/console#admin", wait_until="networkidle")
        pg.wait_for_selector(".role-card")

        # --- structure / copy fidelity ---
        assert pg.locator("h1.view-h1", has_text="Admin").count() == 1
        assert pg.locator(".guide", has_text="authenticate").count() == 1
        assert pg.locator(".adm-h", has_text="How should agents authenticate").count() == 1
        assert pg.locator(".adm-h", has_text="Who does what").count() == 1
        assert pg.locator(".role-card").count() == 4, "one card per agent role"
        assert pg.locator(".card", has_text="Data sources").count() == 1
        assert pg.locator(".card", has_text="Lab settings").count() == 1
        assert pg.locator(".card", has_text="Health gates").count() == 1

        # --- auth=api_key (fixture default): provider list, role_only excluded ---
        assert pg.locator(".prov-search").first.is_visible()
        assert pg.locator(".prov-item").count() == 3, "3 key providers (role_only CLI excluded)"
        assert pg.locator(".prov-item", has_text="Anthropic").locator(
            ".badge.ok", has_text="configured").count() == 1

        # --- provider search filters client-side (no POST) ---
        n = len(posts["providers"])
        pg.fill(".prov-search", "openai")
        assert pg.locator(".prov-item:visible").count() == 1
        assert pg.locator(".prov-item:visible", has_text="OpenAI").count() == 1
        pg.fill(".prov-search", "")
        assert len(posts["providers"]) == n, "search must not POST"

        # --- expand a provider + save key/model (real POST payload) ---
        # The Default-model field is a picklist of the provider's known models (no
        # typing an id from memory) with a Custom fallback — assert the options come
        # from the server's model list, then pick one.
        pg.locator(".prov-row", has_text="OpenAI").click()
        opts = pg.locator("#pm-openai option").all_inner_texts()
        assert "gpt-5.5" in opts and any("Custom" in o for o in opts), opts
        # Custom fallback reveals a free-text id box; a known model hides it again.
        pg.select_option("#pm-openai", "__custom__")
        assert pg.locator("#pmc-openai").is_visible()
        pg.select_option("#pm-openai", "gpt-5.5")
        assert not pg.locator("#pmc-openai").is_visible()
        pg.fill("#pk-openai", "sk-test-123")
        pg.locator("#prov-openai").get_by_role("button", name="Save & make active").click()
        pg.wait_for_timeout(200)
        save = posts["providers"][-1]
        assert save["id"] == "openai" and save["key"] == "sk-test-123" \
            and save["model"] == "gpt-5.5" and save["active"] is True, save
        # re-render reflected server state: OpenAI now configured + active
        assert pg.locator(".prov-item", has_text="OpenAI").locator(
            ".badge.ok", has_text="configured").count() == 1

        # --- auth toggle -> subscription panel, then back ---
        pg.get_by_role("button", name="Use a subscription").click()
        pg.wait_for_selector("#adm-auth-sub")
        assert posts["providers"][-1] == {"auth_method": "subscription"}
        assert pg.locator("#adm-auth-sub", has_text="Claude Pro/Max").is_visible()
        assert pg.locator("#adm-auth-sub .adm-pre", has_text="claude").count() == 1
        pg.get_by_role("button", name="Use an API key").click()
        pg.wait_for_selector(".prov-search")

        # --- role: switch provider via pill (POST provider-only) ---
        analyst = pg.locator(".role-card", has_text="Analyst")
        analyst.locator(".pill", has_text="Ollama").click()
        pg.wait_for_timeout(200)
        rp = posts["providers"][-1]
        assert rp.get("role") == "analyst" and rp["config"]["provider"] == "ollama", rp
        analyst = pg.locator(".role-card", has_text="Analyst")
        assert "on" in (analyst.locator(".pill", has_text="Ollama").get_attribute("class") or "")

        # --- role: change effort -> auto-save with effort ---
        analyst.locator("#role-e-analyst button", has_text="fast").click()
        pg.wait_for_timeout(150)
        assert posts["providers"][-1]["config"]["effort"] == "fast"

        # --- role: live Test (intercepted) shows a success line ---
        analyst.get_by_role("button", name="Test").click()
        pg.wait_for_selector("#role-t-analyst:has-text('works')")
        assert posts["test_role"][-1]["role"] == "analyst"

        # --- dataset onboarding: validated add (intercepted, no fs write) ---
        pg.locator(".adm-adds-t").click()
        pg.fill("#ds-name", "Manila rainfall daily")
        pg.fill("#ds-src", "PAGASA")
        pg.fill("#ds-csv", "date,value\n2025-01-01,12.3\n")
        pg.get_by_role("button", name="Validate & add").click()
        pg.wait_for_selector("#ds-report .guide")
        assert posts["datasets"][-1]["name"] == "Manila rainfall daily"
        assert pg.locator("#ds-report", has_text="Validated & added").count() == 1
        assert pg.locator("#ds-report", has_text="128 rows").count() == 1

        # --- lab settings save (real POST payload) ---
        pg.fill("#set-m", "999")
        pg.fill("#set-owner", "Juan dela Cruz (lab owner)")
        pg.get_by_role("button", name="Save settings").click()
        pg.wait_for_timeout(150)
        st = posts["config"][-1]["settings"]
        assert st["default_m"] == 999 and st["owner"] == "Juan dela Cruz (lab owner)", st

        pg.screenshot(path=SHOT, full_page=True)
        assert not errs, f"console/page errors: {errs}"
        b.close()

    # No repo writes: dataset dir + config.local.json untouched (POSTs intercepted).
    assert _snapshot(USER_DS) == ds_before, "datasets/user must be unchanged"
    assert (os.path.exists(CFG) and open(CFG, "rb").read()) == cfg_before, \
        "config.local.json must be unchanged (provider/config POSTs were intercepted)"

    print(f"ADMIN E2E OK — 4 role cards; auth toggle round-trips; provider "
          f"search filters ({len(posts['providers'])} provider POSTs captured); "
          f"provider save sends key+model+active; role provider/effort auto-save; "
          f"Test intercepted; dataset add sends CSV (no fs write); settings save "
          f"sends {{default_m,owner}}; datasets/user + config.local.json untouched. "
          f"Shot: {SHOT}")


if __name__ == "__main__":
    run()
