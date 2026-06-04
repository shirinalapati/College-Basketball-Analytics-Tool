"""
Normalize MPG/minutes in all sr_cache JSON files.
Fixes rows where Sports Reference season total minutes were stored as per-game MPG.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ingest_sports_reference import CACHE_DIR, normalize_player_record

def main() -> None:
    fixed = 0
    for path in sorted(CACHE_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        players = data.get("players", [])
        new_players = []
        for p in players:
            before_mpg = p.get("mpg")
            after = normalize_player_record(p)
            if after.get("mpg") != before_mpg:
                fixed += 1
            new_players.append(after)
        data["players"] = new_players
        path.write_text(json.dumps(data, indent=2))
    print(f"Repaired cache files in {CACHE_DIR}; {fixed} player MPG rows corrected")


if __name__ == "__main__":
    main()
