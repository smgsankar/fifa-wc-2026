"""End-to-end predict_stage on synthetic history, and point-in-time loading."""

from datetime import date, datetime, timedelta, timezone

from conftest import add_history, hours_ago, hours_ahead, make_match, make_team

from models import Prediction
from round_predictions import _load_history, predict_stage

TEAMS = ["Alpha", "Beta", "Gamma", "Delta"]
# Round-robin pairings, repeated with a rotating result pattern so all three
# outcome classes (home win / draw / away win) appear in training.
PAIRINGS = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
SCORES = [(2, 0), (1, 1), (0, 1)]


def seed_synthetic_history(db, rounds: int = 15) -> None:
    on = date(2006, 1, 7)
    i = 0
    for _ in range(rounds):
        for home, away in PAIRINGS:
            score = SCORES[i % len(SCORES)]
            add_history(db, TEAMS[home], TEAMS[away], score[0], score[1], on)
            on += timedelta(days=7)
            i += 1


def test_predict_stage_writes_normalized_predictions(db):
    seed_synthetic_history(db)
    alpha = make_team(db, 1, "Alpha")
    beta = make_team(db, 2, "Beta")
    fixture = make_match(db, 73, alpha, beta, stage="round32", kickoff=hours_ahead(24))

    written = predict_stage(db, [fixture], datetime.now(timezone.utc))
    assert written == 1

    prediction = db.query(Prediction).filter(Prediction.match_id == 73).one()
    probs = (prediction.team_a_win_prob, prediction.draw_prob, prediction.team_b_win_prob)
    assert all(0.0 <= p <= 1.0 for p in probs)
    assert abs(sum(probs) - 1.0) < 1e-6
    assert prediction.confidence == max(probs)


def test_load_history_respects_cutoff(db):
    alpha = make_team(db, 1, "Alpha")
    beta = make_team(db, 2, "Beta")
    add_history(db, "Alpha", "Beta", 1, 0, date(2020, 3, 1))
    make_match(db, 1, alpha, beta, stage="group", kickoff=hours_ago(72), score=(2, 1))
    make_match(db, 2, beta, alpha, stage="group", kickoff=hours_ago(2), score=(0, 3))
    make_match(db, 3, alpha, beta, stage="round32", kickoff=hours_ahead(24))  # pending

    cutoff = hours_ago(24).replace(tzinfo=timezone.utc)
    history = _load_history(db, cutoff)

    # Historical row + the WC match completed before the cutoff; the more
    # recent completed match and the pending fixture are excluded.
    assert len(history) == 2
    assert history[-1]["home_team"] == "Alpha"
    assert history[-1]["home_score"] == 2
