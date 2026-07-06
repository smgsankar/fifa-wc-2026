# FIFA World Cup 2026 Predictor

A full-stack app that predicts World Cup 2026 results — the group stage up
front and each knockout round as it becomes due — and tracks how the model
performs as real results come in. The dashboard shows the next match with a
live countdown and win probabilities, the full fixture list with filters
(undecided knockout slots appear as placeholders like *Winner SF 1*),
per-match detail (head-to-head, recent form, squads), and global model
accuracy stats.

## Repository layout

| Directory | What it is | Docs |
|---|---|---|
| [`frontend/`](frontend/) | Vite + React 19 + Tailwind v4 dashboard, deployed to Cloudflare Pages | [frontend/README.md](frontend/README.md) |
| [`backend/`](backend/) | FastAPI + SQLAlchemy + PostgreSQL REST API, deployed to Railway | [backend/README.md](backend/README.md) |
| [`backend/ml/`](backend/ml/) | Logistic-regression model behind the pre-tournament group predictions and the per-round knockout retraining | [backend/mlprd.md](backend/mlprd.md) |
| [`backend/seed_data/`](backend/seed_data/) | Checked-in source data (Kaggle history, FIFA schedule, squads, predictions) | [backend/seed_data/README.md](backend/seed_data/README.md) |

Product specs live in `frontend/prd.md` and `backend/prd.md`.

## Quick start

Prerequisites: Python 3.10+, Node ≥ 20, PostgreSQL running locally.

```bash
# Backend (one-time setup)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # adjust DATABASE_URL if needed
createdb wc2026
python scripts/preseed_kaggle.py    # teams, group fixtures, history, h2h, form
python scripts/seed_squads.py       # squads + head coaches
python scripts/seed_predictions.py  # group-stage model predictions
python scripts/seed_knockouts.py    # knockout fixtures + placeholder teams
cd ..

# Frontend (one-time setup)
cd frontend
npm install
cp .env.example .env.local   # VITE_API_BASE_URL=http://localhost:8000
cd ..

# Run both dev servers (frees stale ports automatically)
make
```

Backend runs at http://localhost:8000 (API docs at `/docs`), frontend at
http://localhost:5173. `make backend` / `make frontend` run either one alone.

## During the tournament

Record final scores interactively (prediction correctness and model stats
recompute automatically afterwards):

```bash
cd backend && python scripts/record_results.py
```

It works against whatever `DATABASE_URL` points at, so the same script
records results in production.

Or automate it: with a free [football-data.org](https://www.football-data.org/)
token, the backend can poll for finished scores and record them itself — map
fixtures to the API once with `python scripts/map_external_ids.py`, then run
`python scripts/sync_results.py` (or set `RESULTS_SYNC_ENABLED=true` to have the
API poll on an interval). The same cycle also fills in knockout pairings as
they're decided and retrains the model after each completed round to predict
the next one. See
[backend/README.md](backend/README.md#automated-results-sync-football-dataorg).

## Deployment

- **Backend → Railway**: Postgres service + API service rooted at
  `backend/`; see [backend/README.md](backend/README.md#deploy-to-railway).
- **Frontend → Cloudflare Pages**: git-connected project rooted at
  `frontend/`; see
  [frontend/README.md](frontend/README.md#deploying-to-cloudflare-pages).
- The backend's `ALLOWED_ORIGINS` env var must include the deployed
  frontend origin, and the frontend's `VITE_API_BASE_URL` must point at the
  deployed backend — they reference each other.
