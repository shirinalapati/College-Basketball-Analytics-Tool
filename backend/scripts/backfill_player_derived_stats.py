"""
Backfill derived advanced-proxy columns on players_demo.csv from existing box-score fields.
Preserves BPM/PER/WS from SR advanced ingest; backfills derived rates and optional
estimated shot-profile fields for shot-selection context (not official rim tracking).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.shot_profile import SHOT_PROFILE_COLUMNS, enrich_player_shot_profile

DATA = ROOT / "data"
PLAYERS_PATH = DATA / "players_demo.csv"

ADVANCED_NULL_COLS = [
    "bpm",
    "obpm",
    "dbpm",
    "per",
    "player_ortg",
    "player_drtg",
    "win_shares",
    "win_shares_per_40",
]


def _f(v, default=0.0) -> float:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return default
    return float(v)


def _fga_from_shot_profile(row: pd.Series) -> float:
    """Use tracked/estimated zone attempts when box-score FGA is missing."""
    parts = [
        _f(row.get("rim_attempts", 0)),
        _f(row.get("midrange_attempts", 0)),
        _f(row.get("corner_three_attempts", 0)),
        _f(row.get("above_break_three_attempts", 0)),
    ]
    total = sum(parts)
    return total if total >= 5 else 0.0


def _estimate_season_fga(row: pd.Series, games: int) -> float:
    """
    Best-effort season FGA. PBP zone totals often undercount vs SR FTA/points;
    take the max of credible estimates so FTr = FTA/FGA stays <= ~85%.
    """
    candidates: list[float] = []
    existing = _f(row.get("field_goal_attempts", 0))
    if existing > 0 and existing != 50:  # skip legacy 50-FGA placeholder
        candidates.append(existing)

    profile = _fga_from_shot_profile(row)
    if profile > 0:
        candidates.append(profile)

    tpa = _f(row.get("three_point_attempts", 0))
    tpar = _f(row.get("three_point_attempt_rate", 0))
    if tpar > 0.05 and tpa > 0:
        candidates.append(tpa / tpar)
    elif tpa > 0:
        candidates.append(tpa * 2.2)

    ppg = _f(row.get("ppg", 0))
    ts = max(_f(row.get("ts_pct", 0.52)), 0.35)
    if ppg > 0 and games > 0:
        candidates.append(ppg * games / (2 * ts))

    fta = _f(row.get("free_throw_attempts", 0))
    if fta > 0:
        # Season FTr rarely exceeds ~0.75; use as FGA floor when FTA is trustworthy
        candidates.append(fta / 0.75)

    if not candidates:
        return max(20.0, ppg * games * 0.45)
    return max(candidates)


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    g = out["games_played"].clip(lower=1)
    mpg = out["mpg"].clip(lower=0.1)

    if "field_goal_attempts" not in out.columns:
        out["field_goal_attempts"] = np.nan

    for idx, row in out.iterrows():
        gi = max(int(row.get("games_played", 1)), 1)
        mp = max(_f(row.get("mpg", 20)), 0.1)
        tpa = _f(row.get("three_point_attempts", 0))
        fta = _f(row.get("free_throw_attempts", 0))
        fga = _estimate_season_fga(row, gi)
        tracked_tpa = _f(row.get("corner_three_attempts", 0)) + _f(
            row.get("above_break_three_attempts", 0)
        )
        if tracked_tpa > tpa:
            tpa = tracked_tpa
        if fta > 0 and fga < fta:
            fga = fta / 0.75
        fga_pg = max(fga / gi, 0.1)
        fta_pg = fta / gi
        tov_pg = _f(row.get("tov_per_game", 0.1), 0.1)
        ast_pg = _f(row.get("ast_per_game", 0))
        stl_pg = _f(row.get("stl_per_game", 0))
        blk_pg = _f(row.get("blk_per_game", 0))
        pf_pg = _f(row.get("pf_per_game", 0))
        poss_pg = max(fga_pg + 0.44 * fta_pg + tov_pg, 0.1)
        ts = _f(row.get("ts_pct", 0.52))
        efg = _f(row.get("efg_pct", 0.5))
        tp_pct = _f(row.get("three_point_pct", 0.33))

        two_pa_pg = max(fga_pg - tpa / gi, 0.1)
        two_pm_pg = max((efg * 2 * fga_pg - tp_pct * 3 * (tpa / gi)) / 2, 0)  # rough
        two_pct = min(0.72, max(0.25, two_pm_pg / two_pa_pg))

        out.at[idx, "field_goal_attempts"] = int(round(fga))
        out.at[idx, "three_point_attempt_rate"] = round((tpa / gi) / fga_pg, 3)
        ftr = fta_pg / fga_pg if fga_pg > 0 else 0.0
        out.at[idx, "free_throw_rate"] = round(min(ftr, 1.0), 3)
        out.at[idx, "two_point_pct"] = round(two_pct, 3)
        out.at[idx, "assist_turnover_ratio"] = round(ast_pg / max(tov_pg, 0.1), 2)
        out.at[idx, "fouls_per_40"] = round(pf_pg * 40 / mp, 2)
        out.at[idx, "steal_pct"] = round(100 * stl_pg / poss_pg, 2)
        out.at[idx, "block_pct"] = round(100 * blk_pg / poss_pg, 2)

    for col in ADVANCED_NULL_COLS:
        if col not in out.columns:
            out[col] = np.nan

    for col in SHOT_PROFILE_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan

    records = []
    for _, row in out.iterrows():
        rec = enrich_player_shot_profile(row.to_dict(), estimate_if_missing=True)
        records.append(rec)
    return pd.DataFrame(records)


def main() -> None:
    if not PLAYERS_PATH.exists():
        print("Run build_full_dataset.py first")
        raise SystemExit(1)
    df = pd.read_csv(PLAYERS_PATH)
    enriched = enrich_dataframe(df)
    enriched.to_csv(PLAYERS_PATH, index=False)
    print(f"Updated {PLAYERS_PATH} ({len(enriched)} players)")


if __name__ == "__main__":
    main()
