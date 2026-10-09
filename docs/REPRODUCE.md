# Reproduce / run locally

```bash
python -m venv .venv && .venv/Scripts/pip install "forecasting-tools>=0.2.90,<0.4.0" python-dotenv python-decouple pytest
.venv/Scripts/python -m pytest -q tests               # offline: no network, no keys, synthetic data only
.venv/Scripts/python tools/cost_model.py               # cost table
```
Running the bot itself requires the following (see `ACTIVATE.md`; do not run before the activation gate is cleared):
- `METACULUS_TOKEN` (bot account);
- `OPENROUTER_API_KEY` (paid);
- optionally `FORECAST_PROFILE` and `INCLUDE_MINIBENCH`.

Then:
```bash
python sste_bot.py --mode test_questions --dry-run
```
- **Everything that determines a forecast is in this repository:** prompts (`main.py` template + `sste_bot.py`), models and parameters (`config/models.json`), aggregation (framework median), caps, and market-anchor code.
- **Non-reproducible inputs:** live news and research results, and live market prices at forecast time.
