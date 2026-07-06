"""When rounds become due for prediction, and with which point-in-time cutoff."""

from datetime import timezone

import pytest

import round_predictions
from conftest import hours_ago, hours_ahead, make_match, make_team


@pytest.fixture()
def capture(monkeypatch):
    """Stub out training and stats; record (stage, cutoff, match_ids) per call."""
    calls = []

    def fake_predict_stage(db, matches, cutoff):
        calls.append((matches[0].stage, cutoff, [m.match_id for m in matches]))
        return len(matches)

    monkeypatch.setattr(round_predictions, "predict_stage", fake_predict_stage)
    monkeypatch.setattr(round_predictions, "recompute_stats", lambda: None)
    return calls


def seed_group_and_round32(db, *, group_complete=True, placeholders_in_r32=False):
    """Returns the round32 first kickoff (naive UTC, as stored)."""
    a = make_team(db, 1, "Alpha")
    b = make_team(db, 2, "Beta")
    c = make_team(db, 3, "Gamma")
    d = make_team(db, 4, "Delta")
    make_match(db, 1, a, b, stage="group", kickoff=hours_ago(96), score=(2, 0))
    make_match(
        db, 2, c, d, stage="group", kickoff=hours_ago(72),
        score=(1, 1) if group_complete else None,
    )
    if placeholders_in_r32:
        c = make_team(db, 1001, "Winner Group X", placeholder=True)
    first_kickoff = hours_ago(24)
    make_match(db, 73, a, c, stage="round32", kickoff=first_kickoff)
    make_match(db, 74, b, d, stage="round32", kickoff=hours_ago(20))
    return first_kickoff


def test_round_predicted_when_previous_round_completes(db, capture):
    first_kickoff = seed_group_and_round32(db)
    summary = round_predictions.run_due_round_predictions(db)

    assert summary == {"stages": ["round32"], "predicted": 2}
    stage, cutoff, match_ids = capture[0]
    assert stage == "round32"
    assert match_ids == [73, 74]
    # Point-in-time: the round kicked off in the past, so the cutoff is its
    # first kickoff — not now.
    assert cutoff == first_kickoff.replace(tzinfo=timezone.utc)


def test_cutoff_is_now_for_future_rounds(db, capture):
    a = make_team(db, 1, "Alpha")
    b = make_team(db, 2, "Beta")
    make_match(db, 1, a, b, stage="group", kickoff=hours_ago(96), score=(2, 0))
    make_match(db, 73, a, b, stage="round32", kickoff=hours_ahead(48))

    round_predictions.run_due_round_predictions(db)
    _, cutoff, _ = capture[0]
    assert cutoff < hours_ahead(0.1).replace(tzinfo=timezone.utc)  # ~now, not kickoff


def test_not_due_while_previous_round_unfinished(db, capture):
    seed_group_and_round32(db, group_complete=False)
    summary = round_predictions.run_due_round_predictions(db)
    assert summary == {"stages": [], "predicted": 0}
    assert capture == []


def test_not_due_with_undecided_teams(db, capture):
    seed_group_and_round32(db, placeholders_in_r32=True)
    summary = round_predictions.run_due_round_predictions(db)
    assert summary == {"stages": [], "predicted": 0}
    assert capture == []


def test_already_predicted_round_is_skipped(db, capture, monkeypatch):
    from models import Prediction

    seed_group_and_round32(db)
    for match_id in (73, 74):
        db.add(
            Prediction(
                match_id=match_id,
                team_a_win_prob=0.5,
                team_b_win_prob=0.3,
                draw_prob=0.2,
                confidence=0.5,
            )
        )
    db.commit()

    summary = round_predictions.run_due_round_predictions(db)
    assert summary == {"stages": [], "predicted": 0}
    assert capture == []
