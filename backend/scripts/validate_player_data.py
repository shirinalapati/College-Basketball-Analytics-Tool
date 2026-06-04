"""
Audit player cache/DB for common ingestion errors.
Exit code 1 if any critical issues remain.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ingest_sports_reference import CACHE_DIR, resolve_mpg_and_minutes

CRITICAL = []


def audit_player(p: dict, team_id: str) -> None:
    name = p.get("player_name", "?")
    g = max(int(p.get("games_played", 1)), 1)
    mpg = float(p.get("mpg", 0))
    mins = float(p.get("minutes", 0))
    ppg = float(p.get("ppg", 0))

    fixed_mpg, fixed_mins = resolve_mpg_and_minutes(mpg, g)
    if abs(fixed_mpg - mpg) > 0.5:
        CRITICAL.append(
            f"{team_id}/{name}: MPG {mpg} should be {fixed_mpg} (season minutes misread)"
        )

    if mins > 0 and abs(mins - mpg * g) > 3 and abs(mins - fixed_mins) > 3:
        CRITICAL.append(f"{team_id}/{name}: minutes {mins} inconsistent with mpg {mpg} x {g}")

    if mpg >= 12 and ppg <= 0 and mins >= 120:
        CRITICAL.append(f"{team_id}/{name}: {mpg} MPG but 0.0 PPG ({mins} min)")


def main() -> None:
    for path in sorted(CACHE_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        for p in data.get("players", []):
            audit_player(p, path.stem)

    print(f"Audited {len(list(CACHE_DIR.glob('*.json')))} team caches")
    if CRITICAL:
        print(f"CRITICAL issues: {len(CRITICAL)}")
        for msg in CRITICAL[:30]:
            print(" -", msg)
        if len(CRITICAL) > 30:
            print(f" ... and {len(CRITICAL) - 30} more")
        sys.exit(1)
    print("No critical player data issues found.")


if __name__ == "__main__":
    main()
