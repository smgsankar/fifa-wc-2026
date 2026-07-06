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

## Run the tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

The suite runs against a throwaway SQLite database and covers the
tournament-critical unattended paths: round-prediction triggers and
point-in-time cutoffs, placeholder-slot resolution, score/penalty
orientation, stage+kickoff fixture mapping, live-status windows, and h2h
derivation.

## Seed the database

The data files are checked in under `seed_data/` (see `seed_data/README.md`
for sources and formats). Run the loaders in order, from the `backend/`
directory:

```bash
python scripts/preseed_kaggle.py    # history, teams, group fixtures, h2h, recent form
python scripts/seed_squads.py       # squads + head coaches
python scripts/seed_predictions.py  # model predictions for the 72 group fixtures
python scripts/seed_knockouts.py    # knockout fixtures 73-104 + placeholder teams
```

All loaders are idempotent — re-run safely after fixing a data file.

The knockout seed creates the 32 knockout fixtures from
`seed_data/knockout_schedule.csv`. Slots whose teams aren't decided yet
(e.g. the final) reference placeholder team rows (`is_placeholder=true`,
shown as e.g. *WSF1 — Winner SF 1*); the results sync swaps in the real
teams as each feeding round finishes. Knockout predictions are not seeded
from a file — they're generated round by round (see below).

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

### Automated results sync (football-data.org)

Instead of recording by hand, the backend can pull finished scores from
[football-data.org](https://www.football-data.org/). Get a free API token and
add it to `backend/.env` as `FOOTBALL_DATA_API_TOKEN=<token>` — config loads
that file regardless of where you invoke the scripts from, so both steps below
pick the token up automatically. (You can still override it inline per command,
e.g. `FOOTBALL_DATA_API_TOKEN=<token> python scripts/...`.) Then run it in two
steps.

**1. Map fixtures to football-data.org ids (once):**

```bash
python scripts/map_external_ids.py
```

This pulls the competition's full fixture list, reconciles each match to ours
by team identity (with an alias map for naming differences like *Korea
Republic* → *South Korea*, plus accent-folding), and stores the API's match id
in `Match.external_id`. Knockout fixtures still holding placeholder teams are
reconciled by stage + kickoff instead. Fixtures it can't match are logged as
warnings. The scheduler also re-runs the mapping automatically whenever
unmapped fixtures exist (e.g. right after seeding the knockout rounds).

**2. Poll the fixtures awaiting a result (repeatedly):**

```bash
python scripts/sync_results.py
```

or let the API poll on a schedule. When `RESULTS_SYNC_ENABLED=true` and a
token is set, the FastAPI app starts an in-process APScheduler job that runs
a full cycle every `RESULTS_SYNC_INTERVAL_SECONDS` (default 600, i.e. every
10 minutes):

1. **Map** any fixtures without an `external_id` (no-op otherwise).
2. **Sync results**: collect the `external_id`s of fixtures that have kicked
   off but have no result yet, ask the API for just those matches by id,
   write the full-time score for any that have `FINISHED` (plus how it was
   decided and the shootout score for knockouts), refresh the pair's
   head-to-head record, and recompute model stats.
3. **Resolve knockout slots**: fixtures still holding placeholder teams are
   checked by id; once the API reports the decided teams, the placeholders
   are replaced and an h2h record is derived for the new pairing.
4. **Round predictions**: once every match of a round is completed and the
   next round's teams are all decided, the model is retrained on all
   completed internationals *plus the World Cup matches played so far* and
   the next round's predictions are written (see below).

Polling by id means it only ever queries the handful of matches in flight, and
team-name reconciliation happens once (at mapping time) rather than every poll.
`scripts/sync_results.py` runs the same cycle (minus the mapping) once.

The sync is idempotent — once a fixture is recorded it drops out of the
awaiting set — and it works alongside the manual script (both share the same
writer). Kicked-off fixtures with no `external_id` are logged as warnings
(run the mapping step to fix). Final scores only: the free tier has no live data.

> The mapping and sync steps add columns introduced after a database was
> seeded (`external_id`, `decided_by`, penalty scores) automatically — the app
> otherwise only creates missing tables, never alters them — so no manual
> migration is needed. After upgrading to WC-inclusive head-to-head records,
> run `python scripts/refresh_h2h.py` once to fold already-recorded results
> into existing h2h rows.

Notes:

- The scheduler runs in-process, so it only polls while a worker is up. On a
  multi-instance deployment every instance would poll; that's harmless
  (writes are idempotent) but wasteful — run a single instance, or move the
  sync to a dedicated cron/worker calling `scripts/sync_results.py`.
- Results are recorded after a match finishes (not live); the free tier
  doesn't provide in-play scores. A 10-minute poll picks them up promptly
  and stays well within the free tier's 10 requests/min.

### Round-by-round knockout predictions

Group-stage predictions were computed once before the tournament
(`ml/train_predict.py` → `seed_predictions.py`). Knockout predictions are
generated per round by `round_predictions.py`: a round becomes *due* when
every match of the previous round is completed, all of its own teams are
decided, and at least one of its fixtures has no prediction yet. The model
(same features and algorithm as the pre-tournament one) is then retrained on
completed matches — Kaggle history plus World Cup 2026 results — and each
fixture of the round gets a prediction.

Training and team rolling stats only use matches completed strictly before
`min(now, the round's first kickoff)`, so backfilling a round that already
kicked off produces the predictions the model would have made at the time;
completed fixtures are then scored into the model stats like any other.

The scheduler runs this automatically after each sync cycle. Manual run:

```bash
python round_predictions.py
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
- `stage`: `group` | `round32` | `round16` | `quarterfinal` | `semifinal` |
  `third_place` | `final`

Errors are returned as `{"error": "message"}` with 404 (missing match),
400 (bad request), or 500 (server error).

Full request/response shapes are documented in `prd.md` and live at `/docs`.

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/wc2026` |
| `PORT` | Server port | `8000` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins, no trailing slashes (e.g. `https://wc26.pages.dev`) | `http://localhost:5173` |
| `FOOTBALL_DATA_API_TOKEN` | Token for the football-data.org results sync (blank disables it) | _(empty)_ |
| `FOOTBALL_DATA_COMPETITION` | Competition code to poll | `WC` |
| `RESULTS_SYNC_ENABLED` | Start the in-process results-sync scheduler | `false` |
| `RESULTS_SYNC_INTERVAL_SECONDS` | Seconds between automated polls | `600` |

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
DATABASE_URL="<railway-postgres-public-url>" python scripts/seed_knockouts.py
# or, with the Railway CLI linked to the project:
railway run python scripts/preseed_kaggle.py   # etc.
```
