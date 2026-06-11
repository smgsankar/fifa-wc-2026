"""Seed predictions from predictions.json (keyed by match_id).

Usage (from the backend directory): python scripts/seed_predictions.py
Requires matches to be seeded first. Idempotent: upserts by match_id.
"""

from common import load_json, report

from database import Base, SessionLocal, engine
from models import Match, Prediction

PROB_FIELDS = ("team_a_win_prob", "team_b_win_prob", "draw_prob", "confidence")


def seed_predictions() -> None:
    Base.metadata.create_all(bind=engine)
    data = load_json("predictions.json")

    created, updated, errors = 0, 0, []
    db = SessionLocal()
    try:
        match_ids = {match_id for (match_id,) in db.query(Match.match_id).all()}
        for key, values in data.items():
            try:
                match_id = int(key)
            except ValueError:
                errors.append(f"predictions.json key {key!r}: not a valid match_id")
                continue
            if match_id not in match_ids:
                errors.append(f"prediction for match {match_id}: match not found")
                continue

            probs = {}
            field_errors = []
            for field in PROB_FIELDS:
                try:
                    value = float(values[field])
                except (KeyError, TypeError, ValueError):
                    field_errors.append(f"match {match_id}: missing or invalid {field}")
                    continue
                if not 0.0 <= value <= 1.0:
                    field_errors.append(f"match {match_id}: {field}={value} outside [0, 1]")
                    continue
                probs[field] = value
            if field_errors:
                errors.extend(field_errors)
                continue

            prediction = db.query(Prediction).filter(Prediction.match_id == match_id).first()
            if prediction is None:
                prediction = Prediction(match_id=match_id)
                db.add(prediction)
                created += 1
            else:
                updated += 1
            for field, value in probs.items():
                setattr(prediction, field, value)
        db.commit()
    finally:
        db.close()
    report("predictions", created, updated, errors)


if __name__ == "__main__":
    seed_predictions()
