# Validation status

- **No validation results are published, and none are claimed.**
- **What was withdrawn.** A preliminary retro test (2026-10-08) used Metaculus tournament data collected through the website's internal endpoint. That collection is not authorized by the Metaculus Terms of Use for evaluating algorithms. Its data and numbers were therefore removed from this repository and are not relied on. See `DATA_POLICY.md`.
- **Planned validation, after written authorization from Metaculus:**
  1. **Leakage-safe pastcasting**, using the Bot Benchmarking Access Tier or other data Metaculus authorizes. Rules:
     - only questions opened after the models' knowledge cutoff;
     - forecasters see question text only;
     - pre-registered pass/fail thresholds.
  2. **The bot-testing-area tournament** for end-to-end checks. It is non-scoring and resubmission is allowed.
  3. **The live season itself**, scored by Metaculus.
- **Tooling:** `tools/score.py` computes Brier, log, a peer-style relative score and a percentile against any reference crowd you are allowed to use. It is tested on `tests/fixtures/` (synthetic).
