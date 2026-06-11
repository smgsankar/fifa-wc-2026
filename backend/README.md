# World Cup 2026 Prediction API

REST API serving World Cup 2026 match data, pre-computed predictions, team
data, and model performance stats. Built with FastAPI, SQLAlchemy, and
PostgreSQL. See `prd.md` for the full product spec.

## Requirements

- Python 3.10+
- PostgreSQL (local for development, Railway in production)

## Run locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit DATABASE_URL to point at your Postgres
createdb wc2026        # or create the database any way you like

uvicorn main:app --reload
```

Tables are created automatically on startup. Interactive API docs at
http://localhost:8000/docs.

## Seed the database

The data files are checked in under `seed_data/` (see `seed_data/README.md`
for sources and formats). Run the loaders in order, from the `backend/`
directory:

```bash
python scripts/preseed_kaggle.py    # history, teams, fixtures, h2h, recent form
python scripts/seed_squads.py       # squads + head coaches
python scripts/seed_predictions.py  # model predictions for all 72 fixtures
```

All loaders are idempotent — re-run safely after fixing a data file.

Two supporting scripts regenerate the seed files themselves (not needed
unless the source data changes):

- `scripts/extract_squads.py <pdf>` — extracts `squads.csv` / `coaches.csv`
  from the official FIFA squad-list PDF (needs `pip install pdfplumber`).
- `ml/train_predict.py` — trains the prediction model and writes
  `seed_data/predictions.json` (needs `pip install -r ml/requirements.txt`).
  See `mlprd.md` for the model spec.

## Record results during the tournament

```bash
python scripts/record_results.py
```

Interactively lists matches that have kicked off but have no result yet,
prompts for final scores, and marks them completed. Prediction correctness
and global model stats are recomputed automatically at the end of the
session. It works against whatever `DATABASE_URL` points at, so the same
script records results in production.

To recompute stats without recording anything (e.g. after editing scores
directly in the database), run `python scripts/recompute_stats.py`.

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/matches/upcoming` | Next upcoming match with prediction |
| GET | `/api/matches/next-4` | Next 4 upcoming matches |
| GET | `/api/matches/all` | All matches; filters: `status`, `team_id`, `stage` |
| GET | `/api/matches/{match_id}` | Match detail: squads, recent form, h2h, prediction |
| GET | `/api/model/stats` | Global model accuracy / precision / recall |

Query params for `/api/matches/all`:

- `status`: `pending` | `completed` | `live`
- `team_id`: integer, matches where the team plays on either side
- `stage`: `group` | `round16` | `quarterfinal` | `semifinal` | `final`

Errors are returned as `{"error": "message"}` with 404 (missing match),
400 (bad request), or 500 (server error).

Full request/response shapes are documented in `prd.md` and live at `/docs`.

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/wc2026` |
| `PORT` | Server port | `8000` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins, no trailing slashes (e.g. `https://wc26.pages.dev`) | `http://localhost:5173` |

## Deploy to Railway

1. Create a Railway project.
2. Add a **PostgreSQL** service.
3. Add a service from this repo, with the root directory set to `backend/`.
   The `Procfile` provides the start command.
4. On the API service, set `DATABASE_URL` to the Postgres service reference
   (`${{Postgres.DATABASE_URL}}`) and `ALLOWED_ORIGINS` to the deployed
   frontend origin(s). Railway sets `PORT` automatically.
5. Deploy, then generate a public domain for the API service.

Seed the production database from your machine by pointing the loaders at
the Railway Postgres:

```bash
DATABASE_URL="<railway-postgres-public-url>" python scripts/preseed_kaggle.py
DATABASE_URL="<railway-postgres-public-url>" python scripts/seed_squads.py
DATABASE_URL="<railway-postgres-public-url>" python scripts/seed_predictions.py
# or, with the Railway CLI linked to the project:
railway run python scripts/preseed_kaggle.py   # etc.
```
