"""Novel-model tickets: no lookahead, and the tickets equal what the registered harness scores."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R
import pcso_frozen_law as FL
import pcso_registered_predictions as P
import pcso_sparse_registered as SR
from pcso_sparse_switch import CPSparseSwitch


class _Law:
    def __init__(self, seen):
        self.seen = seen

    def top6(self):
        return [1, 2, 3, 4, 5, 6]

    def logq(self, S):
        return 0.0

    def inclusion(self):
        import numpy as np
        return np.full(42, 6 / 42)


class Spy:
    """Records, at every predict, how many rows it had been updated with."""
    name = "spy"

    def __init__(self):
        self.updates, self.seen_at_predict = 0, []

    def predict(self, P):
        self.seen_at_predict.append(self.updates)
        return _Law(self.updates)

    def update(self, P, S):
        self.updates += 1


class SparseSpy(CPSparseSwitch):
    name = "sparse_spy"

    def __init__(self):
        self.t, self.resets = 5, []

    def predict(self, P):
        self.resets.append(self.t)
        return _Law(0)

    def update(self, P, S):
        self.t += 1


def _rows(dates):
    return [(d, 42, (1, 7, 13, 19, 25, 31)) for d in dates]


def test_every_ticket_is_made_before_its_draw_is_seen():
    spy = Spy()
    rows = _rows(["2026-09-20", "2026-09-21", "2026-09-22", "2026-09-24"])
    per = P.walk([spy], rows, "2026-09-21")
    assert spy.seen_at_predict == [0, 1, 2, 3]            # predict at row i has seen exactly i rows
    assert [r["date"] for r in per["spy"]] == ["2026-09-21", "2026-09-22", "2026-09-24"]
    assert [r["window"] for r in per["spy"]] == ["exploratory", "exploratory", "registered"]
    assert all(r["matches"] == 1 for r in per["spy"])      # ticket 1-6 vs draw containing 1


def test_sparse_clock_restarts_once_at_the_first_registered_draw():
    sp = SparseSpy()
    P.walk([sp], _rows(["2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25"]), "2026-09-01")
    # t before each predict: 5, 6, 7 on conditioning rows; reset to 0 before 2026-09-24, then 1
    assert sp.resets == [5, 6, 0, 1]


def test_summary_sums_full_precision_increments():
    recs = [{"P": 42, "matches": 1, "log_e": 0.0000014, "window": "registered"}] * 3
    assert P.summarize(recs)["all"]["log_evidence"] == round(3 * 0.0000014, 6)   # not 3 * round(.)


@pytest.fixture(scope="module")
def real():
    rows = R.load()
    models = P.roster()
    per = P.walk(models, rows, "0000-00-00")
    return rows, per, models


def test_next_tickets_are_isolated_from_order_and_leave_state_untouched(real):
    rows, _, models = real
    pools = sorted({p for _, p, _ in rows})
    cp = [m for m in models if m.name == "cp_nest"][0]
    rng_before = json.dumps(cp.rng.bit_generator.state, sort_keys=True)
    together = P.next_tickets(models, pools)
    for pool in reversed(pools):                      # any order, one game at a time
        alone = P.next_tickets(models, [pool])
        assert alone == {P.GAME[pool]: together[P.GAME[pool]]}
    assert json.dumps(cp.rng.bit_generator.state, sort_keys=True) == rng_before


def test_next_tickets_follow_c3(real):
    rows, _, models = real
    pools = sorted({p for _, p, _ in rows})
    tickets = P.next_tickets(models, pools)
    for pool in pools:
        for model in models:
            law = copy.deepcopy(model).predict(pool)
            graph = FL._decode_arrays(json.loads(FL.encode(FL.freeze(law, pool))))
            expected = FL.ticket_from_inclusion(FL.inclusion(graph))
            assert tickets[P.GAME[pool]][model.name]["ticket"] == expected
    for pool in (42, 58):
        assert tickets[P.GAME[pool]]["pair_parity"]["ticket"] == [1, 2, 3, 4, 5, 6]


def test_registered_tickets_equal_the_harness_overlaps(real):
    rows, per, _ = real
    base, ens = R.roster(P.SEED)
    harness = R.run_registered([*base, ens], rows)
    for name, h in harness.items():
        mine = [(r["P"], r["matches"]) for r in per[name] if r["window"] == "registered"]
        assert mine == [tuple(x) for x in h["overlaps"]], name
    sparse = SR.score(rows)["registered"]["overlaps"]
    mine = [(r["P"], r["matches"]) for r in per["cp_sparse_switch"] if r["window"] == "registered"]
    assert mine == [tuple(x) for x in sparse]


def test_walk_forward_matches_equal_the_harness_run(real):
    rows, per, _ = real
    base, ens = R.roster(P.SEED)
    res = R.run([*base, ens], rows)
    for name, r in res.items():
        seen, mine = {}, []
        for rec in per[name]:
            n = seen.get(rec["P"], 0)
            if n >= 30:                                   # run()'s warm-up per game
                mine.append((rec["P"], rec["matches"]))
            seen[rec["P"]] = n + 1
        assert mine == [(p, k) for p, k, _ in r["wf"]], name
