#!/usr/bin/env python3
"""Unit tests for the console-redesign server additions (read-only surfaces):
compute_governance / governance_preview (single-source-of-truth multiplicity
math) and dataset_stats (wizard dataset-card previews).

Run:  python3 webapp/test_server.py
"""
import json
import math
import os
import shutil
import sys
import tempfile
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


class TestEquationSandbox(unittest.TestCase):
    def test_series_list_maps_name_to_label(self):
        sl = server.__dict__.get("SERIES")
        base = {k: v[2] for k, v in sl.items()}
        self.assertIn("moon_distance", base)
        self.assertTrue(all(isinstance(v, str) for v in base.values()))

    def test_get_series_returns_dates_and_values(self):
        s = server.get_series("moon_distance")
        self.assertEqual(s["name"], "moon_distance")
        self.assertTrue(s["label"])
        self.assertEqual(len(s["dates"]), len(s["values"]))
        self.assertGreater(len(s["values"]), 100)

    def test_try_equation_happy_path_and_spectrum(self):
        r = server.try_equation({"series": "moon_distance",
                                 "periods_d": [27.555], "trend": False})
        for k in ("rmse_train", "rmse_holdout", "rmse_climatology_holdout",
                  "beats_climatology", "disclaimer", "residual_spectrum",
                  "residual_top_period_d", "residual_top_share", "plot"):
            self.assertIn(k, r)
        self.assertEqual(set(r["plot"]),
                         {"dates", "y", "fit", "train_end_index"})
        self.assertEqual(len(r["plot"]["y"]), len(r["plot"]["fit"]))
        # residual_spectrum is a sorted-by-period list of {period_d, share}
        sp = r["residual_spectrum"]
        self.assertTrue(1 <= len(sp) <= 48)
        self.assertTrue(all({"period_d", "share"} <= set(d) for d in sp))
        self.assertEqual([d["period_d"] for d in sp],
                         sorted(d["period_d"] for d in sp))
        self.assertTrue(all(0 <= d["share"] <= 1 for d in sp))
        self.assertIn("never citable", r["disclaimer"])

    def test_try_equation_rejects_bad_period_count(self):
        with self.assertRaises(ValueError):
            server.try_equation({"series": "moon_distance", "periods_d": []})
        with self.assertRaises(ValueError):
            server.try_equation({"series": "moon_distance",
                                 "periods_d": [1, 2, 3, 4, 5, 6]})


class TestKBFaces(unittest.TestCase):
    """kb_cards() face/status enrichment over the real docs/kb corpus."""

    @classmethod
    def setUpClass(cls):
        cls.cards = server.kb_cards()

    def test_corpus_non_empty(self):
        self.assertTrue(self.cards)

    def test_every_card_has_a_face(self):
        # Regression: the old **Face**-only regex left every current card (all
        # of which use **Domain face**) with an empty face and a dead filter.
        self.assertTrue(all(c["face"] for c in self.cards),
                        "every card must resolve a non-empty normalized face")

    def test_face_taxonomy_is_the_known_set(self):
        faces = {c["face"] for c in self.cards}
        self.assertLessEqual(faces, {"statistical", "dynamical", "algorithmic",
                                     "cross-sectional", "relational", "decision",
                                     "marginal"})

    def test_enriched_keys_present_and_typed(self):
        for c in self.cards:
            self.assertTrue({"face", "face_raw", "status", "admitted"} <= set(c))
            self.assertIsInstance(c["admitted"], bool)

    def test_cross_sectional_not_split_on_hyphen(self):
        faces = {c["face"] for c in self.cards}
        self.assertNotIn("cross", faces)          # never split the token on '-'
        self.assertIn("cross-sectional", faces)

    def test_all_current_cards_are_admitted(self):
        # HONESTY GUARD: no established arsenal card may be flagged non-admitted
        # merely for lacking a Status line. Only the exact kb_add signature marks
        # a card PROPOSED, and none of the shipped cards carry it.
        not_admitted = [c["slug"] for c in self.cards if not c["admitted"]]
        self.assertEqual(not_admitted, [])

    def test_face_normalizer_units(self):
        self.assertEqual(server._kb_norm_face("cross-sectional/physical"),
                         "cross-sectional")
        self.assertEqual(
            server._kb_norm_face("marginal/geometric — and the lab's only *exclusion*"),
            "marginal")
        self.assertEqual(server._kb_norm_face("relational (paired rows)"),
                         "relational")

    def test_both_face_labels_parse(self):
        self.assertTrue(server.KB_FACE_RE.search("**Domain face**: statistical"))
        self.assertTrue(server.KB_FACE_RE.search("**Face**: statistical"))


