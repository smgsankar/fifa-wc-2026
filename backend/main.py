import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from config import (
    ALLOWED_ORIGINS,
    FOOTBALL_DATA_API_TOKEN,
    RESULTS_SYNC_ENABLED,
    RESULTS_SYNC_INTERVAL_SECONDS,
)
from database import Base, engine, get_db

logger = logging.getLogger("uvicorn.error")


def _run_sync_cycle() -> None:
    """Scheduler job: map new fixtures, pull finished results, resolve decided
    knockout slots, then retrain/predict any round that has become due. Errors
    are swallowed so a bad poll (rate limit, network blip) never crashes the
    worker thread."""
    from database import SessionLocal
    from results_sync import map_external_ids, resolve_knockout_teams, sync_results

    try:
        db = SessionLocal()
        try:
            unmapped = (
                db.query(models.Match).filter(models.Match.external_id.is_(None)).count()
            )
        finally:
            db.close()
        if unmapped:
            mapping = map_external_ids()
            if mapping["mapped"]:
                logger.info("Mapped %s fixture(s) to external ids", mapping["mapped"])

        summary = sync_results()
        if summary["updated"]:
            logger.info("Results sync recorded %s new result(s)", summary["updated"])

        resolved = resolve_knockout_teams()
        if resolved["resolved"]:
            logger.info("Resolved teams for %s knockout fixture(s)", resolved["resolved"])
    except Exception:  # noqa: BLE001 — keep the recurring job alive
        logger.exception("Results sync failed")

    # Independent of the poll: rounds can become due from results recorded in
    # an earlier cycle (or manually), and training needs no API access.
    try:
        from round_predictions import run_due_round_predictions

        rounds = run_due_round_predictions()
        if rounds["predicted"]:
            logger.info(
                "Generated %s prediction(s) for round(s): %s",
                rounds["predicted"], ", ".join(rounds["stages"]),
            )
    except Exception:  # noqa: BLE001
        logger.exception("Round prediction run failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    # create_all never alters existing tables; backfill columns added since
    # the database was seeded before serving any query that selects them.
    from database import SessionLocal
    from results_sync import ensure_schema

    with SessionLocal() as db:
        ensure_schema(db)

    scheduler = None
    if RESULTS_SYNC_ENABLED and FOOTBALL_DATA_API_TOKEN:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            _run_sync_cycle,
            "interval",
            seconds=RESULTS_SYNC_INTERVAL_SECONDS,
            id="results_sync",
            max_instances=1,  # never overlap runs
            coalesce=True,  # collapse missed runs into one
            next_run_time=datetime.now(timezone.utc),  # also run once at startup
        )
        scheduler.start()
        logger.info(
            "Results sync enabled: polling every %ss", RESULTS_SYNC_INTERVAL_SECONDS
        )
    elif RESULTS_SYNC_ENABLED:
        logger.warning("RESULTS_SYNC_ENABLED but no FOOTBALL_DATA_API_TOKEN; sync disabled")

    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)


