"""Stage-aware live windows: knockouts stay live through extra time and pens."""

from datetime import datetime, timedelta, timezone

from conftest import hours_ago, hours_ahead

from main import effective_status
from models import Match


def match_with(stage: str, kickoff: datetime, status: str = "pending") -> Match:
    return Match(match_id=1, stage=stage, status=status, match_date=kickoff)


NOW = datetime.now(timezone.utc)


def test_pending_before_kickoff():
    assert effective_status(match_with("group", hours_ahead(1)), NOW) == "pending"


def test_completed_wins_over_clock():
    match = match_with("group", hours_ago(50), status="completed")
    assert effective_status(match, NOW) == "completed"


def test_group_match_past_two_hours_awaits_results():
    # 130 minutes after kickoff: a group game is over, a knockout may be in pens.
    kickoff = NOW.replace(tzinfo=None) - timedelta(minutes=130)
    assert effective_status(match_with("group", kickoff), NOW) == "awaiting_results"
    assert effective_status(match_with("round16", kickoff), NOW) == "live"
    assert effective_status(match_with("final", kickoff), NOW) == "live"


def test_knockout_match_past_live_window_awaits_results():
    kickoff = NOW.replace(tzinfo=None) - timedelta(minutes=180)
    assert effective_status(match_with("round16", kickoff), NOW) == "awaiting_results"
