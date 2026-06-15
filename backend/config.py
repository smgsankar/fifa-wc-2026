import os

from dotenv import load_dotenv

load_dotenv()


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