app = FastAPI(title="World Cup 2026 Prediction API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first.get("loc", []))
    message = first.get("msg", "Invalid request")
    return JSONResponse(status_code=400, content={"error": f"{location}: {message}"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


def match_query(db: Session):
    return db.query(models.Match).options(
        joinedload(models.Match.team_a),
        joinedload(models.Match.team_b),
        joinedload(models.Match.prediction),
    )


# A match is considered live from kickoff until this long after; past the
# window it is "awaiting_results" until actual scores are uploaded. Knockout
# games can go to extra time and penalties (~160+ minutes of wall clock), so
# they get a wider window than group games.
GROUP_LIVE_WINDOW = timedelta(minutes=120)
KNOCKOUT_LIVE_WINDOW = timedelta(minutes=170)


def live_window_for(stage: str) -> timedelta:
    return GROUP_LIVE_WINDOW if stage == "group" else KNOCKOUT_LIVE_WINDOW

# How many of a team's most recent matches to show as "recent form".
RECENT_FORM_SIZE = 5


def effective_status(match: models.Match, now: datetime) -> str:
    """Derive the displayed status from the stored one and the clock."""
    if match.status == "completed":
        return "completed"
    kickoff = match.match_date
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    if now < kickoff:
        return "pending"
    if now < kickoff + live_window_for(match.stage):
        return "live"
    return "awaiting_results"


def upcoming_matches(db: Session, limit: int) -> list[schemas.UpcomingMatch]:
    """Next matches in kickoff order, starting with a live one if ongoing."""
    now = datetime.now(timezone.utc)
    matches = (
        match_query(db)
        .filter(models.Match.status == "pending")
        .filter(models.Match.match_date > now - KNOCKOUT_LIVE_WINDOW)
        .order_by(models.Match.match_date.asc(), models.Match.match_id.asc())
        .all()
    )
    # Kicked-off matches past their stage's live window are awaiting results,
    # not upcoming — drop them rather than showing a stale "next match".
    upcoming = [
        (m, status)
        for m in matches
        if (status := effective_status(m, now)) in ("pending", "live")
    ]
    return [
        schemas.UpcomingMatch.model_validate(m).model_copy(update={"status": status})
        for m, status in upcoming[:limit]
    ]


def get_h2h(db: Session, team_a_id: int, team_b_id: int) -> schemas.H2HOut | None:
    """Find the h2h record for a team pair, flipping wins to match the given order."""
    record = (
        db.query(models.H2H)
        .filter(
            or_(
                (models.H2H.team_a_id == team_a_id) & (models.H2H.team_b_id == team_b_id),
                (models.H2H.team_a_id == team_b_id) & (models.H2H.team_b_id == team_a_id),
            )
        )
        .first()
    )
    if record is None:
        return None
    flipped = record.team_a_id != team_a_id
    last_match = (
        schemas.LastMatch(date=record.last_match_date.date().isoformat())
        if record.last_match_date
        else None
    )
    return schemas.H2HOut(
        team_a_wins=record.team_b_wins if flipped else record.team_a_wins,
        team_b_wins=record.team_a_wins if flipped else record.team_b_wins,
        draws=record.draws,
        last_match=last_match,
    )


@app.get("/")
async def root():
    return {"name": "World Cup 2026 Prediction API", "docs": "/docs"}


@app.get("/api/matches/upcoming", response_model=schemas.UpcomingMatchesResponse)
def get_upcoming_match(db: Session = Depends(get_db)):
    matches = upcoming_matches(db, limit=1)
    return {"upcoming_matches": matches}


@app.get("/api/matches/next-4", response_model=schemas.UpcomingMatchesResponse)
def get_next_4_matches(db: Session = Depends(get_db)):
    matches = upcoming_matches(db, limit=4)
    return {"upcoming_matches": matches}


@app.get("/api/matches/all", response_model=schemas.AllMatchesResponse)
def get_all_matches(
    status: Literal["pending", "live", "awaiting_results", "completed"] | None = Query(
        default=None
    ),
    team_id: int | None = Query(default=None),
    stage: Literal[
        "group", "round32", "round16", "quarterfinal", "semifinal", "third_place", "final"
    ]
    | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = match_query(db)
    if team_id is not None:
        query = query.filter(
            or_(models.Match.team_a_id == team_id, models.Match.team_b_id == team_id)
        )
    if stage is not None:
        query = query.filter(models.Match.stage == stage)
    matches = query.order_by(
        models.Match.match_date.asc(), models.Match.match_id.asc()
    ).all()
    now = datetime.now(timezone.utc)
    items = [
        schemas.MatchListItem(
            match_id=m.match_id,
            team_a=schemas.TeamSummary.model_validate(m.team_a),
            team_b=schemas.TeamSummary.model_validate(m.team_b),
            match_date=m.match_date,
            stadium=m.stadium,
            city=m.city,
            stage=m.stage,
            status=effective_status(m, now),
            actual_score_a=m.actual_score_a,
            actual_score_b=m.actual_score_b,
            decided_by=m.decided_by,
            penalty_score_a=m.penalty_score_a,
            penalty_score_b=m.penalty_score_b,
            prediction=m.prediction,
            prediction_correct=m.prediction.is_correct if m.prediction else None,
        )
        for m in matches
    ]
    # Live and awaiting_results are derived from the clock, so filter
    # on the derived value rather than the stored column.
    if status is not None:
        items = [i for i in items if i.status == status]
    return {"all_matches": items}


def completed_wc_form(db: Session, team: models.Team, before: datetime) -> list[dict]:
    """A team's World Cup fixtures completed before a cutoff, as form entries."""
    matches = (
        db.query(models.Match)
        .options(
            joinedload(models.Match.team_a), joinedload(models.Match.team_b)
        )
        .filter(
            models.Match.status == "completed",
            models.Match.match_date < before,
            or_(
                models.Match.team_a_id == team.id,
                models.Match.team_b_id == team.id,
            ),
        )
        .all()
    )
    entries: list[dict] = []
    for m in matches:
        if m.actual_score_a is None or m.actual_score_b is None:
            continue
        is_a = m.team_a_id == team.id
        own = m.actual_score_a if is_a else m.actual_score_b
        opp = m.actual_score_b if is_a else m.actual_score_a
        opponent = m.team_b if is_a else m.team_a
        kickoff = m.match_date
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=timezone.utc)
        entries.append(
            {
                "match_date": kickoff.astimezone(timezone.utc).date().isoformat(),
                "opponent": opponent.name,
                "result": "W" if own > opp else "L" if own < opp else "D",
                "score": f"{own}-{opp}",
            }
        )
    return entries


def historical_form(db: Session, team: models.Team, before: datetime) -> list[dict]:
    """Pre-tournament form entries from historical results before a cutoff."""
    rows = (
        db.query(models.HistoricalResult)
        .filter(
            or_(
                models.HistoricalResult.home_team == team.name,
                models.HistoricalResult.away_team == team.name,
            ),
            models.HistoricalResult.match_date < before.date(),
        )
        .order_by(models.HistoricalResult.match_date.desc())
        .limit(RECENT_FORM_SIZE)
        .all()
    )
    entries: list[dict] = []
    for r in rows:
        is_home = r.home_team == team.name
        own = r.home_score if is_home else r.away_score
        opp = r.away_score if is_home else r.home_score
        entries.append(
            {
                "match_date": r.match_date.isoformat(),
                "opponent": r.away_team if is_home else r.home_team,
                "result": "W" if own > opp else "L" if own < opp else "D",
                "score": f"{own}-{opp}",
            }
        )
    return entries


def recent_form_for(db: Session, team: models.Team, as_of: datetime) -> list[dict]:
    """The last matches a team played before as_of, newest first.

    Point-in-time: a match detail page shows each team's form as it stood at
    that match's kickoff, blending completed World Cup fixtures with the
    pre-tournament historical results."""
    combined = completed_wc_form(db, team, as_of) + historical_form(db, team, as_of)
    # ISO date strings sort lexically; newer dates float up.
    combined.sort(key=lambda e: e["match_date"], reverse=True)
    return combined[:RECENT_FORM_SIZE]


@app.get("/api/matches/{match_id}", response_model=schemas.MatchDetailResponse)
def get_match_detail(match_id: int, db: Session = Depends(get_db)):
    match = match_query(db).filter(models.Match.match_id == match_id).first()
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    kickoff = match.match_date
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)

    def team_detail(team: models.Team) -> schemas.TeamDetail:
        return schemas.TeamDetail(
            id=team.id,
            name=team.name,
            country_code=team.country_code,
            logo_url=team.logo_url,
            is_placeholder=team.is_placeholder,
            head_coach=team.head_coach,
            squad=team.squad or [],
            recent_form=recent_form_for(db, team, kickoff),
        )

    detail = schemas.MatchDetail(
        match_id=match.match_id,
        team_a=team_detail(match.team_a),
        team_b=team_detail(match.team_b),
        h2h=get_h2h(db, match.team_a_id, match.team_b_id),
        match_date=match.match_date,
        stadium=match.stadium,
        city=match.city,
        stage=match.stage,
        status=effective_status(match, datetime.now(timezone.utc)),
        actual_score_a=match.actual_score_a,
        actual_score_b=match.actual_score_b,
        decided_by=match.decided_by,
        penalty_score_a=match.penalty_score_a,
        penalty_score_b=match.penalty_score_b,
        prediction=match.prediction,
        prediction_correct=match.prediction.is_correct if match.prediction else None,
    )
    return {"match": detail}


@app.get("/api/model/stats", response_model=schemas.StatsResponse)
def get_model_stats(db: Session = Depends(get_db)):
    stats = db.query(models.ModelStats).order_by(models.ModelStats.id.desc()).first()
    if stats is None:
        total = db.query(models.Prediction).count()
        return {
            "stats": schemas.StatsOut(
                total_predictions=total,
                correct_predictions=0,
                incorrect_predictions=0,
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                last_updated=datetime.now(timezone.utc),
            )
        }
    # Only scored predictions (completed matches) count as incorrect;
    # pending matches have is_correct = NULL.
    incorrect = (
        db.query(models.Prediction)
        .filter(models.Prediction.is_correct.is_(False))
        .count()
    )
    return {
        "stats": schemas.StatsOut(
            total_predictions=stats.total_predictions,
            correct_predictions=stats.correct_predictions,
            incorrect_predictions=incorrect,
            accuracy=stats.accuracy,
            precision=stats.precision,
            recall=stats.recall,
            last_updated=stats.updated_at,
        )
    }
