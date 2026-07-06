"""Run one results-sync pass from the command line.

Usage (from the backend directory): python scripts/sync_results.py

Mirrors one cycle of the in-process scheduler: polls football-data.org for the
fixtures awaiting a result (by their mapped external ids), records any that
have finished, resolves knockout placeholder slots whose teams are now
decided, and generates predictions for any round that has become due.
Requires FOOTBALL_DATA_API_TOKEN, and that scripts/map_external_ids.py has been
run first. The RESULTS_SYNC_ENABLED flag only gates the in-process scheduler,
not this CLI.
"""

import logging

import common  # noqa: F401  (adds the backend dir to sys.path)

from results_sync import resolve_knockout_teams, sync_results
from round_predictions import run_due_round_predictions


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    summary = sync_results()
    print(
        f"{summary['awaiting']} fixture(s) awaiting a result; "
        f"fetched {summary['fetched']} from the API, recorded {summary['updated']}."
    )
    if summary["unmapped"]:
        print(
            f"  {summary['unmapped']} kicked-off fixture(s) have no external_id "
            "— run scripts/map_external_ids.py."
        )
    for label in summary["unmatched"]:
        print(f"  unmatched: {label}")

    resolved = resolve_knockout_teams()
    if resolved["checked"]:
        print(
            f"knockout slots: {resolved['resolved']} resolved, "
            f"{resolved['undecided']} still undecided."
        )
    for label in resolved["unmatched"]:
        print(f"  unresolved: {label}")

    rounds = run_due_round_predictions()
    if rounds["predicted"]:
        print(
            f"predicted {rounds['predicted']} match(es) for: {', '.join(rounds['stages'])}"
        )


if __name__ == "__main__":
    main()
