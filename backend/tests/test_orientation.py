"""Score orientation: mapping the feed's home/away onto our team_a/team_b."""

from models import Match, Team
from results_sync import _home_is_team_a, _oriented


def fixture(team_a_name: str, team_b_name: str) -> Match:
    match = Match(match_id=1, stage="group", status="pending")
    match.team_a = Team(id=1, name=team_a_name, country_code="AAA")
    match.team_b = Team(id=2, name=team_b_name, country_code="BBB")
    return match


def test_home_is_team_a():
    assert _home_is_team_a(fixture("Brazil", "Japan"), "Brazil") is True


def test_home_is_team_b():
    assert _home_is_team_a(fixture("Brazil", "Japan"), "Japan") is False


def test_alias_and_accents_resolve():
    match = fixture("South Korea", "Ivory Coast")
    assert _home_is_team_a(match, "Korea Republic") is True
    assert _home_is_team_a(match, "Côte d'Ivoire") is False


def test_unknown_home_team_is_none():
    assert _home_is_team_a(fixture("Brazil", "Japan"), "Atlantis") is None


def test_oriented_flips_scores_and_penalties():
    assert _oriented(True, 2, 1) == (2, 1)
    assert _oriented(False, 2, 1) == (1, 2)
