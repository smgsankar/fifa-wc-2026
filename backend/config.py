import os
from pathlib import Path

from dotenv import load_dotenv

# One config path that serves both environments:
#   - Locally, values come from backend/.env (loaded by explicit path so scripts
#     pick them up regardless of which directory they're invoked from).
#   - On Railway (or any host), service variables / secrets are injected straight
#     into the process environment; there is no .env file in the deploy, so the
#     load below is a harmless no-op and os.getenv reads the injected values.
# override=False means an already-present process-environment variable (i.e. a
# Railway secret) always wins over a .env value, so the same code works in both
# places without branching on the environment.
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


def _normalize_db_url(url: str) -> str:
    # Railway/Heroku style URLs use the deprecated postgres:// scheme
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _normalize_db_url(
    os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/wc2026")
)
PORT = int(os.getenv("PORT", "8000"))


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Automated results sync (football-data.org). The sync only runs when
# RESULTS_SYNC_ENABLED is truthy and a token is set, so it stays off in
# local dev unless explicitly turned on. Free token:
# https://www.football-data.org/client/register
FOOTBALL_DATA_API_TOKEN = os.getenv("FOOTBALL_DATA_API_TOKEN", "").strip()
FOOTBALL_DATA_COMPETITION = os.getenv("FOOTBALL_DATA_COMPETITION", "WC").strip()
RESULTS_SYNC_ENABLED = _as_bool(os.getenv("RESULTS_SYNC_ENABLED", "false"))
RESULTS_SYNC_INTERVAL_SECONDS = int(os.getenv("RESULTS_SYNC_INTERVAL_SECONDS", "600"))

# Comma-separated list of origins allowed by CORS, e.g.
# "https://wc26.pages.dev,https://wc26.example.com". Defaults to the
# local Vite dev server only — deployments must set it explicitly.
# Browsers send Origin without a trailing slash, so strip any.
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip("/ ")
]
