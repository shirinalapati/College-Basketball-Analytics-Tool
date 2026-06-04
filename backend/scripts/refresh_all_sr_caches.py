"""
Re-fetch and rebuild all Sports Reference team caches with corrected parsers.
Usage: python refresh_all_sr_caches.py [--delay 8]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ingest_sports_reference import REQUEST_DELAY, ingest_team
from team_slugs import TEAM_SLUGS
from teams_universe import TEAMS_SPEC


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY)
    args = parser.parse_args()

    import ingest_sports_reference as ing

    ing.REQUEST_DELAY = args.delay

    ok, fail = 0, []
    for i, (tid, tname, conf) in enumerate(TEAMS_SPEC, 1):
        slug = TEAM_SLUGS.get(tid)
        if not slug:
            fail.append(tid)
            continue
        try:
            _, players = ingest_team(tid, tname, conf, slug, force_refresh=True)
            print(f"[{i}/{len(TEAMS_SPEC)}] ✓ {tname}: {len(players)} players")
            ok += 1
        except Exception as e:
            print(f"[{i}/{len(TEAMS_SPEC)}] ✗ {tname}: {e}")
            fail.append(tid)
            time.sleep(args.delay * 2)

    print(f"\nDone: {ok} refreshed, {len(fail)} failed")
    if fail:
        print("Failed:", ", ".join(fail))


if __name__ == "__main__":
    main()
