"""Per-round model retraining and prediction for the knockout stage.

Once every match of a round is completed, the next round's participants are
known (resolve_knockout_teams) and its predictions are generated here: the
model is retrained on all completed internationals PLUS the World Cup 2026
matches played so far, and each fixture of the round gets a prediction.

Point-in-time guarantee: training and team rolling stats only use matches
completed strictly BEFORE the round's first kickoff (or before now, whichever
is earlier). Backfilling a round that already kicked off therefore produces
the same predictions the model would have made at the time — completed rounds
are then scored by recompute_stats exactly like the group stage.

Reuses the feature engineering and training routine from ml/train_predict.py;
only the data source differs (database instead of the seed CSVs).

Runs inside the scheduler cycle (see main.py); manual run from the backend
directory: python round_predictions.py
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sqlalchemy.orm import joinedload

from database import SessionLocal
from ml.train_predict import (
    AWAY_WIN,
    HOME_WIN,
    MIN_PRIOR_MATCHES,
    build_training_set,
    match_features,
    rolling_stats,
    train,
)
from models import HistoricalResult, Match, Prediction

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from recompute_stats import recompute_stats  # noqa: E402

logger = logging.getLogger("round_predictions")

# Which round must be fully completed before a round's predictions are made.
PREVIOUS_STAGE = {
    "round32": "group",
    "round16": "round32",
    "quarterfinal": "round16",
    "semifinal": "quarterfinal",
    "third_place": "semifinal",
    "final": "semifinal",
}
# Chronological order in which rounds become due.
KNOCKOUT_STAGES = ("round32", "round16", "quarterfinal", "semifinal", "third_place", "final")

# Venue city -> host nation, for the home-advantage feature. Everything not
# listed is a United States venue.
MEXICO_CITIES = {"Mexico City", "Zapopan", "Guadalupe, Nuevo León"}
CANADA_CITIES = {"Toronto", "Vancouver"}


def _host_nation(city: str | None) -> str:
    if city in MEXICO_CITIES:
        return "Mexico"
    if city in CANADA_CITIES:
        return "Canada"
    return "United States"


def _is_home_fixture(match: Match) -> bool:
    """True when team_a is the host nation playing in its own country."""
    return match.team_a.name == _host_nation(match.city)


def _kickoff_utc(match: Match) -> datetime:
    kickoff = match.match_date
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    return kickoff.astimezone(timezone.utc)


def _load_history(db, cutoff: datetime) -> list[dict]:
    """Completed matches before the cutoff: Kaggle history + WC2026 results."""
    history = [
        {
            "date": r.match_date,
            "home_team": r.home_team,
            "away_team": r.away_team,
            "home_score": r.home_score,
            "away_score": r.away_score,
            "neutral": r.neutral,
        }
        for r in db.query(HistoricalResult)
        .filter(HistoricalResult.match_date < cutoff.date())
        .order_by(HistoricalResult.match_date.asc())
        .all()
    ]
    wc_matches = (
        db.query(Match)
        .options(joinedload(Match.team_a), joinedload(Match.team_b))
        .filter(
            Match.status == "completed",
            Match.actual_score_a.isnot(None),
            Match.actual_score_b.isnot(None),
        )
        .order_by(Match.match_date.asc(), Match.match_id.asc())
        .all()
    )
    for m in wc_matches:
        if _kickoff_utc(m) >= cutoff:
            continue
        history.append(
            {
                "date": _kickoff_utc(m).date(),
                "home_team": m.team_a.name,
                "away_team": m.team_b.name,
                "home_score": m.actual_score_a,
                "away_score": m.actual_score_b,
                "neutral": not _is_home_fixture(m),
            }
        )
    history.sort(key=lambda r: r["date"])
    return history


def predict_stage(db, matches: list[Match], cutoff: datetime) -> int:
    """Retrain as of the cutoff and upsert predictions for the given fixtures."""
    history = _load_history(db, cutoff)
    X, y, prior = build_training_set(history)
    logger.info(
        "Training on %s rows (%s completed matches before %s)",
        len(X), len(history), cutoff.isoformat(),
    )
    model = train(X, y)
    col = {cls: i for i, cls in enumerate(model.classes_)}

    thin = [
        t.name
        for m in matches
        for t in (m.team_a, m.team_b)
        if len(prior.get(t.name, [])) < MIN_PRIOR_MATCHES
    ]
    if thin:
        raise ValueError(f"Teams with <{MIN_PRIOR_MATCHES} matches before cutoff: {thin}")

    features = np.array(
        [
            match_features(
                rolling_stats(prior[m.team_a.name]),
                rolling_stats(prior[m.team_b.name]),
                1 if _is_home_fixture(m) else 0,
            )
            for m in matches
        ]
    )
    written = 0
    for match, p in zip(matches, model.predict_proba(features)):
        # Round to 4dp, folding the residual into draw_prob so sums are exactly 1.0
        team_a_win = round(float(p[col[HOME_WIN]]), 4)
        team_b_win = round(float(p[col[AWAY_WIN]]), 4)
        draw = round(1.0 - team_a_win - team_b_win, 4)
        prediction = (
            db.query(Prediction).filter(Prediction.match_id == match.match_id).first()
        )
        if prediction is None:
            prediction = Prediction(match_id=match.match_id)
            db.add(prediction)
        prediction.team_a_win_prob = team_a_win
        prediction.team_b_win_prob = team_b_win
        prediction.draw_prob = draw
        prediction.confidence = max(team_a_win, team_b_win, draw)
        written += 1
        logger.info(
            "Predicted match %s %s vs %s: %.4f/%.4f/%.4f",
            match.match_id, match.team_a.name, match.team_b.name,
            team_a_win, draw, team_b_win,
        )
    db.commit()
    return written


def run_due_round_predictions(db=None) -> dict:
    """Predict every knockout round whose previous round is fully completed.

    A round is due when all its previous round's matches are completed, all of
    its own teams are decided (no placeholders), and at least one of its
    fixtures has no prediction yet. Training uses only matches completed before
    min(now, the round's first kickoff), so late backfills stay point-in-time.
    """
    owns_session = db is None
    db = db or SessionLocal()
    summary = {"stages": [], "predicted": 0}
    try:
        matches = (
            db.query(Match)
            .options(
                joinedload(Match.team_a),
                joinedload(Match.team_b),
                joinedload(Match.prediction),
            )
            .all()
        )
        by_stage: dict[str, list[Match]] = {}
        for m in matches:
            by_stage.setdefault(m.stage, []).append(m)

        now = datetime.now(timezone.utc)
        for stage in KNOCKOUT_STAGES:
            stage_matches = by_stage.get(stage, [])
            if not stage_matches:
                continue
            if all(m.prediction is not None for m in stage_matches):
                continue
            if any(m.team_a.is_placeholder or m.team_b.is_placeholder for m in stage_matches):
                continue
            previous = by_stage.get(PREVIOUS_STAGE[stage], [])
            if not previous or any(m.status != "completed" for m in previous):
                continue

            cutoff = min(now, min(_kickoff_utc(m) for m in stage_matches))
            stage_matches.sort(key=_kickoff_utc)
            written = predict_stage(db, stage_matches, cutoff)
            summary["stages"].append(stage)
            summary["predicted"] += written

        if summary["predicted"]:
            recompute_stats()
    finally:
        if owns_session:
            db.close()
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(run_due_round_predictions())
