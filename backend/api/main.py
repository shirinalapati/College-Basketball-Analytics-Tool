"""
DevelopmentIQ FastAPI backend.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "developmentiq.db"

app = FastAPI(
    title="DevelopmentIQ API",
    description="College Basketball Player Development Priority Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Database not initialized. Run: python scripts/seed_database.py",
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": "DevelopmentIQ API",
        "docs": "Use /docs for interactive API explorer",
        "health": "/api/health",
        "frontend": "Open http://localhost:5173 for the dashboard (npm run dev in frontend/)",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": str(DB_PATH.exists())}


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    conn = get_conn()
    teams = conn.execute("SELECT COUNT(*) as c FROM teams").fetchone()["c"]
    players = conn.execute("SELECT COUNT(*) as c FROM players").fetchone()["c"]
    conn.close()
    manifest_path = DB_PATH.parent / "data_manifest.json"
    manifest = {}
    if manifest_path.exists():
        import json
        manifest = json.loads(manifest_path.read_text())
    return {
        "teams_count": teams,
        "players_count": players,
        "season": 2025,
        "data_label": manifest.get("label", "DEMO DATA"),
        "description": manifest.get("description", ""),
    }


@app.get("/api/teams")
def list_teams() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM teams ORDER BY team_name"
    ).fetchall()
    conn.close()
    return rows_to_dicts(rows)


@app.get("/api/teams/{team_id}")
def get_team(team_id: str) -> dict:
    conn = get_conn()
    team = conn.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,)).fetchone()
    if not team:
        conn.close()
        raise HTTPException(404, "Team not found")
    needs = conn.execute(
        "SELECT * FROM team_need_scores WHERE team_id = ?", (team_id,)
    ).fetchone()
    conn.close()
    return {"team": dict(team), "needs": dict(needs) if needs else {}}


@app.get("/api/teams/{team_id}/players")
def team_players(team_id: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT p.*, d.development_leverage_score, d.top_priority, d.second_priority,
               d.third_priority
        FROM players p
        LEFT JOIN development_leverage_scores d ON p.player_id = d.player_id
        WHERE p.team_id = ?
        ORDER BY p.mpg DESC
        """,
        (team_id,),
    ).fetchall()
    conn.close()
    return rows_to_dicts(rows)


@app.get("/api/teams/{team_id}/development-board")
def development_board(team_id: str) -> list[dict]:
    conn = get_conn()
    players = conn.execute(
        "SELECT player_id, player_name, position, mpg FROM players WHERE team_id = ?",
        (team_id,),
    ).fetchall()
    board = []
    for pl in players:
        pid = pl["player_id"]
        top = conn.execute(
            """
            SELECT * FROM development_priority_scores
            WHERE player_id = ? ORDER BY development_priority_score DESC LIMIT 1
            """,
            (pid,),
        ).fetchone()
        lev = conn.execute(
            "SELECT development_leverage_score FROM development_leverage_scores WHERE player_id = ?",
            (pid,),
        ).fetchone()
        if top:
            board.append({
                "player_id": pid,
                "player_name": pl["player_name"],
                "position": pl["position"],
                "mpg": pl["mpg"],
                "top_priority": top["skill_category"],
                "development_priority_score": top["development_priority_score"],
                "projected_points_added": top["projected_points_added"],
                "development_leverage_score": lev["development_leverage_score"] if lev else None,
                "main_reason": top["explanation"],
            })
    conn.close()
    board.sort(key=lambda x: x.get("development_priority_score") or 0, reverse=True)
    return board


@app.get("/api/players/{player_id}")
def get_player(player_id: str) -> dict:
    conn = get_conn()
    player = conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
    if not player:
        conn.close()
        raise HTTPException(404, "Player not found")
    team = conn.execute(
        "SELECT * FROM teams WHERE team_id = ?", (player["team_id"],)
    ).fetchone()
    priorities = conn.execute(
        """
        SELECT * FROM development_priority_scores
        WHERE player_id = ? ORDER BY development_priority_score DESC
        """,
        (player_id,),
    ).fetchall()
    opps = conn.execute(
        "SELECT * FROM player_opportunity_scores WHERE player_id = ?", (player_id,)
    ).fetchone()
    leverage = conn.execute(
        "SELECT * FROM development_leverage_scores WHERE player_id = ?", (player_id,)
    ).fetchone()
    conn.close()
    return {
        "player": dict(player),
        "team": dict(team) if team else {},
        "priorities": rows_to_dicts(priorities),
        "opportunities": dict(opps) if opps else {},
        "leverage": dict(leverage) if leverage else {},
    }


