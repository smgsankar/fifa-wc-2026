"""Placeholder resolution: decided knockout slots get their real teams."""

from datetime import date

import results_sync
from conftest import add_history, hours_ahead, make_match, make_team
from models import H2H


def test_resolve_knockout_teams_orientation_and_h2h(db, monkeypatch):
    brazil = make_team(db, 1, "Brazil")
    norway = make_team(db, 2, "Norway")
    w1 = make_team(db, 1001, "Winner QF 1", placeholder=True)
    w2 = make_team(db, 1002, "Winner QF 2", placeholder=True)
    fixture = make_match(
        db, 200, w1, w2, stage="semifinal", kickoff=hours_ahead(48), external_id=5001
    )
    # One historical meeting (Brazil win) + one completed WC meeting (draw):
    # the derived h2h must count both.
    add_history(db, "Brazil", "Norway", 2, 0, date(2019, 6, 1))
    make_match(db, 30, brazil, norway, stage="group", kickoff=hours_ahead(-100), score=(1, 1))

    monkeypatch.setattr(
        results_sync,
        "fetch_matches_by_ids",
        lambda ids, token=None: [
            {"id": 5001, "homeTeam": {"name": "Brazil"}, "awayTeam": {"name": "Norway"}}
        ],
    )
    summary = results_sync.resolve_knockout_teams(db)

    assert summary == {"checked": 1, "resolved": 1, "undecided": 0, "unmatched": []}
    db.refresh(fixture)
    assert fixture.team_a_id == brazil.id  # feed home -> team_a
    assert fixture.team_b_id == norway.id

    h2h = db.query(H2H).filter(H2H.team_a_id.in_([1, 2])).one()
    oriented = h2h.team_a_id == brazil.id
    assert (h2h.team_a_wins if oriented else h2h.team_b_wins) == 1
    assert h2h.draws == 1


def test_undecided_slots_stay_placeholders(db, monkeypatch):
    w1 = make_team(db, 1001, "Winner SF 1", placeholder=True)
    w2 = make_team(db, 1002, "Winner SF 2", placeholder=True)
    fixture = make_match(
        db, 201, w1, w2, stage="final", kickoff=hours_ahead(72), external_id=5002
    )

    monkeypatch.setattr(
        results_sync,
        "fetch_matches_by_ids",
        lambda ids, token=None: [
            {"id": 5002, "homeTeam": {"name": None}, "awayTeam": {"name": None}}
        ],
    )
    summary = results_sync.resolve_knockout_teams(db)

    assert summary["resolved"] == 0
    assert summary["undecided"] == 1
    db.refresh(fixture)
    assert fixture.team_a_id == w1.id


def test_unmapped_fixtures_are_not_polled(db, monkeypatch):
    w1 = make_team(db, 1001, "Winner SF 1", placeholder=True)
    w2 = make_team(db, 1002, "Winner SF 2", placeholder=True)
    make_match(db, 202, w1, w2, stage="final", kickoff=hours_ahead(72))  # no external_id

    def boom(ids, token=None):
        raise AssertionError("should not fetch when nothing is mapped")

    monkeypatch.setattr(results_sync, "fetch_matches_by_ids", boom)
    assert results_sync.resolve_knockout_teams(db)["checked"] == 0
