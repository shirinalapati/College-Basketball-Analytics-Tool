#!/usr/bin/env python3
"""
Pre-submit sanity checks for DevelopmentIQ scoring / labels.
Run from backend/: python3 scripts/run_pre_submit_checks.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.scoring import ScoringEngine, rank_player_priorities, top_priority_skills
from models.shot_profile import has_rim_location_data, rim_pressure_skill_label

DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "developmentiq.db"

EXTREME_TEAM_NEED = 75.0
REAL_OPP_GAP = 25.0  # normalized opportunity after engine; raw pre-norm also checked

# Baseline from pre-tune validation (2026-05-27)
BASELINE = {
    "elite_shooting_top1": 1,
    "elite_shooting_bad": 1,
    "ht_guard_ball_sec_top3": 105 / 257,
    "foul_big_top3": 11 / 16,
    "drb_top3": 30 / 35,
    "orb_top3": 55 / 60,
    "low_min_top20": 0,
    "mpg_lev_corr": 0.849,
    "guard_ball_sec_top1": None,  # filled on first run if missing
}


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    teams = pd.read_csv(DATA_DIR / "teams_demo.csv")
    players = pd.read_csv(DATA_DIR / "players_demo.csv")
    engine = ScoringEngine(teams, players)
    results = engine.run_all()
    pri = results["development_priority_scores"]
    opps = results["player_opportunity_scores"]
    lev = results["development_leverage_scores"]
    needs = results["team_need_scores"]
    return players, pri, opps, lev, needs


def position_group(pos: str) -> str:
    p = str(pos or "F").upper()[:1]
    return p if p in ("G", "F", "C") else "F"


def peer_threshold(players: pd.DataFrame, col: str, group_col: str = "position") -> pd.Series:
    """Position-group median per player row."""
    med = players.groupby(group_col)[col].transform("median")
    return med


def section(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)


def main() -> int:
    players, pri, opps, lev, needs = load_frames()
    qualified = players[players["mpg"] >= 10].copy()
    qualified["_pos"] = qualified["position"].map(position_group)

    failures = 0

    # --- 1. Elite shooters ---
    section("1. Elite shooters (top priority should not be shooting without extreme need + gap)")
    elite = qualified[
        (qualified["three_point_pct"] >= 0.38)
        & (qualified["three_point_attempts"].fillna(0) >= 40)
        & (qualified["efg_pct"] >= qualified.groupby("_pos")["efg_pct"].transform(lambda s: s.quantile(0.6)))
    ].copy()
    elite_pri = pri[pri["player_id"].isin(elite["player_id"])]
    top_rows = []
    for pid in elite["player_id"]:
        pp = elite_pri[elite_pri["player_id"] == pid]
        if pp.empty:
            continue
        ranked = rank_player_priorities(pp)
        top = ranked.iloc[0] if not ranked.empty else None
        if top is None or top["skill_category"] != "shooting":
            continue
        tid = elite.loc[elite["player_id"] == pid, "team_id"].iloc[0]
        shoot_need = float(
            needs.loc[needs["team_id"] == tid, "shooting_need"].iloc[0]
            if tid in needs["team_id"].values
            else 0
        )
        shoot_opp = float(top["player_improvement_opportunity"])
        top_rows.append(
            {
                "player_id": pid,
                "name": elite.loc[elite["player_id"] == pid, "player_name"].iloc[0],
                "3p%": elite.loc[elite["player_id"] == pid, "three_point_pct"].iloc[0],
                "shoot_need": shoot_need,
                "shoot_opp": shoot_opp,
                "dps": top["development_priority_score"],
                "actionable": top.get("actionable", 0),
            }
        )
    bad_elite = [
        r
        for r in top_rows
        if not (r["shoot_need"] >= EXTREME_TEAM_NEED and r["shoot_opp"] >= REAL_OPP_GAP)
    ]
    print(f"  Elite shooters (n={len(elite)}): {len(top_rows)} have shooting as #1 priority")
    print(f"  Failures (no extreme need + real gap): {len(bad_elite)}")
    for r in bad_elite[:8]:
        print(
            f"    - {r['name']}: 3P%={r['3p%']:.1%}, team shoot need={r['shoot_need']:.0f}, "
            f"shoot opp={r['shoot_opp']:.0f}, DPS={r['dps']:.1f}"
        )
    if len(bad_elite) > 8:
        print(f"    ... and {len(bad_elite) - 8} more")
    pass_rate = 1.0 - (len(bad_elite) / max(len(top_rows), 1))
    print(f"  Pass rate among elite with shooting #1: {pass_rate:.0%}")
    if len(bad_elite) > len(top_rows) * 0.15:
        failures += 1
        print("  STATUS: WARN/FAIL (>15% unjustified shooting tops)")

    # --- 2. High-turnover guards ---
    section("2. High-turnover guards (should often show Ball Security in top 3)")
    g = qualified[qualified["_pos"] == "G"].copy()
    g_med_tov = g["turnover_rate"].median()
    g_med_ast = g["assist_turnover_ratio"].median()
    ht = g[
        (g["usage_rate"].fillna(0) >= 0.22)
        & (
            (g["turnover_rate"] > g_med_tov * 1.1)
            | (g["assist_turnover_ratio"].fillna(99) < g_med_ast * 0.85)
        )
    ]
    hit = 0
    misses = []
    for _, row in ht.iterrows():
        pid = row["player_id"]
        pp = pri[pri["player_id"] == pid]
        skills = top_priority_skills(pp, 3)
        if "ball_security" in skills:
            hit += 1
        else:
            misses.append(
                (row["player_name"], row["turnover_rate"], row.get("assist_turnover_ratio"), skills)
            )
    rate = hit / max(len(ht), 1)
    print(f"  Cohort: high-usage guards with elevated TOV% or weak AST/TOV (n={len(ht)})")
    print(f"  Ball security in top 3: {hit}/{len(ht)} ({rate:.0%})")
    for m in misses[:6]:
        print(f"    MISS: {m[0]} TOV={m[1]:.3f} AST/TOV={m[2]} top3={m[3]}")
    if rate < 0.55:
        failures += 1
        print("  STATUS: FAIL (<55% show ball security in top 3)")

    # --- 3. Foul-prone bigs ---
    section("3. Foul-prone bigs (should often show Foul Discipline in top 3)")
    c = qualified[qualified["_pos"] == "C"].copy()
    fp40_p75 = c["fouls_per_40"].quantile(0.75)
    # fouls_per_40 in demo CSV is on 0–1 scale (not literal per-40); use position p75
    foul_big = c[c["fouls_per_40"] >= fp40_p75]
    hit = 0
    misses = []
    for _, row in foul_big.iterrows():
        pid = row["player_id"]
        pp = pri[pri["player_id"] == pid]
        skills = top_priority_skills(pp, 3)
        if "foul_discipline" in skills:
            hit += 1
        else:
            misses.append((row["player_name"], row["fouls_per_40"], skills))
    rate = hit / max(len(foul_big), 1)
    print(f"  Cohort: centers fouls/40 >= position p75 ({fp40_p75:.3f}) (n={len(foul_big)})")
    print(f"  Foul discipline in top 3: {hit}/{len(foul_big)} ({rate:.0%})")
    for m in misses[:6]:
        print(f"    MISS: {m[0]} fouls/40={m[1]:.2f} top3={m[2]}")
    if rate < 0.50:
        failures += 1
        print("  STATUS: FAIL (<50% show foul discipline in top 3)")

    # --- 4. Rebounding ---
    section("4. Poor rebounders on bad rebounding teams (rebounding in top 3)")
    needs_idx = needs.set_index("team_id")
    poor_drb = qualified[
        qualified["defensive_rebound_rate"]
        < qualified.groupby("_pos")["defensive_rebound_rate"].transform(lambda s: s.quantile(0.25))
    ]
    poor_orb = qualified[
        qualified["offensive_rebound_rate"]
        < qualified.groupby("_pos")["offensive_rebound_rate"].transform(lambda s: s.quantile(0.25))
    ]

    def reb_check(cohort: pd.DataFrame, need_col: str, skill: str, label: str) -> float:
        hit = 0
        misses = []
        for _, row in cohort.iterrows():
            tid = row["team_id"]
            if tid not in needs_idx.index:
                continue
            if float(needs_idx.loc[tid, need_col]) < 60:
                continue
            pid = row["player_id"]
            pp = pri[pri["player_id"] == pid]
            skills = top_priority_skills(pp, 3)
            if skill in skills:
                hit += 1
            else:
                misses.append((row["player_name"], float(needs_idx.loc[tid, need_col]), skills))
        total = len(misses) + hit
        rate = hit / max(total, 1)
        print(f"  {label}: n={total}, {skill} in top 3: {hit}/{total} ({rate:.0%})")
        for m in misses[:4]:
            print(f"    MISS: {m[0]} team need={m[1]:.0f} top3={m[2]}")
        return rate

    drb_rate = reb_check(poor_drb, "defensive_rebounding_need", "defensive_rebounding", "Poor DRB% + team DRB need≥60")
    orb_rate = reb_check(poor_orb, "offensive_rebounding_need", "offensive_rebounding", "Poor ORB% + team ORB need≥60")
    if drb_rate < 0.45 and orb_rate < 0.45:
        failures += 1
        print("  STATUS: FAIL (both rebounding cohorts <45%)")

    # --- 5. Stretch forwards / finisher labels ---
    section("5. Stretch forwards (no true-finisher label without rim tracking)")
    f = qualified[qualified["_pos"] == "F"].copy()
    tpar = f["three_point_attempt_rate"].fillna(
        f["three_point_attempts"] / f["field_goal_attempts"].replace(0, np.nan)
    )
    stretch = f[(tpar >= 0.42) & (f["three_point_attempts"].fillna(0) >= 30)]
    stretch = stretch.copy()
    stretch["rim_tracked"] = stretch.apply(has_rim_location_data, axis=1)
    stretch["rim_rate"] = stretch["rim_attempt_rate"].fillna(0)

    # Top priority rim_pressure among stretch wings
    rim_top = []
    label_violations = []
    finisher_phrase = []
    for _, row in stretch.iterrows():
        pid = row["player_id"]
        pp = pri[pri["player_id"] == pid]
        ranked = rank_player_priorities(pp)
        if ranked.empty:
            continue
        top = ranked.iloc[0]
        if top["skill_category"] != "rim_pressure":
            continue
        label = rim_pressure_skill_label(row)
        expl = str(top.get("explanation", "")).lower()
        rim_top.append(row)
        if not row["rim_tracked"] and label != "Rim Pressure / Finishing (proxy)":
            label_violations.append(row["player_name"])
        if not row["rim_tracked"] and "finisher" in expl and "proxy" not in expl[: expl.find("finisher") + 20]:
            # finisher language without proxy context
            if "rim finisher" in expl or "efficient rim finisher" in expl:
                finisher_phrase.append((row["player_name"], expl[:120]))
        if row["rim_tracked"] and float(row["rim_rate"] or 0) < 0.22:
            # stretch profile but tracked — should not read as paint big
            if "finisher" in expl and "low rim frequency" not in expl:
                finisher_phrase.append((row["player_name"], "tracked low-rim: " + expl[:100]))

    print(f"  Stretch forwards (high 3PA rate, n={len(stretch)}): {len(rim_top)} have rim_pressure #1")
    print(f"  Label violations (estimated but not Proxy label): {len(label_violations)}")
    print(f"  Misleading finisher phrasing in #1 explanation: {len(finisher_phrase)}")
    for v in label_violations[:5]:
        print(f"    LABEL: {v}")
    for v in finisher_phrase[:5]:
        print(f"    TEXT: {v[0]} — {v[1]}...")
    if label_violations or finisher_phrase:
        failures += 1
        print("  STATUS: FAIL")

    # --- 6. Low-minute leverage ---
    section("6. Low-minute players (should not dominate Development Leverage)")
    lev = lev.merge(players[["player_id", "mpg", "player_name"]], on="player_id")
    top20 = lev.nlargest(20, "development_leverage_score")
    low_in_top20 = top20[top20["mpg"] < 14]
    low_top10 = lev[lev["mpg"] < 12].nlargest(10, "development_leverage_score")
    print(f"  Top 20 leverage: {len(low_in_top20)} with MPG < 14")
    for _, r in low_in_top20.iterrows():
        print(f"    - {r['player_name']}: MPG={r['mpg']:.1f} DLS={r['development_leverage_score']:.1f}")
    print(f"  Highest leverage among MPG<12 (should be rare):")
    for _, r in low_top10.head(5).iterrows():
        print(f"    - {r['player_name']}: MPG={r['mpg']:.1f} DLS={r['development_leverage_score']:.1f}")
    # Also: correlation mpg vs leverage (expect positive)
    corr = lev["mpg"].corr(lev["development_leverage_score"])
    print(f"  Correlation(MPG, leverage score): {corr:.3f}")
    if len(low_in_top20) >= 4 or corr < 0.15:
        failures += 1
        print("  STATUS: FAIL (too many low-minute in top leverage or weak MPG correlation)")

    # --- 7. Missing data / confidence ---
    section("7. Missing data (low completeness → lower opportunity, not fake highs)")
    OFFICIAL = {"tracking", "official", "synergy", "sports_reference", "hoop_explorer"}

    def completeness(row: pd.Series) -> float:
        parts = []
        src = str(row.get("shot_profile_source", "") or "").lower()
        parts.append(1.0 if src in OFFICIAL else 0.0)
        for col in ("bpm", "dbpm", "obpm", "assist_turnover_ratio", "fouls_per_40"):
            parts.append(1.0 if pd.notna(row.get(col)) else 0.0)
        core = ("three_point_pct", "efg_pct", "turnover_rate", "ts_pct")
        parts.append(sum(1 for c in core if pd.notna(row.get(c))) / len(core))
        return float(np.mean(parts))

    qualified["data_completeness"] = qualified.apply(completeness, axis=1)
    opps_long = opps.melt(id_vars=["player_id"], var_name="metric", value_name="opp")
    opps_long["skill"] = opps_long["metric"].str.replace("_opportunity", "")

    low_data = qualified[qualified["data_completeness"] < 0.45]
    high_opp_low_data = []
    for pid in low_data["player_id"]:
        row = opps[opps["player_id"] == pid]
        if row.empty:
            continue
        vals = row.iloc[0, 1:].astype(float)
        if vals.max() >= 70:  # normalized opportunity still high
            high_opp_low_data.append(
                (
                    qualified.loc[qualified["player_id"] == pid, "player_name"].iloc[0],
                    qualified.loc[qualified["player_id"] == pid, "data_completeness"].iloc[0],
                    vals.idxmax(),
                    vals.max(),
                )
            )
    print(f"  Low completeness players (<0.45): n={len(low_data)}")
    print(f"  With any normalized opportunity ≥70: {len(high_opp_low_data)}")
    for h in high_opp_low_data[:8]:
        print(f"    - {h[0]}: completeness={h[1]:.2f}, max {h[2]}={h[3]:.1f}")
    corr_comp = qualified["data_completeness"].corr(
        opps[[c for c in opps.columns if c.endswith("_opportunity")]].max(axis=1)
    )
    print(f"  Correlation(completeness, max opportunity): {corr_comp:.3f}")
    if len(high_opp_low_data) > len(low_data) * 0.08:
        failures += 1
        print("  STATUS: WARN (>8% sparse players still peak opp ≥70)")

    # Center low-volume 3PT guardrail
    section("8. Center low-volume 3PT guardrail")
    from models.shot_profile import (
        center_position_median_three_point_attempt_rate,
        player_three_point_attempt_rate,
    )

    c_med = center_position_median_three_point_attempt_rate(qualified)
    centers = qualified[qualified["_pos"] == "C"].copy()
    centers["_tpa"] = centers["three_point_attempts"].fillna(0).astype(int)
    centers["_tpar"] = centers.apply(player_three_point_attempt_rate, axis=1)
    low_vol = centers[
        (centers["_tpa"] < 30) | (centers["_tpar"] < c_med * 0.5)
    ]
    rim_only = centers[centers["_tpa"] <= 5]
    shoot_pri = pri[pri["skill_category"] == "shooting"]
    low_bad = shoot_pri[
        shoot_pri["player_id"].isin(low_vol["player_id"]) & (shoot_pri["actionable"] == 1)
    ]
    rim_bad = shoot_pri[
        shoot_pri["player_id"].isin(rim_only["player_id"]) & (shoot_pri["actionable"] == 1)
    ]
    print(f"  Low-volume centers (n={len(low_vol)}): actionable shooting rows = {len(low_bad)}")
    print(f"  Rim-only centers (3PA<=5, n={len(rim_only)}): actionable shooting rows = {len(rim_bad)}")
    if len(low_bad) or len(rim_bad):
        failures += 1
        print("  STATUS: FAIL (low-volume / rim-only center has actionable Three-Point Shooting)")

    # Guard dominance guardrail
    section("9. Ball Security guard dominance (should not be every guard)")
    guards = qualified[qualified["_pos"] == "G"]
    lev_g = lev.merge(guards[["player_id", "player_name"]], on="player_id", how="inner")
    bs_top1 = (lev_g["top_priority"] == "ball_security").mean()
    bs_top3 = 0
    for pid in guards["player_id"]:
        pp = pri[pri["player_id"] == pid]
        if "ball_security" in top_priority_skills(pp, 3):
            bs_top3 += 1
    bs_top3_rate = bs_top3 / max(len(guards), 1)
    print(f"  Guards (n={len(guards)}): ball_security #1 = {bs_top1:.0%}, in top 3 = {bs_top3_rate:.0%}")
    if bs_top1 > 0.50:
        failures += 1
        print("  STATUS: FAIL (>50% of guards have ball_security as #1 — over-dominant)")
    elif bs_top1 > 0.40:
        print("  STATUS: note — {:.0%} of guards #1 ball_security (watch but OK if turnover cohort on target)".format(bs_top1))

    metrics = {
        "elite_shooting_top1": len(top_rows),
        "elite_shooting_bad": len(bad_elite),
        "ht_guard_ball_sec_top3": rate,
        "foul_big_top3": hit / max(len(foul_big), 1),
        "drb_top3": drb_rate,
        "orb_top3": orb_rate,
        "low_min_top20": len(low_in_top20),
        "mpg_lev_corr": corr,
        "guard_ball_sec_top1": bs_top1,
    }

    section("BEFORE / AFTER (key checks)")
    print(f"  {'Metric':<42} {'Before':>10} {'After':>10}")
    print(f"  {'-'*42} {'-'*10} {'-'*10}")
    rows = [
        ("Elite w/ shooting #1 (bad)", f"{BASELINE['elite_shooting_bad']}", f"{metrics['elite_shooting_bad']}"),
        (
            "HT guard: ball_security in top 3",
            f"{BASELINE['ht_guard_ball_sec_top3']:.0%}",
            f"{metrics['ht_guard_ball_sec_top3']:.0%}",
        ),
        ("Foul-prone C: foul_disc in top 3", f"{BASELINE['foul_big_top3']:.0%}", f"{metrics['foul_big_top3']:.0%}"),
        ("Poor DRB + team need: DRB top 3", f"{BASELINE['drb_top3']:.0%}", f"{metrics['drb_top3']:.0%}"),
        ("Poor ORB + team need: ORB top 3", f"{BASELINE['orb_top3']:.0%}", f"{metrics['orb_top3']:.0%}"),
        ("Top-20 leverage with MPG < 14", f"{BASELINE['low_min_top20']}", f"{metrics['low_min_top20']}"),
        ("MPG ↔ leverage correlation", f"{BASELINE['mpg_lev_corr']:.3f}", f"{metrics['mpg_lev_corr']:.3f}"),
        (
            "Guards: ball_security #1",
            "—" if BASELINE["guard_ball_sec_top1"] is None else f"{BASELINE['guard_ball_sec_top1']:.0%}",
            f"{metrics['guard_ball_sec_top1']:.0%}",
        ),
    ]
    for label, before, after in rows:
        print(f"  {label:<42} {before:>10} {after:>10}")

    # Summary
    section("SUMMARY")
    target_ht = 0.65 <= metrics["ht_guard_ball_sec_top3"] <= 0.85
    if not target_ht:
        failures += 1
        print(
            f"  High-turnover guard check: {metrics['ht_guard_ball_sec_top3']:.0%} "
            f"(target 65–75%)"
        )
    if failures:
        print(f"  {failures} check group(s) flagged FAIL/WARN — review samples above.")
        return 1
    print("  All checks within thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
