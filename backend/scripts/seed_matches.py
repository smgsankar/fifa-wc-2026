"""Seed matches from matches.csv.

Usage (from the backend directory): python scripts/seed_matches.py
Requires teams to be seeded first. Idempotent: upserts by match_id.
"""

from datetime import datetime

from common import VALID_STAGES, load_csv, report

from database import Base, SessionLocal, engine
from models import Match, Team


def seed_matches() -> None:
    Base.metadata.create_all(bind=engine)
    rows = load_csv("matches.csv")

    created, updated, errors = 0, 0, []
    db = SessionLocal()
    try:
        team_ids = {team_id for (team_id,) in db.query(Team.id).all()}
        for row in rows:
            try:
                match_id = int(row["match_id"])
                team_a_id = int(row["team_a_id"])
                team_b_id = int(row["team_b_id"])
            except (KeyError, ValueError):
                errors.append(f"matches.csv row {row}: invalid or missing ids")
                continue
            if team_a_id not in team_ids or team_b_id not in team_ids:
                errors.append(f"match {match_id}: unknown team id (a={team_a_id}, b={team_b_id})")
                continue
            stage = (row.get("stage") or "").strip()
            if stage not in VALID_STAGES:
                errors.append(f"match {match_id}: invalid stage {stage!r}")
                continue
            try:
                match_date = datetime.fromisoformat(row["match_date"].replace("Z", "+00:00"))
            except (KeyError, ValueError):
                errors.append(f"match {match_id}: invalid match_date {row.get('match_date')!r}")
                continue

            match = db.query(Match).filter(Match.match_id == match_id).first()
            if match is None:
                match = Match(match_id=match_id, status="pending")
                db.add(match)
                created += 1
            else:
                updated += 1
            match.team_a_id = team_a_id
            match.team_b_id = team_b_id
            match.match_date = match_date
            match.stage = stage
        db.commit()
    finally:
        db.close()
    report("matches", created, updated, errors)


if __name__ == "__main__":
    seed_matches()
