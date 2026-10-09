"""SSTE forecasting bot: the Metaculus Fall 2026 template plus the changes validated in our held-out test.

Changes vs the template (see README "What we changed and why"):
  1. Prompt ensemble: binary samples alternate between the template's status-quo prompt and a
     reasons-for/against-first prompt (the v2 held-out ensemble). No fixed base-rate anchor.
  2. Model ensemble: the committed profile in config/models.json (FORECAST_PROFILE selects one) lists the
     forecasting models that rotate across samples; the framework aggregates the samples by median.
  3. Market anchors: public Manifold and Polymarket prices for similar markets are appended to the
     research (allowed by the rules: "publicly available forecasts on other platforms").
  4. QA: binary probabilities are capped to [P_MIN, P_MAX] (log scoring punishes overconfidence hardest).

Run: python sste_bot.py --mode tournament|test_questions|metaculus_cup [--dry-run]
"""
import argparse
import asyncio
import json
import logging
import os
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Literal

from main import FallTemplateBot2026  # the official template (kept unchanged for easy upstream merges)
from bot_helpers import check_environment, print_run_summary_banner, print_startup_banner
from forecasting_tools import (
    BinaryQuestion,
    GeneralLlm,
    MetaculusClient,
    MetaculusQuestion,
    ReasonedPrediction,
    clean_indents,
)

logger = logging.getLogger(__name__)

P_MIN, P_MAX = 0.02, 0.98
MARKET_TIMEOUT_S = 8


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "sste-forecast-bot/1.0"})
    with urllib.request.urlopen(req, timeout=MARKET_TIMEOUT_S) as r:
        return json.loads(r.read().decode("utf-8"))


def market_context(query: str, limit: int = 4) -> str:
    """Probabilities from public prediction markets with similar titles. Never raises."""
    q = urllib.parse.quote(query[:120])
    lines = []
    try:
        for m in _get_json(f"https://api.manifold.markets/v0/search-markets?term={q}&limit={limit}&filter=open"):
            if m.get("outcomeType") == "BINARY" and m.get("probability") is not None:
                lines.append(f"- Manifold: \"{m.get('question')}\" → {m['probability']:.0%} ({m.get('uniqueBettorCount', '?')} traders)")
    except Exception as e:  # network or schema problems must never break a forecast
        logger.info(f"manifold lookup failed: {e}")
    try:
        data = _get_json(f"https://gamma-api.polymarket.com/public-search?q={q}&limit_per_type={limit}")
        for ev in (data.get("events") or [])[:limit]:
            for mk in (ev.get("markets") or [])[:2]:
                prices = mk.get("outcomePrices")
                prices = json.loads(prices) if isinstance(prices, str) else prices
                if prices:
                    lines.append(f"- Polymarket: \"{mk.get('question')}\" → Yes {float(prices[0]):.0%} (volume ${float(mk.get('volume') or 0):,.0f})")
    except Exception as e:
        logger.info(f"polymarket lookup failed: {e}")
    if not lines:
        return ""
    return (
        "Prediction markets with similar titles (they may describe a DIFFERENT event, deadline or threshold; "
        "use a price only if it matches this question's resolution criteria):\n" + "\n".join(lines)
    )


