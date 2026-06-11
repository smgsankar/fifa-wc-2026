"""Seed the full database from files in seed_data/.

Usage (from the backend directory): python scripts/seed.py
Runs all loaders in dependency order: teams -> matches -> predictions -> h2h.
Idempotent: safe to re-run after fixing a data file.
"""

from seed_h2h import seed_h2h
from seed_matches import seed_matches
from seed_predictions import seed_predictions
from seed_teams import seed_teams

if __name__ == "__main__":
    print("Seeding database from seed_data/ ...")
    seed_teams()
    seed_matches()
    seed_predictions()
    seed_h2h()
    print("Done.")
