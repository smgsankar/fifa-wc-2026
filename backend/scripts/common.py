"""Shared helpers for seed scripts.

Each script is runnable standalone from the backend directory:
    python scripts/preseed_kaggle.py
"""

import csv
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
SEED_DIR = BACKEND_DIR / "seed_data"

sys.path.insert(0, str(BACKEND_DIR))


def load_csv(filename: str) -> list[dict]:
    path = SEED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required seed file missing: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
