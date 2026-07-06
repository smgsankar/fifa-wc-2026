"""Automated match-result ingestion from football-data.org.

Two steps, run independently:

  1. Mapping (`scripts/map_external_ids.py` -> `map_external_ids`): once, pull
     the competition's full fixture list and reconcile each match against our
     fixtures by team identity, storing the football-data.org match id in
     Match.external_id.

  2. Sync (`scripts/sync_results.py` / the APScheduler job -> `sync_results`):
     repeatedly, collect the external ids of fixtures that have kicked off but
     have no result yet, ask the API for just those matches by id, and write the
     full-time score for any that have FINISHED. Then recompute model stats.

Polling by id means we only ever query the handful of matches we're actually
waiting on, and team-name reconciliation happens once (at mapping time) rather
than on every poll. The shared `apply_result()` helper is also used by the
interactive `scripts/record_results.py` so manual and automated recording write
results identically.
"""

import logging
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from config import (
    FOOTBALL_DATA_API_TOKEN,
    FOOTBALL_DATA_COMPETITION,
)
from database import SessionLocal
from h2h import upsert_h2h
from models import Match, Team

# recompute_stats lives under scripts/; make it importable from the backend root.
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from recompute_stats import recompute_stats  # noqa: E402

logger = logging.getLogger("results_sync")

API_BASE_URL = "https://api.football-data.org/v4"
REQUEST_TIMEOUT = 15.0
# football-data.org accepts a comma-separated `ids` list on /v4/matches; keep
# each request small to stay clear of any URL-length / per-request id cap.
MAX_IDS_PER_REQUEST = 50

# football-data.org names that differ semantically from our Team.name values.
# Spelling/accent differences (e.g. Curaçao/Curacao) are handled by normalize();
# only genuine renamings need an entry here.
API_NAME_ALIASES = {
    "Czechia": "Czech Republic",
    "Korea Republic": "South Korea",
    "Korea DPR": "North Korea",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "IR Iran": "Iran",
    "Cabo Verde": "Cape Verde",
    "Cape Verde Islands": "Cape Verde",
    "Türkiye": "Turkey",
    "Turkiye": "Turkey",
    "USA": "United States",
    "United States of America": "United States",
    "Congo DR": "DR Congo",
    "DR Congo": "DR Congo",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}

# football-data.org stage values -> our Match.stage values. Used to reconcile
# knockout fixtures whose teams are still placeholders (no team pair to match
# on) by stage + kickoff instead.
API_STAGE_MAP = {
    "GROUP_STAGE": "group",
    "LAST_32": "round32",
    "ROUND_OF_32": "round32",
    "LAST_16": "round16",
    "ROUND_OF_16": "round16",
    "QUARTER_FINALS": "quarterfinal",
    "SEMI_FINALS": "semifinal",
    "THIRD_PLACE": "third_place",
    "FINAL": "final",
}


def _normalize(name: str) -> str:
    """Lowercase, strip accents, and drop non-alphanumerics for matching."""
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    return "".join(ch for ch in ascii_only.lower() if ch.isalnum())


# football-data.org score.duration values -> Match.decided_by
DURATION_MAP = {
    "REGULAR": "regular",
    "EXTRA_TIME": "extra_time",
    "PENALTY_SHOOTOUT": "penalties",
}


def apply_result(
    match: Match,
    score_a: int,
    score_b: int,
    *,
    decided_by: str | None = None,
    penalties: tuple[int, int] | None = None,
) -> None:
    """Write a final score onto a match (does not commit).

    score_a/score_b is the full-time score including extra time; penalties is
    the shootout score (team_a, team_b) when the match went that far.
    """
    match.actual_score_a = score_a
    match.actual_score_b = score_b
    match.decided_by = decided_by
    match.penalty_score_a, match.penalty_score_b = penalties or (None, None)
    match.status = "completed"


# --- football-data.org HTTP ------------------------------------------------


