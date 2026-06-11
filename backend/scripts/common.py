"""Shared helpers for seed scripts.

Each script is runnable standalone from the backend directory:
    python scripts/seed_teams.py
"""

import csv
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
SEED_DIR = BACKEND_DIR / "seed_data"

sys.path.insert(0, str(BACKEND_DIR))

VALID_STAGES = {"group", "round16", "quarterfinal", "semifinal", "final"}
VALID_RESULTS = {"W", "D", "L"}


def load_csv(filename: str) -> list[dict]:
    path = SEED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required seed file missing: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(filename: str, required: bool = True) -> dict | None:
    path = SEED_DIR / filename
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required seed file missing: {path}")
        print(f"  [skip] optional file not found: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def report(label: str, created: int, updated: int, errors: list[str]) -> None:
    print(f"{label}: {created} created, {updated} updated, {len(errors)} errors")
    for err in errors:
        print(f"  [error] {err}")
