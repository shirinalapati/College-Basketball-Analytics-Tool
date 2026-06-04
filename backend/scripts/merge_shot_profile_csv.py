"""
Merge optional shot-profile columns from CSV into players_demo.csv.

CSV must include player_id plus any shot_profile columns (see models/shot_profile.py).
Set shot_profile_source to tracking, official, synergy, sports_reference, or hoop_explorer
for rim formulas to use tracked rim data.

Usage:
  python scripts/merge_shot_profile_csv.py backend/data/shot_profile_import.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.shot_profile import SHOT_PROFILE_COLUMNS

PLAYERS_PATH = ROOT / "data" / "players_demo.csv"


def merge_into_players(import_path: Path, players_path: Path = PLAYERS_PATH) -> int:
    players = pd.read_csv(players_path).set_index("player_id")
    incoming = pd.read_csv(import_path)
    if "player_id" not in incoming.columns:
        raise SystemExit("import.csv must include player_id")
    incoming = incoming.drop_duplicates(subset=["player_id"]).set_index("player_id")
    incoming = incoming.loc[incoming.index.intersection(players.index)]

    for col in SHOT_PROFILE_COLUMNS:
        if col in incoming.columns:
            players.loc[incoming.index, col] = incoming[col]

    players.reset_index().to_csv(players_path, index=False)
    merged = players.reset_index()
    if "shot_profile_source" in merged.columns:
        return int(merged["shot_profile_source"].notna().sum())
    return 0


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: merge_shot_profile_csv.py <import.csv>")
        raise SystemExit(1)
    import_path = Path(sys.argv[1])
    if not import_path.exists():
        raise SystemExit(f"Not found: {import_path}")
    if not PLAYERS_PATH.exists():
        raise SystemExit(f"Run build_full_dataset first: {PLAYERS_PATH}")

    n = merge_into_players(import_path)
    print(f"Merged shot profile into {PLAYERS_PATH} ({n} rows with shot_profile_source)")


if __name__ == "__main__":
    main()
