"""Map our fixtures to their football-data.org match ids.

Usage (from the backend directory): python scripts/map_external_ids.py

Pulls the competition's full fixture list, reconciles each match to ours by
team identity, and stores the football-data.org id in Match.external_id. Run
this once (and again if the fixture set changes, e.g. knockout pairings are
decided) before relying on scripts/sync_results.py, which polls by those ids.

Requires FOOTBALL_DATA_API_TOKEN to be set.
"""

import logging

import common  # noqa: F401  (adds the backend dir to sys.path)

from results_sync import map_external_ids


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    summary = map_external_ids()
    print(
        f"Fetched {summary['fetched']} fixture(s) from the API: "
        f"{summary['mapped']} newly mapped, {summary['unchanged']} already current, "
        f"{len(summary['unmatched'])} unmatched."
    )
    for label in summary["unmatched"]:
        print(f"  unmatched: {label}")


if __name__ == "__main__":
    main()
