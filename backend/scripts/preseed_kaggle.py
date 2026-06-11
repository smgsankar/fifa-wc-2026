"""Preseed the database from the Kaggle international results dataset.

Usage (from the backend directory): python scripts/preseed_kaggle.py

Input files in seed_data/ (from the "International football results 1872-2025"
Kaggle dataset):
  - results.csv       date,home_team,away_team,home_score,away_score,
                      tournament,city,country,neutral
                      Rows with score "NA" are the upcoming World Cup 2026
                      fixtures; all other rows are completed matches.
  - former_names.csv  current,former,start_date,end_date

Plus the official match schedule (from the FIFA schedule via Wikipedia):
  - schedule.csv      match_no,group,home_team,away_team,kickoff_utc,
                      stadium,city
                      One row per WC2026 fixture with the UTC kickoff
                      datetime. Teams follow the official listing, which
                      reverses home/away for a few host fixtures, so the
                      lookup tries both orientations.

Pipeline (idempotent, safe to re-run):
  1. historical_results  <- completed rows, former team names normalized
  2. teams               <- 48 teams appearing in WC 2026 fixtures, with
                            flag images from Flagpedia's CDN as logo_url
  3. matches             <- 72 group-stage fixtures (match_id by date order)
  4. h2h                 <- derived from history for each fixture's team pair
  5. teams.recent_form   <- derived from history (last 5 matches per team)

Squads are seeded separately by scripts/seed_squads.py; predictions are
seeded separately when their data files arrive.
"""

from datetime import date, datetime, timezone

from common import load_csv

from database import Base, SessionLocal, engine
from models import H2H, HistoricalResult, Match, Team

# ISO 3166-1 alpha-2 codes for flag images from Flagpedia's CDN
# (https://flagpedia.net/download/api); England/Scotland use GB subdivision codes.
ISO2_CODES = {
    "Algeria": "dz", "Argentina": "ar", "Australia": "au", "Austria": "at",
    "Belgium": "be", "Bosnia and Herzegovina": "ba", "Brazil": "br",
    "Canada": "ca", "Cape Verde": "cv", "Colombia": "co", "Croatia": "hr",
    "Curaçao": "cw", "Czech Republic": "cz", "DR Congo": "cd",
    "Ecuador": "ec", "Egypt": "eg", "England": "gb-eng", "France": "fr",
    "Germany": "de", "Ghana": "gh", "Haiti": "ht", "Iran": "ir",
    "Iraq": "iq", "Ivory Coast": "ci", "Japan": "jp", "Jordan": "jo",
    "Mexico": "mx", "Morocco": "ma", "Netherlands": "nl",
    "New Zealand": "nz", "Norway": "no", "Panama": "pa", "Paraguay": "py",
    "Portugal": "pt", "Qatar": "qa", "Saudi Arabia": "sa", "Scotland": "gb-sct",
    "Senegal": "sn", "South Africa": "za", "South Korea": "kr",
    "Spain": "es", "Sweden": "se", "Switzerland": "ch", "Tunisia": "tn",
    "Turkey": "tr", "United States": "us", "Uruguay": "uy",
    "Uzbekistan": "uz",
}

# FIFA country codes for the 48 qualified teams
COUNTRY_CODES = {
    "Algeria": "ALG", "Argentina": "ARG", "Australia": "AUS", "Austria": "AUT",
    "Belgium": "BEL", "Bosnia and Herzegovina": "BIH", "Brazil": "BRA",
    "Canada": "CAN", "Cape Verde": "CPV", "Colombia": "COL", "Croatia": "CRO",
    "Curaçao": "CUW", "Czech Republic": "CZE", "DR Congo": "COD",
    "Ecuador": "ECU", "Egypt": "EGY", "England": "ENG", "France": "FRA",
    "Germany": "GER", "Ghana": "GHA", "Haiti": "HAI", "Iran": "IRN",
    "Iraq": "IRQ", "Ivory Coast": "CIV", "Japan": "JPN", "Jordan": "JOR",
    "Mexico": "MEX", "Morocco": "MAR", "Netherlands": "NED",
    "New Zealand": "NZL", "Norway": "NOR", "Panama": "PAN", "Paraguay": "PAR",
    "Portugal": "POR", "Qatar": "QAT", "Saudi Arabia": "KSA", "Scotland": "SCO",
    "Senegal": "SEN", "South Africa": "RSA", "South Korea": "KOR",
    "Spain": "ESP", "Sweden": "SWE", "Switzerland": "SUI", "Tunisia": "TUN",
    "Turkey": "TUR", "United States": "USA", "Uruguay": "URU",
    "Uzbekistan": "UZB",
}

