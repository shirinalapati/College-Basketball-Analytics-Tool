"""
Derive Basketball Impact priors from Dean Oliver's Four Factors (+ secondary defense).

Offensive four-factor weights (standard CBB efficiency decomposition):
  eFG% 40% | TOV% 25% | ORB% 20% | FTR 15%

Skills not in the four factors get secondary raw weights, then all nine
scores are normalized to a 20–100 scale for DPS (10% weight).
"""

from __future__ import annotations

# Offensive four factors → skill allocation (points sum to 100)
EFG_TOTAL = 40
TOV_TOTAL = 25
ORB_TOTAL = 20
FTR_TOTAL = 15

RAW_IMPACT_POINTS: dict[str, float] = {
    # TOV 25%
    "ball_security": TOV_TOTAL,
    # eFG 40% — spacing vs finishing at rim
    "shooting": EFG_TOTAL * 0.60,
    "rim_pressure": EFG_TOTAL * 0.40 + FTR_TOTAL * 0.50,
    # ORB 20%
    "offensive_rebounding": ORB_TOTAL,
    # FTR 15% — converting at the line
    "free_throw": FTR_TOTAL * 0.50,
    # Secondary (defense / creation — not in offensive four factors)
    "defensive_rebounding": 14,
    "playmaking": 11,
    "defensive_activity": 10,
    "foul_discipline": 8,
}

FLOOR = 20
CEILING = 100


def normalize_impact(raw: dict[str, float]) -> dict[str, int]:
    lo = min(raw.values())
    hi = max(raw.values())
    span = hi - lo or 1.0
    return {
        k: int(round(FLOOR + (v - lo) / span * (CEILING - FLOOR)))
        for k, v in raw.items()
    }


def main() -> None:
    impact = normalize_impact(RAW_IMPACT_POINTS)
    print("# Four-factor impact priors (normalized 20-100)")
    for skill in sorted(impact, key=lambda s: -impact[s]):
        pts = RAW_IMPACT_POINTS[skill]
        print(f"  {skill}: {impact[skill]}  # raw {pts}")


if __name__ == "__main__":
    main()
