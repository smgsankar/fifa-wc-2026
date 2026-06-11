"""Seed teams.squad and teams.head_coach from seed_data/ (idempotent).

Usage (from the backend directory): python scripts/seed_squads.py

squads.csv and coaches.csv come from the official FIFA squad-list PDF via
scripts/extract_squads.py:
  - squads.csv   country_code,team,number,position,name,dob,club
  - coaches.csv  country_code,team,name

Teams are matched on country_code. player_id is assigned globally in
(country_code, shirt number) order, so re-runs produce identical ids.
"""

from sqlalchemy import text

from common import load_csv

from database import Base, SessionLocal, engine
from models import Team


def seed_squads() -> None:
    Base.metadata.create_all(bind=engine)
    # create_all never alters existing tables; add the column for DBs
    # created before head_coach existed (no migration tooling in this repo).
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE teams ADD COLUMN IF NOT EXISTS head_coach VARCHAR"))

    rows = sorted(load_csv("squads.csv"), key=lambda r: (r["country_code"], int(r["number"])))
    squads: dict[str, list[dict]] = {}
    for player_id, row in enumerate(rows, start=1):
        squads.setdefault(row["country_code"], []).append(
            {
                "player_id": player_id,
                "name": row["name"],
                "position": row["position"],
                "number": int(row["number"]),
            }
        )

    coaches = {r["country_code"]: r["name"] for r in load_csv("coaches.csv")}

    db = SessionLocal()
    try:
        teams = db.query(Team).all()
        missing = [t.country_code for t in teams if t.country_code not in squads]
        missing += [t.country_code for t in teams if t.country_code not in coaches]
        if missing:
            raise ValueError(f"No squad/coach in seed_data for teams: {sorted(set(missing))}")

        for team in teams:
            team.squad = squads[team.country_code]
            team.head_coach = coaches[team.country_code]
        db.commit()
        print(f"squads: updated {len(teams)} teams ({len(rows)} players, {len(coaches)} coaches)")
    finally:
        db.close()


if __name__ == "__main__":
    seed_squads()
