"""
Seed SQLite database from demo CSVs and run scoring engine.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.class_year import add_projected_class_year
from models.scoring import ScoringEngine, SKILL_CATEGORIES

DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "developmentiq.db"


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS teams (
        team_id TEXT PRIMARY KEY,
        team_name TEXT NOT NULL,
        conference TEXT,
        season INTEGER,
        games_played INTEGER,
        pace REAL,
        offensive_rating REAL,
        defensive_rating REAL,
        efg_pct REAL,
        three_point_rate REAL,
        three_point_pct REAL,
        free_throw_pct REAL,
        two_point_pct REAL,
        turnover_rate REAL,
        offensive_rebound_rate REAL,
        defensive_rebound_rate REAL,
        free_throw_rate REAL,
        assist_rate REAL,
        block_rate REAL,
        steal_rate REAL,
        foul_rate REAL,
        team_rim_attempt_rate REAL,
        team_rim_fg_pct REAL,
        data_source TEXT
    );

    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        player_name TEXT NOT NULL,
        team_id TEXT REFERENCES teams(team_id),
        position TEXT,
        class_year TEXT,
        class_year_2026_27 TEXT,
        games_played INTEGER,
        minutes REAL,
        mpg REAL,
        usage_rate REAL,
        points REAL,
        ppg REAL,
        efg_pct REAL,
        ts_pct REAL,
        three_point_attempts INTEGER,
        three_point_pct REAL,
        free_throw_attempts INTEGER,
        free_throw_pct REAL,
        turnover_rate REAL,
        assist_rate REAL,
        offensive_rebound_rate REAL,
        defensive_rebound_rate REAL,
        steal_rate REAL,
        block_rate REAL,
        foul_rate REAL,
        orb_per_game REAL,
        drb_per_game REAL,
        ast_per_game REAL,
        field_goal_attempts INTEGER,
        three_point_attempt_rate REAL,
        two_point_pct REAL,
        assist_turnover_ratio REAL,
        fouls_per_40 REAL,
        steal_pct REAL,
        block_pct REAL,
        bpm REAL,
        obpm REAL,
        dbpm REAL,
        per REAL,
        player_ortg REAL,
        player_drtg REAL,
        win_shares REAL,
        win_shares_per_40 REAL,
        shot_profile_source TEXT,
        rim_attempts INTEGER,
        rim_makes INTEGER,
        rim_fg_pct REAL,
        rim_attempt_rate REAL,
        midrange_attempts INTEGER,
        midrange_makes INTEGER,
        midrange_fg_pct REAL,
        midrange_attempt_rate REAL,
        corner_three_attempts INTEGER,
        corner_three_makes INTEGER,
        corner_three_pct REAL,
        corner_three_attempt_rate REAL,
        above_break_three_attempts INTEGER,
        above_break_three_makes INTEGER,
        above_break_three_pct REAL,
        above_break_three_attempt_rate REAL,
        assisted_rim_rate REAL,
        assisted_three_rate REAL,
        data_source TEXT
    );

    CREATE TABLE IF NOT EXISTS team_need_scores (
        team_id TEXT PRIMARY KEY REFERENCES teams(team_id),
        shooting_need REAL,
        free_throw_need REAL,
        ball_security_need REAL,
        offensive_rebounding_need REAL,
        defensive_rebounding_need REAL,
        foul_discipline_need REAL,
        playmaking_need REAL,
        defensive_activity_need REAL,
        rim_pressure_need REAL,
        need_explanations TEXT
    );

    CREATE TABLE IF NOT EXISTS player_opportunity_scores (
        player_id TEXT PRIMARY KEY REFERENCES players(player_id),
        shooting_opportunity REAL,
        free_throw_opportunity REAL,
        ball_security_opportunity REAL,
        offensive_rebounding_opportunity REAL,
        defensive_rebounding_opportunity REAL,
        foul_discipline_opportunity REAL,
        playmaking_opportunity REAL,
        defensive_activity_opportunity REAL,
        rim_pressure_opportunity REAL
    );

    CREATE TABLE IF NOT EXISTS development_priority_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id TEXT REFERENCES players(player_id),
        team_id TEXT REFERENCES teams(team_id),
        skill_category TEXT,
        development_priority_score REAL,
        raw_priority_score REAL,
        position_fit_multiplier REAL,
        player_improvement_opportunity REAL,
        team_need_alignment REAL,
        role_leverage REAL,
        improvement_realism REAL,
        basketball_impact_value REAL,
        projected_points_added REAL,
        actionable INTEGER DEFAULT 0,
        explanation TEXT,
        UNIQUE(player_id, skill_category)
    );

    CREATE TABLE IF NOT EXISTS development_leverage_scores (
        player_id TEXT PRIMARY KEY REFERENCES players(player_id),
        team_id TEXT REFERENCES teams(team_id),
        development_leverage_score REAL,
        top_priority TEXT,
        second_priority TEXT,
        third_priority TEXT
    );
    """)


