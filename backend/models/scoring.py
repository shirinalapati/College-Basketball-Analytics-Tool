"""
DevelopmentIQ scoring engine.
Computes team needs, player opportunities, development priorities, and leverage scores.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SKILL_CATEGORIES = [
    "shooting",
    "free_throw",
    "ball_security",
    "defensive_rebounding",
    "offensive_rebounding",
    "foul_discipline",
    "playmaking",
    "defensive_activity",
    "rim_pressure",
]

SKILL_LABELS = {
    "shooting": "Three-Point Shooting",
    "free_throw": "Free Throw Shooting",
    "ball_security": "Ball Security / Turnover Reduction",
    "defensive_rebounding": "Defensive Rebounding",
    "offensive_rebounding": "Offensive Rebounding",
    "foul_discipline": "Foul Discipline",
    "playmaking": "Playmaking / Assist Creation",
    "defensive_activity": "Defensive Activity",
    "rim_pressure": "Rim Pressure / Finishing",
}

# Default realism (0-100) and basketball impact value
REALISM_DEFAULTS = {
    "free_throw": 88,
    "ball_security": 82,
    "foul_discipline": 80,
    "defensive_rebounding": 65,
    "offensive_rebounding": 62,
    "shooting": 58,
    "rim_pressure": 60,
    "playmaking": 48,
    "defensive_activity": 45,
}

IMPACT_DEFAULTS = {
    "ball_security": 90,
    "shooting": 88,
    "defensive_rebounding": 84,
    "foul_discipline": 80,
    "playmaking": 78,
    "defensive_activity": 78,
    "rim_pressure": 76,
    "free_throw": 74,
    "offensive_rebounding": 72,
}

# Team stat columns used to derive needs (higher raw = worse for team when inverted)
TEAM_NEED_MAP = {
    "shooting": ("three_point_rate", "efg_pct", False),  # low 3PA rate / low eFG
    "free_throw": ("free_throw_rate", None, False),
    "ball_security": ("turnover_rate", None, True),  # high TOV = high need
    "offensive_rebounding": ("offensive_rebound_rate", None, False),
    "defensive_rebounding": ("defensive_rebound_rate", None, False),
    "foul_discipline": ("foul_rate", None, True),
    "playmaking": ("assist_rate", None, False),
    "defensive_activity": ("steal_rate", "block_rate", False),
    "rim_pressure": ("efg_pct", "free_throw_rate", False),
}

# Player stat columns for opportunity (low value = high opportunity when invert)
PLAYER_OPP_MAP = {
    "shooting": ("three_point_pct", "efg_pct"),
    "free_throw": ("free_throw_pct",),
    "ball_security": ("turnover_rate",),
    "offensive_rebounding": ("offensive_rebound_rate",),
    "defensive_rebounding": ("defensive_rebound_rate",),
    "foul_discipline": ("foul_rate",),
    "playmaking": ("assist_rate",),
    "defensive_activity": ("steal_rate", "block_rate"),
    "rim_pressure": ("ts_pct", "efg_pct"),
}

HIGHER_IS_WORSE_OPP = {"ball_security", "foul_discipline"}


def normalize_series(s: pd.Series, invert: bool = False) -> pd.Series:
    """Normalize to 0-100 scale using min-max across series."""
    if s.empty or s.nunique() <= 1:
        return pd.Series(50.0, index=s.index)
    mn, mx = s.min(), s.max()
    if mx == mn:
        out = pd.Series(50.0, index=s.index)
    else:
        out = (s - mn) / (mx - mn) * 100
    if invert:
        out = 100 - out
    return out.clip(0, 100)


class ScoringEngine:
    """Compute all DevelopmentIQ scores from teams and players DataFrames."""

    def __init__(self, teams: pd.DataFrame, players: pd.DataFrame):
        self.teams = teams.copy()
        self.players = players.copy()
        self.field_avg: dict[str, float] = {}

    def run_all(self) -> dict[str, pd.DataFrame]:
        self._compute_field_averages()
        team_needs = self.compute_team_needs()
        player_opps = self.compute_player_opportunities()
        priorities = self.compute_development_priorities(team_needs, player_opps)
        leverage = self.compute_development_leverage(team_needs, priorities)
        return {
            "team_need_scores": team_needs,
            "player_opportunity_scores": player_opps,
            "development_priority_scores": priorities,
            "development_leverage_scores": leverage,
        }

    def _compute_field_averages(self) -> None:
        for col in [
            "efg_pct", "three_point_pct", "free_throw_pct", "turnover_rate",
            "offensive_rebound_rate", "defensive_rebound_rate", "steal_rate",
            "block_rate", "foul_rate", "assist_rate", "ts_pct", "usage_rate",
        ]:
            if col in self.players.columns:
                self.field_avg[col] = float(self.players[col].mean())

    def compute_team_needs(self) -> pd.DataFrame:
        rows = []
        for _, team in self.teams.iterrows():
            tid = team["team_id"]
            scores = {}
            for skill in SKILL_CATEGORIES:
                need = self._team_need_for_skill(team, skill)
                scores[skill] = need
            row = {"team_id": tid, **{f"{s}_need": scores[s] for s in SKILL_CATEGORIES}}
            rows.append(row)
        df = pd.DataFrame(rows)
        # Re-normalize each need column across teams for interpretability
        for skill in SKILL_CATEGORIES:
            col = f"{skill}_need"
            raw = df[col]
            df[col] = normalize_series(raw, invert=False)
        return df

    def _team_need_for_skill(self, team: pd.Series, skill: str) -> float:
        mapping = TEAM_NEED_MAP[skill]
        vals = []
        if skill == "shooting":
            # Poor spacing: low 3P rate component + low team eFG on threes proxy via efg
            tpr = 1 - (team.get("three_point_rate", 0.35) or 0.35)
            efg_short = 1 - (team.get("efg_pct", 0.50) or 0.50)
            vals = [tpr * 100, efg_short * 100]
        elif skill == "ball_security":
            vals = [(team.get("turnover_rate", 0.18) or 0.18) * 400]
        elif skill == "foul_discipline":
            vals = [(team.get("foul_rate", 0.20) or 0.20) * 350]
        elif skill == "defensive_rebounding":
            dr = team.get("defensive_rebound_rate", 0.28) or 0.28
            vals = [(1 - dr) * 120]
        elif skill == "offensive_rebounding":
            or_ = team.get("offensive_rebound_rate", 0.28) or 0.28
            vals = [(1 - or_) * 120]
        elif skill == "playmaking":
            ar = team.get("assist_rate", 0.50) or 0.50
            vals = [(1 - ar) * 100]
        elif skill == "defensive_activity":
            st = team.get("steal_rate", 0.09) or 0.09
            bl = team.get("block_rate", 0.08) or 0.08
            drtg = team.get("defensive_rating", 100) or 100
            vals = [(1 - st / 0.12) * 50, (1 - bl / 0.12) * 50, (drtg - 95) / 15 * 50]
        elif skill == "free_throw":
            ftr = team.get("free_throw_rate", 0.32) or 0.32
            vals = [(1 - ftr) * 80]
        elif skill == "rim_pressure":
            efg = team.get("efg_pct", 0.50) or 0.50
            ftr = team.get("free_throw_rate", 0.32) or 0.32
            vals = [(1 - efg) * 90, (1 - ftr) * 60]
        return float(np.mean(vals)) if vals else 50.0

    def compute_player_opportunities(self) -> pd.DataFrame:
        rows = []
        qualified = self.players[self.players["mpg"] >= 10].copy()

        for skill in SKILL_CATEGORIES:
            cols = PLAYER_OPP_MAP[skill]
            invert = skill in HIGHER_IS_WORSE_OPP

        for _, player in qualified.iterrows():
            pid = player["player_id"]
            pos = player.get("position", "G")
            pos_peers = qualified[qualified["position"] == pos]
            team_peers = qualified[qualified["team_id"] == player["team_id"]]

            scores = {}
            for skill in SKILL_CATEGORIES:
                scores[skill] = self._player_opp_for_skill(
                    player, skill, pos_peers, team_peers, qualified
                )
            row = {"player_id": pid, **{f"{s}_opportunity": scores[s] for s in SKILL_CATEGORIES}}
            rows.append(row)

        df = pd.DataFrame(rows)
        for skill in SKILL_CATEGORIES:
            col = f"{skill}_opportunity"
            df[col] = normalize_series(df[col], invert=False)
        return df

    def _player_opp_for_skill(
        self,
        player: pd.Series,
        skill: str,
        pos_peers: pd.DataFrame,
        team_peers: pd.DataFrame,
        field: pd.DataFrame,
    ) -> float:
        invert = skill in HIGHER_IS_WORSE_OPP
        cols = PLAYER_OPP_MAP[skill]
        gaps = []

        for col in cols:
            if col not in player.index:
                continue
            val = player.get(col)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                continue
            pos_med = pos_peers[col].median() if len(pos_peers) else self.field_avg.get(col, val)
            field_med = field[col].median() if len(field) else self.field_avg.get(col, val)

            if invert:
                # Higher stat = more opportunity (e.g. turnovers, fouls)
                gap_pos = max(0, val - pos_med) / (max(pos_peers[col].max(), 0.001) + 0.001) * 100
                gap_field = max(0, val - field_med) / (max(field[col].max(), 0.001) + 0.001) * 100
            else:
                gap_pos = max(0, pos_med - val) / (max(pos_med, 0.001)) * 100
                gap_field = max(0, field_med - val) / (max(field_med, 0.001)) * 100
            gaps.extend([gap_pos, gap_field])

        if skill == "shooting" and player.get("three_point_attempts", 0) < 30:
            gaps = [g * 0.5 for g in gaps]  # low volume dampens shooting opp

        return float(np.mean(gaps)) if gaps else 40.0

    def compute_development_priorities(
        self,
        team_needs: pd.DataFrame,
        player_opps: pd.DataFrame,
    ) -> pd.DataFrame:
        rows = []
        needs_by_team = team_needs.set_index("team_id")
        opps_by_player = player_opps.set_index("player_id")

        mpg_max = self.players["mpg"].max() or 35

        for _, player in self.players.iterrows():
            if player["mpg"] < 10:
                continue
            pid = player["player_id"]
            tid = player["team_id"]
            if tid not in needs_by_team.index or pid not in opps_by_player.index:
                continue

            team_need = needs_by_team.loc[tid]
            player_opp = opps_by_player.loc[pid]
            role_leverage = min(100, (player["mpg"] / mpg_max) * 100)

            for skill in SKILL_CATEGORIES:
                opp = float(player_opp[f"{skill}_opportunity"])
                need = float(team_need[f"{skill}_need"])
                realism = REALISM_DEFAULTS[skill]
                impact = IMPACT_DEFAULTS[skill]

                dps = (
                    0.30 * opp
                    + 0.30 * need
                    + 0.20 * role_leverage
                    + 0.10 * realism
                    + 0.10 * impact
                )

                projected = self._projected_impact(player, skill, self.teams, tid)
                explanation = self._build_explanation(
                    player, skill, opp, need, role_leverage, projected
                )

                rows.append({
                    "player_id": pid,
                    "team_id": tid,
                    "skill_category": skill,
                    "development_priority_score": round(dps, 2),
                    "player_improvement_opportunity": round(opp, 2),
                    "team_need_alignment": round(need, 2),
                    "role_leverage": round(role_leverage, 2),
                    "improvement_realism": realism,
                    "basketball_impact_value": impact,
                    "projected_points_added": round(projected, 2),
                    "explanation": explanation,
                })

        return pd.DataFrame(rows)

    def _projected_impact(
        self, player: pd.Series, skill: str, teams: pd.DataFrame, team_id: str
    ) -> float:
        team = teams[teams["team_id"] == team_id]
        ppp = 1.05
        if not team.empty:
            ortg = team.iloc[0].get("offensive_rating", 105) or 105
            pace = team.iloc[0].get("pace", 68) or 68
            ppp = ortg / 100

        games = max(player.get("games_played", 30), 1)
        minutes = player.get("minutes", 500) or 500

        if skill == "shooting":
            cur = player.get("three_point_pct", 0.30) or 0.30
            tpa = player.get("three_point_attempts", 50) or 50
            target = min(cur + 0.04, 0.38)
            return tpa * (target - cur) * 3

        if skill == "free_throw":
            cur = player.get("free_throw_pct", 0.70) or 0.70
            fta = player.get("free_throw_attempts", 40) or 40
            target = min(cur + 0.07, 0.80)
            return fta * (target - cur)

        if skill == "ball_security":
            tov_rate = player.get("turnover_rate", 0.15) or 0.15
            usage = player.get("usage_rate", 0.20) or 0.20
            est_tov = minutes * usage * tov_rate * 0.02
            prevented = est_tov * 0.10
            return prevented * ppp

        if skill == "foul_discipline":
            foul_r = player.get("foul_rate", 0.04) or 0.04
            est_fouls = minutes * foul_r * 0.5
            reduced = est_fouls * 0.10
            return reduced * 0.7

        if skill == "defensive_rebounding":
            dr = player.get("defensive_rebound_rate", 0.12) or 0.12
            delta = 0.02
            missed = minutes * 0.8
            extra = missed * delta
            return extra * 1.1

        if skill == "offensive_rebounding":
            or_ = player.get("offensive_rebound_rate", 0.08) or 0.08
            delta = 0.02
            missed = minutes * 0.7
            extra = missed * delta
            return extra * 1.15

        if skill == "playmaking":
            ar = player.get("assist_rate", 0.10) or 0.10
            extra_assists = minutes * ar * 0.05
            return extra_assists * 1.5

        if skill == "defensive_activity":
            st = player.get("steal_rate", 0.02) or 0.02
            bl = player.get("block_rate", 0.02) or 0.02
            extra = minutes * (st + bl) * 0.08
            return extra * 1.2

        if skill == "rim_pressure":
            ts = player.get("ts_pct", 0.52) or 0.52
            target_ts = min(ts + 0.03, 0.58)
            fga_proxy = minutes * 0.35
            return fga_proxy * (target_ts - ts) * 0.8

        return 0.0

    def _build_explanation(
        self,
        player: pd.Series,
        skill: str,
        opp: float,
        need: float,
        role: float,
        projected: float,
    ) -> str:
        label = SKILL_LABELS[skill]
        name = player.get("player_name", "Player")
        mpg = player.get("mpg", 0)
        parts = []
        if opp >= 60:
            parts.append(f"{name} has significant room to improve in {label.lower()} relative to positional peers")
        elif opp >= 40:
            parts.append(f"{name} has moderate improvement opportunity in {label.lower()}")
        if need >= 60:
            parts.append("the team has a strong need in this area")
        elif need >= 40:
            parts.append("this skill aligns with moderate team needs")
        else:
            parts.append("team need for this skill is lower, reducing priority despite individual weakness")
        if role >= 65:
            parts.append(f"playing {mpg:.1f} MPG increases the value of improvement")
        if projected > 0:
            parts.append(f"a realistic improvement scenario projects ~{projected:.1f} points of value")
        return ". ".join(parts).capitalize() + "."

    def compute_development_leverage(
        self,
        team_needs: pd.DataFrame,
        priorities: pd.DataFrame,
    ) -> pd.DataFrame:
        rows = []
        for pid in priorities["player_id"].unique():
            player_pri = priorities[priorities["player_id"] == pid]
            player = self.players[self.players["player_id"] == pid]
            if player.empty:
                continue
            player = player.iloc[0]
            tid = player["team_id"]

            top3 = player_pri.nlargest(3, "development_priority_score")
            top_priority = top3.iloc[0]["skill_category"] if len(top3) > 0 else ""
            second = top3.iloc[1]["skill_category"] if len(top3) > 1 else ""
            third = top3.iloc[2]["skill_category"] if len(top3) > 2 else ""

            ts = player.get("ts_pct", 0.52) or 0.52
            usage = player.get("usage_rate", 0.20) or 0.20
            ppg = player.get("ppg", 8) or 8
            production = normalize_series(
                pd.Series([ts * 100 + usage * 50 + ppg * 3]), invert=False
            ).iloc[0]

            upside = float(player_pri["development_priority_score"].nlargest(3).mean())
            team_row = team_needs[team_needs["team_id"] == tid]
            if not team_row.empty:
                need_cols = [f"{s}_need" for s in SKILL_CATEGORIES]
                team_need_vec = team_row.iloc[0][need_cols].astype(float)
                top_skills = top3["skill_category"].tolist()
                alignment = float(
                    np.mean([team_need_vec.get(f"{s}_need", 50) for s in top_skills])
                )
            else:
                alignment = 50.0

            mpg = player.get("mpg", 15) or 15
            role_lev = min(100, mpg / 35 * 100)

            class_year = str(player.get("class_year", "Jr"))
            runway_map = {"Fr": 85, "So": 80, "Jr": 70, "Sr": 55, "Gr": 50}
            runway = runway_map.get(class_year[:2], 70)

            dls = (
                0.30 * production
                + 0.25 * upside
                + 0.20 * alignment
                + 0.15 * role_lev
                + 0.10 * runway
            )

            rows.append({
                "player_id": pid,
                "team_id": tid,
                "development_leverage_score": round(dls, 2),
                "top_priority": top_priority,
                "second_priority": second,
                "third_priority": third,
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df["development_leverage_score"] = normalize_series(
                df["development_leverage_score"], invert=False
            )
        return df
