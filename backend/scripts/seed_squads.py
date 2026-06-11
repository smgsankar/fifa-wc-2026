"""Seed teams.squad from seed_data/squads.csv (idempotent, safe to re-run).

Usage (from the backend directory): python scripts/seed_squads.py

squads.csv comes from the official FIFA squad-list PDF via
scripts/extract_squads.py: country_code,team,number,position,name,dob,club

Teams are matched on country_code. player_id is assigned globally in
(country_code, shirt number) order, so re-runs produce identical ids.
"""

from common import load_csv

from database import Base, SessionLocal, engine
from models import Team


def seed_squads() -> None:
    Base.metadata.create_all(bind=engine)
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

    db = SessionLocal()
    try:
        teams = db.query(Team).all()
        missing = [t.country_code for t in teams if t.country_code not in squads]
        if missing:
            raise ValueError(f"No squad in squads.csv for teams: {missing}")

        for team in teams:
            team.squad = squads[team.country_code]
        db.commit()
        print(f"squads: updated {len(teams)} teams ({len(rows)} players)")
    finally:
        db.close()


if __name__ == "__main__":
    seed_squads()
