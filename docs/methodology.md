# DevelopmentIQ — Technical Methodology

## Problem Statement

College basketball staffs must decide which player-skill improvements create the most **team value** during a season. Development cannot be evaluated in isolation: priority depends on player weakness, team need, role/minutes, realism of improvement, and basketball value of the skill.

## Data Layer

| Source (intended) | Metrics |
|-------------------|---------|
| BartTorvik | Team/player efficiency, rates |
| Sports Reference | Box score, shooting splits |
| NCAA public stats | Games, minutes |
| **v1 DEMO CSV** | Full schema mirror, 64 teams, 608 rotation players |

**Rotation filter:** MPG ≥ 10 OR total minutes ≥ 250.

## Database Schema (SQLite, PostgreSQL-compatible)

- `teams` — team efficiency profile
- `players` — rotation player rates
- `team_need_scores` — 9 need dimensions per team
- `player_opportunity_scores` — 9 opportunity dimensions per player
- `development_priority_scores` — player × skill DPS rows
- `development_leverage_scores` — composite leverage per player

## Team Need Alignment

Derived from team rates vs field expectations. Examples:

- **Shooting need:** low `three_point_rate`, low `efg_pct`
- **Ball security:** high `turnover_rate`
- **Defensive rebounding:** low `defensive_rebound_rate`
- **Foul discipline:** high `foul_rate`
- **Playmaking:** low `assist_rate`
- **Defensive activity:** low steal/block rates, weaker `defensive_rating`

Scores normalized 0–100 across the curated team universe.

## Player Improvement Opportunity

Gap vs positional peers and field median. Higher-is-worse stats (turnovers, fouls) invert the gap logic. Low 3PA volume dampens shooting opportunity.

## Development Priority Score (DPS)

```
DPS = 0.30 × Opportunity
    + 0.30 × Team Need
    + 0.20 × Role Leverage (MPG normalized)
    + 0.10 × Improvement Realism (category defaults)
    + 0.10 × Basketball Impact Value (category defaults)
```

### Skill Categories

1. Three-Point Shooting  
2. Free Throw Shooting  
3. Ball Security  
4. Defensive Rebounding  
5. Offensive Rebounding  
6. Foul Discipline  
7. Playmaking  
8. Defensive Activity  
9. Rim Pressure / Finishing  

## Projected Impact (Transparent Heuristics)

| Skill | Formula (season proxy) |
|-------|------------------------|
| 3P Shooting | `3PA × (target_3p - current_3p) × 3`, target capped +4% |
| FT Shooting | `FTA × (target_ft - current_ft)`, target capped +7% |
| Turnovers | `prevented_TO × team_PPP` (~10% reduction) |
| Fouls | `fouls_reduced × 0.7` proxy |
| Rebounding | `extra_rebounds × second_chance_proxy` |
| Playmaking | `extra_assists × 1.5` |

## Development Leverage Score

```
DLS = 0.30 × current_production_value
    + 0.25 × improvement_upside (top-3 DPS avg)
    + 0.20 × team_need_alignment (top priorities)
    + 0.15 × minutes_role_leverage
    + 0.10 × development_runway (class year)
```

## API Endpoints

- `GET /api/overview` — dashboard aggregates  
- `GET /api/teams`, `/api/teams/{id}`  
- `GET /api/teams/{id}/development-board`  
- `GET /api/players/{id}`  
- `GET /api/leaderboard/leverage`  
- `POST /api/simulate` — slider-driven impact  

## Stack

Python 3 · pandas · FastAPI · SQLite · React · TypeScript · Vite · Tailwind · Recharts