class TestKBAdd(unittest.TestCase):
    """kb_add() writes a PROPOSED card. Runs against an isolated temp ROOT so the
    real (frozen) docs/kb corpus is never touched."""

    def setUp(self):
        self._real_root = server.ROOT
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "docs", "kb"))
        server.ROOT = self.tmp

    def tearDown(self):
        server.ROOT = self._real_root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _valid(self, **over):
        p = {"title": "Runs test — Wald-Wolfowitz",
             "face": "statistical",
             "statement": "Counts of runs are asymptotically normal under H0.",
             "h0": "Expected run count for an iid binary sequence.",
             "detects": "Serial clustering and over-alternation.",
             "blind": "Higher-order structure beyond one-step runs."}
        p.update(over)
        return p

    def test_creates_proposed_card_read_back_as_not_admitted(self):
        r = server.kb_add(self._valid())
        self.assertIn("slug", r)
        made = [c for c in server.kb_cards() if c["slug"] == r["slug"]]
        self.assertEqual(len(made), 1)
        c = made[0]
        self.assertFalse(c["admitted"])           # carries the PROPOSED signature
        self.assertEqual(c["status"], "proposed")
        self.assertEqual(c["face"], "statistical")  # **Face** label parses back

    def test_real_docs_kb_untouched(self):
        r = server.kb_add(self._valid(title="Isolation probe theorem card"))
        real_made = os.path.join(self._real_root, "docs", "kb", r["slug"] + ".md")
        self.assertFalse(os.path.exists(real_made),
                         "kb_add must not write into the real docs/kb")

    def test_validation_rejects_short_fields(self):
        with self.assertRaises(ValueError):
            server.kb_add(self._valid(title="x"))            # title too short
        with self.assertRaises(ValueError):
            server.kb_add(self._valid(statement="short"))    # < 10 chars


class TestApprovalsGate(unittest.TestCase):
    """The REAL human gate behind the redesigned Approvals view: record_approval()
    must genuinely append the signature to the append-only log AND fill the
    registration's approved_by_human line, and approvals_list() must reflect the
    queue draining. Runs against an isolated temp ROOT so no real (frozen)
    registration or the real results/ log is ever touched."""

    BLANK = "- approved_by_human: ____________  date: ____________"

    def setUp(self):
        self._real_root, self._real_appr = server.ROOT, server.APPROVALS
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "docs"))
        os.makedirs(os.path.join(self.tmp, "results"))
        server.ROOT = self.tmp
        server.APPROVALS = os.path.join(self.tmp, "results", "webapp_approvals.jsonl")
        self.doc = "docs/REGISTRATION_GATE_FIXTURE.md"
        with open(os.path.join(self.tmp, self.doc), "w") as f:
            f.write("# Gate fixture registration\n\n## Governance\n" + self.BLANK + "\n")

    def tearDown(self):
        server.ROOT, server.APPROVALS = self._real_root, self._real_appr
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_unsigned_registration_is_pending(self):
        q = server.approvals_list()
        self.assertEqual([p["doc"] for p in q["pending"]], [self.doc])
        self.assertEqual(q["recorded"], [])

    def test_missing_name_raises_the_gate(self):
        with self.assertRaises(ValueError):
            server.record_approval({"doc": self.doc, "name": "  "})

    def test_doc_outside_docs_is_rejected(self):
        with self.assertRaises(ValueError):
            server.record_approval({"doc": "../secrets.md", "name": "x"})

    def test_signing_patches_doc_appends_log_and_drains_queue(self):
        entry = server.record_approval(
            {"doc": self.doc, "name": "Juan dela Cruz (lab owner)", "decision": "approve"})
        # (a) registration approval line genuinely filled
        self.assertTrue(entry["doc_patched"])
        txt = open(os.path.join(self.tmp, self.doc)).read()
        self.assertIn("approved_by_human: Juan dela Cruz (lab owner) (via webapp)", txt)
        self.assertNotIn("____________", txt)
        # (b) append-only log carries the signature + a pre-image hash
        self.assertTrue(os.path.exists(server.APPROVALS))
        logged = [json.loads(l) for l in open(server.APPROVALS) if l.strip()]
        self.assertEqual(len(logged), 1)
        self.assertEqual(logged[0]["name"], "Juan dela Cruz (lab owner)")
        self.assertEqual(logged[0]["channel"], "webapp")
        self.assertTrue(logged[0]["sha_before"])
        # (c) queue drains; the now-signed doc appears under recorded
        q = server.approvals_list()
        self.assertEqual(q["pending"], [])
        self.assertEqual(q["recorded"][0]["doc"], self.doc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
