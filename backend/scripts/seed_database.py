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
        turnover_rate REAL,
        offensive_rebound_rate REAL,
        defensive_rebound_rate REAL,
        free_throw_rate REAL,
        assist_rate REAL,
        block_rate REAL,
        steal_rate REAL,
        foul_rate REAL,
        data_source TEXT
    );

    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        player_name TEXT NOT NULL,
        team_id TEXT REFERENCES teams(team_id),
        position TEXT,
        class_year TEXT,
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
        rim_pressure_need REAL
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
        player_improvement_opportunity REAL,
        team_need_alignment REAL,
        role_leverage REAL,
        improvement_realism REAL,
        basketball_impact_value REAL,
        projected_points_added REAL,
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


def load_and_score() -> None:
    teams_path = DATA_DIR / "teams_demo.csv"
    players_path = DATA_DIR / "players_demo.csv"
    if not teams_path.exists():
        from scripts.generate_demo_data import main as gen
        gen()

    teams = pd.read_csv(teams_path)
    players = pd.read_csv(players_path)

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
