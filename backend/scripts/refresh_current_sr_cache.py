#!/usr/bin/env python3
"""Re-fetch 2025-26 SR cache so per-game stat fields exist for YoY calibration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ingest_sports_reference import REQUEST_DELAY, configure_ingest, ingest_team  # noqa: E402
from team_slugs import TEAM_SLUGS  # noqa: E402
from teams_universe import TEAMS_SPEC  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=8.0)
    args = parser.parse_args()

    import ingest_sports_reference as ing

    configure_ingest(sr_year=2026)
    ing.REQUEST_DELAY = args.delay
    for tid, tname, conf in TEAMS_SPEC:
        slug = TEAM_SLUGS.get(tid)
        if not slug:
            continue
        try:
            _, pl = ingest_team(tid, tname, conf, slug, force_refresh=True)
            print(f"  ✓ {tname}: {len(pl)} players")
        except Exception as e:
            print(f"  ✗ {tname}: {e}")
    print("Done.")


if __name__ == "__main__":
    main()