class SSTEForecastBot(FallTemplateBot2026):
    _sample_counter = 0

    def __init__(self, *args, forecast_models: list[str] | None = None, reasoning_effort: str | None = None,
                 parser_validation_samples: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        extra = {"reasoning_effort": reasoning_effort} if reasoning_effort else {}
        self._forecast_llms = [GeneralLlm(model=m, temperature=0.4, timeout=120, allowed_tries=2, **extra)
                               for m in (forecast_models or [])]
        if parser_validation_samples:
            self._structure_output_validation_samples = parser_validation_samples
        self._default_llm = self._llms["default"]  # restored after every per-sample swap

    async def run_research(self, question: MetaculusQuestion) -> str:
        research = await super().run_research(question)
        markets = await asyncio.to_thread(market_context, question.question_text)
        return f"{research}\n\n{markets}".strip()

    def _next_sample(self) -> int:
        SSTEForecastBot._sample_counter += 1
        return SSTEForecastBot._sample_counter

    async def _run_forecast_on_binary(self, question: BinaryQuestion, research: str) -> ReasonedPrediction[float]:
        n = self._next_sample()
        if n % 2 == 0:
            prompt = clean_indents(
                f"""
                You are a superforecaster. Question:
                {question.question_text}

                Background:
                {question.background_info}

                Resolution criteria (not yet satisfied):
                {question.resolution_criteria}

                {question.fine_print}

                Research and market context:
                {research}

                Today is {datetime.now().strftime("%Y-%m-%d")}.

                Work in this order:
                1. The strongest reasons this resolves YES.
                2. The strongest reasons this resolves NO.
                3. What exactly the criteria and fine print require, and how much time remains.
                4. If a prediction market above clearly matches this exact question, treat its price as a strong prior.
                {self._get_conditional_disclaimer_if_necessary(question)}
                The last thing you write is your final answer as: "Probability: ZZ%", 0-100
                """
            )
            pred = await self._binary_with_model(question, prompt, n)
        else:
            pred = await self._binary_with_model(question, None, n, research=research)
        value = min(P_MAX, max(P_MIN, pred.prediction_value))
        return ReasonedPrediction(prediction_value=value, reasoning=pred.reasoning)

    async def _binary_with_model(self, question, prompt, n, research=None):
        """Use a rotating model from FORECAST_MODELS if configured, else the template default.

        The swap is safe per sample because the framework reads get_llm("default") synchronously,
        before its first await. The model index uses n // 2 so that model and prompt style are not
        confounded (n % 2 picks the prompt).
        """
        if self._forecast_llms:
            self._llms["default"] = self._forecast_llms[(n // 2) % len(self._forecast_llms)]
        try:
            if prompt is None:
                return await super()._run_forecast_on_binary(question, research)
            return await self._binary_prompt_to_forecast(question, prompt)
        finally:
            self._llms["default"] = self._default_llm


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "models.json")


def load_profile(name: str | None = None) -> dict:
    """Read the committed model profile (config/models.json). FORECAST_PROFILE selects one."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    name = name or os.getenv("FORECAST_PROFILE") or cfg["default_profile"]
    if name not in cfg["profiles"]:
        raise ValueError(f"Unknown FORECAST_PROFILE '{name}'. Choose one of {sorted(cfg['profiles'])}")
    return {"name": name, **cfg["profiles"][name]}


def bot_kwargs_from_profile(profile: dict) -> dict:
    """Translate a profile into SSTEForecastBot keyword arguments (no network, no keys needed)."""
    llms = {}
    if profile.get("forecasters"):
        # Non-binary questions use "default" for every sample (only binary samples rotate across forecasters).
        extra = {"reasoning_effort": profile["reasoning_effort"]} if profile.get("reasoning_effort") else {}
        llms["default"] = GeneralLlm(model=profile["forecasters"][0], temperature=0.4, timeout=120, allowed_tries=2, **extra)
    if profile.get("researcher"):
        llms["researcher"] = GeneralLlm(model=profile["researcher"], temperature=0, timeout=120, allowed_tries=2)
    if profile.get("parser"):
        llms["parser"] = profile["parser"]
    summarizer = profile.get("summarizer")
    if summarizer and summarizer != "default":
        llms["summarizer"] = summarizer
    return {
        "predictions_per_research_report": profile["samples_per_question"],
        "enable_summarize_research": summarizer is not None,
        "llms": llms or None,
        "forecast_models": profile.get("forecasters") or [],
        "reasoning_effort": profile.get("reasoning_effort"),
        "parser_validation_samples": profile.get("parser_validation_samples"),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="SSTE forecasting bot")
    parser.add_argument("--mode", choices=["tournament", "metaculus_cup", "test_questions"], default="tournament")
    parser.add_argument("--dry-run", action="store_true", help="forecast but do not publish")
    args = parser.parse_args()
    mode: Literal["tournament", "metaculus_cup", "test_questions"] = args.mode

    check_environment(strict=True)
    publish = not args.dry_run
    print_startup_banner(mode, will_publish=publish)
    profile = load_profile()
    logger.info(f"Model profile: {profile['name']} (~${profile.get('_cost_per_question_usd')}/question)")
    bot = SSTEForecastBot(
        research_reports_per_question=1,
        use_research_summary_to_forecast=False,
        publish_reports_to_metaculus=publish,
        folder_to_save_reports_to="reports" if os.getenv("SAVE_REPORTS") else None,
        skip_previously_forecasted_questions=True,
        extra_metadata_in_explanation=True,
        **bot_kwargs_from_profile(profile),
    )
    client = MetaculusClient()
    if mode == "tournament":
        reports = asyncio.run(bot.forecast_on_tournament(client.CURRENT_AI_COMPETITION_ID, return_exceptions=True))
        # MiniBench roughly doubles LLM cost; an unset repo variable arrives as "" and means the default (true)
        if (os.getenv("INCLUDE_MINIBENCH") or "true").strip().lower() == "true":
            reports += asyncio.run(bot.forecast_on_tournament(client.CURRENT_MINIBENCH_ID, return_exceptions=True))
    elif mode == "metaculus_cup":
        bot.skip_previously_forecasted_questions = False
        reports = asyncio.run(bot.forecast_on_tournament(client.CURRENT_METACULUS_CUP_ID, return_exceptions=True))
    else:
        bot.skip_previously_forecasted_questions = False
        reports = asyncio.run(bot.forecast_on_tournament("bot-testing-area", return_exceptions=True))
    bot.log_report_summary(reports)
    print_run_summary_banner(reports, will_publish=publish, tournament_url=None)
