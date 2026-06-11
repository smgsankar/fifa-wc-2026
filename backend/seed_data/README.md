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

This loads `historical_results`, creates the 48 teams and 72 group fixtures
(with flag images from [Flagpedia's CDN](https://flagpedia.net/download/api)
as `teams.logo_url`), and derives `h2h` records (per fixture pair) and
`teams.recent_form` (last 5 matches per team). Idempotent — safe to re-run.

## Squads (checked in)

- `squads.csv` — 26-player rosters for all 48 teams, extracted from the
  official FIFA squad-list PDF. Columns:
  `country_code,team,number,position,name,dob,club`.

Regenerate from the PDF (needs `pip install pdfplumber`), then seed
`teams.squad`:

```bash
python scripts/extract_squads.py ~/Downloads/SquadLists-English.pdf
python scripts/seed_squads.py
```

Idempotent — safe to re-run.

## Still pending (seeded separately when the data arrives)

- **Predictions** — pre-computed model output per match
