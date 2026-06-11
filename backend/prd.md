# BACKEND (FastAPI + Python + PostgreSQL)

**Project: World Cup 2026 Prediction API**
**Deployment: Railway**
**Tech Stack: FastAPI, Python 3.10+, PostgreSQL, SQLAlchemy, Pydantic**


## Scope

Build a REST API that serves match data, predictions, team data, and model performance stats. Predictions are pre-computed and stored in PostgreSQL database.

## Features

### Match Data Management
- Store all 64 World Cup 2026 matches
- Track match status (pending/completed/live)
- Store actual scores for completed matches
- Link matches to predictions

### Team Data Management
- Store 32 World Cup teams with metadata
- Store full squad rosters (player name, position, number)
- Store recent form (last 5 matches: opponent, result, score)
- Store team logos/country codes

### Head-to-Head History
- Store h2h records between team pairs
- Track: wins, draws, losses, last match date
- Calculate head-to-head stats on demand

### Predictions Storage
- Store pre-computed predictions for all 64 matches
- Include: win probabilities, draw probability, confidence score
- Link predictions to matches

### Model Performance Stats
- Calculate global: accuracy, precision, recall
- Track: total predictions, correct predictions
- Update stats as match results come in


## DATABASE SCHEMA

```python
# SQLAlchemy Models (ORM)

class Team(Base):
    __tablename__ = "teams"
    
    id: int (PK)
    name: str (unique)
    country_code: str
    logo_url: str (nullable)
    squad: JSON (array of {player_id, name, position, number})
    created_at: datetime
    updated_at: datetime

class Match(Base):
    __tablename__ = "matches"
    
    id: int (PK)
    match_id: int (unique)
    team_a_id: int (FK → Team)
    team_b_id: int (FK → Team)
    match_date: datetime
    stage: str (group/round16/quarterfinal/semifinal/final)
    status: str (pending/completed/live)
    actual_score_a: int (nullable, for completed matches)
    actual_score_b: int (nullable, for completed matches)
    prediction_id: int (FK → Prediction)
    created_at: datetime
    updated_at: datetime

class Prediction(Base):
    __tablename__ = "predictions"
    
    id: int (PK)
    match_id: int (FK → Match)
    team_a_win_prob: float (0-1)
    team_b_win_prob: float (0-1)
    draw_prob: float (0-1)
    confidence: float (0-1)
    is_correct: bool (nullable, calculated after match completes)
    created_at: datetime
    updated_at: datetime

class H2H(Base):
    __tablename__ = "h2h"
    
    id: int (PK)
    team_a_id: int (FK → Team)
    team_b_id: int (FK → Team)
    team_a_wins: int
    team_b_wins: int
    draws: int
    last_match_date: datetime (nullable)
    created_at: datetime
    updated_at: datetime

class ModelStats(Base):
    __tablename__ = "model_stats"
    
    id: int (PK)
    total_predictions: int
    correct_predictions: int
    accuracy: float
    precision: float
    recall: float
    updated_at: datetime
```

## API ENDPOINTS

**BASE_URL: https://your-backend.railway.app**

### GET /api/matches/upcoming
Get next upcoming match(es).

**Response:**
```json
{
  "upcoming_matches": [
    {
      "match_id": 1,
      "team_a": {
        "id": 1,
        "name": "Argentina",
        "country_code": "ARG",
        "logo_url": "https://..."
      },
      "team_b": {
        "id": 2,
        "name": "France",
        "country_code": "FRA",
        "logo_url": "https://..."
      },
      "match_date": "2026-06-12T12:30:00Z",
      "stage": "group",
      "status": "pending",
      "prediction": {
        "team_a_win_prob": 0.65,
        "team_b_win_prob": 0.25,
        "draw_prob": 0.10,
        "confidence": 0.78
      }
    }
  ]
}
```

### GET /api/matches/next-4
Get next 4 upcoming matches (1 primary + 3 secondary).

**Response: Same format as /upcoming, but returns only next 4.**

### GET /api/matches/all
Get all 64 World Cup matches (past, present, future).
Query Params:

status (optional): "pending" | "completed" | all
team_id (optional): Filter by team
stage (optional): "group" | "round16" | etc.


**Response:**
```json
{
  "all_matches": [
    {
      "match_id": 1,
      "team_a": { ... },
      "team_b": { ... },
      "match_date": "2026-06-12T12:30:00Z",
      "stage": "group",
      "status": "pending",
      "actual_score_a": null,
      "actual_score_b": null,
      "prediction": { ... },
      "prediction_correct": null
    },
    {
      "match_id": 2,
      "team_a": { ... },
      "team_b": { ... },
      "match_date": "2026-06-12T15:00:00Z",
      "stage": "group",
      "status": "completed",
      "actual_score_a": 2,
      "actual_score_b": 1,
      "prediction": { "team_a_win_prob": 0.60, ... },
      "prediction_correct": true
    }
  ]
}
```

### GET /api/matches/:match_id
Get detailed match info including team data, h2h, recent form, squad.