def _get(path: str, params: dict, token: str) -> dict:
    """GET a football-data.org endpoint, raising clear errors on the usual codes."""
    if not token:
        raise RuntimeError(
            "FOOTBALL_DATA_API_TOKEN is not set; cannot reach football-data.org. "
            "Register for a free token at https://www.football-data.org/client/register"
        )
    response = httpx.get(
        f"{API_BASE_URL}{path}",
        params=params,
        headers={"X-Auth-Token": token},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 403:
        raise RuntimeError(
            "football-data.org rejected the token (403). Check FOOTBALL_DATA_API_TOKEN "
            "and that your plan covers the competition."
        )
    if response.status_code == 429:
        raise RuntimeError("football-data.org rate limit hit (429); try a longer interval.")
    response.raise_for_status()
    return response.json()


def fetch_competition_matches(
    token: str = FOOTBALL_DATA_API_TOKEN,
    competition: str = FOOTBALL_DATA_COMPETITION,
) -> list[dict]:
    """Return every match in the competition (used to build the id mapping)."""
    return _get(f"/competitions/{competition}/matches", {}, token).get("matches", [])


def fetch_matches_by_ids(
    ids: list[int],
    token: str = FOOTBALL_DATA_API_TOKEN,
) -> list[dict]:
    """Return the given matches by football-data.org id, batched to stay small."""
    matches: list[dict] = []
    for start in range(0, len(ids), MAX_IDS_PER_REQUEST):
        batch = ids[start : start + MAX_IDS_PER_REQUEST]
        csv = ",".join(str(i) for i in batch)
        matches.extend(_get("/matches", {"ids": csv}, token).get("matches", []))
    return matches


# --- reconciliation helpers ------------------------------------------------


def _build_team_index(db) -> dict:
    """Map normalized team name -> Team for the real (non-placeholder) teams."""
    teams = db.query(Team).filter(Team.is_placeholder.is_(False)).all()
    return {_normalize(team.name): team for team in teams}


def _resolve_team(api_name: str, index: dict):
    """Resolve a football-data.org team name to one of our Teams, or None."""
    canonical = API_NAME_ALIASES.get(api_name, api_name)
    return index.get(_normalize(canonical))


def _all_fixtures(db) -> list[Match]:
    return (
        db.query(Match)
        .options(joinedload(Match.team_a), joinedload(Match.team_b))
        .all()
    )


def _api_kickoff(api_match: dict) -> datetime | None:
    raw = api_match.get("utcDate")
    if not raw:
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)


def _api_kickoff_date(api_match: dict):
    kickoff = _api_kickoff(api_match)
    return kickoff.date() if kickoff else None


def _kickoff_utc(match: Match) -> datetime:
    kickoff = match.match_date
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    return kickoff.astimezone(timezone.utc)


def _has_placeholder_team(match: Match) -> bool:
    return match.team_a.is_placeholder or match.team_b.is_placeholder


def _select_by_stage_kickoff(matches: list[Match], api_match: dict):
    """Pick the fixture an API match refers to by stage + kickoff.

    Used for fixtures still holding placeholder teams, where matching by team
    pair is impossible. Prefers an exact kickoff-datetime match; falls back to
    the stage's sole fixture on that calendar day (kickoffs occasionally shift
    by an hour or two for weather delays).
    """
    stage = API_STAGE_MAP.get(api_match.get("stage"))
    kickoff = _api_kickoff(api_match)
    if stage is None or kickoff is None:
        return None
    candidates = [m for m in matches if m.stage == stage]
    exact = [m for m in candidates if _kickoff_utc(m) == kickoff]
    if len(exact) == 1:
        return exact[0]
    same_day = [m for m in candidates if _kickoff_utc(m).date() == kickoff.date()]
    if len(same_day) == 1:
        return same_day[0]
    return None


def _select_fixture(candidates: list, api_match: dict):
    """Pick the fixture for an API match from same-pairing candidates."""
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    # Two teams meeting more than once (e.g. group + knockout): disambiguate by date.
    api_date = _api_kickoff_date(api_match)
    for match in candidates:
        kickoff = match.match_date
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=timezone.utc)
        if api_date and kickoff.astimezone(timezone.utc).date() == api_date:
            return match
    return None


_schema_ensured = False


def ensure_schema(db) -> None:
    """Backfill columns added after a database was seeded.

    The app creates tables with Base.metadata.create_all, which never alters an
    existing table — so this idempotent DDL adds columns introduced later
    (external_id, is_placeholder, decided_by, penalty scores). Runs at app
    startup (main.py lifespan) so a deploy self-migrates before serving any
    query that selects the new columns. Postgres-only: other dialects (e.g.
    SQLite in tests) get the full schema from create_all anyway.
    """
    global _schema_ensured
    if _schema_ensured or db.bind.dialect.name != "postgresql":
        return
    db.execute(
        text(
            "ALTER TABLE teams ADD COLUMN IF NOT EXISTS "
            "is_placeholder BOOLEAN NOT NULL DEFAULT FALSE"
        )
    )
    db.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS external_id INTEGER"))
    db.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_matches_external_id "
            "ON matches (external_id)"
        )
    )
    db.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS decided_by VARCHAR"))
    db.execute(
        text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS penalty_score_a INTEGER")
    )
    db.execute(
        text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS penalty_score_b INTEGER")
    )
    db.commit()
    _schema_ensured = True


# --- step 1: map our fixtures to football-data.org ids ---------------------


