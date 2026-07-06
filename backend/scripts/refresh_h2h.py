"""Refresh every fixture pairing's head-to-head record.

Usage (from the backend directory): python scripts/refresh_h2h.py

Recomputes h2h for each fixture's team pair (skipping undecided knockout
slots) using historical results PLUS completed World Cup 2026 meetings.
Run once after upgrading to WC-inclusive h2h; ongoing results keep records
current automatically (the sync refreshes the pair whenever it records a
result).
"""

import common  # noqa: F401  (adds the backend dir to sys.path)
from sqlalchemy.orm import joinedload

from database import SessionLocal
from h2h import upsert_h2h
from models import Match


def refresh_h2h() -> None:
    db = SessionLocal()
    try:
        matches = (
            db.query(Match)
            .options(joinedload(Match.team_a), joinedload(Match.team_b))
            .all()
        )
        pairs = {}
        for m in matches:
            if m.team_a.is_placeholder or m.team_b.is_placeholder:
                continue
            pairs[frozenset({m.team_a_id, m.team_b_id})] = (m.team_a, m.team_b)
        for team_a, team_b in pairs.values():
            upsert_h2h(db, team_a, team_b)
        db.commit()
        print(f"h2h refreshed for {len(pairs)} fixture pairings")
    finally:
        db.close()


if __name__ == "__main__":
    refresh_h2h()
