# Seed Data

## Kaggle dataset (checked in)

From the "International football results 1872–2025" Kaggle dataset:

- `results.csv` — all international matches. Columns:
  `date,home_team,away_team,home_score,away_score,tournament,city,country,neutral`.
  Rows with score `NA` are the upcoming World Cup 2026 group-stage fixtures
  (72 matches, 48 teams); everything else is completed history.
- `former_names.csv` — country renames (`current,former,start_date,end_date`),
  used to normalize old team names while loading history.

Preseed everything derived from this dataset:

```bash
python scripts/preseed_kaggle.py
```

This loads `historical_results`, creates the 48 teams and 72 group fixtures,
and derives `h2h` records (per fixture pair) and `teams.recent_form` (last 5
matches per team). Idempotent — safe to re-run.

## Still pending (seeded separately when the data arrives)

- **Team metadata / squads / players** — logos, squad rosters
  (file format TBD; will be provided later)
- **Predictions** — pre-computed model output per match
