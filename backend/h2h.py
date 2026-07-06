"""Derive a head-to-head record for a team pair.

Counts the pre-tournament historical results plus any completed World Cup 2026
meetings between the pair, so a rematch later in the tournament (or a match
detail page for a completed fixture) reflects their most recent meeting.

Used at seed time (scripts/preseed_kaggle.py seeds the initial records from
history only; scripts/seed_knockouts.py and scripts/refresh_h2h.py use this),
whenever a result is recorded by the sync, and whenever a knockout fixture's
placeholder slots resolve to real teams.
"""

from datetime import datetime, timezone

from sqlalchemy import or_

from models import H2H, HistoricalResult, Match, Team


def _wc_meetings(db, team_a: Team, team_b: Team) -> list[Match]:
    """Completed WC2026 fixtures between the pair, either orientation."""
    return (
        db.query(Match)
        .filter(
            Match.status == "completed",
            Match.actual_score_a.isnot(None),
            Match.actual_score_b.isnot(None),
            or_(
                (Match.team_a_id == team_a.id) & (Match.team_b_id == team_b.id),
                (Match.team_a_id == team_b.id) & (Match.team_b_id == team_a.id),
            ),
        )
        .all()
    )


def upsert_h2h(db, team_a: Team, team_b: Team) -> H2H:
    """Create or refresh the h2h record for a pair (does not commit)."""
    rows = (
        db.query(HistoricalResult)
        .filter(
            (
                (HistoricalResult.home_team == team_a.name)
                & (HistoricalResult.away_team == team_b.name)
            )
            | (
                (HistoricalResult.home_team == team_b.name)
                & (HistoricalResult.away_team == team_a.name)
            )
        )
        .all()
    )
    a_wins = b_wins = draws = 0
    last_date: datetime | None = None

    def count(a_score: int, b_score: int, played_at: datetime) -> None:
        nonlocal a_wins, b_wins, draws, last_date
        if a_score > b_score:
            a_wins += 1
        elif b_score > a_score:
            b_wins += 1
        else:
            draws += 1
        if last_date is None or played_at > last_date:
            last_date = played_at

    for r in rows:
        a_score = r.home_score if r.home_team == team_a.name else r.away_score
        b_score = r.away_score if r.home_team == team_a.name else r.home_score
        count(
            a_score,
            b_score,
            datetime.combine(r.match_date, datetime.min.time(), tzinfo=timezone.utc),
        )

    for m in _wc_meetings(db, team_a, team_b):
        is_a = m.team_a_id == team_a.id
        a_score = m.actual_score_a if is_a else m.actual_score_b
        b_score = m.actual_score_b if is_a else m.actual_score_a
        kickoff = m.match_date
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=timezone.utc)
        count(a_score, b_score, kickoff.astimezone(timezone.utc))

    record = (
        db.query(H2H)
        .filter(
            ((H2H.team_a_id == team_a.id) & (H2H.team_b_id == team_b.id))
            | ((H2H.team_a_id == team_b.id) & (H2H.team_b_id == team_a.id))
        )
        .first()
    )
    if record is None:
        record = H2H(team_a_id=team_a.id, team_b_id=team_b.id)
        db.add(record)
    elif record.team_a_id != team_a.id:
        a_wins, b_wins = b_wins, a_wins
    record.team_a_wins = a_wins
    record.team_b_wins = b_wins
    record.draws = draws
    record.last_match_date = last_date
    return record
