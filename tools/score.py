"""Score binary probability forecasts against outcomes, optionally relative to a reference crowd.

Generic tool: it only reads files you pass in. It ships with synthetic fixtures (tests/fixtures).
Use it only on data you are allowed to use; see docs/DATA_POLICY.md.

Inputs (JSON):
  forecasts: [{"id": str|int, "p": float}]
  outcomes:  [{"id": str|int, "outcome": 0|1, "reference": [p, p, ...] (optional)}]

Metrics:
  brier  mean (p - y)^2
  log    mean ln(p assigned to the realised outcome)
  peer   100 * (ln p_ours - mean ln p_reference), the shape of a Metaculus-style relative score
  pct    share of reference forecasters whose log score we beat (ties count half)

Usage: python tools/score.py forecasts.json outcomes.json
"""
import json
import math
import statistics as st
import sys

CLIP = (0.001, 0.999)


def log_score(p: float, y: int) -> float:
    p = min(max(p, CLIP[0]), CLIP[1])
    return math.log(p if y else 1 - p)


def score(forecasts: list[dict], outcomes: list[dict]) -> dict:
    preds = {str(f["id"]): float(f["p"]) for f in forecasts}
    rows = []
    for o in outcomes:
        key = str(o["id"])
        if key not in preds:
            continue
        p, y = preds[key], int(o["outcome"])
        ours = log_score(p, y)
        row = {"id": key, "p": p, "y": y, "brier": (p - y) ** 2, "log": ours}
        ref = o.get("reference") or []
        if ref:
            ref_logs = [log_score(r, y) for r in ref]
            row["peer"] = 100 * (ours - st.mean(ref_logs))
            row["pct"] = (sum(r < ours for r in ref_logs) + 0.5 * sum(r == ours for r in ref_logs)) / len(ref_logs)
        rows.append(row)

    def mean_of(k):
        vals = [r[k] for r in rows if k in r]
        return round(st.mean(vals), 4) if vals else None

    return {"n": len(rows), "brier": mean_of("brier"), "log": mean_of("log"),
            "peer_mean": mean_of("peer"), "pct_mean": mean_of("pct"), "rows": rows}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    fc = json.load(open(sys.argv[1], encoding="utf-8"))
    oc = json.load(open(sys.argv[2], encoding="utf-8"))
    result = score(fc, oc)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=1))
