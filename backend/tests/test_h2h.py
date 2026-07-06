"""H2H derivation counts historical results plus completed WC2026 meetings."""

from datetime import date

from conftest import add_history, hours_ago, make_match, make_team
from h2h import upsert_h2h


def test_upsert_h2h_blends_history_and_wc_results(db):
    spain = make_team(db, 1, "Spain")
    portugal = make_team(db, 2, "Portugal")
    add_history(db, "Spain", "Portugal", 1, 0, date(2010, 6, 29))
    add_history(db, "Portugal", "Spain", 3, 3, date(2018, 6, 15))
    # Completed WC meeting, reversed orientation relative to the pair queried.
    wc = make_match(db, 68, portugal, spain, stage="group", kickoff=hours_ago(200), score=(0, 2))

    record = upsert_h2h(db, spain, portugal)
    db.commit()

    assert (record.team_a_wins, record.team_b_wins, record.draws) == (2, 0, 1)
    assert record.last_match_date.date() == wc.match_date.date()


def test_upsert_h2h_ignores_unfinished_wc_fixtures(db):
    spain = make_team(db, 1, "Spain")
    portugal = make_team(db, 2, "Portugal")
    make_match(db, 93, portugal, spain, stage="round16", kickoff=hours_ago(1))  # pending

    record = upsert_h2h(db, spain, portugal)
    db.commit()

    assert (record.team_a_wins, record.team_b_wins, record.draws) == (0, 0, 0)
    assert record.last_match_date is None
