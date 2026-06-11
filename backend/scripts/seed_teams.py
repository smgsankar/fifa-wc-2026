"""Seed teams from teams.csv, merging squad_data.json and recent_form.json.

Usage (from the backend directory): python scripts/seed_teams.py
Idempotent: upserts by team id, safe to re-run.
"""

from common import VALID_RESULTS, load_csv, load_json, report

from database import Base, SessionLocal, engine
from models import Team


def validate_squad(team_id: str, squad: list, errors: list[str]) -> list:
    valid = []
    for i, player in enumerate(squad):
        missing = {"player_id", "name", "position", "number"} - set(player)
        if missing:
            errors.append(f"squad for team {team_id}, player #{i}: missing {sorted(missing)}")
            continue
        valid.append(
            {
                "player_id": int(player["player_id"]),
                "name": str(player["name"]),
                "position": str(player["position"]),
                "number": int(player["number"]),
            }
        )
    return valid


def validate_form(team_id: str, form: list, errors: list[str]) -> list:
    valid = []
    for i, entry in enumerate(form):
        missing = {"match_date", "opponent", "result", "score"} - set(entry)
        if missing:
            errors.append(f"form for team {team_id}, entry #{i}: missing {sorted(missing)}")
            continue
        if entry["result"] not in VALID_RESULTS:
            errors.append(
                f"form for team {team_id}, entry #{i}: result must be W/D/L, got {entry['result']!r}"
            )
            continue
        valid.append(
            {
                "match_date": str(entry["match_date"]),
                "opponent": str(entry["opponent"]),
                "result": entry["result"],
                "score": str(entry["score"]),
            }
        )
    return valid


def seed_teams() -> None:
    Base.metadata.create_all(bind=engine)
    rows = load_csv("teams.csv")
    squads = load_json("squad_data.json", required=False) or {}
    forms = load_json("recent_form.json", required=False) or {}

    created, updated, errors = 0, 0, []
    db = SessionLocal()
    try:
        for row in rows:
            try:
                team_id = int(row["team_id"])
            except (KeyError, ValueError):
                errors.append(f"teams.csv row {row}: invalid or missing team_id")
                continue
            name = (row.get("name") or "").strip()
            country_code = (row.get("country_code") or "").strip()
            if not name or not country_code:
                errors.append(f"team {team_id}: name and country_code are required")
                continue

            key = str(team_id)
            squad = validate_squad(key, squads.get(key, []), errors)
            form = validate_form(key, forms.get(key, []), errors)

            team = db.get(Team, team_id)
            if team is None:
                team = Team(id=team_id)
                db.add(team)
                created += 1
            else:
                updated += 1
            team.name = name
            team.country_code = country_code
            team.logo_url = (row.get("logo_url") or "").strip() or None
            team.squad = squad
            team.recent_form = form
        db.commit()
    finally:
        db.close()
    report("teams", created, updated, errors)


if __name__ == "__main__":
    seed_teams()
