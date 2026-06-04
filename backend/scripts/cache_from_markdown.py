"""
Build sr_cache JSON from Sports Reference page content (markdown from WebFetch).
Usage: python cache_from_markdown.py <team_id> <markdown_file>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_demo_data import SEASON_YEAR, _team_profile
from ingest_sports_reference import (
    CACHE_DIR,
    MIN_MPG,
    MIN_MINUTES,
    class_from_roster,
    parse_team_row,
    player_rows_from_df,
    resolve_mpg_and_minutes,
)
from team_slugs import TEAM_SLUGS
from teams_universe import TEAMS_SPEC

TEAM_MAP = {t[0]: (t[1], t[2]) for t in TEAMS_SPEC}


def _html_like(md: str) -> str:
    """Wrap markdown tables so pandas read_html can parse pipe tables."""
    return md.replace("| Roster Table |", "<table>").replace("| Per Game Table |", "<table>")


def _pick_best_stat_row(candidates: list[dict]) -> dict:
    """Prefer per-game table rows over season-totals rows for the same player."""

    def rank(r: dict) -> tuple:
        mp = float(r["MP"])
        g = max(float(r["G"]), 1)
        pts = float(r.get("PTS", 0) or 0)
        has_decimal = abs(mp - round(mp)) >= 0.05
        mpg_est = mp if has_decimal and mp <= 42 else mp / g
        if has_decimal and 0 < mp <= 42 and pts > 0:
            return (0, -mpg_est)
        if has_decimal and 0 < mp <= 42:
            return (1, -mpg_est)
        if 0 < mpg_est <= 8 and pts > 0:
            return (2, -mpg_est)
        if 5 <= mpg_est <= 42 and pts > 0:
            return (3, -mpg_est)
        if 0 < mpg_est <= 8:
            return (4, -mpg_est)
        if 5 <= mpg_est <= 42:
            return (5, -mpg_est)
        return (9, mp)

    return min(candidates, key=rank)


def parse_per_game_md(md: str) -> pd.DataFrame:
    by_name: dict[str, list[dict]] = {}
    for line in md.splitlines():
        if not line.startswith("|") or "Player" in line or "---" in line:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 10:
            continue
        if parts[0].isdigit() and parts[1] not in ("Player", "Team Totals"):
            try:
                mp_raw = float(parts[5])
                g = float(parts[3])
                mpg_check, _ = resolve_mpg_and_minutes(mp_raw, int(g))
                if mpg_check <= 0 or mpg_check > 42:
                    continue
                name = parts[1]
                by_name.setdefault(name, []).append({
                    "Rk": parts[0],
                    "Player": parts[1],
                    "Pos": parts[2],
                    "G": parts[3],
                    "GS": parts[4],
                    "MP": parts[5],
                    "FG": parts[6],
                    "FGA": parts[7],
                    "FG%": parts[8],
                    "3P": parts[9] if len(parts) > 9 else 0,
                    "3PA": parts[10] if len(parts) > 10 else 0,
                    "3P%": parts[11] if len(parts) > 11 else 0,
                    "2P": parts[12] if len(parts) > 12 else 0,
                    "2PA": parts[13] if len(parts) > 13 else 0,
                    "2P%": parts[14] if len(parts) > 14 else 0,
                    "eFG%": parts[15] if len(parts) > 15 else parts[8],
                    "FT": parts[16] if len(parts) > 16 else 0,
                    "FTA": parts[17] if len(parts) > 17 else 0,
                    "FT%": parts[18] if len(parts) > 18 else 0,
                    "ORB": parts[18] if len(parts) > 18 else 0,
                    "DRB": parts[19] if len(parts) > 19 else 0,
                    "TRB": parts[20] if len(parts) > 20 else 0,
                    "AST": parts[21] if len(parts) > 21 else 0,
                    "STL": parts[22] if len(parts) > 22 else 0,
                    "BLK": parts[23] if len(parts) > 23 else 0,
                    "TOV": parts[24] if len(parts) > 24 else 0,
                    "PF": parts[25] if len(parts) > 25 else 0,
                    "PTS": parts[26] if len(parts) > 26 else 0,
                })
            except (ValueError, IndexError):
                continue
    if not by_name:
        raise ValueError("No per-game rows parsed from markdown")
    rows = [_pick_best_stat_row(cands) for cands in by_name.values()]
    df = pd.DataFrame(rows)
    for col in ["MP", "G", "FGA", "FTA", "PTS", "3PA", "3P%", "FT%", "eFG%", "ORB", "DRB", "AST", "STL", "BLK", "TOV", "PF"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def cache_team(team_id: str, md: str) -> int:
    tname, conf = TEAM_MAP[team_id]
    html = _html_like(md)
    prof = parse_team_row(html) or {"games_played": 32}
    prof = {**_team_profile(team_id), **prof}
    team_row = {
        "team_id": team_id,
        "team_name": tname,
        "conference": conf,
        "season": SEASON_YEAR,
        "data_source": "Sports Reference 2025-26",
        **prof,
    }
    try:
        pdf = parse_per_game_md(md)
    except ValueError:
        from io import StringIO
        from ingest_sports_reference import parse_player_table
        pdf = parse_player_table(html)
    cmap = class_from_roster(html)
    players = player_rows_from_df(pdf, team_id, cmap, int(prof.get("games_played", 32)))
    players = [p for p in players if p["mpg"] >= MIN_MPG or p["minutes"] >= MIN_MINUTES]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{team_id}.json"
    path.write_text(json.dumps({"team": team_row, "players": players}, indent=2))
    return len(players)


if __name__ == "__main__":
    tid, fpath = sys.argv[1], sys.argv[2]
    n = cache_team(tid, Path(fpath).read_text())
    print(f"Cached {tid}: {n} players")
