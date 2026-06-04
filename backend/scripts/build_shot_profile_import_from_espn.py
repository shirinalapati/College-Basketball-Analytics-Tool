"""
Aggregate shot-location profiles from ESPN play-by-play (public API).

Usage (from backend/scripts):
  python3 build_shot_profile_import_from_espn.py
  python3 build_shot_profile_import_from_espn.py --only-missing
  python3 build_shot_profile_import_from_espn.py --team illinois
  python3 merge_shot_profile_csv.py ../data/shot_profile_import.csv
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import defaultdict
from difflib import SequenceMatcher
from http.client import IncompleteRead
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_DIR = ROOT / "data"
PLAYERS_PATH = DATA_DIR / "players_demo.csv"
OUT_PATH = DATA_DIR / "shot_profile_import.csv"
CACHE_DIR = DATA_DIR / "espn_pbp_cache"
SEASON = 2026
REQUEST_DELAY = 0.10
GET_RETRIES = 4
MIN_FGA = 1
FUZZY_THRESHOLD = 0.82

# Manual fixes when ESPN slug/name does not match TEAMS_SPEC
MANUAL_TEAM_ESPN: dict[str, str] = {
    "pittsburgh": "221",
}

# data_source "transfer from Providence" -> team_id
_TRANSFER_FROM: dict[str, str] = {
    "providence": "2507",
    "kentucky": "96",
    "michigan": "130",
    "tennessee": "2633",
    "uconn": "41",
    "gonzaga": "2250",
    "baylor": "239",
    "arizona": "12",
    "houston": "248",
    "marquette": "269",
    "creighton": "156",
    "villanova": "222",
    "st johns": "2599",
    "st. john's": "2599",
    "seton hall": "2550",
    "xavier": "2752",
    "butler": "2086",
    "purdue": "2509",
    "indiana": "84",
    "ohio state": "194",
    "michigan state": "127",
}

RIM_TYPES = frozenset(
    {
        "LayUpShot",
        "DunkShot",
        "TipShot",
        "AlleyOopDunkShot",
        "AlleyOopLayupShot",
        "ReverseLayupShot",
        "DrivingLayupShot",
        "DrivingDunkShot",
        "PutbackLayupShot",
        "PutbackDunkShot",
        "RunningLayupShot",
        "RunningDunkShot",
        "FingerRollShot",
        "HookShot",
        "TurnaroundHookShot",
    }
)

CORNER_THREE_SHARE = 0.35
_NAME_FROM_PLAY = re.compile(r"^(.+?)\s+(made|missed)\s", re.IGNORECASE)
_SUFFIXES = frozenset({"jr", "sr", "ii", "iii", "iv", "v"})


def _get(url: str) -> dict:
    last_exc: Exception | None = None
    for attempt in range(GET_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DevelopmentIQ/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except (IncompleteRead, urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_exc = exc
            time.sleep(0.5 * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def _norm_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z ]", "", s.lower())
    parts = s.split()
    while parts and parts[-1] in _SUFFIXES:
        parts = parts[:-1]
    return " ".join(parts)


def _name_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _load_espn_team_map() -> dict[str, str]:
    from teams_universe import TEAMS_SPEC

    name_to_tid = {name.lower(): tid for tid, name, _ in TEAMS_SPEC}
    slug_to_tid = {tid.replace("_", "-"): tid for tid, _, _ in TEAMS_SPEC}
    slug_to_tid.update({tid: tid for tid, _, _ in TEAMS_SPEC})

    mapping = dict(MANUAL_TEAM_ESPN)
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/basketball/"
        "mens-college-basketball/teams?limit=500"
    )
    data = _get(url)
    for item in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
        entry = item.get("team", item)
        espn_id = str(entry.get("id", ""))
        slug = (entry.get("slug") or "").lower()
        display = (entry.get("displayName") or entry.get("name") or "").lower()
        loc = (entry.get("location") or "").lower()
        tid = (
            slug_to_tid.get(slug)
            or name_to_tid.get(display)
            or name_to_tid.get(loc)
        )
        if not tid and "pittsburgh" in slug:
            tid = "pittsburgh"
        if tid and espn_id:
            mapping[tid] = espn_id
    return mapping


def _transfer_espn_id(data_source: str, espn_map: dict[str, str]) -> str | None:
    if not isinstance(data_source, str):
        return None
    m = re.search(r"transfer from ([A-Za-z.' ]+)", data_source, re.IGNORECASE)
    if not m:
        return None
    school = m.group(1).strip().lower().rstrip(".")
    if school in _TRANSFER_FROM:
        return _TRANSFER_FROM[school]
    slug = school.replace(" ", "_").replace(".", "").replace("'", "")
    if slug in espn_map:
        return espn_map[slug]
    from teams_universe import TEAMS_SPEC

    for tid, name, _ in TEAMS_SPEC:
        nm = name.lower()
        if school == nm or school.replace(" ", "") == nm.replace(" ", ""):
            return espn_map.get(tid)
        if school in nm or nm in school:
            return espn_map.get(tid)
    return None


def _roster_athletes(espn_team_id: str) -> dict[str, str]:
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/basketball/"
        f"mens-college-basketball/teams/{espn_team_id}/roster"
    )
    data = _get(url)
    out: dict[str, str] = {}
    for ath in data.get("athletes", []):
        aid = str(ath.get("id", ""))
        for key in ("fullName", "displayName", "shortName"):
            nm = ath.get(key)
            if nm and aid:
                out[_norm_name(nm)] = aid
    return out


def _names_from_boxscore(summary: dict, espn_team_id: str) -> dict[str, str]:
    """athlete id -> normalized name from game boxscore."""
    out: dict[str, str] = {}
    for block in summary.get("boxscore", {}).get("players", []):
        if str((block.get("team") or {}).get("id", "")) != espn_team_id:
            continue
        for row in block.get("statistics", []):
            ath = row.get("athlete") or {}
            aid = str(ath.get("id", ""))
            nm = ath.get("displayName") or ath.get("shortName")
            if aid and nm:
                out[aid] = _norm_name(nm)
    return out


def _name_from_play_text(text: str) -> str | None:
    m = _NAME_FROM_PLAY.match(text or "")
    if m:
        return _norm_name(m.group(1))
    return None


def _team_schedule_event_ids(espn_team_id: str) -> list[str]:
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/basketball/"
        f"mens-college-basketball/teams/{espn_team_id}/schedule?season={SEASON}"
    )
    data = _get(url)
    ids: list[str] = []
    for ev in data.get("events", []):
        eid = str(ev.get("id", ""))
        st = (ev.get("competitions") or [{}])[0].get("status", {}).get("type", {})
        if eid and st.get("completed"):
            ids.append(eid)
    return ids


def _cached_summary(event_id: str) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{event_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/basketball/"
        f"mens-college-basketball/summary?event={event_id}"
    )
    data = _get(url)
    path.write_text(json.dumps(data))
    return data


def _classify_shot(play: dict) -> str | None:
    if not play.get("shootingPlay"):
        return None
    pts = int(play.get("pointsAttempted") or 0)
    text = (play.get("text") or "").lower()
    stype = (play.get("type") or {}).get("text") or ""

    if pts == 3 or "three point" in text:
        return "three"
    if stype in RIM_TYPES:
        return "rim"
    if stype == "JumpShot" and pts == 2:
        return "mid"
    if stype in ("LayUpShot", "DunkShot", "TipShot") or "layup" in text or "dunk" in text:
        return "rim"
    if stype == "JumpShot":
        return "mid" if pts == 2 else "three"
    return None


def _aggregate_team_pbp(espn_team_id: str) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    """All shot stats + athlete id -> name for this team's side of the ball."""
    stats: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "rim_a": 0.0,
            "rim_m": 0.0,
            "mid_a": 0.0,
            "mid_m": 0.0,
            "three_a": 0.0,
            "three_m": 0.0,
        }
    )
    aid_names: dict[str, str] = {}

    for eid in _team_schedule_event_ids(espn_team_id):
        try:
            summary = _cached_summary(eid)
        except Exception as exc:
            print(f"    skip game {eid}: {exc}")
            continue
        time.sleep(REQUEST_DELAY)

        for aid, nm in _names_from_boxscore(summary, espn_team_id).items():
            aid_names.setdefault(aid, nm)

        for play in summary.get("plays", []):
            if str((play.get("team") or {}).get("id", "")) != espn_team_id:
                continue
            zone = _classify_shot(play)
            if not zone:
                continue
            parts = play.get("participants") or []
            if not parts:
                continue
            aid = str((parts[0].get("athlete") or {}).get("id", ""))
            if not aid:
                continue
            nm = _name_from_play_text(play.get("text") or "")
            if nm:
                aid_names.setdefault(aid, nm)
            made = bool(play.get("scoringPlay"))
            stats[aid][f"{zone}_a"] += 1
            if made:
                stats[aid][f"{zone}_m"] += 1

    return stats, aid_names