def map_external_ids(db=None) -> dict:
    """Populate Match.external_id by reconciling the competition fixture list.

    Fixtures with both teams decided are reconciled by team pair (kickoff date
    disambiguates repeat pairings); fixtures still holding placeholder teams are
    reconciled by stage + kickoff instead. Returns {fetched, mapped, unchanged,
    unmatched}. Re-runnable: it re-resolves every fixture and only writes ids
    that changed.
    """
    owns_session = db is None
    db = db or SessionLocal()
    summary = {"fetched": 0, "mapped": 0, "unchanged": 0, "unmatched": []}
    try:
        ensure_schema(db)
        api_matches = fetch_competition_matches()
        summary["fetched"] = len(api_matches)
        team_index = _build_team_index(db)

        fixtures = _all_fixtures(db)
        by_pair: dict = {}
        placeholder_fixtures = []
        for m in fixtures:
            if _has_placeholder_team(m):
                placeholder_fixtures.append(m)
            else:
                by_pair.setdefault(frozenset({m.team_a_id, m.team_b_id}), []).append(m)

        changed = False
        for api_match in api_matches:
            external_id = api_match.get("id")
            if external_id is None:
                continue
            home_name = (api_match.get("homeTeam") or {}).get("name")
            away_name = (api_match.get("awayTeam") or {}).get("name")

            match = None
            if home_name and away_name:
                home = _resolve_team(home_name, team_index)
                away = _resolve_team(away_name, team_index)
                if home is None or away is None:
                    summary["unmatched"].append(f"{home_name} vs {away_name} (unknown team)")
                    continue
                match = _select_fixture(
                    by_pair.get(frozenset({home.id, away.id}), []), api_match
                )
            if match is None:
                # Undecided slots (or a decided pairing we still hold as
                # placeholders): reconcile by stage + kickoff.
                match = _select_by_stage_kickoff(placeholder_fixtures, api_match)
            if match is None:
                summary["unmatched"].append(
                    f"{home_name or 'TBD'} vs {away_name or 'TBD'} (no matching fixture)"
                )
                continue

            if match.external_id == external_id:
                summary["unchanged"] += 1
                continue

            match.external_id = external_id
            changed = True
            summary["mapped"] += 1
            logger.info(
                "Mapped match %s (%s vs %s) -> external id %s",
                match.match_id, match.team_a.name, match.team_b.name, external_id,
            )

        if changed:
            db.commit()
    finally:
        if owns_session:
            db.close()

    if summary["unmatched"]:
        logger.warning("Unmapped fixtures: %s", "; ".join(summary["unmatched"]))
    return summary


# --- step 1b: swap placeholder slots for decided teams ----------------------


def resolve_knockout_teams(db=None) -> dict:
    """Replace placeholder teams with the real ones football-data.org reports.

    Looks up mapped fixtures that still hold a placeholder slot, asks the API
    for them by id, and writes the decided team(s). Newly completed pairings
    also get an h2h record. Returns {checked, resolved, undecided, unmatched}.
    """
    owns_session = db is None
    db = db or SessionLocal()
    summary = {"checked": 0, "resolved": 0, "undecided": 0, "unmatched": []}
    try:
        pending = [
            m
            for m in _all_fixtures(db)
            if _has_placeholder_team(m) and m.external_id is not None
        ]
        summary["checked"] = len(pending)
        if not pending:
            return summary

        team_index = _build_team_index(db)
        by_external = {m.external_id: m for m in pending}
        api_matches = fetch_matches_by_ids(list(by_external))

        changed = False
        for api_match in api_matches:
            match = by_external.get(api_match.get("id"))
            if match is None:
                continue
            home_name = (api_match.get("homeTeam") or {}).get("name")
            away_name = (api_match.get("awayTeam") or {}).get("name")
            if not home_name and not away_name:
                summary["undecided"] += 1
                continue

            # Our fixtures follow the official bracket's home/away order, so
            # the feed's home team fills team_a and its away team fills team_b.
            resolved_any = False
            for name, side in ((home_name, "team_a"), (away_name, "team_b")):
                if not name or not getattr(match, side).is_placeholder:
                    continue
                team = _resolve_team(name, team_index)
                if team is None:
                    summary["unmatched"].append(
                        f"match {match.match_id}: unknown team {name!r}"
                    )
                    continue
                setattr(match, f"{side}_id", team.id)
                setattr(match, side, team)
                resolved_any = True
                logger.info(
                    "Resolved match %s %s -> %s", match.match_id, side, team.name
                )
            if not resolved_any:
                summary["undecided"] += 1
                continue

            changed = True
            summary["resolved"] += 1
            if not _has_placeholder_team(match):
                upsert_h2h(db, match.team_a, match.team_b)

        if changed:
            db.commit()
    finally:
        if owns_session:
            db.close()

    if summary["unmatched"]:
        logger.warning(
            "Could not resolve knockout slots: %s", "; ".join(summary["unmatched"])
        )
    return summary


