"""Offline tests for the SSTE additions (no network, no LLM, no Metaculus token needed)."""
import asyncio
import os

os.environ.setdefault("METACULUS_TOKEN", "test")

import sste_bot
from forecasting_tools import ReasonedPrediction


def test_market_context_never_raises(monkeypatch):
    def boom(url):
        raise OSError("network down")
    monkeypatch.setattr(sste_bot, "_get_json", boom)
    assert sste_bot.market_context("anything") == ""


def test_market_context_formats_both_sources(monkeypatch):
    def fake(url):
        if "manifold" in url:
            return [{"outcomeType": "BINARY", "probability": 0.42, "question": "Q1", "uniqueBettorCount": 9},
                    {"outcomeType": "MULTIPLE_CHOICE", "question": "skip me"}]
        return {"events": [{"markets": [{"question": "Q2", "outcomePrices": "[\"0.7\", \"0.3\"]", "volume": "1234.5"}]}]}
    monkeypatch.setattr(sste_bot, "_get_json", fake)
    out = sste_bot.market_context("q")
    assert "Manifold: \"Q1\" → 42%" in out
    assert "Polymarket: \"Q2\" → Yes 70%" in out
    assert "skip me" not in out
    assert "DIFFERENT event" in out  # mismatch warning is always present


def _bot():
    return sste_bot.SSTEForecastBot(research_reports_per_question=1, predictions_per_research_report=2,
                                    publish_reports_to_metaculus=False, forecast_models=["m/a", "m/b"])


def test_binary_is_capped_and_prompts_alternate(monkeypatch):
    bot = _bot()
    calls = []

    async def fake_with_model(question, prompt, n, research=None):
        calls.append("reasons-first" if prompt else "template")
        return ReasonedPrediction(prediction_value=0.999 if n % 2 else 0.0001, reasoning="r")

    monkeypatch.setattr(bot, "_binary_with_model", fake_with_model)

    class Q:  # minimal stand-in; only used for prompt formatting
        question_text = background_info = resolution_criteria = fine_print = "x"
        conditional_type = None

    vals = [asyncio.run(bot._run_forecast_on_binary(Q(), "research")).prediction_value for _ in range(4)]
    assert all(sste_bot.P_MIN <= v <= sste_bot.P_MAX for v in vals)
    assert sste_bot.P_MAX in vals and sste_bot.P_MIN in vals
    assert set(calls) == {"reasons-first", "template"}


def test_model_rotation_restores_default():
    bot = _bot()
    original = bot._llms["default"]

    async def run():
        async def fake_prompt_to_forecast(question, prompt):
            return ReasonedPrediction(prediction_value=bot.get_llm("default", "llm").model == "m/b" and 0.5 or 0.4, reasoning="")
        bot._binary_prompt_to_forecast = fake_prompt_to_forecast
        return await bot._binary_with_model(object(), "prompt", 2)

    pred = asyncio.run(run())
    assert pred.prediction_value == 0.5  # n=2 → (2 // 2) % 2 == 1 → "m/b"
    assert bot._llms["default"] is original


def test_committed_profiles_load_and_translate():
    import json
    cfg = json.load(open(sste_bot.CONFIG_PATH, encoding="utf-8"))
    assert cfg["default_profile"] in cfg["profiles"]
    for name in cfg["profiles"]:
        p = sste_bot.load_profile(name)
        kw = sste_bot.bot_kwargs_from_profile(p)
        assert kw["predictions_per_research_report"] >= 1
        assert kw["enable_summarize_research"] == (p["summarizer"] is not None)
        bot = sste_bot.SSTEForecastBot(research_reports_per_question=1, publish_reports_to_metaculus=False, **kw)
        assert len(bot._forecast_llms) == len(p["forecasters"])


def test_unknown_profile_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        sste_bot.load_profile("does-not-exist")
