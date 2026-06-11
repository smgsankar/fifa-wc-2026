# ML MODEL TRAINING & PREDICTIONS

**Project: World Cup 2026 Match Prediction Model**
**Input Data: Kaggle international football results (1872 to 2026-06-10; training filtered to 2006 onward)**
**Output: Pre-computed predictions for all 72 group stage matches**

## OBJECTIVE

Train a simple, fast ML model using historical international football matches to predict outcomes for the 72 World Cup 2026 group stage matches.

**Output Format:** JSON file consumable by backend API.

## DATA REQUIREMENTS

**Input:**

- `seed_data/results.csv` — Kaggle "International football results" dataset. Completed
  matches from 1872 through 2026-06-10 (the eve of the tournament), **plus** the 72
  World Cup 2026 group-stage fixture rows appended with `home_score`/`away_score` = `NA`
  (dates 2026-06-11 to 2026-06-27, tournament `FIFA World Cup`). There is no separate
  schedule file — the fixtures ARE the NA-score rows.
- `seed_data/former_names.csv` — `current,former,start_date,end_date`. Historical team
  names must be normalized to current names within their validity window (e.g.
  Zaïre → DR Congo), exactly as `scripts/preseed_kaggle.py` does, so historical stats
  join against fixture team names.

**results.csv columns:**
date, home_team, away_team, home_score, away_score, tournament, city, country, neutral

(`neutral` is TRUE/FALSE and drives the `home_advantage` feature.)

**match_id contract:** fixtures sorted by `(date, home_team, away_team)` and numbered
1-72 — must match `seed_matches()` in `scripts/preseed_kaggle.py`. `team_a` is the
fixture row's `home_team`, `team_b` is its `away_team`.

**Training filter:** completed matches from 2006-01-01 onward (earlier matches still
warm up each team's rolling history).

## FEATURE ENGINEERING (MINIMAL)

For each team, calculate these stats from recent matches (last 10 matches):
```python
# Team Statistics (from historical data)
team_stats = {
    "team_name": {
        "avg_goals_for": float,        # Avg goals scored
        "avg_goals_against": float,    # Avg goals conceded
        "win_rate": float,             # Wins / total matches
        "draw_rate": float,            # Draws / total matches
        "loss_rate": float,            # Losses / total matches
    }
}

# For each group stage match, create features:
features = {
    "team_a_avg_goals_for": float,
    "team_a_avg_goals_against": float,
    "team_a_win_rate": float,
    "team_b_avg_goals_for": float,
    "team_b_avg_goals_against": float,
    "team_b_win_rate": float,
    "home_advantage": 1 or 0,  # 1 if neutral=FALSE (team_a is truly at home), 0 if neutral=TRUE
                               # (9 of the 72 fixtures are host-nation home games: MEX/USA/CAN)
}

# Target variable
target = {
    0: "away_team_wins",
    1: "draw",
    2: "home_team_wins"
}
```

## MODEL
Algorithm: Logistic Regression (multiclass, 3 outcomes)
Why: Fast, interpretable, highly competitive for match prediction
```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    solver='lbfgs',   # multinomial by default for multiclass; the multi_class
    max_iter=1000,    # kwarg is removed in current scikit-learn
    random_state=42
)

model.fit(X_train, y_train)
```

## PREDICTIONS OUTPUT FORMAT

Generate predictions for all 72 World Cup matches and output as predictions.json:

```json
{
  "predictions": [
    {
      "match_id": 1,
      "team_a": "Argentina",
      "team_b": "Paraguay",
      "team_a_win_prob": 0.65,
      "team_b_win_prob": 0.20,
      "draw_prob": 0.15,
      "confidence": 0.72,
      "predicted_outcome": "team_a_wins"
    },
    {
      "match_id": 2,
      "team_a": "Argentina",
      "team_b": "Peru",
      "team_a_win_prob": 0.72,
      "team_b_win_prob": 0.15,
      "draw_prob": 0.13,
      "confidence": 0.78,
      "predicted_outcome": "team_a_wins"
    }
  ],
  "model_info": {
    "algorithm": "Logistic Regression",
    "training_data": "International matches 2006-2026",
    "total_matches_used": 18000,
    "generated_at": "2026-06-12T10:30:00Z"
  }
}
```

Confidence: Max of the three probabilities

## TECHNICAL IMPLEMENTATION
**Language:** Python
**Libraries:** scikit-learn, numpy (CSV loading via stdlib csv, matching the seed scripts)
```python
# Pseudocode workflow
from sklearn.linear_model import LogisticRegression
import json

# 1. Load data: split results.csv into completed history and the 72
#    NA-score fixture rows; normalize names via former_names.csv
history, fixtures = load_dataset('seed_data/results.csv', 'seed_data/former_names.csv')

# 2. Calculate rolling team stats (point-in-time, no leakage)
team_stats = calculate_team_statistics(history)

# 3. Engineer features for training (matches from 2006-01-01 onward)
X_train, y_train = engineer_features_historical(history)

# 4. Train model
model = LogisticRegression(solver='lbfgs')
model.fit(X_train, y_train)

# 5. Generate features for World Cup matches
X_wc = engineer_features_worldcup(fixtures, team_stats)

# 6. Predict probabilities
predictions_proba = model.predict_proba(X_wc)

# 7. Format and save as JSON
output = format_predictions(schedule, predictions_proba)
with open('predictions.json', 'w') as f:
    json.dump(output, f)
```

## DELIVERABLES

✅ predictions.json - All 72 match predictions (for backend to consume)
✅ model.pkl - Trained model file (optional, for reference)
✅ team_stats.json - Team statistics used (optional, for transparency)


## SUCCESS CRITERIA

✅ All 72 matches have predictions
✅ Probabilities sum to 1.0 for each match
✅ JSON format matches backend API contract exactly
✅ Model trains in <5 mins
✅ Ready for backend to consume


## INTEGRATION WITH BACKEND

Finally,
- Load predictions.json
- Insert into PostgreSQL predictions table

