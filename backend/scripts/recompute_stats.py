"""Recompute prediction correctness and global model stats.

Usage (from the backend directory): python scripts/recompute_stats.py

For every completed match with a prediction, marks the prediction correct if
the highest-probability outcome (team A win / draw / team B win) matches the
actual result, then upserts the single model_stats row. Precision and recall
are macro-averaged over the three outcome classes.

Run this after recording match results (not needed before the tournament).
"""

import common  # noqa: F401  (adds the backend dir to sys.path)

from database import Base, SessionLocal, engine
from models import Match, ModelStats, Prediction

CLASSES = ("team_a", "draw", "team_b")


def predicted_outcome(p: Prediction) -> str:
    probs = {"team_a": p.team_a_win_prob, "draw": p.draw_prob, "team_b": p.team_b_win_prob}
    return max(probs, key=probs.get)


def actual_outcome(m: Match) -> str:
    if m.actual_score_a > m.actual_score_b:
        return "team_a"
    if m.actual_score_a < m.actual_score_b:
        return "team_b"
    return "draw"


def macro_precision_recall(pairs: list[tuple[str, str]]) -> tuple[float, float]:
    """pairs: (predicted, actual) per completed match."""
    precisions, recalls = [], []
    for cls in CLASSES:
        tp = sum(1 for pred, act in pairs if pred == cls and act == cls)
        fp = sum(1 for pred, act in pairs if pred == cls and act != cls)
        fn = sum(1 for pred, act in pairs if pred != cls and act == cls)
        if tp + fp:
            precisions.append(tp / (tp + fp))
        if tp + fn:
            recalls.append(tp / (tp + fn))
    precision = sum(precisions) / len(precisions) if precisions else 0.0
    recall = sum(recalls) / len(recalls) if recalls else 0.0
    return precision, recall


def recompute_stats() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        completed = (
            db.query(Match, Prediction)
            .join(Prediction, Prediction.match_id == Match.match_id)
            .filter(
                Match.status == "completed",
                Match.actual_score_a.isnot(None),
                Match.actual_score_b.isnot(None),
            )
            .all()
        )

        pairs = []
        for match, prediction in completed:
            pred, act = predicted_outcome(prediction), actual_outcome(match)
            prediction.is_correct = pred == act
            pairs.append((pred, act))

        total = db.query(Prediction).count()
        correct = sum(1 for pred, act in pairs if pred == act)
        accuracy = correct / len(pairs) if pairs else 0.0
        precision, recall = macro_precision_recall(pairs)

        stats = db.query(ModelStats).first()
        if stats is None:
            stats = ModelStats()
            db.add(stats)
        stats.total_predictions = total
        stats.correct_predictions = correct
        stats.accuracy = accuracy
        stats.precision = precision
        stats.recall = recall
        db.commit()

        print(
            f"model_stats updated: {len(pairs)} completed matches scored, "
            f"{correct} correct, accuracy={accuracy:.4f}, "
            f"precision={precision:.4f}, recall={recall:.4f}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    recompute_stats()
