"""
Patch ORtg / DRtg / pace on cached sr_cache team JSON files.

Uses Sports Reference season-total_totals when --fetch is set (slow; respect rate limits).
Default: estimate from each team's four-factor rates so pool ranks differ (replace with --fetch later).

Usage:
  python scripts/patch_team_efficiency.py
  python scripts/patch_team_efficiency.py --fetch --delay 12
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ingest_sports_reference import (
    CACHE_DIR,
    configure_ingest,
    estimate_team_efficiency,
    fetch_html,
    parse_team_efficiency_from_html,
)
from team_slugs import TEAM_SLUGS
from teams_universe import TEAMS_SPEC

PLACEHOLDER = {108.0, 100.0, 68.0}


def needs_patch(team: dict) -> bool:
    return (
        float(team.get("offensive_rating", 108)) in PLACEHOLDER
        or float(team.get("defensive_rating", 100)) in PLACEHOLDER
        or float(team.get("pace", 68)) in PLACEHOLDER
    )


def patch_file(path: Path, eff: dict) -> None:
    payload = json.loads(path.read_text())
    payload["team"].update(eff)
    path.write_text(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Re-fetch SR pages for true ORtg/DRtg/pace")
    parser.add_argument("--delay", type=float, default=12.0)
    args = parser.parse_args()

    configure_ingest()
    updated = 0
    for tid, _name, _conf in TEAMS_SPEC:
        path = CACHE_DIR / f"{tid}.json"
        if not path.exists():
            continue
        team = json.loads(path.read_text())["team"]
        if not needs_patch(team):
            continue

        eff: dict = {}
        if args.fetch:
            slug = TEAM_SLUGS.get(tid)
            if slug:
                try:
                    html = fetch_html(slug)
                    eff = parse_team_efficiency_from_html(html)
                    time.sleep(args.delay)
                except Exception as e:
                    print(f"  fetch {tid}: {e}")
        if not eff:
            eff = estimate_team_efficiency(team)

        patch_file(path, eff)
        updated += 1
        print(f"  {tid}: ORtg {eff['offensive_rating']} DRtg {eff['defensive_rating']} Pace {eff['pace']}")

    print(f"Patched {updated} teams in {CACHE_DIR}")


if __name__ == "__main__":
    main()