def _match_player_to_athlete(
    pname: str,
    roster_map: dict[str, str],
    aid_names: dict[str, str],
) -> str | None:
    target = _norm_name(pname)
    if target in roster_map:
        return roster_map[target]

    best_aid = ""
    best_score = 0.0
    pool: list[tuple[str, str]] = list(aid_names.items())
    for nm, aid in roster_map.items():
        pool.append((aid, nm))

    last = target.split()[-1] if target else ""
    for aid, nm in pool:
        score = _name_ratio(target, nm)
        if target and nm and (target in nm or nm in target):
            score = max(score, 0.95)
        if last and len(last) > 3 and nm.endswith(last):
            score = max(score, 0.88)
        if score > best_score:
            best_score = score
            best_aid = aid

    if best_score >= FUZZY_THRESHOLD:
        return best_aid
    return None


def _row_from_stats(pid: str, s: dict[str, float], games: int) -> dict | None:
    rim_a = int(s["rim_a"])
    mid_a = int(s["mid_a"])
    three_a = int(s["three_a"])
    fga = rim_a + mid_a + three_a
    if fga < MIN_FGA:
        return None
    rim_m = int(s["rim_m"])
    mid_m = int(s["mid_m"])
    three_m = int(s["three_m"])
    g = max(games, 1)
    corner_a = int(round(three_a * CORNER_THREE_SHARE))
    ab_a = three_a - corner_a
    corner_m = int(round(three_m * CORNER_THREE_SHARE))
    ab_m = three_m - corner_m
    fga_pg = fga / g
    return {
        "player_id": pid,
        "shot_profile_source": "tracking",
        "rim_attempts": rim_a,
        "rim_makes": rim_m,
        "rim_fg_pct": round(rim_m / rim_a, 3) if rim_a else None,
        "rim_attempt_rate": round((rim_a / g) / max(fga_pg, 0.1), 3),
        "midrange_attempts": mid_a,
        "midrange_makes": mid_m,
        "midrange_fg_pct": round(mid_m / mid_a, 3) if mid_a else None,
        "midrange_attempt_rate": round((mid_a / g) / max(fga_pg, 0.1), 3),
        "corner_three_attempts": corner_a,
        "corner_three_makes": corner_m,
        "corner_three_pct": round(corner_m / corner_a, 3) if corner_a else None,
        "corner_three_attempt_rate": round((corner_a / g) / max(fga_pg, 0.1), 3),
        "above_break_three_attempts": ab_a,
        "above_break_three_makes": ab_m,
        "above_break_three_pct": round(ab_m / ab_a, 3) if ab_a else None,
        "above_break_three_attempt_rate": round((ab_a / g) / max(fga_pg, 0.1), 3),
    }


