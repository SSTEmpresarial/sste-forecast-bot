# Costs: base case with ZERO free LLM credits

Commercial bots are not eligible for Metaculus LLM credits by default. Every token is paid. The figures come from:
- `tools/cost_model.py`;
- OpenRouter public prices (snapshot 2026-10-09; batch pricing excluded because questions are open only ~1.5 h);
- the per-call token assumptions documented in that file.

Other fixed costs:
- **Research:** one Perplexity Sonar call per question, about $0.007 including the web-search fee.
- **GitHub Actions:** free for public repositories.
- **Market anchors:** free.

| config | $/forecast (median member) | $/question | 300 q | 500 q | MiniBench ~420 q | 500 + MiniBench |
|---|---|---|---|---|---|---|
| A. validated-like (6 samples, Opus/Sonnet alternating, medium reasoning) | $0.0929 | $0.426 | $128 | $213 | $179 | $392 |
| B. frontier-lean (3 samples: Sonnet, GPT-5.6-sol, Gemini-3.1-pro; low reasoning) | $0.0265 | $0.090 | $27 | $45 | $38 | $83 |
| C. LOW-COST (3 samples: Sonnet low + Gemini-3.6-flash + DeepSeek-v4-pro) | $0.0100 | $0.050 | $15 | $25 | $21 | $46 |
| D. budget (3 samples: GPT-5.6-luna, Qwen3.7-plus, DeepSeek-v4-pro) | $0.0037 | $0.021 | $6 | $10 | $9 | $19 |
| E. floor (3 samples gpt-oss-120b) | $0.0005 | $0.009 | $3 | $4 | $4 | $8 |

Per-member marginal cost per question (forecast + parser):
- A. validated-like: claude-opus-5.5[medium] $0.0929, claude-sonnet-5.5[medium] $0.0465, claude-opus-5.5[medium] $0.0929
- B. frontier-lean: claude-sonnet-5.5[low] $0.0265, gpt-5.6-sol[low] $0.0265, gemini-3.1-pro-preview[low] $0.0305
- C. LOW-COST: claude-sonnet-5.5[low] $0.0265, gemini-3.6-flash[low] $0.0100, deepseek-v4-pro[low] $0.0070
- D. budget: gpt-5.6-luna[low] $0.0031, qwen3.7-plus[low] $0.0037, deepseek-v4-pro[low] $0.0070
- E. floor: gpt-oss-120b[low] $0.0005, gpt-oss-120b[low] $0.0005, gpt-oss-120b[low] $0.0005

## Which ensemble members are worth their cost
- **No member-level evidence.** We have no authorized evaluation data, so member-level cost/benefit cannot be measured yet. The withdrawn retro test is not used.
- **Variance model instead.** The decision below rests on a standard variance argument for averaging forecasts: with k samples whose errors have pairwise correlation ρ, the idiosyncratic error variance shrinks by a factor of ρ + (1−ρ)/k.
- **Assumed correlations (not measured):**
  - same-lab samples: ρ ≈ 0.7;
  - cross-lab: ρ ≈ 0.5.

| ensemble | k | ρ (assumed) | noise factor | $/question |
|---|---|---|---|---|
| 1 frontier model | 1 | — | 1.00 | ≈ $0.03 |
| A. Opus/Sonnet alternating | 6 | 0.7 | 0.75 | $0.43 |
| B. Sonnet + GPT-5.6-sol + Gemini-3.1-pro | 3 | 0.5 | 0.67 | $0.09 |
| C. Sonnet + Gemini-3.6-flash + DeepSeek-v4-pro | 3 | 0.5 | 0.67 (members individually weaker) | $0.05 |

- **Reading:** under these assumptions, three diverse frontier models (B) reduce noise at least as much as six samples from one lab (A), at about 1/5 of the cost. C saves another ~45% but replaces two frontier members with cheaper models whose forecasting quality is unvalidated.
- **Default profile:** `frontier_lean` (B).
- **Cost levers, cheapest first:**
  1. Disable the research summarizer (report-only).
  2. Use 1 parser validation sample instead of 2.
  3. Use low instead of medium reasoning.
  4. Set `INCLUDE_MINIBENCH=false`, which removes ~45% of the volume.
  5. Downgrade members (C → D), which risks quality.

## Season budget (profile B)
| scope | questions | cost |
|---|---|---|
| seasonal only | 300–500 | ≈ $27–45 |
| seasonal + MiniBench | 720–920 | ≈ $65–83 |

Plus about 10% retries and overhead. **All of these exceed the experiment's US$5 budget and need explicit owner approval.**

**Note on question types.** Only binary samples rotate across the profile's models. Numeric, multiple-choice and date questions use the first forecaster for every sample. With `frontier_lean` that is Sonnet × 3, about \$0.09 per question, the same as the table.
