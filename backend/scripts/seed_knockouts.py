"""Seed the knockout-stage fixtures (matches 73-104) from knockout_schedule.csv.

Usage (from the backend directory): python scripts/seed_knockouts.py

knockout_schedule.csv holds one row per knockout fixture: match_no, stage,
home_team, away_team, kickoff_utc, stadium, city. The team columns contain
either a real team name (rounds whose participants are already decided) or a
placeholder slot code from PLACEHOLDERS below (e.g. WSF1 = "Winner SF 1").

Placeholder slots become dedicated Team rows (is_placeholder=True, ids 1001+)
so every fixture always references two teams and the API/UI need no special
casing. As the tournament progresses, results_sync.resolve_knockout_teams()
swaps the placeholders for the real teams reported by football-data.org.

Idempotent, safe to re-run: existing fixtures keep their status/scores, and a
fixture whose slot has already been resolved to a real team is never reverted
to a placeholder. H2H records are derived for every decided pairing.

Run scripts/preseed_kaggle.py first (teams + group fixtures must exist).
"""

from datetime import datetime, timezone

from common import load_csv

from database import Base, SessionLocal, engine
from h2h import upsert_h2h
from models import Match, Team
from results_sync import ensure_schema

# Slot code -> (team id, display name). Codes double as the country_code so
# badges/logos fall back to something meaningful (e.g. "WSF1").
PLACEHOLDERS = {
    "W93": (1001, "Winner Match 93"),
    "W94": (1002, "Winner Match 94"),
    "W95": (1003, "Winner Match 95"),
    "W96": (1004, "Winner Match 96"),
    "WQF1": (1005, "Winner QF 1"),
    "WQF2": (1006, "Winner QF 2"),
    "WQF3": (1007, "Winner QF 3"),
    "WQF4": (1008, "Winner QF 4"),
    "WSF1": (1009, "Winner SF 1"),
    "WSF2": (1010, "Winner SF 2"),
    "LSF1": (1011, "Loser SF 1"),
    "LSF2": (1012, "Loser SF 2"),
}


def seed_placeholder_teams(db) -> None:
    created, updated = 0, 0
    for code, (team_id, name) in PLACEHOLDERS.items():
        team = db.get(Team, team_id)
        if team is None:
            team = Team(id=team_id)
            db.add(team)
            created += 1
        else:
            updated += 1
        team.name = name
        team.country_code = code
        team.logo_url = None
        team.is_placeholder = True
    db.commit()
    print(f"placeholder teams: {created} created, {updated} updated")


def resolve_team_id(db, value: str, real_teams: dict[str, Team]) -> int:
    if value in PLACEHOLDERS:
        return PLACEHOLDERS[value][0]
    team = real_teams.get(value)
    if team is None:
        raise ValueError(f"knockout_schedule.csv references unknown team: {value!r}")
    return team.id


def seed_knockout_matches(db) -> None:
    real_teams = {
        t.name: t for t in db.query(Team).filter(Team.is_placeholder.is_(False)).all()
    }
    placeholder_ids = {team_id for team_id, _ in PLACEHOLDERS.values()}

    created, updated = 0, 0
    decided_pairs: set[tuple[int, int]] = set()
    for row in load_csv("knockout_schedule.csv"):
        match_id = int(row["match_no"])
        team_a_id = resolve_team_id(db, row["home_team"], real_teams)
        team_b_id = resolve_team_id(db, row["away_team"], real_teams)

        match = db.query(Match).filter(Match.match_id == match_id).first()
        if match is None:
            match = Match(match_id=match_id, status="pending")
            match.team_a_id = team_a_id
            match.team_b_id = team_b_id
            db.add(match)
            created += 1
        else:
            updated += 1
            # Never revert a slot the sync has already resolved to a real team.
            if not (team_a_id in placeholder_ids and match.team_a_id not in placeholder_ids):
                match.team_a_id = team_a_id
            if not (team_b_id in placeholder_ids and match.team_b_id not in placeholder_ids):
                match.team_b_id = team_b_id

        match.match_date = datetime.fromisoformat(row["kickoff_utc"]).replace(
            tzinfo=timezone.utc
        )
        match.stadium = row["stadium"]
        match.city = row["city"]
        match.stage = row["stage"]

        if (
            match.team_a_id not in placeholder_ids
            and match.team_b_id not in placeholder_ids
        ):
            decided_pairs.add((match.team_a_id, match.team_b_id))
    db.commit()
    print(f"knockout matches: {created} created, {updated} updated")

    teams_by_id = {t.id: t for t in real_teams.values()}
    for team_a_id, team_b_id in sorted(decided_pairs):
        upsert_h2h(db, teams_by_id[team_a_id], teams_by_id[team_b_id])
    db.commit()
    print(f"h2h: refreshed for {len(decided_pairs)} decided knockout pairings")


def seed_knockouts() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_schema(db)
        seed_placeholder_teams(db)
        seed_knockout_matches(db)
    finally:
        db.close()
    print("Done.")


if __name__ == "__main__":
    seed_knockouts()
