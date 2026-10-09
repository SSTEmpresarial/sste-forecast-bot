# Changelog (significant changes; the tournament rules require disclosing mid-season updates)

## 2026-10-09
- Repository history rewritten into a single commit, so that earlier commits containing Metaculus-derived data are no longer reachable from any branch. No forecasts had ever been submitted.
- Removed all Metaculus-derived data from the repository: validation rows, shadow forecasts with question titles, and the scoring script tied to them. Added `docs/DATA_POLICY.md`.
- Validation claims withdrawn (`docs/VALIDATION.md`).
- Model configuration is now committed in `config/models.json`, with profiles `frontier_lean` (default), `low_cost`, `validated_like` and `metaculus_credits`. Selected via `FORECAST_PROFILE`.
- `INCLUDE_MINIBENCH` switch.
- Configurable reasoning effort and parser validation samples.
- Added `tools/cost_model.py`, `docs/COSTS.md`, `tools/score.py` with synthetic fixtures, `LICENSE` (SSTE files only), `NOTICE` and `docs/REPRODUCE.md`.
- The bot remains **inactive** (`BOT_ENABLED` unset) pending written authorization from Metaculus.

## 2026-10-08
- Initial SSTE version on top of the Metaculus Fall 2026 template:
  - alternating prompt styles;
  - model rotation;
  - Manifold/Polymarket market anchors;
  - [2%, 98%] caps;
  - dormant workflows.
