"""Seed head-to-head records from h2h_data.json (keyed "teamA_teamB").

Usage (from the backend directory): python scripts/seed_h2h.py
Requires teams to be seeded first. Idempotent: upserts by team pair
(either orientation).
"""

from datetime import datetime

from common import load_json, report

from database import Base, SessionLocal, engine
from models import H2H, Team

COUNT_FIELDS = ("team_a_wins", "team_b_wins", "draws")


def seed_h2h() -> None:
    Base.metadata.create_all(bind=engine)
    data = load_json("h2h_data.json")

    created, updated, errors = 0, 0, []
    db = SessionLocal()
    try:
        team_ids = {team_id for (team_id,) in db.query(Team.id).all()}
        for key, values in data.items():
            try:
                team_a_id, team_b_id = (int(part) for part in key.split("_"))
            except ValueError:
                errors.append(f"h2h_data.json key {key!r}: expected format 'teamA_teamB'")
                continue
            if team_a_id not in team_ids or team_b_id not in team_ids:
                errors.append(f"h2h {key}: unknown team id")
                continue

            counts = {}
            field_errors = []
            for field in COUNT_FIELDS:
                try:
                    value = int(values[field])
                except (KeyError, TypeError, ValueError):
                    field_errors.append(f"h2h {key}: missing or invalid {field}")
                    continue
                if value < 0:
                    field_errors.append(f"h2h {key}: {field} must be >= 0")
                    continue
                counts[field] = value
            if field_errors:
                errors.extend(field_errors)
                continue

            last_match_date = None
            raw_date = values.get("last_match_date")
            if raw_date:
                try:
                    last_match_date = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"h2h {key}: invalid last_match_date {raw_date!r}")
                    continue

            record = (
                db.query(H2H)
                .filter(
                    ((H2H.team_a_id == team_a_id) & (H2H.team_b_id == team_b_id))
                    | ((H2H.team_a_id == team_b_id) & (H2H.team_b_id == team_a_id))
                )
                .first()
            )
            if record is None:
                record = H2H(team_a_id=team_a_id, team_b_id=team_b_id)
                db.add(record)
                created += 1
            else:
                updated += 1
                if record.team_a_id != team_a_id:
                    # stored in flipped orientation; flip incoming wins to match
                    counts["team_a_wins"], counts["team_b_wins"] = (
                        counts["team_b_wins"],
                        counts["team_a_wins"],
                    )
            record.team_a_wins = counts["team_a_wins"]
            record.team_b_wins = counts["team_b_wins"]
            record.draws = counts["draws"]
            record.last_match_date = last_match_date
        db.commit()
    finally:
        db.close()
    report("h2h", created, updated, errors)


if __name__ == "__main__":
    seed_h2h()
