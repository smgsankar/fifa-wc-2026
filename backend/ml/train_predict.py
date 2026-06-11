"""Train the WC2026 match prediction model and write predictions.json.

Usage (from the backend directory):
    pip install -r ml/requirements.txt
    python ml/train_predict.py

Input (see mlprd.md):
  - seed_data/results.csv       completed matches 1872 to 2026-06-10, plus the
                                72 WC2026 fixture rows with score "NA"
  - seed_data/former_names.csv  historical team name renames

Trains a multinomial logistic regression on completed matches from 2006-01-01
onward. Features are point-in-time rolling stats (each team's previous 10
matches BEFORE the match being predicted) so there is no target leakage.

Output:
  - seed_data/predictions.json  all 72 predictions, consumed by
                                scripts/seed_predictions.py
  - ml/artifacts/model.pkl      trained sklearn pipeline (reference)
  - ml/artifacts/team_stats.json  final last-10 stats per team (transparency)
"""

import csv
import json
import pickle
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BACKEND_DIR = Path(__file__).resolve().parent.parent
SEED_DIR = BACKEND_DIR / "seed_data"
ARTIFACTS_DIR = BACKEND_DIR / "ml" / "artifacts"

ROLLING_WINDOW = 10
MIN_PRIOR_MATCHES = 10
TRAINING_START = date(2006, 1, 1)

# Target classes: 0 = away win (team_b), 1 = draw, 2 = home win (team_a)
AWAY_WIN, DRAW, HOME_WIN = 0, 1, 2


def load_csv(filename: str) -> list[dict]:
    path = SEED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required seed file missing: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_name_normalizer() -> "callable":
    """Map former team names (within their validity window) to current names.

    Mirrors scripts/preseed_kaggle.py (not imported: that module pulls in
    database/, which this script must not depend on).
    """
    renames = []
    for row in load_csv("former_names.csv"):
        renames.append(
            (
                row["former"],
                date.fromisoformat(row["start_date"]),
                date.fromisoformat(row["end_date"]),
                row["current"],
            )
        )

    def normalize(name: str, on: date) -> str:
        for former, start, end, current in renames:
            if name == former and start <= on <= end:
                return current
        return name

    return normalize


def load_dataset() -> tuple[list[dict], list[dict]]:
    """Returns (completed matches sorted by date, WC2026 fixture rows)."""
    normalize = build_name_normalizer()
    history, fixtures = [], []
    for row in load_csv("results.csv"):
        if row["home_score"] == "NA":
            fixtures.append(row)
        else:
            match_date = date.fromisoformat(row["date"])
            history.append(
                {
                    "date": match_date,
                    "home_team": normalize(row["home_team"], match_date),
                    "away_team": normalize(row["away_team"], match_date),
                    "home_score": int(row["home_score"]),
                    "away_score": int(row["away_score"]),
                    "neutral": row["neutral"].upper() == "TRUE",
                }
            )
    history.sort(key=lambda m: m["date"])
    return history, fixtures


def rolling_stats(results: list[tuple[int, int]]) -> dict:
    """Stats over the last ROLLING_WINDOW of a team's (goals_for, goals_against)."""
    window = results[-ROLLING_WINDOW:]
    n = len(window)
    wins = sum(1 for gf, ga in window if gf > ga)
    draws = sum(1 for gf, ga in window if gf == ga)
    return {
        "avg_goals_for": sum(gf for gf, _ in window) / n,
        "avg_goals_against": sum(ga for _, ga in window) / n,
        "win_rate": wins / n,
        "draw_rate": draws / n,
        "loss_rate": (n - wins - draws) / n,
    }


def match_features(stats_a: dict, stats_b: dict, home_advantage: int) -> list[float]:
    return [
        stats_a["avg_goals_for"],
        stats_a["avg_goals_against"],
        stats_a["win_rate"],
        stats_b["avg_goals_for"],
        stats_b["avg_goals_against"],
        stats_b["win_rate"],
        home_advantage,
    ]


