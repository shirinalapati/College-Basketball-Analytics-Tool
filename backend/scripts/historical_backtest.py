"""
Historical backtest: 2024-25 model Top Priority vs 2025-26 actual skill movement.

Uses sr_cache_prior (2024-25) to score players/teams, then checks whether
same-school returners (10+ MPG both seasons) improved in the recommended skill.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from calibrate_realism_priors import (  # noqa: E402
    CURRENT_CACHE,
    MIN_MPG,
    PRIOR_CACHE,
    SKILL_YOY_COLS,
    load_players_from_cache,
)
from models.scoring import SKILL_CATEGORIES, SKILL_LABELS, ScoringEngine, rank_player_priorities  # noqa: E402

# Primary direction for "improved" (first available column wins if multiple)
SKILL_IMPROVE: dict[str, dict] = {
    "shooting": {"cols": ("three_point_pct", "efg_pct"), "lower_is_better": False},
    "free_throw": {"cols": ("free_throw_pct",), "lower_is_better": False},
    "ball_security": {"cols": ("turnover_rate", "tov_per_game"), "lower_is_better": True},
    "offensive_rebounding": {"cols": ("orb_per_game", "offensive_rebound_rate"), "lower_is_better": False},
    "defensive_rebounding": {"cols": ("drb_per_game", "defensive_rebound_rate"), "lower_is_better": False},
    "foul_discipline": {"cols": ("pf_per_game", "foul_rate"), "lower_is_better": True},
    "playmaking": {"cols": ("ast_per_game", "assist_rate"), "lower_is_better": False},
    "defensive_activity": {"cols": ("stl_per_game", "blk_per_game"), "lower_is_better": False},
    "rim_pressure": {"cols": ("ts_pct", "efg_pct"), "lower_is_better": False},
}


def enrich_team_shooting_from_players(teams: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """Aggregate team 3P% / FT% from rotation players (SR team cache omits these)."""
    teams = teams.copy()
    for col in ("three_point_pct", "free_throw_pct"):
        if col not in teams.columns:
            teams[col] = np.nan

    for pct_col, att_col in (
        ("three_point_pct", "three_point_attempts"),
        ("free_throw_pct", "free_throw_attempts"),
    ):
        att = players[att_col].fillna(0)
        makes = players[pct_col].fillna(0) * att
        agg = (
            players.assign(_makes=makes, _att=att)
            .groupby("team_id")[["_makes", "_att"]]
            .sum()
        )
        rate = agg["_makes"] / agg["_att"].clip(lower=1)
        missing = teams[pct_col].isna()
        if missing.any():
            teams.loc[missing, pct_col] = teams.loc[missing, "team_id"].map(rate)

    if "two_point_pct" not in teams.columns:
        teams["two_point_pct"] = teams["efg_pct"] if "efg_pct" in teams.columns else 0.50
    return teams


def load_teams_from_cache(cache_dir: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(cache_dir.glob("*.json")):
        payload = json.loads(path.read_text())
        if payload.get("team"):
            rows.append(payload["team"])
    return pd.DataFrame(rows)


def skill_improved(cur: pd.Series, prior: pd.Series, skill: str) -> bool | None:
    cfg = SKILL_IMPROVE[skill]
    for col in cfg["cols"]:
        if col not in cur.index or col not in prior.index:
            continue
        a, b = float(cur[col]), float(prior[col])
        if pd.isna(a) or pd.isna(b):
            continue
        if cfg["lower_is_better"]:
            return a < b
        return a > b
    return None


def skill_has_stats(cur: pd.Series, prior: pd.Series, skill: str) -> bool:
    cols = SKILL_YOY_COLS.get(skill, SKILL_IMPROVE[skill]["cols"])
    for col in cols:
        if col in cur.index and col in prior.index:
            if not pd.isna(cur[col]) and not pd.isna(prior[col]):
                return True
    return False


def run_backtest() -> dict:
    prior_players = load_players_from_cache(PRIOR_CACHE)
    current_players = load_players_from_cache(CURRENT_CACHE)
    prior_teams = load_teams_from_cache(PRIOR_CACHE)
    prior_teams = enrich_team_shooting_from_players(prior_teams, prior_players)

    prior_players = prior_players[
        (prior_players["mpg"] >= MIN_MPG) | (prior_players["minutes"] >= 250)
    ].copy()
    current_players = current_players[
        (current_players["mpg"] >= MIN_MPG) | (current_players["minutes"] >= 250)
    ].copy()

    engine = ScoringEngine(prior_teams, prior_players)
    results = engine.run_all()
    pri = results["development_priority_scores"]

    cur = current_players.set_index("player_id")
    pr = prior_players.set_index("player_id")
    common = cur.index.intersection(pr.index)

    matched_rows = []
    transfer_rows = []

    for pid in common:
        same_school = cur.loc[pid, "team_id"] == pr.loc[pid, "team_id"]
        if not (
            float(pr.loc[pid, "mpg"]) >= MIN_MPG
            and float(cur.loc[pid, "mpg"]) >= MIN_MPG
        ):
            continue

        player_pri = pri[pri["player_id"] == pid]
        ranked = rank_player_priorities(player_pri)
        if ranked.empty:
            continue
        top = ranked.iloc[0]
        top_skill = top["skill_category"]
        actionable = int(top.get("actionable", 0))

        if not skill_has_stats(cur.loc[pid], pr.loc[pid], top_skill):
            continue

        improved = skill_improved(cur.loc[pid], pr.loc[pid], top_skill)
        if improved is None:
            continue

        row = {
            "player_id": pid,
            "player_name": pr.loc[pid, "player_name"],
            "team_id": pr.loc[pid, "team_id"],
            "top_skill": top_skill,
            "actionable": actionable,
            "dps": float(top["development_priority_score"]),
            "improved": bool(improved),
            "same_school": same_school,
        }
        if same_school:
            matched_rows.append(row)
        else:
            transfer_rows.append(row)

    matched = pd.DataFrame(matched_rows)
    transfers = pd.DataFrame(transfer_rows)

    # Baseline: non-recommended skills for same matched players
    baseline_improved = []
    baseline_total = []
    if not matched.empty:
        matched_ids = set(matched["player_id"])
        for pid in matched_ids:
            for skill in SKILL_CATEGORIES:
                top_skill = matched.loc[matched["player_id"] == pid, "top_skill"].iloc[0]
                if skill == top_skill:
                    continue
                if not skill_has_stats(cur.loc[pid], pr.loc[pid], skill):
                    continue
                imp = skill_improved(cur.loc[pid], pr.loc[pid], skill)
                if imp is None:
                    continue
                baseline_total.append(1)
                if imp:
                    baseline_improved.append(1)

    by_skill = []
    if not matched.empty:
        for skill in SKILL_CATEGORIES:
            sub = matched[matched["top_skill"] == skill]
            if len(sub) < 5:
                continue
            by_skill.append(
                {
                    "skill": skill,
                    "label": SKILL_LABELS.get(skill, skill),
                    "n": len(sub),
                    "pct_improved": round(100 * sub["improved"].mean(), 1),
                    "actionable_n": int(sub["actionable"].sum()),
                }
            )

    # Named examples: mix of hits and misses
    examples = []
    if not matched.empty:
        hits = matched[matched["improved"]].sort_values("dps", ascending=False).head(2)
        misses = matched[~matched["improved"]].sort_values("dps", ascending=False).head(2)
        for _, r in pd.concat([hits, misses]).iterrows():
            examples.append(
                {
                    "player": r["player_name"],
                    "team": r["team_id"],
                    "top_priority": SKILL_LABELS.get(r["top_skill"], r["top_skill"]),
                    "dps": round(r["dps"], 1),
                    "improved": r["improved"],
                    "actionable": bool(r["actionable"]),
                }
            )

    rec_pct = 100 * matched["improved"].mean() if len(matched) else 0.0
    base_pct = 100 * sum(baseline_improved) / len(baseline_total) if baseline_total else 0.0

    actionable_sub = matched[matched["actionable"] == 1] if not matched.empty else matched
    rec_action_pct = (
        100 * actionable_sub["improved"].mean() if len(actionable_sub) else None
    )

    return {
        "matched_players": len(matched),
        "transfer_players_flagged": len(transfers),
        "pct_improved_recommended": round(rec_pct, 1),
        "pct_improved_actionable_only": round(rec_action_pct, 1) if rec_action_pct is not None else None,
        "actionable_matched": len(actionable_sub),
        "baseline_pairs": len(baseline_total),
        "pct_improved_baseline_non_recommended": round(base_pct, 1),
        "by_skill": by_skill,
        "examples": examples,
        "transfer_note": (
            f"{len(transfers)} portal movers with 10+ MPG in both seasons were scored "
            "but excluded from the main same-school cohort."
        ),
    }


def main() -> None:
    out = run_backtest()
    print("=" * 60)
    print("DevelopmentIQ Historical Backtest (2024-25 → 2025-26)")
    print("=" * 60)
    print(f"1. Matched same-school returners (10+ MPG both seasons): {out['matched_players']}")
    print(f"   Transfers flagged separately: {out['transfer_players_flagged']}")
    print(f"2. Improved in recommended Top Priority skill: {out['pct_improved_recommended']}%")
    if out["pct_improved_actionable_only"] is not None:
        print(
            f"   (Actionable Top Priority only, n={out['actionable_matched']}): "
            f"{out['pct_improved_actionable_only']}%"
        )
    print(
        f"3. Baseline — improved in non-recommended skills "
        f"({out['baseline_pairs']} player-skill pairs): "
        f"{out['pct_improved_baseline_non_recommended']}%"
    )
    print("4. By skill (Top Priority recommendations with n≥5):")
    for row in out["by_skill"]:
        print(
            f"   - {row['label']}: {row['pct_improved']}% improved "
            f"(n={row['n']}, actionable={row['actionable_n']})"
        )
    print("5. Examples:")
    for ex in out["examples"]:
        status = "improved" if ex["improved"] else "did not improve"
        act = "actionable" if ex["actionable"] else "relative focus"
        print(
            f"   - {ex['player']} ({ex['team']}): {ex['top_priority']} "
            f"(DPS {ex['dps']}, {act}) — {status}"
        )
    print("6. Interpretation:")
    diff = out["pct_improved_recommended"] - out["pct_improved_baseline_non_recommended"]
    if diff > 5:
        print(f"   Model edge vs baseline: +{diff:.1f} pp (modest positive signal).")
    elif diff < -5:
        print(f"   Model underperformed baseline by {abs(diff):.1f} pp — results are mixed.")
    else:
        print(f"   Results are mixed; edge vs baseline is only {diff:+.1f} pp.")
    print(f"   {out['transfer_note']}")


if __name__ == "__main__":
    main()