# --- step 2: poll the awaiting fixtures by id ------------------------------


def _home_is_team_a(match: Match, home_name: str) -> bool | None:
    """Whether the feed's home team is our team_a (drives score orientation).

    Returns None if the feed's home team matches neither of our teams
    (shouldn't happen for a mapped fixture, but guards a bad alias).
    """
    canonical_home = _normalize(API_NAME_ALIASES.get(home_name, home_name))
    if canonical_home == _normalize(match.team_a.name):
        return True
    if canonical_home == _normalize(match.team_b.name):
        return False
    return None


def _oriented(home_is_a: bool, home_value: int, away_value: int) -> tuple[int, int]:
    return (home_value, away_value) if home_is_a else (away_value, home_value)


def _matches_awaiting_result(db, now: datetime) -> list[Match]:
    """Fixtures that have kicked off, aren't recorded, and have an external id."""
    return (
        db.query(Match)
        .options(joinedload(Match.team_a), joinedload(Match.team_b))
        .filter(
            Match.status != "completed",
            Match.match_date < now,
            Match.external_id.isnot(None),
        )
        .all()
    )


def sync_results(db=None, *, recompute: bool = True) -> dict:
    """Poll football-data.org for the fixtures awaiting a result and record them.

    Looks up the matches that have kicked off but aren't recorded yet, asks the
    API for just those (by external id), and writes the score for any FINISHED.
    Returns {awaiting, fetched, updated, unmatched, unmapped}: `unmapped` counts
    awaiting fixtures with no external_id (run map_external_ids to fix), and
    `unmatched` lists IDs the API returned that we couldn't orient.
    """
    owns_session = db is None
    db = db or SessionLocal()
    summary = {"awaiting": 0, "fetched": 0, "updated": 0, "unmatched": [], "unmapped": 0}
    try:
        ensure_schema(db)
        now = datetime.now(timezone.utc)
        awaiting = _matches_awaiting_result(db, now)
        summary["awaiting"] = len(awaiting)

        # Warn about kicked-off fixtures we can't poll because they were never mapped.
        summary["unmapped"] = (
            db.query(Match)
            .filter(
                Match.status != "completed",
                Match.match_date < now,
                Match.external_id.is_(None),
            )
            .count()
        )

        if not awaiting:
            if summary["unmapped"]:
                logger.warning(
                    "%s fixture(s) awaiting results have no external_id; "
                    "run scripts/map_external_ids.py",
                    summary["unmapped"],
                )
            return summary

        by_external = {m.external_id: m for m in awaiting}
        api_matches = fetch_matches_by_ids(list(by_external))
        summary["fetched"] = len(api_matches)

        changed = False
        for api_match in api_matches:
            if api_match.get("status") != "FINISHED":
                continue  # in progress / postponed — nothing to record yet
            match = by_external.get(api_match.get("id"))
            if match is None:
                continue

            score = api_match.get("score") or {}
            full_time = score.get("fullTime") or {}
            home_score, away_score = full_time.get("home"), full_time.get("away")
            home_name = (api_match.get("homeTeam") or {}).get("name")
            if home_score is None or away_score is None or not home_name:
                continue

            home_is_a = _home_is_team_a(match, home_name)
            if home_is_a is None:
                summary["unmatched"].append(f"external id {api_match.get('id')} ({home_name})")
                continue
            score_a, score_b = _oriented(home_is_a, home_score, away_score)

            shootout = score.get("penalties") or {}
            penalties = None
            if shootout.get("home") is not None and shootout.get("away") is not None:
                penalties = _oriented(home_is_a, shootout["home"], shootout["away"])

            apply_result(
                match,
                score_a,
                score_b,
                decided_by=DURATION_MAP.get(score.get("duration")),
                penalties=penalties,
            )
            # Keep the pair's head-to-head current now that they've met again.
            upsert_h2h(db, match.team_a, match.team_b)
            changed = True
            summary["updated"] += 1
            logger.info(
                "Recorded match %s: %s %s-%s %s%s",
                match.match_id, match.team_a.name, score_a, score_b, match.team_b.name,
                f" (pens {penalties[0]}-{penalties[1]})" if penalties else "",
            )

        if changed:
            db.commit()
    finally:
        if owns_session:
            db.close()

    if summary["unmatched"]:
        logger.warning("Could not orient results for: %s", "; ".join(summary["unmatched"]))
    if summary["unmapped"]:
        logger.warning(
            "%s kicked-off fixture(s) have no external_id; run scripts/map_external_ids.py",
            summary["unmapped"],
        )
    if summary["updated"] and recompute:
        recompute_stats()
    return summary
