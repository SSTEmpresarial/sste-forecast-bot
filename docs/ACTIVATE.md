# Activation: human-only steps. DO NOT START before the gate is cleared.

**Preconditions:**
1. **Written reply from Metaculus.** It must confirm:
   - API use for this commercial, open-source FutureEval entry;
   - prize eligibility;
   - credit status;
   - Brazil (Ramp) payout.
2. **Owner approval of the LLM budget** (`docs/COSTS.md`), unless Metaculus grants credits.

**Steps (≈ 15 minutes):**
1. A human signs up at https://www.metaculus.com, with an email a human reads.
2. Settings → My Forecasting Bots → Create a Bot → copy the bot token.
3. Fill in the required participation form (first section): https://forms.gle/aQdYMq9Pisrf1v7d8. State: commercial participant (SSTE), fully open source, the repository URL.
4. GitHub → Settings → Secrets → `METACULUS_TOKEN`, plus `OPENROUTER_API_KEY` (paid key, owner's account) unless credits were granted.
   - Variables:
     - `FORECAST_PROFILE`: `frontier_lean`, or `metaculus_credits` if credits were granted;
     - `INCLUDE_MINIBENCH`: `true` or `false`.
5. Actions → "Test Bot" → Run (bot-testing-area; this does not count in any tournament).
6. Set `BOT_ENABLED=true` and `REVIEW_BOT_ENABLED=true`.

Prizes: paid by Ramp bank transfer after the season (Brazil is listed for BRL). Identity verification and a possible code-review call are required.
