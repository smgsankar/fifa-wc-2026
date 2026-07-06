"""Reconciling API knockout matches to placeholder fixtures by stage + kickoff."""

from datetime import datetime

from models import Match
from results_sync import _select_by_stage_kickoff


def fixture(match_id: int, stage: str, kickoff: str) -> Match:
    return Match(
        match_id=match_id,
        stage=stage,
        status="pending",
        match_date=datetime.fromisoformat(kickoff),
    )


FIXTURES = [
    fixture(101, "semifinal", "2026-07-14T19:00:00"),
    fixture(102, "semifinal", "2026-07-15T19:00:00"),
    fixture(104, "final", "2026-07-19T19:00:00"),
]


def api_match(stage: str, utc_date: str) -> dict:
    return {"stage": stage, "utcDate": utc_date}


def test_exact_kickoff_match():
    picked = _select_by_stage_kickoff(FIXTURES, api_match("SEMI_FINALS", "2026-07-14T19:00:00Z"))
    assert picked.match_id == 101


def test_same_day_fallback_for_shifted_kickoff():
    # Weather delays shift kickoffs; a lone same-stage fixture that day still maps.
    picked = _select_by_stage_kickoff(FIXTURES, api_match("FINAL", "2026-07-19T20:00:00Z"))
    assert picked.match_id == 104


def test_ambiguous_same_day_returns_none():
    fixtures = [
        fixture(97, "quarterfinal", "2026-07-11T17:00:00"),
        fixture(98, "quarterfinal", "2026-07-11T21:00:00"),
    ]
    assert _select_by_stage_kickoff(fixtures, api_match("QUARTER_FINALS", "2026-07-11T18:00:00Z")) is None


def test_unknown_stage_returns_none():
    assert _select_by_stage_kickoff(FIXTURES, api_match("PLAYOFFS", "2026-07-14T19:00:00Z")) is None
