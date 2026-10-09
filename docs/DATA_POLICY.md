# Data policy

- **Source of tournament data.** The bot obtains tournament questions and submits forecasts **only through the official Metaculus API**, with the bot's own token. It does so only for the purpose of participating in the FutureEval tournaments.
- **Nothing republished.** No Metaculus content is stored in or published from this repository: no question text, no community or aggregate forecasts, no resolutions, no scores.
- **Validation and evaluation.** These use only:
  - synthetic data (`tests/fixtures`);
  - our own public non-Metaculus sources;
  - Metaculus data that Metaculus has authorized in writing for that purpose (e.g. the Bot Benchmarking Access Tier).
- **Correction notice (2026-10-09).**
  - What happened: an earlier commit of this repository included per-question aggregates and question titles from Metaculus. They were collected during exploratory research through the website's internal endpoint, before we identified the Terms of Use restriction.
  - What we did: the files were removed from the working tree, and the local copies were quarantined.
  - What is pending: Metaculus has been asked for guidance; history cleanup is pending the owner's decision.
- **Market anchors.** Prices are read live from the public Manifold and Polymarket APIs at forecast time and used only as research context. They are not stored.
