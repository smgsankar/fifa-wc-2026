# Seed Data Files

Drop the following files in this directory, then run `python scripts/seed.py`
from the `backend/` directory. All formats are defined in `prd.md`.

## teams.csv (required)

```csv
team_id,name,country_code,logo_url
1,Argentina,ARG,https://example.com/arg.png
2,France,FRA,https://example.com/fra.png
```

## matches.csv (required)

`stage` must be one of: `group`, `round16`, `quarterfinal`, `semifinal`, `final`.

```csv
match_id,team_a_id,team_b_id,match_date,stage
1,1,2,2026-06-12T12:30:00Z,group
```

## squad_data.json (optional)

Keyed by team_id.

```json
{
  "1": [
    {"player_id": 101, "name": "Lionel Messi", "position": "F", "number": 10}
  ]
}
```

## recent_form.json (optional)

Keyed by team_id, last 5 matches. `result` must be `W`, `D`, or `L`.

```json
{
  "1": [
    {"match_date": "2026-06-08", "opponent": "Brazil", "result": "W", "score": "3-0"}
  ]
}
```

## predictions.json (required for predictions)

Keyed by match_id. All values must be floats in [0, 1].

```json
{
  "1": {"team_a_win_prob": 0.65, "team_b_win_prob": 0.25, "draw_prob": 0.10, "confidence": 0.78}
}
```

## h2h_data.json (required for h2h)

Keyed by `"<team_a_id>_<team_b_id>"`. `last_match_date` is optional.

```json
{
  "1_2": {"team_a_wins": 3, "team_b_wins": 2, "draws": 1, "last_match_date": "2024-03-15"}
}
```

## Seeding order

`scripts/seed.py` runs everything in dependency order. To run loaders
individually: teams first, then matches, then predictions and h2h. All loaders
are idempotent — re-running after fixing a file updates existing rows.
