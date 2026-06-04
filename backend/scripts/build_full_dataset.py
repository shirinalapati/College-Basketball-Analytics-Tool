"""
Build 2025-26 dataset from Sports Reference cache only (real names + stats).
Run ingest_sports_reference.py first to populate backend/data/sr_cache/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT))

from generate_demo_data import SEASON_LABEL, SEASON_YEAR, generate_teams
from ingest_sports_reference import DATA_DIR, _load_cache, normalize_player_record
from models.class_year import add_projected_class_year
from models.shot_profile import enrich_player_shot_profile
from roster_corrections import apply_roster_corrections, load_roster_corrections
from roster_status import roster_status_manifest
from teams_universe import TEAMS_SPEC


def load_teams_from_sr_cache() -> tuple[pd.DataFrame, list[str]]:
    """Team efficiency stats from SR cache — must match player baseline source."""
    team_rows: list[dict] = []
    missing: list[str] = []
    fallback = generate_teams().set_index("team_id")

    for tid, _name, conf in TEAMS_SPEC:
        cached = _load_cache(tid)
        if cached and cached.get("team"):
            row = dict(cached["team"])
            row["conference"] = conf
            team_rows.append(row)
        elif tid in fallback.index:
            row = fallback.loc[tid].to_dict()
            row["data_source"] = row.get("data_source", "") + " · team stats fallback (no SR cache)"
            team_rows.append(row)
            missing.append(tid)
        else:
            missing.append(tid)

    return pd.DataFrame(team_rows), missing


def build() -> None:
    teams_df, team_missing = load_teams_from_sr_cache()
    all_players: list[dict] = []
    player_missing: list[str] = []

    for tid in teams_df["team_id"]:
        cached = _load_cache(tid)
        if cached and cached.get("players"):
            all_players.extend(
                normalize_player_record(p) for p in cached["players"]
            )
        else:
            player_missing.append(tid)

    all_players, correction_logs = apply_roster_corrections(all_players)
    for line in correction_logs:
        print(f"  roster: {line}")

    players_df = pd.DataFrame(all_players).drop_duplicates(subset=["player_id"])
    if players_df.empty:
        raise RuntimeError("No player data in cache. Run: python ingest_batches.py")

    if "class_year_source" not in players_df.columns:
        players_df["class_year"] = "Unknown"

    players_df = players_df[(players_df["mpg"] >= 10) | (players_df["minutes"] >= 250)]
    players_df = pd.DataFrame(
        [enrich_player_shot_profile(row.to_dict(), estimate_if_missing=True) for _, row in players_df.iterrows()]
    )
    players_df = add_projected_class_year(players_df)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    teams_df.to_csv(DATA_DIR / "teams_demo.csv", index=False)
    players_df.to_csv(DATA_DIR / "players_demo.csv", index=False)

    import_path = DATA_DIR / "shot_profile_import.csv"
    if import_path.exists():
        from merge_shot_profile_csv import merge_into_players  # noqa: PLC0415

        players_path = DATA_DIR / "players_demo.csv"
        merge_into_players(import_path, players_path)
        players_df = pd.read_csv(players_path)
        print(f"  Re-applied shot profile import ({import_path.name})")

    sr_teams = int(players_df["team_id"].nunique())
    corrections = load_roster_corrections()
    n_xfer = len(corrections.get("transfers", []))
    meta = {
        "label": "2026-27 ROSTERS · SR STATS",
        "description": (
            f"{sr_teams}/{len(teams_df)} teams. Player stats from 2025-26 Sports Reference; "
            f"rosters adjusted for {n_xfer} documented transfer-portal moves (2026-27) plus "
            f"manual roster_status.csv overrides."
        ),
        "season": SEASON_YEAR,
        "season_label": "2026-27",
        "stats_season_label": SEASON_LABEL,
        "teams_count": len(teams_df),
        "players_count": len(players_df),
        "teams_with_data": sr_teams,
        "sources": ["Sports Reference", "roster_status.csv"],
        **roster_status_manifest(),
    }
    with open(DATA_DIR / "data_manifest.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Built {len(teams_df)} teams, {len(players_df)} players from {sr_teams} SR caches")
    if team_missing:
        print(f"Note: {len(team_missing)} teams used fallback team stats (missing SR team cache)")
    if player_missing:
        print(f"Note: {len(player_missing)} teams missing player cache — re-run ingest")
        raise SystemExit(1)


if __name__ == "__main__":
    build()
