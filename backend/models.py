from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Team(TimestampMixin, Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    country_code: Mapped[str] = mapped_column(String, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    squad: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    recent_form: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)


class Match(TimestampMixin, Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    team_a_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team_b_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    actual_score_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_score_b: Mapped[int | None] = mapped_column(Integer, nullable=True)

    team_a: Mapped[Team] = relationship(foreign_keys=[team_a_id])
    team_b: Mapped[Team] = relationship(foreign_keys=[team_b_id])
    prediction: Mapped["Prediction | None"] = relationship(
        back_populates="match", uselist=False
    )


class Prediction(TimestampMixin, Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.match_id"), unique=True, nullable=False
    )
    team_a_win_prob: Mapped[float] = mapped_column(Float, nullable=False)
    team_b_win_prob: Mapped[float] = mapped_column(Float, nullable=False)
    draw_prob: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    match: Mapped[Match] = relationship(back_populates="prediction")


class H2H(TimestampMixin, Base):
    __tablename__ = "h2h"
    __table_args__ = (UniqueConstraint("team_a_id", "team_b_id", name="uq_h2h_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_a_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team_b_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team_a_wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    team_b_wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    draws: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_match_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class HistoricalResult(Base):
    """Completed international matches (Kaggle dataset), used to derive
    h2h records and recent form. Team names are normalized to current names."""

    __tablename__ = "historical_results"
    __table_args__ = (
        Index("ix_historical_home_date", "home_team", "match_date"),
        Index("ix_historical_away_date", "away_team", "match_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    home_team: Mapped[str] = mapped_column(String, nullable=False)
    away_team: Mapped[str] = mapped_column(String, nullable=False)
    home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    tournament: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    neutral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ModelStats(Base):
    __tablename__ = "model_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_predictions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_predictions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    precision: Mapped[float] = mapped_column("precision", Float, nullable=False, default=0.0)
    recall: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
