"""Regenerate the synthetic scoring fixtures (deterministic). Contains no real-world questions or platform data."""
import json, os, random

rng = random.Random(20261009)
here = os.path.dirname(os.path.abspath(__file__))
forecasts, outcomes = [], []
for i in range(1, 41):
    true_p = rng.uniform(0.05, 0.95)
    y = int(rng.random() < true_p)
    noisy = min(0.98, max(0.02, true_p + rng.gauss(0, 0.12)))
    reference = [round(min(0.99, max(0.01, true_p + rng.gauss(0, 0.2))), 2) for _ in range(25)]
    forecasts.append({"id": f"syn-{i:03d}", "p": round(noisy, 3)})
    outcomes.append({"id": f"syn-{i:03d}", "outcome": y, "reference": reference})
json.dump(forecasts, open(os.path.join(here, "synthetic_forecasts.json"), "w"), indent=1)
json.dump(outcomes, open(os.path.join(here, "synthetic_outcomes.json"), "w"), indent=1)
