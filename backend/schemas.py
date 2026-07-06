from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


def iso_z(dt: datetime) -> str:
    """Serialize a datetime as ISO 8601 UTC with a Z suffix."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class TeamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country_code: str
    logo_url: str | None = None
    # True for undecided knockout slots ("Winner SF 1"): the UI renders them
    # as placeholders and keeps them out of team filters.
    is_placeholder: bool = False


class SquadPlayer(BaseModel):
    player_id: int
    name: str
    position: str
    number: int


class FormEntry(BaseModel):
    match_date: str
    opponent: str
    result: str
    score: str


class TeamDetail(TeamSummary):
    head_coach: str | None = None
    squad: list[SquadPlayer] = []
    recent_form: list[FormEntry] = []


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_a_win_prob: float
    team_b_win_prob: float
    draw_prob: float
    confidence: float


class LastMatch(BaseModel):
    date: str
    result: str | None = None
    score: str | None = None


class H2HOut(BaseModel):
    team_a_wins: int
    team_b_wins: int
    draws: int
    last_match: LastMatch | None = None


class MatchBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    match_date: datetime
    stadium: str | None = None
    city: str | None = None
    stage: str
    status: str
    prediction: PredictionOut | None = None

    @field_serializer("match_date")
    def serialize_match_date(self, dt: datetime) -> str:
        return iso_z(dt)


class UpcomingMatch(MatchBase):
    team_a: TeamSummary
    team_b: TeamSummary


class MatchListItem(UpcomingMatch):
    actual_score_a: int | None = None
    actual_score_b: int | None = None
    # "regular" | "extra_time" | "penalties"; null when unknown. The actual
    # score includes extra time; the shootout score is penalty_score_*.
    decided_by: str | None = None
    penalty_score_a: int | None = None
    penalty_score_b: int | None = None
    prediction_correct: bool | None = None


class MatchDetail(MatchBase):
    team_a: TeamDetail
    team_b: TeamDetail
    h2h: H2HOut | None = None
    actual_score_a: int | None = None
    actual_score_b: int | None = None
    decided_by: str | None = None
    penalty_score_a: int | None = None
    penalty_score_b: int | None = None
    prediction_correct: bool | None = None


class StatsOut(BaseModel):
    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int
    accuracy: float
    precision: float
    recall: float
    last_updated: datetime

    @field_serializer("last_updated")
    def serialize_last_updated(self, dt: datetime) -> str:
        return iso_z(dt)


class UpcomingMatchesResponse(BaseModel):
    upcoming_matches: list[UpcomingMatch]


class AllMatchesResponse(BaseModel):
    all_matches: list[MatchListItem]


class MatchDetailResponse(BaseModel):
    match: MatchDetail


class StatsResponse(BaseModel):
    stats: StatsOut
