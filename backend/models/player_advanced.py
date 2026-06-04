"""
Helpers for derived player stats and gap-based opportunity scoring.

BPM/PER/Win Shares are only used when populated for the full player pool so
scores stay comparable across players (no per-player advanced vs proxy mix).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def position_group(position: str) -> str:
    p = str(position or "F").strip().upper()[:1]
    return p if p in ("G", "F", "C") else "F"


def stat_or_none(player: pd.Series | dict, col: str) -> float | None:
    if isinstance(player, dict):
        v = player.get(col)
    else:
        v = player.get(col) if col in player.index else None
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return float(v)


def peer_medians(
    peers: pd.DataFrame, field: pd.DataFrame, col: str, field_avg: dict[str, float]
) -> tuple[float, float]:
    if col not in peers.columns and col not in field.columns:
        return field_avg.get(col, 0.0), field_avg.get(col, 0.0)
    pos_med = float(peers[col].median()) if len(peers) and col in peers.columns else field_avg.get(col, 0.0)
    field_med = float(field[col].median()) if len(field) and col in field.columns else field_avg.get(col, 0.0)
    return pos_med, field_med


def gap_vs_peers(
    val: float,
    pos_med: float,
    field_med: float,
    pos_peers: pd.DataFrame,
    field: pd.DataFrame,
    col: str,
    *,
    invert: bool = False,
) -> list[float]:
    """Return position + pool gap scores (0–100 scale) where lower raw stat = higher gap unless invert."""
    gaps: list[float] = []
    pos_max = float(pos_peers[col].max()) if col in pos_peers.columns and len(pos_peers) else pos_med + 0.001
    field_max = float(field[col].max()) if col in field.columns and len(field) else field_med + 0.001

    if invert:
        gaps.append(max(0.0, val - pos_med) / (pos_max + 0.001) * 100)
        gaps.append(max(0.0, val - field_med) / (field_max + 0.001) * 100)
    else:
        gaps.append(max(0.0, pos_med - val) / (max(pos_med, 0.001)) * 100)
        gaps.append(max(0.0, field_med - val) / (max(field_med, 0.001)) * 100)
    return gaps


def gaps_for_column(
    player: pd.Series,
    pos_peers: pd.DataFrame,
    field: pd.DataFrame,
    col: str,
    field_avg: dict[str, float],
    *,
    invert: bool = False,
) -> list[float]:
    val = stat_or_none(player, col)
    if val is None:
        return []
    pos_med, field_med = peer_medians(pos_peers, field, col, field_avg)
    return gap_vs_peers(val, pos_med, field_med, pos_peers, field, col, invert=invert)


# Missing gap data → no invented opportunity (never default to ~40 "moderate").
NO_GAP_DATA_OPPORTUNITY = 0.0


def mean_gap(gaps: list[float]) -> float:
    """Average gap terms; empty list means no usable peer comparison (0, not a neutral 40)."""
    return float(np.mean(gaps)) if gaps else NO_GAP_DATA_OPPORTUNITY


def stat_coverage(player: pd.Series | dict, columns: list[str]) -> float:
    """Share of listed stat columns present on the player (0–1)."""
    if not columns:
        return 0.0
    present = sum(1 for col in columns if stat_or_none(player, col) is not None)
    return present / len(columns)


def confidence_from_coverage(coverage: float) -> float:
    """
    Scale opportunity down when inputs are incomplete.
    Full coverage → 1.0; no coverage → 0.0 (via opportunity_score).
    """
    coverage = max(0.0, min(1.0, float(coverage)))
    return 0.25 + 0.75 * coverage


def opportunity_score(
    gaps: list[float],
    *,
    core_columns: list[str] | None = None,
    player: pd.Series | dict | None = None,
) -> float:
    """
    Peer-gap opportunity with optional confidence dampening when core stats are missing.
    """
    if not gaps:
        return NO_GAP_DATA_OPPORTUNITY
    base = mean_gap(gaps)
    if core_columns and player is not None:
        return base * confidence_from_coverage(stat_coverage(player, core_columns))
    return base


def weighted_opportunity_components(
    components: list[tuple[list[float], float]],
) -> float:
    """Weighted mean of per-stat gaps; only stats with data count; missing stats excluded."""
    parts: list[tuple[float, float]] = []
    for gap_list, weight in components:
        if gap_list:
            parts.append((mean_gap(gap_list), weight))
    if not parts:
        return NO_GAP_DATA_OPPORTUNITY
    total_w = sum(w for _, w in parts)
    return sum(score * w for score, w in parts) / total_w


def scale_gaps(gaps: list[float], factor: float) -> list[float]:
    return [g * factor for g in gaps]


def usage_pressure_modifier(usage_rate: float) -> float:
    """Turnover-risk pressure from usage share (usage_rate as 0–1, e.g. 0.24 = 24%)."""
    pct = usage_rate * 100.0 if usage_rate <= 1.5 else usage_rate
    if pct < 18:
        return 0.0
    if pct < 22:
        return 35.0
    if pct < 26:
        return 60.0
    if pct < 30:
        return 80.0
    return 100.0


def ball_security_opportunity_raw(
    player: pd.Series,
    pos_peers: pd.DataFrame,
    field: pd.DataFrame,
    field_avg: dict[str, float],
) -> float:
    """
    Raw ball-security opportunity (0–100) before pool normalization.
    TOV gap + AST/TOV weakness + usage pressure, with guard creator boosts.
    """
    tov_gap = mean_gap(
        gaps_for_column(player, pos_peers, field, "turnover_rate", field_avg, invert=True)
    )
    ast_to_gap = mean_gap(
        gaps_for_column(
            player, pos_peers, field, "assist_turnover_ratio", field_avg, invert=False
        )
    )
    usage = float(player.get("usage_rate", 0.2) or 0.2)
    usage_mod = usage_pressure_modifier(usage)
    tov = stat_or_none(player, "turnover_rate")
    if tov is not None and "turnover_rate" in pos_peers.columns:
        med_tov = float(pos_peers["turnover_rate"].median())
        if tov <= med_tov:
            usage_mod *= 0.45
    raw = 0.45 * tov_gap + 0.35 * ast_to_gap + 0.20 * usage_mod

    if position_group(str(player.get("position", "F"))) == "G":
        ast_to = stat_or_none(player, "assist_turnover_ratio")
        mpg = float(player.get("mpg", 0) or 0)
        if ast_to is not None and "assist_turnover_ratio" in pos_peers.columns:
            med_ast = float(pos_peers["assist_turnover_ratio"].median())
            if usage >= 0.22 and ast_to < med_ast:
                raw += 10.0
        if tov is not None and "turnover_rate" in pos_peers.columns:
            med_tov = float(pos_peers["turnover_rate"].median())
            if usage >= 0.25 and tov > med_tov:
                raw += 8.0
            if mpg >= 25 and tov > med_tov:
                raw += 5.0

    return min(100.0, raw)


def pool_advanced_metrics_ready(
    players: pd.DataFrame, *, min_coverage: float = 1.0
) -> bool:
    """True when BPM (primary advanced flag) is present for at least min_coverage of the pool."""
    if "bpm" not in players.columns or len(players) == 0:
        return False
    filled = int(players["bpm"].notna().sum())
    return filled / len(players) >= min_coverage
