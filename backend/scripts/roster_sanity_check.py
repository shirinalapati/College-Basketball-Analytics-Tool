"""
Automated player/roster sanity checks before submission.

Usage:
  python scripts/roster_sanity_check.py
  python scripts/roster_sanity_check.py --fail-on-warn
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parent))

from ingest_sports_reference import DATA_DIR
from models.scoring import ScoringEngine
from roster_status import load_roster_status_rows

# Known elite shooters — top priority should not be shooting unless explained by zero projection
ELITE_SHOOTERS = [
    ("Milan Momcilovic", 0.36, 80),
    ("Stefan Vaaks", 0.34, 80),
]

GUARD_NATURAL = {"shooting", "ball_security", "playmaking", "defensive_activity", "free_throw", "rim_pressure"}
BIG_NATURAL = {"defensive_rebounding", "offensive_rebounding", "foul_discipline", "rim_pressure", "defensive_activity"}
WING_NATURAL = GUARD_NATURAL | {"defensive_rebounding", "offensive_rebounding"}

MAX_GUARD_ORB_TOP_PCT = 0.12
MAX_BIG_PLAYMAKING_TOP_PCT = 0.20


class Finding:
    def __init__(self, level: str, category: str, message: str):
        self.level = level
        self.category = category
        self.message = message


def check_shooting_strength_vs_priority(
    players: pd.DataFrame, leverage: pd.DataFrame, priorities: pd.DataFrame
) -> list[Finding]:
    findings: list[Finding] = []
    for name, min_3p, min_att in ELITE_SHOOTERS:
        p = players[players["player_name"].str.contains(name.split()[-1], case=False, na=False)]
        if p.empty:
            continue
        row = p.iloc[0]
        if float(row.get("three_point_pct", 0)) < min_3p or int(row.get("three_point_attempts", 0)) < min_att:
            continue
        pid = row["player_id"]
        top = leverage[leverage["player_id"] == pid]
        if top.empty:
            continue
        top_skill = top.iloc[0]["top_priority"]
        shoot_opp = priorities[
            (priorities["player_id"] == pid) & (priorities["skill_category"] == "shooting")
        ]["player_improvement_opportunity"]
        opp = float(shoot_opp.iloc[0]) if len(shoot_opp) else 99
        if top_skill == "shooting" and opp < 25:
            findings.append(
                Finding(
                    "WARN",
                    "shooting",
                    f"{row['player_name']}: elite shooter ({row['three_point_pct']*100:.1f}% on "
                    f"{int(row['three_point_attempts'])} 3PA) labeled top priority shooting (opp={opp:.0f})",
                )
            )
        elif top_skill != "shooting" and opp <= 20:
            findings.append(
                Finding(
                    "OK",
                    "shooting",
                    f"{row['player_name']}: shooter strength recognized (top={top_skill}, shoot opp={opp:.0f})",
                )
            )
    return findings


def check_position_top_priority_mix(leverage: pd.DataFrame, players: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    merged = leverage.merge(players[["player_id", "position"]], on="player_id")

    guards = merged[merged["position"] == "G"]
    if len(guards):
        orb_pct = (guards["top_priority"] == "offensive_rebounding").mean()
        if orb_pct > MAX_GUARD_ORB_TOP_PCT:
            findings.append(
                Finding(
                    "WARN",
                    "position",
                    f"Guards: {orb_pct*100:.1f}% top priority = offensive rebounding "
                    f"(target ≤{MAX_GUARD_ORB_TOP_PCT*100:.0f}%)",
                )
            )
        else:
            findings.append(
                Finding(
                    "OK",
                    "position",
                    f"Guards: {orb_pct*100:.1f}% top priority ORB (within target)",
                )
            )
        unnatural = guards[~guards["top_priority"].isin(GUARD_NATURAL)]
        if len(unnatural) > len(guards) * 0.05:
            findings.append(
                Finding(
                    "WARN",
                    "position",
                    f"Guards: {len(unnatural)} with uncommon top priorities "
                    f"({unnatural['top_priority'].value_counts().head(3).to_dict()})",
                )
            )

    bigs = merged[merged["position"] == "C"]
    if len(bigs):
        pm_pct = (bigs["top_priority"] == "playmaking").mean()
        if pm_pct > MAX_BIG_PLAYMAKING_TOP_PCT:
            findings.append(
                Finding(
                    "WARN",
                    "position",
                    f"Bigs: {pm_pct*100:.1f}% top priority = playmaking (target ≤{MAX_BIG_PLAYMAKING_TOP_PCT*100:.0f}%)",
                )
            )

    return findings


def check_foul_discipline_big(
    players: pd.DataFrame, leverage: pd.DataFrame, priorities: pd.DataFrame
) -> list[Finding]:
    findings: list[Finding] = []
    bigs = players[(players["position"] == "C") & (players["mpg"] >= 15)]
    pool_foul = float(players["foul_rate"].median())
    for _, row in bigs.iterrows():
        if float(row.get("foul_rate", 0)) < pool_foul * 1.25:
            continue
        pid = row["player_id"]
        top = leverage[leverage["player_id"] == pid]
        if top.empty:
            continue
        if top.iloc[0]["top_priority"] == "foul_discipline":
            continue
        foul_opp = priorities[
            (priorities["player_id"] == pid) & (priorities["skill_category"] == "foul_discipline")
        ]["player_improvement_opportunity"]
        if len(foul_opp) and float(foul_opp.iloc[0]) >= 50:
            findings.append(
                Finding(
                    "INFO",
                    "fouls",
                    f"{row['player_name']}: high foul rate but top={top.iloc[0]['top_priority']} "
                    f"(foul opp={float(foul_opp.iloc[0]):.0f})",
                )
            )
    return findings[:8]


def check_roster_status_overrides(players: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    for row in load_roster_status_rows():
        name = row["player_name"]
        new_tid = row["new_team"]
        old_tid = row["old_team"]
        p = players[players["player_name"].str.lower() == name.lower()]
        if row["status"] in ("transferred_in", "transferred", "committed") and new_tid:
            on_new = p[p["team_id"] == new_tid]
            on_old = p[p["team_id"] == old_tid] if old_tid else pd.DataFrame()
            if on_new.empty:
                findings.append(
                    Finding("FAIL", "roster", f"{name}: expected on {new_tid} per roster_status.csv — MISSING")
                )
            if not on_old.empty:
                findings.append(
                    Finding("FAIL", "roster", f"{name}: still listed on old team {old_tid} — remove stale row")
                )
            elif on_new.empty is False:
                findings.append(
                    Finding("OK", "roster", f"{name}: correctly on {new_tid}")
                )
    # Aberdeen explicit
    ab = players[players["player_name"].str.contains("Aberdeen", case=False, na=False)]
    if not ab.empty and ab.iloc[0]["team_id"] == "kentucky":
        findings.append(Finding("FAIL", "roster", "Denzel Aberdeen still on Kentucky — fix roster_status.csv"))
    elif not ab.empty and ab.iloc[0]["team_id"] == "florida":
        findings.append(Finding("OK", "roster", "Denzel Aberdeen on Florida (not Kentucky)"))
    return findings


def check_high_usage_turnovers(
    players: pd.DataFrame, leverage: pd.DataFrame
) -> list[Finding]:
    findings: list[Finding] = []
    guards = players[(players["position"] == "G") & (players["usage_rate"] >= 0.22)]
    pool_tov = float(players["turnover_rate"].median())
    for _, row in guards.iterrows():
        if float(row["turnover_rate"]) < pool_tov * 1.15:
            continue
        top = leverage[leverage["player_id"] == row["player_id"]]
        if top.empty:
            continue
        skill = top.iloc[0]["top_priority"]
        if skill in ("ball_security", "playmaking"):
            findings.append(
                Finding(
                    "OK",
                    "usage",
                    f"{row['player_name']}: high TOV → top {skill} (reasonable)",
                )
            )
            break
    return findings[:3]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit 1 if any WARN/FAIL")
    args = parser.parse_args()

    players = pd.read_csv(DATA_DIR / "players_demo.csv")
    players = players[(players["mpg"] >= 10) | (players["minutes"] >= 250)]

    engine = ScoringEngine(pd.read_csv(DATA_DIR / "teams_demo.csv"), players)
    res = engine.run_all()
    leverage = res["development_leverage_scores"]
    priorities = res["development_priority_scores"]

    all_findings: list[Finding] = []
    all_findings.extend(check_roster_status_overrides(players))
    all_findings.extend(check_shooting_strength_vs_priority(players, leverage, priorities))
    all_findings.extend(check_position_top_priority_mix(leverage, players))
    all_findings.extend(check_foul_discipline_big(players, leverage, priorities))
    all_findings.extend(check_high_usage_turnovers(players, leverage))

    print("# Roster & model sanity check\n")
    for level in ("FAIL", "WARN", "INFO", "OK"):
        items = [f for f in all_findings if f.level == level]
        if not items:
            continue
        print(f"## {level} ({len(items)})\n")
        for f in items:
            print(f"- [{f.category}] {f.message}")
        print()

    fails = sum(1 for f in all_findings if f.level == "FAIL")
    warns = sum(1 for f in all_findings if f.level == "WARN")
    oks = sum(1 for f in all_findings if f.level == "OK")
    print(f"**Summary:** {oks} OK · {warns} WARN · {fails} FAIL")

    out = DATA_DIR / "sanity_check_report.md"
    lines = ["# Roster & model sanity check\n"]
    for level in ("FAIL", "WARN", "INFO", "OK"):
        items = [f for f in all_findings if f.level == level]
        if items:
            lines.append(f"## {level}\n")
            for f in items:
                lines.append(f"- [{f.category}] {f.message}")
            lines.append("")
    lines.append(f"**Summary:** {oks} OK · {warns} WARN · {fails} FAIL\n")
    out.write_text("\n".join(lines))
    print(f"\nWrote {out}")

    if args.fail_on_warn and (fails or warns):
        sys.exit(1)


if __name__ == "__main__":
    main()
