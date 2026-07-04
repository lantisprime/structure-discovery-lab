#!/usr/bin/env python3
"""Unit tests for the console-redesign server additions (read-only surfaces):
compute_governance / governance_preview (single-source-of-truth multiplicity
math) and dataset_stats (wizard dataset-card previews).

Run:  python3 webapp/test_server.py
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server  # noqa: E402


class TestGovernance(unittest.TestCase):
    def test_empty_selection_has_no_correction(self):
        g = server.compute_governance([])
        self.assertEqual(g["families_engaged"], [])
        self.assertEqual(g["n_families"], 0)
        self.assertEqual(g["claims"], 0)
        self.assertIsNone(g["alpha_corrected"])
        self.assertIsNone(g["m_min"])

    def test_unknown_instruments_are_dropped(self):
        g = server.compute_governance(["not_an_instrument", "mmd"])
        self.assertEqual(g["instruments"], ["mmd"])
        self.assertEqual(g["claims"], 1)

    def test_same_family_instruments_count_once(self):
        # mmd -> two-sample, half-corr -> hit-count-temporal (2 families);
        # lambda-max -> hit-count-cooc adds a 3rd. Two instruments in ONE
        # family must not inflate the family count.
        single_fam = server.compute_governance(["matrix-completion",
                                                 "knn-recovery"])  # both recovery
        self.assertEqual(single_fam["n_families"], 1)
        self.assertEqual(single_fam["claims"], 2)

    def test_sidak_and_floor_formulas(self):
        g = server.compute_governance(["mmd", "half-corr", "lambda-max"])
        self.assertEqual(g["n_families"], 3)
        expected_alpha = 1 - (1 - 0.05) ** (1.0 / 3)
        self.assertAlmostEqual(g["alpha_corrected"], round(expected_alpha, 6))
        self.assertEqual(g["m_min"], math.ceil(2 / expected_alpha) - 1)

    def test_more_families_tighten_alpha(self):
        a2 = server.compute_governance(["mmd", "half-corr"])["alpha_corrected"]
        a3 = server.compute_governance(
            ["mmd", "half-corr", "lambda-max"])["alpha_corrected"]
        self.assertLess(a3, a2)  # more families -> smaller corrected alpha

    def test_preview_matches_enforcement_source(self):
        # governance_preview must return exactly what compute_governance does
        insts = ["mmd", "cca-covariates", "delay-embed-H1"]
        self.assertEqual(server.governance_preview({"instruments": insts}),
                         server.compute_governance(insts))

    def test_preview_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            server.governance_preview({"instruments": "mmd"})     # not a list
        with self.assertRaises(ValueError):
            server.governance_preview({"instruments": ["x"] * 41})  # too many


class TestDatasetStats(unittest.TestCase):
    def test_lottery_game_stats(self):
        s = server.dataset_stats("Lotto 6/42")
        self.assertIsNotNone(s)
        self.assertGreaterEqual(s["rows"], 150)
        self.assertLessEqual(s["rows"], 170)
        self.assertTrue(s["first_date"].startswith("2025"))
        self.assertTrue(s["last_date"].startswith("2026"))
        self.assertTrue(1 <= len(s["sparkline"]) <= 24)
        self.assertTrue(all(isinstance(v, float) for v in s["sparkline"]))
        self.assertEqual(s["source"], server.PCSO_DRAWS)
        self.assertTrue(s["preview"])

    def test_all_five_lottery_sets_resolve(self):
        for name in server.LOTTO_GAME:
            self.assertIsNotNone(server.dataset_stats(name), name)

    def test_astro_series_stats(self):
        s = server.dataset_stats("moon_distance")
        self.assertIsNotNone(s)
        self.assertEqual(s["rows"], 366)
        self.assertTrue(s["sparkline"])

    def test_unknown_dataset_is_none(self):
        self.assertIsNone(server.dataset_stats("no_such_dataset"))

    def test_stats_are_cached(self):
        a = server.dataset_stats("Mega Lotto 6/45")
        b = server.dataset_stats("Mega Lotto 6/45")
        self.assertIs(a, b)  # same object back from the mtime cache

    def test_experiment_options_is_additive(self):
        opts = server.experiment_options()
        # old contract intact: datasets is still name -> description string
        self.assertIn("datasets", opts)
        self.assertTrue(all(isinstance(v, str)
                            for v in opts["datasets"].values()))
        # new contract: dataset_stats keyed by the same dataset names
        self.assertIn("dataset_stats", opts)
        self.assertEqual(set(opts["dataset_stats"]), set(opts["datasets"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
