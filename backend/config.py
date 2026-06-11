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

# Comma-separated list of origins allowed by CORS, e.g.
# "https://wc26.pages.dev,https://wc26.example.com". Defaults to the
# local Vite dev server only — deployments must set it explicitly.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
