# DevelopmentIQ

**College Basketball Player Development Priority Engine**

Illinois Men's Basketball Analytics Internship submission — a full-stack decision-support tool that identifies which player-skill improvements would create the most value for a team by combining player weaknesses, team needs, role/minutes leverage, improvement realism, and basketball impact.

![UIUC Theme — Illinois Orange #FF5F05 & Blue #13294B](https://img.shields.io/badge/Illini-Orange-FF5F05) ![Stack](https://img.shields.io/badge/React-TypeScript-61DAFB) ![API](https://img.shields.io/badge/FastAPI-009688)

---

## Problem Solved

College staffs must answer: **"Which skill improvement would create the most value for this player and this team?"**

DevelopmentIQ is not a generic stat dashboard. It weights recommendations by:

1. Player improvement opportunity  
2. Team need alignment  
3. Minutes / role leverage  
4. Improvement realism  
5. Basketball impact value  

---

## Assignment Alignment

| Requirement | How DevelopmentIQ Satisfies It |
|-------------|--------------------------------|
| Clear college basketball use case | Player development + team needs prioritization |
| Public data (BartTorvik, SR, NCAA) | Schema-aligned ingestion; demo CSV included |
| Functioning data product | React dashboard + FastAPI + SQLite model outputs |
| Write-up | `docs/writeup.md` + in-app Methodology page |
| Actionable value | DPS, leverage leaderboard, simulator, team-relative explanations |

---

## Quick Start

### One command (recommended)

```bash
cd developmentiq-cbb
chmod +x start.sh
./start.sh
```

Open **http://localhost:5173**

### Prerequisites

- Python 3.10+  
- Node.js 18+  

### Manual setup

### 1. Backend

```bash
cd developmentiq-cbb/backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/generate_demo_data.py
python scripts/seed_database.py
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd developmentiq-cbb/frontend
npm install
npm run dev
```

Open **http://localhost:5173** — API proxied to port 8000.

> **Note:** Visit `http://localhost:5173` for the UI. Port `8000` is the JSON API only (`/api/*`, `/docs`).

### First-time setup

```bash
npm run setup   # from project root — venv, seed DB, npm install
```

### Internship submission

See **[SUBMISSION.md](SUBMISSION.md)** and attach **`docs/writeup.md`** to your reply email.

### Build for production

```bash
cd frontend && npm run build
# Serve dist/ via Vercel/Netlify; point VITE_API_URL or proxy to backend
```

---

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Overview — mission, counts, top needs, Illinois feature |
| `/team-needs` | Team Needs Map — radar + ranked needs |
| `/development-board` | Per-team player development priorities |
| `/player/:id` | Player profile — top 3 priorities + breakdown |
| `/simulator` | Improvement scenario sliders |
| `/leaderboard` | Development Leverage Leaderboard |
| `/methodology` | Full internship write-up sections |

---

## Data Sources

**Intended:** BartTorvik, Sports Reference, NCAA public stats, CSV exports.

**v1:** Labeled **DEMO** data in `backend/data/` — 64 teams, 600+ rotation players (≥10 MPG or 250 minutes). Replace via `scripts/generate_demo_data.py` or new ingestion scripts without changing schema.

---

## Model (Short)

**Development Priority Score (per skill):**

```
DPS = 0.30×Opportunity + 0.30×TeamNeed + 0.20×Role + 0.10×Realism + 0.10×Impact
```

**Development Leverage Score:** production + upside + need match + minutes + class runway.

Details: [`docs/methodology.md`](docs/methodology.md)

---

## Project Structure

```
developmentiq-cbb/
├── frontend/          # React + Vite + Tailwind + Recharts
├── backend/
│   ├── api/           # FastAPI
│   ├── models/        # Scoring engine
│   ├── scripts/       # Demo data + DB seed
│   └── data/          # SQLite + CSVs
└── docs/
    ├── methodology.md
    └── writeup.md
```

---

## Why Useful to Illinois / College Staff

- **Coaches:** Tie development plans to team weaknesses; explain *why* each priority matters.  
- **GM/Analytics:** Roster need map, internal upside, portal gap analysis.  
- **Featured default:** Illinois Fighting Illini team context.

---

## Limitations

Public data cannot capture scheme, matchups, or shot quality. Projections are transparent heuristics. Demo data is synthetic until live feeds are connected.

---

## License

MIT — built for internship evaluation.