def _weighted_rate(
    players: pd.DataFrame, team_col: str, att_col: str, pct_col: str
) -> pd.Series:
    att = players[att_col].fillna(0)
    makes = players[pct_col].fillna(0) * att
    grouped = players.assign(_makes=makes, _att=att).groupby(team_col)[["_makes", "_att"]].sum()
    return grouped["_makes"] / grouped["_att"].clip(lower=1)


def enrich_team_shooting_stats(teams: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """Fill team 3P%, FT%, and 2P% from rotation-weighted player stats when missing on teams CSV."""
    teams = teams.copy()
    for col in ("three_point_pct", "free_throw_pct", "two_point_pct"):
        if col not in teams.columns:
            teams[col] = float("nan")

    agg_3p = _weighted_rate(players, "team_id", "three_point_attempts", "three_point_pct")
    agg_ft = _weighted_rate(players, "team_id", "free_throw_attempts", "free_throw_pct")

    fga = players["field_goal_attempts"].fillna(0)
    tpa = players["three_point_attempts"].fillna(0)
    two_att = (fga - tpa).clip(lower=0)
    two_makes = players["two_point_pct"].fillna(0) * two_att
    grouped_2p = (
        players.assign(_makes=two_makes, _att=two_att)
        .groupby("team_id")[["_makes", "_att"]]
        .sum()
    )
    agg_2p = grouped_2p["_makes"] / grouped_2p["_att"].clip(lower=1)

    for col, agg in (
        ("three_point_pct", agg_3p),
        ("free_throw_pct", agg_ft),
        ("two_point_pct", agg_2p),
    ):
        missing = teams[col].isna()
        if missing.any():
            teams.loc[missing, col] = teams.loc[missing, "team_id"].map(agg)
    return teams


def enrich_team_rim_stats(teams: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """Aggregate tracked player rim attempts/makes into team-level rim splits."""
    teams = teams.copy()
    for col in ("team_rim_attempt_rate", "team_rim_fg_pct"):
        if col not in teams.columns:
            teams[col] = float("nan")

    required = {"team_id", "shot_profile_source", "rim_attempts", "rim_makes", "field_goal_attempts"}
    if not required.issubset(players.columns):
        return teams

    tracked = players[
        players["shot_profile_source"].astype(str).str.lower().isin(
            {"tracking", "official", "synergy", "sports_reference", "hoop_explorer"}
        )
    ].copy()
    if tracked.empty:
        return teams

    for col in ("rim_attempts", "rim_makes", "field_goal_attempts"):
        tracked[col] = pd.to_numeric(tracked[col], errors="coerce").fillna(0)

    grouped = tracked.groupby("team_id")[["rim_attempts", "rim_makes", "field_goal_attempts"]].sum()
    rim_attempt_rate = grouped["rim_attempts"] / grouped["field_goal_attempts"].clip(lower=1)
    rim_fg_pct = grouped["rim_makes"] / grouped["rim_attempts"].clip(lower=1)

    teams["team_rim_attempt_rate"] = teams["team_id"].map(rim_attempt_rate)
    teams["team_rim_fg_pct"] = teams["team_id"].map(rim_fg_pct)
    return teams


def load_and_score() -> None:
    teams_path = DATA_DIR / "teams_demo.csv"
    players_path = DATA_DIR / "players_demo.csv"
    if not teams_path.exists():
        from build_full_dataset import build
        build()

    teams = pd.read_csv(teams_path)
    players = pd.read_csv(players_path)
    players = add_projected_class_year(players)
    teams = enrich_team_shooting_stats(teams, players)
    teams = enrich_team_rim_stats(teams, players)
    teams.to_csv(teams_path, index=False)

    engine = ScoringEngine(teams, players)
    results = engine.run_all()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)

    teams.to_sql("teams", conn, if_exists="replace", index=False)
    players.to_sql("players", conn, if_exists="replace", index=False)
    results["team_need_scores"].to_sql("team_need_scores", conn, if_exists="replace", index=False)
    results["player_opportunity_scores"].to_sql(
        "player_opportunity_scores", conn, if_exists="replace", index=False
    )
    results["development_priority_scores"].to_sql(
        "development_priority_scores", conn, if_exists="replace", index=False
    )
    results["development_leverage_scores"].to_sql(
        "development_leverage_scores", conn, if_exists="replace", index=False
    )
    conn.close()
    print(f"Database seeded: {DB_PATH}")
    print(f"  Teams: {len(teams)}, Players: {len(players)}")
    print(f"  Priority rows: {len(results['development_priority_scores'])}")


if __name__ == "__main__":
    load_and_score()
