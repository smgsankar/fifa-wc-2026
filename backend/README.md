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

Place the data files in `seed_data/` (see `seed_data/README.md` for the
expected formats), then:

```bash
python scripts/seed.py
```

Loaders are idempotent — re-run safely after fixing a data file. Individual
loaders can also be run standalone (`python scripts/seed_teams.py`, etc.).

Once match results start coming in (scores recorded on `matches` rows with
status set to `completed`), refresh prediction correctness and model stats
with:

```bash
python scripts/recompute_stats.py
```

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

## Deploy to Railway

1. Create a Railway project.
2. Add a **PostgreSQL** service.
3. Add a service from this repo, with the root directory set to `backend/`.
   The `Procfile` provides the start command.
4. On the API service, set `DATABASE_URL` to the Postgres service reference
   (`${{Postgres.DATABASE_URL}}`). Railway sets `PORT` automatically.
5. Deploy, then generate a public domain for the API service.

Seed the production database from your machine:

```bash
DATABASE_URL="<railway-postgres-public-url>" python scripts/seed.py
# or, with the Railway CLI linked to the project:
railway run python scripts/seed.py
```
