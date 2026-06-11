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
from database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="World Cup 2026 Prediction API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
# window it is "awaiting_results" until actual scores are uploaded.
LIVE_WINDOW = timedelta(minutes=100)


def effective_status(match: models.Match, now: datetime) -> str:
    """Derive the displayed status from the stored one and the clock."""
    if match.status == "completed":
        return "completed"
    kickoff = match.match_date
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    if now < kickoff:
        return "pending"
    if now < kickoff + LIVE_WINDOW:
        return "live"
    return "awaiting_results"


def upcoming_matches(db: Session, limit: int) -> list[schemas.UpcomingMatch]:
    """Next matches in kickoff order, starting with a live one if ongoing."""
    now = datetime.now(timezone.utc)
    matches = (
        match_query(db)
        .filter(models.Match.status == "pending")
        .filter(models.Match.match_date > now - LIVE_WINDOW)
        .order_by(models.Match.match_date.asc(), models.Match.match_id.asc())
        .limit(limit)
        .all()
    )
    return [
        schemas.UpcomingMatch.model_validate(m).model_copy(
            update={"status": effective_status(m, now)}
        )
        for m in matches
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
    stage: Literal["group", "round16", "quarterfinal", "semifinal", "final"] | None = Query(
        default=None
    ),
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


@app.get("/api/matches/{match_id}", response_model=schemas.MatchDetailResponse)
def get_match_detail(match_id: int, db: Session = Depends(get_db)):
    match = match_query(db).filter(models.Match.match_id == match_id).first()
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    def team_detail(team: models.Team) -> schemas.TeamDetail:
        return schemas.TeamDetail(
            id=team.id,
            name=team.name,
            country_code=team.country_code,
            logo_url=team.logo_url,
            head_coach=team.head_coach,
            squad=team.squad or [],
            recent_form=team.recent_form or [],
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
