"""Seed the predictions table from seed_data/predictions.json (idempotent).

Usage (from the backend directory): python scripts/seed_predictions.py

predictions.json is produced by ml/train_predict.py. Before writing anything,
the file is validated against the schedule already seeded by
scripts/preseed_kaggle.py: exactly 72 predictions with match_ids 1-72,
probabilities summing to 1, and team names matching each fixture's teams
(guards against match_id ordering drift between the two scripts).

Re-runs update probabilities in place and leave is_correct untouched
(scripts/recompute_stats.py owns that field).
"""

import json

from common import SEED_DIR

from database import Base, SessionLocal, engine
from models import Match, Prediction

EXPECTED_MATCHES = 72
PROB_SUM_TOLERANCE = 1e-3


def load_predictions() -> list[dict]:
    path = SEED_DIR / "predictions.json"
    if not path.exists():
        raise FileNotFoundError(f"Required seed file missing: {path}")
    with open(path, encoding="utf-8") as f:
        predictions = json.load(f)["predictions"]

    ids = sorted(p["match_id"] for p in predictions)
    if ids != list(range(1, EXPECTED_MATCHES + 1)):
        raise ValueError(
            f"Expected match_ids 1-{EXPECTED_MATCHES}, got {len(ids)} entries"
        )
    for p in predictions:
        probs = (p["team_a_win_prob"], p["team_b_win_prob"], p["draw_prob"])
        if any(not 0.0 <= x <= 1.0 for x in probs):
            raise ValueError(f"match {p['match_id']}: probability out of [0, 1]: {probs}")
        if abs(sum(probs) - 1.0) > PROB_SUM_TOLERANCE:
            raise ValueError(f"match {p['match_id']}: probabilities sum to {sum(probs)}")
    return predictions


def seed_predictions() -> None:
    Base.metadata.create_all(bind=engine)
    predictions = load_predictions()

    db = SessionLocal()
    try:
        matches = {m.match_id: m for m in db.query(Match).all()}
        mismatches = []
        for p in predictions:
            match = matches.get(p["match_id"])
            if match is None:
                mismatches.append(f"match {p['match_id']}: not in matches table")
            elif (match.team_a.name, match.team_b.name) != (p["team_a"], p["team_b"]):
                mismatches.append(
                    f"match {p['match_id']}: predictions.json has "
                    f"{p['team_a']} vs {p['team_b']}, DB fixture is "
                    f"{match.team_a.name} vs {match.team_b.name}"
                )
        if mismatches:
            raise ValueError(
                "predictions.json does not line up with seeded fixtures "
                "(run scripts/preseed_kaggle.py first?):\n  " + "\n  ".join(mismatches)
            )

        created, updated = 0, 0
        for p in predictions:
            prediction = (
                db.query(Prediction).filter(Prediction.match_id == p["match_id"]).first()
            )
            if prediction is None:
                prediction = Prediction(match_id=p["match_id"])
                db.add(prediction)
                created += 1
            else:
                updated += 1
            prediction.team_a_win_prob = p["team_a_win_prob"]
            prediction.team_b_win_prob = p["team_b_win_prob"]
            prediction.draw_prob = p["draw_prob"]
            prediction.confidence = p["confidence"]
        db.commit()
        print(f"predictions: {created} created, {updated} updated ({len(predictions)} total)")
    finally:
        db.close()


if __name__ == "__main__":
    seed_predictions()