def _players_for_team(
    team_players: pd.DataFrame,
    espn_team_id: str,
    espn_map: dict[str, str],
) -> list[dict]:
    roster_map = _roster_athletes(espn_team_id)
    time.sleep(REQUEST_DELAY)
    agg, aid_names = _aggregate_team_pbp(espn_team_id)

    rows: list[dict] = []
    for _, pl in team_players.iterrows():
        pid = pl["player_id"]
        pname = pl["player_name"]
        games = int(pl.get("games_played", 1))

        aid = _match_player_to_athlete(pname, roster_map, aid_names)
        if aid and aid in agg:
            row = _row_from_stats(pid, agg[aid], games)
            if row:
                rows.append(row)
                continue

        xfer_espn = _transfer_espn_id(str(pl.get("data_source", "")), espn_map)
        if xfer_espn and xfer_espn != espn_team_id:
            try:
                x_roster = _roster_athletes(xfer_espn)
                time.sleep(REQUEST_DELAY)
                x_agg, x_names = _aggregate_team_pbp(xfer_espn)
                x_aid = _match_player_to_athlete(pname, x_roster, x_names)
                if x_aid and x_aid in x_agg:
                    row = _row_from_stats(pid, x_agg[x_aid], games)
                    if row:
                        rows.append(row)
            except Exception as exc:
                print(f"    transfer PBP {xfer_espn} for {pname}: {exc}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", help="Only process one team_id")
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Only build profiles for players not already in shot_profile_import.csv",
    )
    args = parser.parse_args()

    if not PLAYERS_PATH.exists():
        raise SystemExit(f"Missing {PLAYERS_PATH}")

    players = pd.read_csv(PLAYERS_PATH)
    existing_ids: set[str] = set()
    if args.only_missing and OUT_PATH.exists():
        existing_ids = set(pd.read_csv(OUT_PATH)["player_id"])
        players = players[~players["player_id"].isin(existing_ids)]
        print(f"Targeting {len(players)} players without tracking import rows")

    espn_map = _load_espn_team_map()
    time.sleep(REQUEST_DELAY)

    team_ids = sorted(players["team_id"].unique())
    if args.team:
        team_ids = [args.team]

    new_rows: list[dict] = []
    missing_espn: list[str] = []

    for tid in team_ids:
        if tid not in espn_map:
            missing_espn.append(tid)
            continue
        espn_tid = espn_map[tid]
        team_players = players[players["team_id"] == tid]
        if team_players.empty:
            continue
        print(f"{tid}: ESPN {espn_tid}, {len(team_players)} players to match")
        try:
            matched = _players_for_team(team_players, espn_tid, espn_map)
            print(f"  → {len(matched)} tracking profiles")
            new_rows.extend(matched)
        except Exception as exc:
            print(f"  failed: {exc}")

    if not new_rows and not existing_ids:
        raise SystemExit("No shot profiles built.")

    new_df = pd.DataFrame(new_rows)
    if existing_ids and OUT_PATH.exists():
        old = pd.read_csv(OUT_PATH)
        combined = pd.concat(
            [old[~old["player_id"].isin(new_df["player_id"])], new_df],
            ignore_index=True,
        )
    else:
        combined = new_df

    combined.to_csv(OUT_PATH, index=False)
    print(f"\nWrote {len(combined)} total rows → {OUT_PATH} (+{len(new_df)} new)")
    if missing_espn:
        print(f"No ESPN id ({len(missing_espn)}): {', '.join(sorted(missing_espn))}")


if __name__ == "__main__":
    sys.path.insert(0, str(SCRIPT_DIR))
    main()
