#!/usr/bin/env python3
"""Playwright e2e regression test for lotto_picker.html (static file, no server needed).

Guards the 'New random pair' button: tickets C/D must regenerate on click, tickets A/B must
stay fixed (posterior sets), the regeneration stamp must appear, and no console/page errors
may occur. Skips gracefully if the playwright browsers are not installed.
Run: .venv/bin/python -m pytest webapp/test_lotto_picker_e2e.py -v
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "lotto_picker.html"

try:
    from playwright.sync_api import sync_playwright
    HAS_PW = True
except ImportError:
    HAS_PW = False


@unittest.skipUnless(HAS_PW and PAGE.exists(), "playwright or lotto_picker.html missing")
class TestLottoPickerPage(unittest.TestCase):
    url = PAGE.as_uri()

    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.pg = self.browser.new_page()
        self.errors: list[str] = []
        self.pg.on("pageerror", lambda e: self.errors.append(str(e)))
        self.pg.goto(self.url)
        self.pg.wait_for_timeout(1000)

    def tearDown(self):
        self.pg.close()

    def test_page_renders_cards_without_errors(self):
        self.assertGreaterEqual(self.pg.locator(".card").count(), 2)
        self.assertEqual(self.errors, [])

    def test_new_random_pair_button_regenerates_c_and_d(self):
        before = self.pg.locator(".tk.b2 .ball").all_inner_texts()
        self.assertTrue(before, "no random pair rendered on load")
        self.pg.click("button:has-text('New random pair')")
        self.pg.wait_for_timeout(400)
        after = self.pg.locator(".tk.b2 .ball").all_inner_texts()
        self.assertNotEqual(before, after, "tickets C/D did not regenerate on click")
        self.assertEqual(self.errors, [])

    def test_regeneration_stamp_appears(self):
        self.pg.click("button:has-text('New random pair')")
        self.pg.wait_for_timeout(400)
        stamp = self.pg.locator("#regen").inner_text().strip()
        self.assertTrue(stamp.startswith("random pair C/D regenerated at"), stamp)

    def test_posterior_tickets_a_and_b_stay_fixed(self):
        a0 = self.pg.locator(".tk.pred .ball").all_inner_texts()
        b0 = self.pg.locator(".tk.pred2 .ball").all_inner_texts()
        self.pg.click("button:has-text('New random pair')")
        self.pg.wait_for_timeout(400)
        a1 = self.pg.locator(".tk.pred .ball").all_inner_texts()
        b1 = self.pg.locator(".tk.pred2 .ball").all_inner_texts()
        self.assertEqual(a0, a1, "posterior ticket A must not change on regenerate")
        self.assertEqual(b0, b1, "posterior ticket B must not change on regenerate")

    def test_csi_parity_selftest_passes(self):
        parity = self.pg.locator("#parity").inner_text()
        self.assertIn("8/8 vectors OK", parity, parity)

    def test_documentation_collapsed_by_default_and_expandable(self):
        doc = self.pg.locator("details.doc")
        self.assertGreaterEqual(doc.count(), 8, "expected collapsible doc sections")
        self.assertEqual(self.pg.locator(".banner").count(), 1)
        self.assertFalse(self.pg.locator(".banner").is_visible(), "banner must be collapsed by default")
        doc.first.locator("summary").click()
        self.pg.wait_for_timeout(200)
        self.assertTrue(self.pg.locator(".banner").is_visible(), "banner must expand on tap")
        card_doc = self.pg.locator("details.carddoc").first
        card_doc.scroll_into_view_if_needed()
        self.assertFalse(card_doc.locator(".meta.mono").is_visible())
        card_doc.locator("summary").click()
        self.assertTrue(card_doc.locator(".meta.mono").is_visible())


if __name__ == "__main__":
    unittest.main()
