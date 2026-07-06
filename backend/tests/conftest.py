"""Test harness: run the backend against a throwaway SQLite database.

DATABASE_URL must be set before any backend module is imported (database.py
binds its engine at import time), which is why the environment setup sits
above the imports here. config.py's load_dotenv uses override=False, so this
value wins over backend/.env.
"""

import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

_TMPDIR = tempfile.mkdtemp(prefix="wc2026-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMPDIR}/test.db"

from datetime import datetime, timedelta, timezone  # noqa: E402

import pytest  # noqa: E402

from database import Base, SessionLocal, engine  # noqa: E402
from models import HistoricalResult, Match, Team  # noqa: E402


@pytest.fixture()
def db():
    """A fresh schema + session per test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


# SQLite stores naive datetimes; the app code normalizes naive values to UTC,
# so tests use naive-UTC datetimes throughout for consistent comparisons.
def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hours_ago(hours: float) -> datetime:
    return utc_now_naive() - timedelta(hours=hours)


def hours_ahead(hours: float) -> datetime:
    return utc_now_naive() + timedelta(hours=hours)


def make_team(db, team_id: int, name: str, *, placeholder: bool = False) -> Team:
    team = Team(
        id=team_id,
        name=name,
        country_code=name[:3].upper(),
        is_placeholder=placeholder,
    )
    db.add(team)
    db.commit()
    return team


def make_match(
    db,
    match_id: int,
    team_a: Team,
    team_b: Team,
    *,
    stage: str,
    kickoff: datetime,
    score: tuple[int, int] | None = None,
    external_id: int | None = None,
) -> Match:
    match = Match(
        match_id=match_id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        match_date=kickoff,
        stage=stage,
        status="completed" if score else "pending",
        external_id=external_id,
    )
    if score:
        match.actual_score_a, match.actual_score_b = score
    db.add(match)
    db.commit()
    return match


def add_history(db, home: str, away: str, home_score: int, away_score: int, on) -> None:
    db.add(
        HistoricalResult(
            match_date=on,
            home_team=home,
            away_team=away,
            home_score=home_score,
            away_score=away_score,
            tournament="Friendly",
            neutral=False,
        )
    )
    db.commit()
