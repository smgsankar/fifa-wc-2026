"""Diagnostic: print an env-driven config value to confirm loading works.

Usage (from the backend directory): python scripts/check_env.py

Imports `config`, which loads variables via load_dotenv (backend/.env locally)
or, where no .env exists, straight from the process environment (e.g. Railway
service variables / secrets). It then logs RESULTS_SYNC_ENABLED so you can
verify the same code path resolves the value in both environments. Reads
nothing else and changes nothing.
"""

import logging

import common  # noqa: F401  (adds the backend dir to sys.path)

from config import RESULTS_SYNC_ENABLED

logger = logging.getLogger("check_env")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger.info(
        "RESULTS_SYNC_ENABLED = %s (loaded via config / load_dotenv)",
        RESULTS_SYNC_ENABLED,
    )


if __name__ == "__main__":
    main()
