"""
Populate projected 2026-27 class labels from ESPN roster experience.

ESPN roster class/experience is treated as the source class for the 2025-26 stat
season. We advance it one year for the projected 2026-27 roster, then the normal
roster-correction pipeline carries the label through transfers.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from models.class_year import advance_class_year, normalize_class_year
from teams_universe import TEAMS_SPEC

DATA_DIR = ROOT / "data"
OUT_PATH = DATA_DIR / "projected_class_year_2027.csv"
PLAYERS_PATH = DATA_DIR / "players_demo.csv"
TRANSFERS_PATH = DATA_DIR / "roster_transfers_2027.json"
SOURCE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"

MANUAL_TEAM_ESPN = {
    "illinois": "356",
}


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "DevelopmentIQ-Academic/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _norm(name: str) -> str:
    name = re.sub(r"[^a-z0-9 ]+", " ", str(name).lower())
    name = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", name)
    return " ".join(name.split())


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def espn_team_map() -> dict[str, str]:
    name_to_tid = {name.lower(): tid for tid, name, _ in TEAMS_SPEC}
    slug_to_tid = {tid.replace("_", "-"): tid for tid, _, _ in TEAMS_SPEC}
    slug_to_tid.update({tid: tid for tid, _, _ in TEAMS_SPEC})
    mapping = dict(MANUAL_TEAM_ESPN)
    data = _get(f"{SOURCE_URL}/teams?limit=500")
    for item in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
        entry = item.get("team", item)
        espn_id = str(entry.get("id", ""))
        slug = (entry.get("slug") or "").lower()
        display = (entry.get("displayName") or entry.get("name") or "").lower()
        loc = (entry.get("location") or "").lower()
        tid = slug_to_tid.get(slug) or name_to_tid.get(display) or name_to_tid.get(loc)
        if not tid and "pittsburgh" in slug:
            tid = "pittsburgh"
        if tid and espn_id:
            mapping[tid] = espn_id
    return mapping


def roster_classes(espn_team_id: str) -> dict[str, str]:
    data = _get(f"{SOURCE_URL}/teams/{espn_team_id}/roster")
    out: dict[str, str] = {}
    for ath in data.get("athletes", []):
        name = ath.get("fullName") or ath.get("displayName")
        exp = ath.get("experience") or {}
        cls = normalize_class_year(exp.get("displayValue") or exp.get("abbreviation"))
        if name and cls != "Unknown":
            out[_norm(name)] = cls
    return out


def best_class_for_player(player_name: str, roster: dict[str, str]) -> str:
    key = _norm(player_name)
    if key in roster:
        return roster[key]
    best_name = ""
    best_score = 0.0
    for candidate in roster:
        score = _ratio(key, candidate)
        if score > best_score:
            best_name = candidate
            best_score = score
    return roster[best_name] if best_score >= 0.92 else "Unknown"


def transfer_source_map() -> dict[tuple[str, str], str]:
    if not TRANSFERS_PATH.exists():
        return {}
    payload = json.loads(TRANSFERS_PATH.read_text())
    out: dict[tuple[str, str], str] = {}
    for row in payload.get("transfers", []):
        name = row.get("player_name")
        from_tid = row.get("from_team_id")
        to_tid = row.get("to_team_id")
        if name and from_tid and to_tid:
            out[(_norm(name), str(to_tid))] = str(from_tid)
    return out


def main() -> None:
    if not PLAYERS_PATH.exists():
        raise SystemExit(f"Missing {PLAYERS_PATH}; build players first.")

    players = pd.read_csv(PLAYERS_PATH)
    mapping = espn_team_map()
    roster_by_team: dict[str, dict[str, str]] = {}
    for tid, _, _ in TEAMS_SPEC:
        espn_id = mapping.get(tid)
        if not espn_id:
            continue
        try:
            roster_by_team[tid] = roster_classes(espn_id)
            time.sleep(0.05)
        except Exception as exc:  # noqa: BLE001
            print(f"skip {tid}: {exc}")

    transfer_sources = transfer_source_map()
    rows: list[dict[str, str]] = []
    for _, player in players.iterrows():
        tid = str(player["team_id"])
        cls = best_class_for_player(str(player["player_name"]), roster_by_team.get(tid, {}))
        source_tid = tid
        if cls == "Unknown":
            from_tid = transfer_sources.get((_norm(str(player["player_name"])), tid))
            if from_tid:
                source_cls = best_class_for_player(
                    str(player["player_name"]), roster_by_team.get(from_tid, {})
                )
                if source_cls != "Unknown":
                    cls = source_cls
                    source_tid = from_tid
        projected = advance_class_year(cls)
        if projected == "Unknown":
            continue
        rows.append(
            {
                "player_name": str(player["player_name"]),
                "team_id": tid,
                "class_year_2026_27": projected,
                "source_url": f"{SOURCE_URL}/teams/{mapping.get(source_tid, '')}/roster",
                "notes": f"ESPN roster experience {cls} on {source_tid}; advanced one year for 2026-27",
            }
        )

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["player_name", "team_id", "class_year_2026_27", "source_url", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} projected class rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
