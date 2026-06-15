"""Run one results-sync pass from the command line.

Usage (from the backend directory): python scripts/sync_results.py

Polls football-data.org for the fixtures awaiting a result (by their mapped
external ids), records any that have finished, and recomputes model stats.
Requires FOOTBALL_DATA_API_TOKEN, and that scripts/map_external_ids.py has been
run first. The RESULTS_SYNC_ENABLED flag only gates the in-process scheduler,
not this CLI.
"""

import logging

import common  # noqa: F401  (adds the backend dir to sys.path)

from results_sync import sync_results


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


if __name__ == "__main__":
    main()
