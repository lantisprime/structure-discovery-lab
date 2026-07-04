#!/usr/bin/env python3
"""Regression test for the console cut-over routing (server.py do_GET).

After the redesign cut-over the REDESIGNED console is the default: `/`, `/index.html`,
`/console` all serve webapp/static/console.html, while the original app stays
reachable at `/classic`. This guards that mapping so a future edit can't silently
send `/` back to the classic app (or drop the /classic fallback).

The two documents are told apart by their <title>:
  console.html -> "Structure Lab · Console"
  index.html   -> "Structure Discovery Lab"

Run:  python3 webapp/test_routing.py [http://localhost:8799]   (server must be running)
"""
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8799"
CONSOLE_TITLE = "<title>Structure Lab · Console</title>"
CLASSIC_TITLE = "<title>Structure Discovery Lab</title>"


def _get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return r.read().decode("utf-8", "replace")


def run():
    console_routes = ["/", "/index.html", "/console", "/console.html"]
    classic_routes = ["/classic", "/classic.html"]

    for p in console_routes:
        html = _get(p)
        assert CONSOLE_TITLE in html, f"{p} must serve the redesigned console"
        assert CLASSIC_TITLE not in html, f"{p} must NOT serve the classic app"

    for p in classic_routes:
        html = _get(p)
        assert CLASSIC_TITLE in html, f"{p} must serve the classic app"
        assert CONSOLE_TITLE not in html, f"{p} must NOT serve the redesigned console"

    print(f"ROUTING OK — default console at {console_routes}; "
          f"classic fallback at {classic_routes}.")


if __name__ == "__main__":
    run()
