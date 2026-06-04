"""
Map YoY-calibrated projection scenario → Improvement Simulator slider bases (per player).
"""

from __future__ import annotations

from typing import Any

from models.scoring import PROJECTION_SCENARIO

SLIDER_KEYS = (
    "three_point_pct_delta",
    "free_throw_pct_delta",
    "turnover_reduction_pct",
    "foul_reduction_pct",
    "defensive_rebounding_delta",
    "offensive_rebounding_delta",
    "assist_improvement_pct",
    "ts_pct_improvement_pts",
    "stl_blk_improvement_pct",
)

SLIDER_MAX: dict[str, float] = {
    "three_point_pct_delta": 8.0,
    "free_throw_pct_delta": 10.0,
    "turnover_reduction_pct": 20.0,
    "foul_reduction_pct": 20.0,
    "defensive_rebounding_delta": 5.0,
    "offensive_rebounding_delta": 5.0,
    "assist_improvement_pct": 15.0,
    "ts_pct_improvement_pts": 5.0,
    "stl_blk_improvement_pct": 25.0,
}

SLIDER_STEP: dict[str, float] = {
    "three_point_pct_delta": 0.5,
    "free_throw_pct_delta": 0.5,
    "turnover_reduction_pct": 1.0,
    "foul_reduction_pct": 1.0,
    "defensive_rebounding_delta": 0.5,
    "offensive_rebounding_delta": 0.5,
    "assist_improvement_pct": 1.0,
    "ts_pct_improvement_pts": 0.5,
    "stl_blk_improvement_pct": 1.0,
}

DPS_FULL_SCALE = 65.0
MIN_SCALE = 0.2
CLOSENESS_DPS = 8.0
TIER_MULTIPLIERS = (1.0, 0.7, 0.35, 0.15)


