"""Tests for tools/score.py using hand-checkable cases and synthetic fixtures only."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import score  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def test_hand_checked_values():
    r = score.score([{"id": 1, "p": 0.8}], [{"id": 1, "outcome": 1, "reference": [0.5, 0.5]}])
    assert r["n"] == 1
    assert math.isclose(r["brier"], 0.04, abs_tol=1e-4)
    assert math.isclose(r["log"], math.log(0.8), abs_tol=1e-4)
    assert math.isclose(r["peer_mean"], 100 * (math.log(0.8) - math.log(0.5)), abs_tol=1e-3)
    assert r["pct_mean"] == 1.0


def test_unmatched_ids_and_missing_reference():
    r = score.score([{"id": "a", "p": 0.3}], [{"id": "a", "outcome": 0}, {"id": "b", "outcome": 1}])
    assert r["n"] == 1 and r["peer_mean"] is None and r["pct_mean"] is None


def test_extreme_probabilities_are_clipped():
    r = score.score([{"id": 1, "p": 1.0}], [{"id": 1, "outcome": 0}])
    assert math.isfinite(r["log"])


def test_synthetic_fixture_runs():
    fc = json.load(open(os.path.join(FIX, "synthetic_forecasts.json")))
    oc = json.load(open(os.path.join(FIX, "synthetic_outcomes.json")))
    r = score.score(fc, oc)
    assert r["n"] == 40
    assert 0 <= r["brier"] <= 1 and 0 <= r["pct_mean"] <= 1