**Response:**
```json
{
  "match": {
    "match_id": 1,
    "team_a": {
      "id": 1,
      "name": "Argentina",
      "country_code": "ARG",
      "logo_url": "https://...",
      "squad": [
        {
          "player_id": 101,
          "name": "Lionel Messi",
          "position": "F",
          "number": 10
        },
        {
          "player_id": 102,
          "name": "Cristian Romero",
          "position": "D",
          "number": 3
        }
      ],
      "recent_form": [
        {
          "match_date": "2026-06-08",
          "opponent": "Brazil",
          "result": "W",
          "score": "3-0"
        },
        {
          "match_date": "2026-06-05",
          "opponent": "Chile",
          "result": "W",
          "score": "2-1"
        },
        {
          "match_date": "2026-06-02",
          "opponent": "Paraguay",
          "result": "D",
          "score": "1-1"
        },
        {
          "match_date": "2026-05-30",
          "opponent": "Uruguay",
          "result": "L",
          "score": "0-2"
        },
        {
          "match_date": "2026-05-27",
          "opponent": "Colombia",
          "result": "W",
          "score": "2-0"
        }
      ]
    },
    "team_b": { ... (same structure) },
    "h2h": {
      "team_a_wins": 3,
      "team_b_wins": 2,
      "draws": 1,
      "last_match": {
        "date": "2024-03-15",
        "result": "D",
        "score": "1-1"
      }
    },
    "match_date": "2026-06-12T12:30:00Z",
    "stage": "group",
    "status": "pending",
    "actual_score_a": null,
    "actual_score_b": null,
    "prediction": {
      "team_a_win_prob": 0.65,
      "team_b_win_prob": 0.25,
      "draw_prob": 0.10,
      "confidence": 0.78
    },
    "prediction_correct": null
  }
}
```

### GET /api/model/stats
Get global model performance stats.

**Response:**
```json
{
  "stats": {
    "total_predictions": 45,
    "correct_predictions": 26,
    "incorrect_predictions": 19,
    "accuracy": 0.5777,
    "precision": 0.62,
    "recall": 0.55,
    "last_updated": "2026-06-12T14:30:00Z"
  }
}
```

## INPUT DATA REQUIREMENTS
You will provide (as CSV or JSON):

### matches.csv
match_id,team_a_id,team_b_id,match_date,stage
1,1,2,2026-06-12T12:30:00Z,group
2,3,4,2026-06-12T15:00:00Z,group
...

### teams.csv
team_id,name,country_code,logo_url
1,Argentina,ARG,https://...
2,France,FRA,https://...
...

### squad_data.json
```json
{
  "1": [
    {"player_id": 101, "name": "Messi", "position": "F", "number": 10},
    {"player_id": 102, "name": "Romero", "position": "D", "number": 3}
  ],
  "2": [...]
}
```

### recent_form.json
```json
{
  "1": [
    {"match_date": "2026-06-08", "opponent": "Brazil", "result": "W", "score": "3-0"}
  ]
}
```

### h2h_data.json
```json
{
  "1_2": {
    "team_a_wins": 3,
    "team_b_wins": 2,
    "draws": 1,
    "last_match_date": "2024-03-15"
  }
}
```

### predictions.json
```json
{
  "1": {
    "team_a_win_prob": 0.65,
    "team_b_win_prob": 0.25,
    "draw_prob": 0.10,
    "confidence": 0.78
  }
}
```

## TECHNICAL REQUIREMENTS

### Framework & Libraries
FastAPI (async REST API)
SQLAlchemy (ORM)
Pydantic (request/response validation)
psycopg2 or asyncpg (PostgreSQL driver)
python-dotenv (environment variables)

### Project Structure
backend/
├── main.py (FastAPI app + route handlers)
├── models.py (SQLAlchemy ORM models)
├── schemas.py (Pydantic request/response schemas)
├── database.py (Database connection & setup)
├── config.py (Configuration from env variables)
├── requirements.txt
├── .env (DATABASE_URL, etc.)
└── seed_data/ (CSV/JSON files for initial data load)

### Database Setup

PostgreSQL on Railway (connection via DATABASE_URL env var)
SQLAlchemy create_all() to initialize tables
Seed data from CSV/JSON files on startup

### CORS

Enable CORS for frontend (Cloudflare Pages origin)
Allow all origins for now: origins = ["*"]

### Environment Variables
DATABASE_URL=postgresql://user:password@railway...
PORT=8000

### Error Handling
```python
- 404 for missing matches
- 400 for bad requests
- 500 for server errors
- Return JSON error responses: {"error": "message"}
```

## DEPLOYMENT

### Railway Setup
- Create Railway project
- Add PostgreSQL service
- Add Python service (pointing to this repo)
- Set DATABASE_URL env var from PostgreSQL service
- Deploy

### API URL
**https://your-project.railway.app**

## DELIVERABLES

✅ FastAPI application with all 5 endpoints working
✅ PostgreSQL database schema created (tables, relationships)
✅ SQLAlchemy models for all tables
✅ Pydantic schemas for request/response validation
✅ Data seeding script (loads CSV/JSON into database)
✅ Deployed to Railway with public URL
✅ CORS enabled for frontend
✅ README with:

- How to run locally
- How to deploy to Railway
- API documentation (endpoint specs)
- Environment setup instructions

## SUCCESS CRITERIA

✅ All 5 endpoints return correct JSON format
✅ Can hit /api/matches/upcoming → get next match with prediction
✅ Can hit /api/matches/:match_id → get detailed match info
✅ Can hit /api/matches/all → get all 64 matches
✅ Can hit /api/model/stats → get accuracy/precision/recall
✅ Database has all data seeded correctly
✅ Deployed to Railway and publicly accessible
✅ CORS working (frontend can call API)

## NOTES

- Predictions are static (not generated on-demand)
- Model stats are recalculated when match results are added
- All timestamps in ISO 8601 format with Z (UTC)
- Confidence score is a single float (overall model confidence for that prediction)
- Recent form is last 5 matches (hardcoded in data)