def _clip(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _round_to_step(val: float, step: float) -> float:
    if step <= 0:
        return round(val, 2)
    return round(val / step) * step


def _stored_or_est(player: dict[str, Any], key: str, est_fn) -> float:
    v = player.get(key)
    if v is not None and float(v) > 0:
        return float(v)
    return est_fn(player)


def _est_drb_per_game(player: dict[str, Any]) -> float:
    """Inverse of ingest rate heuristic: drb_rate ≈ drb_pg / mpg * 0.055."""
    rate = float(player.get("defensive_rebounding_rate", 0.05) or 0.05)
    mpg = float(player.get("mpg", 20) or 20)
    return max(0.2, rate * mpg / 0.055)


def _est_orb_per_game(player: dict[str, Any]) -> float:
    rate = float(player.get("offensive_rebound_rate", 0.03) or 0.03)
    mpg = float(player.get("mpg", 20) or 20)
    return max(0.08, rate * mpg / 0.04)


def _est_ast_per_game(player: dict[str, Any]) -> float:
    """Assist rate × possessions proxy per game."""
    ar = float(player.get("assist_rate", 0.1) or 0.1)
    mpg = float(player.get("mpg", 20) or 20)
    return max(0.15, ar * mpg * 0.5)


def drb_per_game(player: dict[str, Any]) -> float:
    return _stored_or_est(player, "drb_per_game", _est_drb_per_game)


def orb_per_game(player: dict[str, Any]) -> float:
    return _stored_or_est(player, "orb_per_game", _est_orb_per_game)


def ast_per_game(player: dict[str, Any]) -> float:
    return _stored_or_est(player, "ast_per_game", _est_ast_per_game)


def stl_blk_per_game(player: dict[str, Any]) -> float:
    stl = float(player.get("stl_per_game", 0) or 0)
    blk = float(player.get("blk_per_game", 0) or 0)
    return max(0.15, stl + blk)


def calibrated_slider_bases(player: dict[str, Any]) -> dict[str, float]:
    """
    Full slider caps (scale = 1) from projection_calibration.json.
    Shooting / TOV / fouls use calibration units directly; reb / playmaking convert
    per-game increments using this player's estimated per-game rates.
    """
    sc = PROJECTION_SCENARIO

    drb_inc = float(sc["defensive_rebounding"]["drb_per_game_increment"])
    orb_inc = float(sc["offensive_rebounding"]["orb_per_game_increment"])
    ast_inc = float(sc["playmaking"]["ast_per_game_increment"])
    ts_inc = float(sc["rim_pressure"]["ts_pct_increment"])
    stl_blk_inc = float(sc["defensive_activity"]["stl_blk_per_game_increment"])

    bases = {
        "three_point_pct_delta": float(sc["shooting"]["three_point_pct_increment"]) * 100,
        "free_throw_pct_delta": float(sc["free_throw"]["free_throw_pct_increment"]) * 100,
        "turnover_reduction_pct": float(sc["ball_security"]["turnover_reduction_fraction"]) * 100,
        "foul_reduction_pct": float(sc["foul_discipline"]["foul_reduction_fraction"]) * 100,
        "defensive_rebounding_delta": _clip(
            100 * drb_inc / drb_per_game(player), 0.5, SLIDER_MAX["defensive_rebounding_delta"]
        ),
        "offensive_rebounding_delta": _clip(
            100 * orb_inc / orb_per_game(player), 0.5, SLIDER_MAX["offensive_rebounding_delta"]
        ),
        "assist_improvement_pct": _clip(
            100 * ast_inc / ast_per_game(player), 1.0, SLIDER_MAX["assist_improvement_pct"]
        ),
        "ts_pct_improvement_pts": _clip(ts_inc * 100, 0.5, SLIDER_MAX["ts_pct_improvement_pts"]),
        "stl_blk_improvement_pct": _clip(
            100 * stl_blk_inc / stl_blk_per_game(player), 1.0, SLIDER_MAX["stl_blk_improvement_pct"]
        ),
    }
    for key in SLIDER_KEYS:
        bases[key] = round(_clip(bases[key], 0, SLIDER_MAX[key]), 2)
    return bases


def slider_key_to_skill(slider_key: str) -> str:
    return {
        "three_point_pct_delta": "shooting",
        "free_throw_pct_delta": "free_throw",
        "turnover_reduction_pct": "ball_security",
        "foul_reduction_pct": "foul_discipline",
        "defensive_rebounding_delta": "defensive_rebounding",
        "offensive_rebounding_delta": "offensive_rebounding",
        "assist_improvement_pct": "playmaking",
        "ts_pct_improvement_pts": "rim_pressure",
        "stl_blk_improvement_pct": "defensive_activity",
    }[slider_key]


def _slider_to_skill(slider_key: str) -> str:
    return slider_key_to_skill(slider_key)


def _dps_rank_by_skill(dps_by_skill: dict[str, float]) -> dict[str, int]:
    ordered = sorted(dps_by_skill.items(), key=lambda x: x[1], reverse=True)
    return {skill: rank for rank, (skill, _) in enumerate(ordered, start=1)}


def _tier_index_from_rank(rank: int) -> int:
    if rank <= 1:
        return 0
    if rank <= 3:
        return 1
    if rank <= 6:
        return 2
    return 3


def opportunity_slider_factor(opportunity: float) -> float:
    if opportunity < 10:
        return 0.0
    if opportunity < 20:
        return 0.25
    if opportunity < 40:
        return 0.60
    return 1.0


def opportunity_value_factor(opportunity: float) -> float:
    """Dampen projected points in Suggested mode only."""
    if opportunity < 10:
        return 0.0
    if opportunity < 20:
        return 0.50
    if opportunity < 40:
        return 0.80
    return 1.0


def tiered_suggested_preset(
    player: dict[str, Any],
    dps_by_skill: dict[str, float],
    opportunity_by_skill: dict[str, float],
) -> dict[str, float]:
    """
    Tiered emphasis by adjusted DPS rank (all 9 skills), closeness bump, opportunity gating.
    """
    bases = calibrated_slider_bases(player)
    ranks = _dps_rank_by_skill(dps_by_skill)
    top_dps = max(dps_by_skill.values()) if dps_by_skill else 0.0
    out: dict[str, float] = {}

    for key in SLIDER_KEYS:
        skill = slider_key_to_skill(key)
        rank = ranks.get(skill, 9)
        tier_idx = _tier_index_from_rank(rank)
        dps = float(dps_by_skill.get(skill, 0) or 0)
        if top_dps - dps <= CLOSENESS_DPS and tier_idx > 0:
            tier_idx -= 1
        val = bases[key] * TIER_MULTIPLIERS[tier_idx]
        opp = float(opportunity_by_skill.get(skill, 40) or 40)
        val *= opportunity_slider_factor(opp)
        step = SLIDER_STEP[key]
        out[key] = _round_to_step(_clip(val, 0, SLIDER_MAX[key]), step)
    return out


def apply_suggested_value_dampening(
    impacts_by_skill: dict[str, float],
    opportunity_by_skill: dict[str, float],
) -> dict[str, float]:
    return {
        skill: round(val * opportunity_value_factor(float(opportunity_by_skill.get(skill, 40) or 40)), 2)
        for skill, val in impacts_by_skill.items()
    }


def scaled_simulator_preset(
    player: dict[str, Any],
    dps_by_skill: dict[str, float],
    *,
    dps_full_scale: float = DPS_FULL_SCALE,
) -> dict[str, float]:
    """Legacy: calibrated base × clamp(DPS ÷ 65, 0.2, 1). Prefer tiered_suggested_preset."""
    bases = calibrated_slider_bases(player)
    out: dict[str, float] = {}
    for key in SLIDER_KEYS:
        skill = _slider_to_skill(key)
        dps = float(dps_by_skill.get(skill, 0) or 0)
        scale = _clip(dps / dps_full_scale, MIN_SCALE, 1.0)
        step = SLIDER_STEP[key]
        out[key] = _round_to_step(bases[key] * scale, step)
    return out


def simulator_preset_payload(
    player: dict[str, Any],
    dps_by_skill: dict[str, float] | None = None,
    opportunity_by_skill: dict[str, float] | None = None,
) -> dict:
    bases = calibrated_slider_bases(player)
    payload: dict[str, Any] = {
        "calibration_source": "projection_calibration.json",
        "dps_full_scale": DPS_FULL_SCALE,
        "bases_at_full_focus": bases,
        "suggested_mode": "tiered_dps_opportunity",
    }
    if dps_by_skill is not None:
        if opportunity_by_skill is not None:
            payload["suggested"] = tiered_suggested_preset(
                player, dps_by_skill, opportunity_by_skill
            )
        else:
            payload["suggested"] = scaled_simulator_preset(player, dps_by_skill)
    return payload
