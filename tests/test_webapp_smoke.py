#!/usr/bin/env python3
"""Webapp smoke test: boots the real server on an ephemeral port and checks
the local-first guarantees the browser e2e suite assumes — no external
requests needed, fonts served locally, secrets never leave masked form.

Run: python3 -m pytest tests/test_webapp_smoke.py -q
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def server():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen(
        [sys.executable, os.path.join(REPO, "webapp", "server.py"),
         str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/api/state", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    else:
        proc.kill()
        pytest.fail("server did not come up")
    yield base
    proc.terminate()
    proc.wait(timeout=5)


def get(base, path):
    try:
        with urllib.request.urlopen(base + path, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def test_api_state(server):
    code, body = get(server, "/api/state")
    assert code == 200
    assert "pipeline" in json.loads(body)


def test_console_uses_only_local_fonts(server):
    code, body = get(server, "/")
    assert code == 200
    html = body.decode()
    assert "fonts.googleapis.com" not in html, \
        "console must not depend on a CDN (local-first)"
    assert '/fonts/fonts.css' in html


def test_fonts_served_locally(server):
    code, body = get(server, "/fonts/fonts.css")
    assert code == 200
    css = body.decode()
    assert "https://" not in css, "vendored css must reference local files"
    for m in ("Newsreader", "Hanken Grotesk", "IBM Plex Mono"):
        assert m in css
    # every referenced woff2 actually resolves
    import re
    for name in set(re.findall(r"/fonts/([\w.-]+\.woff2)", css)):
        code, body = get(server, f"/fonts/{name}")
        assert code == 200 and body[:4] == b"wOF2", name


def test_fonts_route_rejects_traversal(server):
    for probe in ("/fonts/../server.py", "/fonts/..%2fserver.py",
                  "/fonts/x.py"):
        code, _ = get(server, probe)
        assert code == 404, probe


def test_config_keys_always_masked(server):
    code, body = get(server, "/api/config")
    assert code == 200
    cfg = json.loads(body)
    for v in cfg.get("api_keys", {}).values():
        assert v == "set" or "…" in v, "keys must never be served in plaintext"


def test_lan_gate_logic():
    """Unit test the --lan token gate: loopback exempt, valid token grants a
    cookie session, bad/absent token denied, non-LAN mode wide open."""
    sys.path.insert(0, os.path.join(REPO, "webapp"))
    try:
        import server
    finally:
        sys.path.pop(0)
    g = server.lan_gate
    tok = "sekret123"
    # not in LAN mode: everything allowed
    assert g("192.168.1.50", {}, "", None) == "allow"
    # LAN mode: loopback always exempt (scripts + launcher keep working)
    assert g("127.0.0.1", {}, "", tok) == "allow"
    assert g("::1", {}, "", tok) == "allow"
    # LAN peer without credentials: denied
    assert g("192.168.1.50", {}, "", tok) == "deny"
    # LAN peer with wrong token: denied
    assert g("192.168.1.50", {"token": "wrong"}, "", tok) == "deny"
    assert g("192.168.1.50", {}, "labtoken=wrong", tok) == "deny"
    # valid ?token= -> one-time cookie grant; valid cookie -> allowed
    assert g("192.168.1.50", {"token": tok}, "", tok) == "set-cookie"
    assert g("192.168.1.50", {}, f"labtoken={tok}", tok) == "allow"
    assert g("192.168.1.50", {}, f"other=x; labtoken={tok}", tok) == "allow"


def test_localhost_unaffected_by_lan_gate(server):
    """The running (non---lan) server must not demand any token."""
    code, _ = get(server, "/api/state")
    assert code == 200


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
