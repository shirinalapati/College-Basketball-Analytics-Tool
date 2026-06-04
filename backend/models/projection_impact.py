"""
Shared projection impact engine for Dev Board Proj. Value and Improvement Simulator.

Slider values map to fractions of the calibrated scenario via per-player caps from
simulator_presets.calibrated_slider_bases; scale=1.0 matches full Proj. Value math.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from models.scoring import PROJECTION_SCENARIO
from models.simulator_presets import SLIDER_KEYS, calibrated_slider_bases, slider_key_to_skill

SIMULATOR_SKILLS = (
    "shooting",
    "free_throw",
    "ball_security",
    "foul_discipline",
    "defensive_rebounding",
    "offensive_rebounding",
    "playmaking",
    "rim_pressure",
    "defensive_activity",
)


def _as_dict(player: dict[str, Any] | pd.Series) -> dict[str, Any]:
    if isinstance(player, pd.Series):
        return player.to_dict()
    return player


def _ppp_for_team(team: dict[str, Any] | pd.Series | None) -> float:
    if team is None:
        return 1.05
    if isinstance(team, pd.Series):
        team = team.to_dict()
    ortg = team.get("offensive_rating", 105) or 105
    return ortg / 100


def projected_impact_for_skill(
    player: dict[str, Any] | pd.Series,
    skill: str,
    *,
    team: dict[str, Any] | pd.Series | None = None,
    scale: float = 1.0,
    scenario: dict | None = None,
) -> float:
    """
    Points proxy for improving one skill by `scale` × calibrated increment.
    scale=1.0 matches Dev Board Proj. Value for that skill.
    """
    sc = scenario or PROJECTION_SCENARIO
    pv = sc.get("point_values", {})
    p = _as_dict(player)
    ppp = _ppp_for_team(team)

    scale = max(0.0, float(scale))
    if scale <= 0:
        return 0.0

    games = max(int(p.get("games_played", 30)), 1)
    minutes = p.get("minutes", 500) or 500

    if skill == "shooting":
        cfg = sc["shooting"]
        cur = p.get("three_point_pct", 0.30) or 0.30
        tpa = p.get("three_point_attempts", 50) or 50
        inc = cfg["three_point_pct_increment"] * scale
        target = min(cur + inc, cfg["three_point_pct_ceiling"])
        return max(0.0, tpa * (target - cur) * 3)

    if skill == "free_throw":
        cfg = sc["free_throw"]
        cur = p.get("free_throw_pct", 0.70) or 0.70
        fta = p.get("free_throw_attempts", 40) or 40
        inc = cfg["free_throw_pct_increment"] * scale
        target = min(cur + inc, cfg["free_throw_pct_ceiling"])
        return max(0.0, fta * (target - cur))

    if skill == "ball_security":
        tov_rate = p.get("turnover_rate", 0.15) or 0.15
        usage = p.get("usage_rate", 0.20) or 0.20
        est_tov = minutes * usage * tov_rate * 0.02
        frac = sc["ball_security"]["turnover_reduction_fraction"] * scale
        prevented = est_tov * frac
        return prevented * ppp

    if skill == "foul_discipline":
        foul_r = p.get("foul_rate", 0.04) or 0.04
        est_fouls = minutes * foul_r * 0.5
        frac = sc["foul_discipline"]["foul_reduction_fraction"] * scale
        reduced = est_fouls * frac
        return reduced * pv.get("foul_proxy", 0.7)

    if skill == "defensive_rebounding":
        extra = games * sc["defensive_rebounding"]["drb_per_game_increment"] * scale
        return extra * pv.get("second_chance_def_reb", 1.1)

    if skill == "offensive_rebounding":
        extra = games * sc["offensive_rebounding"]["orb_per_game_increment"] * scale
        return extra * pv.get("second_chance_off_reb", 1.15)

    if skill == "playmaking":
        extra_assists = games * sc["playmaking"]["ast_per_game_increment"] * scale
        return extra_assists * pv.get("assist_to_points", 1.5)

    if skill == "defensive_activity":
        extra = games * sc["defensive_activity"]["stl_blk_per_game_increment"] * scale
        return extra * pv.get("activity_to_points", 1.2)

    if skill == "rim_pressure":
        cfg = sc["rim_pressure"]
        ts = p.get("ts_pct", 0.52) or 0.52
        inc = cfg["ts_pct_increment"] * scale
        target_ts = min(ts + inc, cfg["ts_pct_ceiling"])
        fga_proxy = minutes * pv.get("rim_fga_per_min", 0.35)
        return max(0.0, fga_proxy * (target_ts - ts) * pv.get("rim_efficiency_mult", 0.8))

    return 0.0


def skill_scales_from_sliders(
    player: dict[str, Any] | pd.Series,
    slider_inputs: dict[str, Any],
) -> dict[str, float]:
    """Map simulator slider values → scenario scale (0 = off, 1 = full calibrated cap)."""
    p = _as_dict(player)
    bases = calibrated_slider_bases(p)
    scales: dict[str, float] = {}
    for key in SLIDER_KEYS:
        skill = slider_key_to_skill(key)
        val = float(slider_inputs.get(key, 0) or 0)
        if val <= 0:
            continue
        base = float(bases.get(key, 0) or 0)
        if base > 0:
            scales[skill] = val / base
        else:
            scales[skill] = 1.0
    return scales


def simulate_impacts_from_sliders(
    player: dict[str, Any] | pd.Series,
    team: dict[str, Any] | pd.Series | None,
    slider_inputs: dict[str, Any],
) -> dict[str, float]:
    """Per-skill impacts and total for Improvement Simulator (unified with Proj. Value)."""
    scales = skill_scales_from_sliders(player, slider_inputs)
    impacts: dict[str, float] = {}
    for skill in SIMULATOR_SKILLS:
        s = scales.get(skill, 0.0)
        impacts[skill] = (
            projected_impact_for_skill(player, skill, team=team, scale=s) if s > 0 else 0.0
        )
    return impacts
