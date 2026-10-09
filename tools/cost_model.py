"""LLM cost model for the SSTE bot, assuming ZERO free credits (every token paid).

Prices: OpenRouter public model list (https://openrouter.ai/api/v1/models), snapshot 2026-10-09, USD per 1M
tokens (input, output) plus a per-request web-search fee where relevant. Batch prices are NOT used: tournament
questions stay open for ~1.5 h, too short for batch turnaround.

Token assumptions per call (estimated from the prompts in main.py / sste_bot.py; tune after real runs):
  research : 500 in, 1,500 out, 1 web-search request
  summarizer (report only): 1,900 in, 300 out
  forecast : 3,200 in (instructions + question + research + market context), output depends on reasoning:
             reasoning off ~800 tokens, low ~2,000, medium ~4,000 (hidden reasoning tokens are billed as output)
  parser   : 1,000 in, 60 out, per validation sample

Run: python tools/cost_model.py   (prints a markdown table)
"""
from dataclasses import dataclass, field

PRICES = {  # model: (in $/M, out $/M, web $/request)
    "anthropic/claude-opus-5.5": (4.0, 20.0, 0.01),
    "anthropic/claude-sonnet-5.5": (2.0, 10.0, 0.01),
    "anthropic/claude-haiku-5.5": (0.1, 0.5, 0.01),
    "openai/gpt-5.6-sol": (2.0, 10.0, 0.01),
    "openai/gpt-5.6-luna": (0.2, 1.2, 0.01),
    "openai/gpt-5-nano": (0.05, 0.4, 0.01),
    "google/gemini-3.6-flash": (0.75, 3.75, 0.014),
    "google/gemini-3.1-pro-preview": (2.0, 12.0, 0.014),
    "deepseek/deepseek-v4-pro": (0.955, 1.911, 0.0),
    "qwen/qwen3.7-plus": (0.32, 1.28, 0.0),
    "openai/gpt-oss-120b": (0.037, 0.17, 0.0),
    "perplexity/sonar": (1.0, 1.0, 0.005),
}
OUT_BY_REASONING = {"off": 800, "low": 2000, "medium": 4000}


def call_cost(model: str, tin: int, tout: int, web: int = 0) -> float:
    pin, pout, pweb = PRICES[model]
    return tin / 1e6 * pin + tout / 1e6 * pout + web * pweb


@dataclass
class Config:
    name: str
    forecasters: list  # one (model, reasoning) per sample
    research: str = "perplexity/sonar"
    parser: str = "openai/gpt-5-nano"
    parser_samples: int = 2  # structure_output validation samples per forecast
    summarizer: str | None = "openai/gpt-5-nano"
    note: str = ""
    per_member: list = field(default_factory=list)

    def per_question(self) -> float:
        c = call_cost(self.research, 500, 1500, web=1)
        if self.summarizer:
            c += call_cost(self.summarizer, 1900, 300)
        self.per_member = []
        for model, reasoning in self.forecasters:
            m = call_cost(model, 3200, OUT_BY_REASONING[reasoning])
            m += self.parser_samples * call_cost(self.parser, 1000, 60)
            self.per_member.append((f"{model.split('/')[1]}[{reasoning}]", m))
            c += m
        return c


CONFIGS = [
    Config("A. validated-like (6 samples, Opus/Sonnet alternating, medium reasoning)",
           [("anthropic/claude-opus-5.5", "medium"), ("anthropic/claude-sonnet-5.5", "medium")] * 3,
           note="closest to the models used in the withdrawn retro test"),
    Config("B. frontier-lean (3 samples: Sonnet, GPT-5.6-sol, Gemini-3.1-pro; low reasoning)",
           [("anthropic/claude-sonnet-5.5", "low"), ("openai/gpt-5.6-sol", "low"), ("google/gemini-3.1-pro-preview", "low")],
           parser_samples=1, summarizer=None, note="cross-lab diversity, half the samples"),
    Config("C. LOW-COST (3 samples: Sonnet low + Gemini-3.6-flash + DeepSeek-v4-pro)",
           [("anthropic/claude-sonnet-5.5", "low"), ("google/gemini-3.6-flash", "low"), ("deepseek/deepseek-v4-pro", "low")],
           parser_samples=1, summarizer=None, note="one frontier anchor + two strong cheap models"),
    Config("D. budget (3 samples: GPT-5.6-luna, Qwen3.7-plus, DeepSeek-v4-pro)",
           [("openai/gpt-5.6-luna", "low"), ("qwen/qwen3.7-plus", "low"), ("deepseek/deepseek-v4-pro", "low")],
           parser_samples=1, summarizer=None, note="no frontier model; quality unvalidated"),
    Config("E. floor (3 samples gpt-oss-120b)",
           [("openai/gpt-oss-120b", "low")] * 3, research="perplexity/sonar",
           parser_samples=1, summarizer=None, note="reference floor; expect clearly worse forecasts"),
]

if __name__ == "__main__":
    print("| config | $/forecast (median member) | $/question | 300 q | 500 q | MiniBench ~420 q | 500 + MiniBench |")
    print("|---|---|---|---|---|---|---|")
    for cfg in CONFIGS:
        q = cfg.per_question()
        members = sorted(m for _, m in cfg.per_member)
        med = members[len(members) // 2]
        print(f"| {cfg.name} | ${med:.4f} | ${q:.3f} | ${300*q:.0f} | ${500*q:.0f} | ${420*q:.0f} | ${920*q:.0f} |")
    print("\nPer-member marginal cost per question (forecast + parser):")
    for cfg in CONFIGS:
        cfg.per_question()
        print(f"- {cfg.name.split(' (')[0]}: " + ", ".join(f"{n} ${c:.4f}" for n, c in cfg.per_member[:3]))