def build_training_set(history: list[dict]) -> tuple[np.ndarray, np.ndarray, dict]:
    """Point-in-time training rows; returns (X, y, full per-team history).

    Each team's running history is updated only AFTER its match is emitted as
    a training row, so features never see the row's own result. Pre-2006
    matches contribute no rows but warm up the histories.
    """
    prior: dict[str, list[tuple[int, int]]] = {}
    X, y = [], []
    for m in history:
        home_prior = prior.setdefault(m["home_team"], [])
        away_prior = prior.setdefault(m["away_team"], [])
        if (
            m["date"] >= TRAINING_START
            and len(home_prior) >= MIN_PRIOR_MATCHES
            and len(away_prior) >= MIN_PRIOR_MATCHES
        ):
            X.append(
                match_features(
                    rolling_stats(home_prior),
                    rolling_stats(away_prior),
                    0 if m["neutral"] else 1,
                )
            )
            if m["home_score"] > m["away_score"]:
                y.append(HOME_WIN)
            elif m["home_score"] < m["away_score"]:
                y.append(AWAY_WIN)
            else:
                y.append(DRAW)
        home_prior.append((m["home_score"], m["away_score"]))
        away_prior.append((m["away_score"], m["home_score"]))
    return np.array(X), np.array(y), prior


def final_team_stats(prior: dict, fixtures: list[dict]) -> dict[str, dict]:
    """Last-10-overall stats for every team appearing in the fixtures."""
    teams = sorted(set(r["home_team"] for r in fixtures) | set(r["away_team"] for r in fixtures))
    thin = [t for t in teams if len(prior.get(t, [])) < MIN_PRIOR_MATCHES]
    if thin:
        raise ValueError(
            f"Fixture teams with <{MIN_PRIOR_MATCHES} historical matches "
            f"(name normalization gap?): {thin}"
        )
    return {t: rolling_stats(prior[t]) for t in teams}


def train(X: np.ndarray, y: np.ndarray):
    """Fit the model; prints holdout accuracy from a chronological 90/10 split."""
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42),
    )
    split = int(len(X) * 0.9)
    model.fit(X[:split], y[:split])
    holdout_acc = (model.predict(X[split:]) == y[split:]).mean()
    print(f"holdout accuracy (last 10% of {len(X)} rows): {holdout_acc:.3f}")
    model.fit(X, y)
    return model


def predict_fixtures(model, fixtures: list[dict], team_stats: dict) -> list[dict]:
    """Predictions for the 72 fixtures, match_id matching preseed_kaggle.py."""
    ordered = sorted(fixtures, key=lambda r: (r["date"], r["home_team"], r["away_team"]))
    X = np.array(
        [
            match_features(
                team_stats[r["home_team"]],
                team_stats[r["away_team"]],
                0 if r["neutral"].upper() == "TRUE" else 1,
            )
            for r in ordered
        ]
    )
    proba = model.predict_proba(X)
    col = {cls: i for i, cls in enumerate(model.classes_)}

    predictions = []
    for match_id, (row, p) in enumerate(zip(ordered, proba), start=1):
        # Round to 4dp, folding the residual into draw_prob so sums are exactly 1.0
        team_a_win = round(float(p[col[HOME_WIN]]), 4)
        team_b_win = round(float(p[col[AWAY_WIN]]), 4)
        draw = round(1.0 - team_a_win - team_b_win, 4)
        outcomes = {"team_a_wins": team_a_win, "draw": draw, "team_b_wins": team_b_win}
        predicted = max(outcomes, key=outcomes.get)
        predictions.append(
            {
                "match_id": match_id,
                "team_a": row["home_team"],
                "team_b": row["away_team"],
                "team_a_win_prob": team_a_win,
                "team_b_win_prob": team_b_win,
                "draw_prob": draw,
                "confidence": outcomes[predicted],
                "predicted_outcome": predicted,
            }
        )
    return predictions


def main() -> None:
    history, fixtures = load_dataset()
    print(f"dataset: {len(history)} completed matches, {len(fixtures)} WC2026 fixtures")

    X, y, prior = build_training_set(history)
    print(
        f"training rows: {len(X)} (from {TRAINING_START.isoformat()}), "
        f"class counts away/draw/home: {np.bincount(y).tolist()}"
    )

    team_stats = final_team_stats(prior, fixtures)
    model = train(X, y)
    predictions = predict_fixtures(model, fixtures, team_stats)

    output = {
        "predictions": predictions,
        "model_info": {
            "algorithm": "Logistic Regression",
            "training_data": f"International matches {TRAINING_START.year}-{history[-1]['date'].year}",
            "total_matches_used": len(X),
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
    predictions_path = SEED_DIR / "predictions.json"
    with open(predictions_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {predictions_path} ({len(predictions)} predictions)")

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    with open(ARTIFACTS_DIR / "model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(ARTIFACTS_DIR / "team_stats.json", "w", encoding="utf-8") as f:
        json.dump(team_stats, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {ARTIFACTS_DIR / 'model.pkl'} and team_stats.json")


if __name__ == "__main__":
    main()