RECENT_FORM_SIZE = 5


def build_name_normalizer() -> "callable":
    """Map former team names (within their validity window) to current names."""
    renames = []
    for row in load_csv("former_names.csv"):
        renames.append(
            (
                row["former"],
                date.fromisoformat(row["start_date"]),
                date.fromisoformat(row["end_date"]),
                row["current"],
            )
        )

    def normalize(name: str, on: date) -> str:
        for former, start, end, current in renames:
            if name == former and start <= on <= end:
                return current
        return name

    return normalize


def split_dataset() -> tuple[list[dict], list[dict]]:
    """Returns (completed historical rows, upcoming WC2026 fixture rows)."""
    history, fixtures = [], []
    for row in load_csv("results.csv"):
        if row["home_score"] == "NA":
            fixtures.append(row)
        else:
            history.append(row)
    return history, fixtures


def load_history(db, history: list[dict]) -> None:
    normalize = build_name_normalizer()
    db.query(HistoricalResult).delete()
    mappings = []
    for row in history:
        match_date = date.fromisoformat(row["date"])
        mappings.append(
            {
                "match_date": match_date,
                "home_team": normalize(row["home_team"], match_date),
                "away_team": normalize(row["away_team"], match_date),
                "home_score": int(row["home_score"]),
                "away_score": int(row["away_score"]),
                "tournament": row["tournament"],
                "city": row["city"] or None,
                "country": row["country"] or None,
                "neutral": row["neutral"].upper() == "TRUE",
            }
        )
    db.bulk_insert_mappings(HistoricalResult, mappings)
    db.commit()
    print(f"historical_results: {len(mappings)} rows loaded")


def seed_teams(db, fixtures: list[dict]) -> dict[str, int]:
    """Create the 48 teams; returns name -> team id."""
    names = sorted(set(r["home_team"] for r in fixtures) | set(r["away_team"] for r in fixtures))
    missing_codes = [n for n in names if n not in COUNTRY_CODES or n not in ISO2_CODES]
    if missing_codes:
        raise ValueError(f"No FIFA/ISO2 code mapped for teams: {missing_codes}")

    created, updated = 0, 0
    name_to_id = {}
    for team_id, name in enumerate(names, start=1):
        team = db.get(Team, team_id)
        if team is None:
            team = Team(id=team_id)
            db.add(team)
            created += 1
        else:
            updated += 1
        team.name = name
        team.country_code = COUNTRY_CODES[name]
        team.logo_url = f"https://flagcdn.com/{ISO2_CODES[name]}.svg"
        name_to_id[name] = team_id
    db.commit()
    print(f"teams: {created} created, {updated} updated ({len(names)} total)")
    return name_to_id


def load_schedule() -> dict[tuple[str, str], dict]:
    """Map (home, away) -> kickoff/venue from schedule.csv, both orientations."""
    schedule = {}
    for row in load_csv("schedule.csv"):
        entry = {
            "kickoff": datetime.fromisoformat(row["kickoff_utc"]).replace(tzinfo=timezone.utc),
            "stadium": row["stadium"],
            "city": row["city"],
        }
        schedule[(row["home_team"], row["away_team"])] = entry
        schedule[(row["away_team"], row["home_team"])] = entry
    return schedule