@app.get("/api/leaderboard/leverage")
def leverage_leaderboard(
    limit: int = Query(50, le=200),
    team_id: str | None = None,
) -> list[dict]:
    conn = get_conn()
    q = """
        SELECT p.player_name, p.player_id, p.position, p.mpg, p.team_id,
               t.team_name, d.development_leverage_score, d.top_priority,
               d.second_priority, d.third_priority
        FROM development_leverage_scores d
        JOIN players p ON d.player_id = p.player_id
        JOIN teams t ON p.team_id = t.team_id
    """
    params: list[Any] = []
    if team_id:
        q += " WHERE p.team_id = ?"
        params.append(team_id)
    q += " ORDER BY d.development_leverage_score DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()

    result = []
    for row in rows:
        pid = row["player_id"]
        top = conn.execute(
            """
            SELECT skill_category, projected_points_added, team_need_alignment
            FROM development_priority_scores
            WHERE player_id = ? ORDER BY development_priority_score DESC LIMIT 1
            """,
            (pid,),
        ).fetchone()
        result.append({
            **dict(row),
            "projected_impact": top["projected_points_added"] if top else 0,
            "team_need_match": top["team_need_alignment"] if top else 0,
        })
    conn.close()
    return result


@app.get("/api/overview")
def overview() -> dict:
    conn = get_conn()
    meta_teams = conn.execute("SELECT COUNT(*) c FROM teams").fetchone()["c"]
    meta_players = conn.execute("SELECT COUNT(*) c FROM players").fetchone()["c"]

    # Aggregate top team needs across dataset
    need_cols = [
        "shooting_need", "ball_security_need", "defensive_rebounding_need",
        "foul_discipline_need", "playmaking_need", "free_throw_need",
        "offensive_rebounding_need", "defensive_activity_need", "rim_pressure_need",
    ]
    avgs = {}
    for col in need_cols:
        r = conn.execute(f"SELECT AVG({col}) as v FROM team_need_scores").fetchone()
        avgs[col] = round(r["v"], 1) if r["v"] else 0

    top_needs = sorted(
        [{"category": k.replace("_need", ""), "score": v} for k, v in avgs.items()],
        key=lambda x: x["score"],
        reverse=True,
    )[:5]

    leverage = conn.execute(
        """
        SELECT p.player_name, t.team_name, d.development_leverage_score, d.top_priority
        FROM development_leverage_scores d
        JOIN players p ON d.player_id = p.player_id
        JOIN teams t ON p.team_id = t.team_id
        ORDER BY d.development_leverage_score DESC LIMIT 10
        """
    ).fetchall()

    illinois = conn.execute(
        "SELECT * FROM team_need_scores WHERE team_id = 'illinois'"
    ).fetchone()
    conn.close()

    return {
        "teams_count": meta_teams,
        "players_count": meta_players,
        "top_team_needs": top_needs,
        "top_leverage_players": rows_to_dicts(leverage),
        "featured_team_id": "illinois",
        "featured_team_needs": dict(illinois) if illinois else {},
    }


@app.post("/api/simulate")
def simulate_impact(body: dict[str, Any]) -> dict:
    """Estimate projected impact from user-adjusted improvement sliders."""
    player_id = body.get("player_id")
    if not player_id:
        raise HTTPException(400, "player_id required")

    conn = get_conn()
    player = conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
    if not player:
        conn.close()
        raise HTTPException(404, "Player not found")
    team = conn.execute(
        "SELECT * FROM teams WHERE team_id = ?", (player["team_id"],)
    ).fetchone()
    conn.close()

    p = dict(player)
    t = dict(team) if team else {}
    ortg = t.get("offensive_rating", 105) or 105
    ppp = ortg / 100
    games = max(p.get("games_played", 30), 1)
    minutes = p.get("minutes", 500) or 500

    tp_imp = body.get("three_point_pct_delta", 0) / 100
    ft_imp = body.get("free_throw_pct_delta", 0) / 100
    tov_red = body.get("turnover_reduction_pct", 0) / 100
    foul_red = body.get("foul_reduction_pct", 0) / 100
    dreb_imp = body.get("defensive_rebounding_delta", 0) / 100
    oreb_imp = body.get("offensive_rebounding_delta", 0) / 100
    ast_imp = body.get("assist_improvement_pct", 0) / 100

    impacts = {
        "shooting": p.get("three_point_attempts", 50) * tp_imp * 3,
        "free_throw": p.get("free_throw_attempts", 40) * ft_imp,
        "ball_security": minutes * p.get("usage_rate", 0.2) * p.get("turnover_rate", 0.15) * 0.02 * tov_red * 10 * ppp,
        "foul_discipline": minutes * p.get("foul_rate", 0.04) * 0.5 * foul_red * 10 * 0.7,
        "defensive_rebounding": minutes * 0.8 * dreb_imp * 1.1,
        "offensive_rebounding": minutes * 0.7 * oreb_imp * 1.15,
        "playmaking": minutes * p.get("assist_rate", 0.1) * ast_imp * 1.5,
    }
    total = sum(impacts.values())

    return {
        "player_id": player_id,
        "impacts_by_skill": {k: round(v, 2) for k, v in impacts.items()},
        "total_projected_value": round(total, 2),
        "inputs": body,
    }
