"""Interactively record final scores for played matches.

Usage (from the backend directory): python scripts/record_results.py

Lists matches that have kicked off but have no result yet, prompts for
final scores one match at a time, and marks each as completed. When the
session ends, prediction correctness and the global model stats are
recomputed automatically (scripts/recompute_stats.py).

Works against whatever DATABASE_URL points at, so it can be run from a
deployed backend's console to record results in production.
"""

from datetime import datetime, timezone

import common  # noqa: F401  (adds the backend dir to sys.path)
from recompute_stats import recompute_stats
from sqlalchemy.orm import joinedload

from database import Base, SessionLocal, engine
from h2h import upsert_h2h
from models import Match
from results_sync import apply_result


def ask(prompt: str) -> str | None:
    """Read one trimmed line; None when the user aborts (Ctrl-C/Ctrl-D)."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def ask_score(team_name: str) -> int | None:
    while True:
        raw = ask(f"  Goals for {team_name}: ")
        if raw is None or raw == "":
            return None
        if raw.isdigit():
            return int(raw)
        print("  Enter a non-negative whole number (blank to cancel).")


def matches_awaiting_result(db) -> list[Match]:
    now = datetime.now(timezone.utc)
    return (
        db.query(Match)
        .options(joinedload(Match.team_a), joinedload(Match.team_b))
        .filter(Match.status == "pending", Match.match_date < now)
        .order_by(Match.match_date.asc(), Match.match_id.asc())
        .all()
    )


def pick_match(db) -> Match | None:
    pending = matches_awaiting_result(db)
    if pending:
        print("\nMatches waiting for a result:")
        for m in pending:
            kickoff = m.match_date.astimezone(timezone.utc)
            print(
                f"  {m.match_id:>3}  {kickoff:%a %d %b %H:%M} UTC"
                f"  {m.team_a.name} vs {m.team_b.name}"
            )
    else:
        print("\nNo played matches are waiting for a result.")

    raw = ask("\nMatch id to record (blank to finish): ")
    if not raw:
        return None
    if not raw.isdigit():
        print("Enter a numeric match id.")
        return pick_match(db)

    match = (
        db.query(Match)
        .options(joinedload(Match.team_a), joinedload(Match.team_b))
        .filter(Match.match_id == int(raw))
        .first()
    )
    if match is None:
        print(f"No match with id {raw}.")
        return pick_match(db)
    return match


def record_one(db, match: Match) -> bool:
    label = f"{match.team_a.name} vs {match.team_b.name}"
    if match.status == "completed":
        answer = ask(
            f"Match {match.match_id} ({label}) already has a result "
            f"{match.actual_score_a}-{match.actual_score_b}. Overwrite? [y/N]: "
        )
        if answer is None or answer.lower() != "y":
            return False
    elif match.match_date.astimezone(timezone.utc) > datetime.now(timezone.utc):
        answer = ask(f"Match {match.match_id} ({label}) hasn't kicked off yet. Record anyway? [y/N]: ")
        if answer is None or answer.lower() != "y":
            return False

    print(f"\nMatch {match.match_id}: {label}")
    score_a = ask_score(match.team_a.name)
    if score_a is None:
        print("Cancelled.")
        return False
    score_b = ask_score(match.team_b.name)
    if score_b is None:
        print("Cancelled.")
        return False

    answer = ask(f"Record {match.team_a.name} {score_a}-{score_b} {match.team_b.name}? [y/N]: ")
    if answer is None or answer.lower() != "y":
        print("Discarded.")
        return False

    apply_result(match, score_a, score_b)
    upsert_h2h(db, match.team_a, match.team_b)
    db.commit()
    print(f"Saved: {match.team_a.name} {score_a}-{score_b} {match.team_b.name}")
    return True


def record_results() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    recorded = 0
    try:
        while True:
            match = pick_match(db)
            if match is None:
                break
            if record_one(db, match):
                recorded += 1
    finally:
        db.close()

    if recorded:
        print(f"\n{recorded} result(s) recorded; recomputing model stats...")
        recompute_stats()
    else:
        print("No results recorded.")


if __name__ == "__main__":
    record_results()