def seed_matches(db, fixtures: list[dict], name_to_id: dict[str, int]) -> None:
    """Create the WC2026 fixtures with deterministic match_ids (date order)."""
    schedule = load_schedule()
    missing = [
        (r["home_team"], r["away_team"])
        for r in fixtures
        if (r["home_team"], r["away_team"]) not in schedule
    ]
    if missing:
        raise ValueError(f"schedule.csv has no kickoff for fixtures: {missing}")

    ordered = sorted(fixtures, key=lambda r: (r["date"], r["home_team"], r["away_team"]))
    created, updated = 0, 0
    for match_id, row in enumerate(ordered, start=1):
        match = db.query(Match).filter(Match.match_id == match_id).first()
        if match is None:
            match = Match(match_id=match_id, status="pending")
            db.add(match)
            created += 1
        else:
            updated += 1
        match.team_a_id = name_to_id[row["home_team"]]
        match.team_b_id = name_to_id[row["away_team"]]
        entry = schedule[(row["home_team"], row["away_team"])]
        match.match_date = entry["kickoff"]
        match.stadium = entry["stadium"]
        match.city = entry["city"]
        match.stage = "group"
    db.commit()
    print(f"matches: {created} created, {updated} updated ({len(ordered)} total)")


def derive_h2h(db, name_to_id: dict[str, int]) -> None:
    """Compute h2h records from history for every scheduled fixture's pair."""
    id_to_name = {v: k for k, v in name_to_id.items()}
    pairs = {
        tuple(sorted((m.team_a_id, m.team_b_id)))
        for m in db.query(Match).all()
    }
    created, updated = 0, 0
    for team_a_id, team_b_id in sorted(pairs):
        name_a, name_b = id_to_name[team_a_id], id_to_name[team_b_id]
        rows = (
            db.query(HistoricalResult)
            .filter(
                ((HistoricalResult.home_team == name_a) & (HistoricalResult.away_team == name_b))
                | ((HistoricalResult.home_team == name_b) & (HistoricalResult.away_team == name_a))
            )
            .all()
        )
        a_wins = b_wins = draws = 0
        last_date = None
        for r in rows:
            a_score = r.home_score if r.home_team == name_a else r.away_score
            b_score = r.away_score if r.home_team == name_a else r.home_score
            if a_score > b_score:
                a_wins += 1
            elif b_score > a_score:
                b_wins += 1
            else:
                draws += 1
            if last_date is None or r.match_date > last_date:
                last_date = r.match_date

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
                a_wins, b_wins = b_wins, a_wins
        record.team_a_wins = a_wins
        record.team_b_wins = b_wins
        record.draws = draws
        record.last_match_date = (
            datetime.combine(last_date, datetime.min.time(), tzinfo=timezone.utc)
            if last_date
            else None
        )
    db.commit()
    print(f"h2h: {created} created, {updated} updated ({len(pairs)} fixture pairs)")


def derive_recent_form(db, name_to_id: dict[str, int]) -> None:
    """Set teams.recent_form to the last N completed matches per team."""
    for name, team_id in name_to_id.items():
        rows = (
            db.query(HistoricalResult)
            .filter(
                (HistoricalResult.home_team == name) | (HistoricalResult.away_team == name)
            )
            .order_by(HistoricalResult.match_date.desc())
            .limit(RECENT_FORM_SIZE)
            .all()
        )
        form = []
        for r in rows:
            is_home = r.home_team == name
            own = r.home_score if is_home else r.away_score
            opp = r.away_score if is_home else r.home_score
            form.append(
                {
                    "match_date": r.match_date.isoformat(),
                    "opponent": r.away_team if is_home else r.home_team,
                    "result": "W" if own > opp else "L" if own < opp else "D",
                    "score": f"{own}-{opp}",
                }
            )
        db.get(Team, team_id).recent_form = form
    db.commit()
    print(f"recent_form: updated for {len(name_to_id)} teams")


def preseed() -> None:
    Base.metadata.create_all(bind=engine)
    history, fixtures = split_dataset()
    print(f"dataset: {len(history)} completed matches, {len(fixtures)} WC2026 fixtures")

    db = SessionLocal()
    try:
        load_history(db, history)
        name_to_id = seed_teams(db, fixtures)
        seed_matches(db, fixtures, name_to_id)
        derive_h2h(db, name_to_id)
        derive_recent_form(db, name_to_id)
    finally:
        db.close()
    print("Done.")


if __name__ == "__main__":
    preseed()
