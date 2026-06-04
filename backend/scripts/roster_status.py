"""
Manual roster-status overrides for 2026-27 projected rosters.

Raw Sports Reference stats = where the player played in 2025-26.
roster_status.csv = where they should appear in the app for 2026-27.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from teams_universe import TEAMS_SPEC

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROSTER_STATUS_PATH = DATA_DIR / "roster_status.csv"

ROSTER_PROJECTION_DEFAULT_DATE = "2026-05-28"
ROSTER_STATUS_WARNING = (
    "Some 2026-27 roster statuses may change due to late transfer commitments, "
    "NBA Draft withdrawal decisions, eligibility waivers, or updated school rosters."
)

REMOVE_STATUSES = frozenset(
    {
        "transferred_out",
        "transfer_out",
        "nba_draft",
        "staying_in_draft",
        "pro",
        "departed",
        "portal_exit",
        "eligibility",
    }
)
TRANSFER_IN_STATUSES = frozenset(
    {"transferred_in", "transfer_in", "committed", "transferred"}
)
KEEP_STATUSES = frozenset({"withdrawn_returning", "returning", "staying", "staying_returning"})
UNKNOWN_STATUSES = frozenset({"unknown", "pending", "unverified"})

_NAME_TO_TEAM_ID: dict[str, str] = {}
for tid, name, _ in TEAMS_SPEC:
    _NAME_TO_TEAM_ID[re.sub(r"\s+", " ", name.strip().lower())] = tid
    _NAME_TO_TEAM_ID[tid] = tid


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower()).replace(".", "")


def resolve_team_id(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    low = s.lower().replace(" ", "_")
    if low in _NAME_TO_TEAM_ID:
        return _NAME_TO_TEAM_ID[low]
    title = s.lower()
    if title in _NAME_TO_TEAM_ID:
        return _NAME_TO_TEAM_ID[title]
    return low


def _player_id(team_id: str, name: str) -> str:
    return f"{team_id}_{re.sub(r'[^a-z0-9]+', '_', name.lower())}"


def load_roster_status_rows() -> list[dict]:
    if not ROSTER_STATUS_PATH.exists():
        return []
    rows: list[dict] = []
    with ROSTER_STATUS_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("player_name") or "").strip()
            if not name:
                continue
            rows.append(
                {
                    "player_name": name,
                    "old_team": resolve_team_id(row.get("old_team") or ""),
                    "new_team": resolve_team_id(row.get("new_team") or ""),
                    "status": (row.get("status") or "").strip().lower(),
                    "source_url": (row.get("source_url") or "").strip(),
                    "last_checked": (row.get("last_checked") or "").strip(),
                    "notes": (row.get("notes") or "").strip(),
                    "class_year_2026_27": (
                        row.get("class_year_2026_27")
                        or row.get("projected_class_year")
                        or row.get("class_year")
                        or ""
                    ).strip(),
                }
            )
    return rows


def roster_status_manifest() -> dict:
    rows = load_roster_status_rows()
    dates = [r["last_checked"] for r in rows if r.get("last_checked")]
    return {
        "roster_projection_last_updated": max(dates) if dates else ROSTER_PROJECTION_DEFAULT_DATE,
        "roster_status_override_count": len(rows),
        "roster_status_warning": ROSTER_STATUS_WARNING,
        "roster_status_source": "backend/data/roster_status.csv",
    }


def apply_roster_status_overrides(players: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Apply roster_status.csv on top of SR + JSON corrections. CSV wins conflicts.
    """
    status_rows = load_roster_status_rows()
    if not status_rows:
        return players, []

    logs: list[str] = []
    out = list(players)
    by_key: dict[tuple[str, str], dict] = {}
    for p in out:
        by_key[(_norm_name(p["player_name"]), p["team_id"])] = p

    for row in status_rows:
        name = row["player_name"]
        nname = _norm_name(name)
        old_tid = row["old_team"]
        new_tid = row["new_team"]
        status = row["status"]
        note = row.get("notes") or status

        if status in REMOVE_STATUSES or status in {"transferred_out", "transfer_out"}:
            if not old_tid:
                logs.append(f"SKIP roster_status (no old_team): {name}")
                continue
            key = (nname, old_tid)
            player = by_key.pop(key, None)
            if player:
                out = [p for p in out if p is not player]
                logs.append(f"Roster status remove ({status}): {name} from {old_tid}")
            else:
                logs.append(f"Roster status remove (not on roster): {name} from {old_tid}")
            continue

        if status in TRANSFER_IN_STATUSES and old_tid and new_tid:
            key = (nname, old_tid)
            player = by_key.pop(key, None)
            if not player:
                logs.append(f"SKIP roster_status transfer (not on {old_tid}): {name}")
                continue
            out = [p for p in out if p is not player]
            new_player = dict(player)
            new_player["team_id"] = new_tid
            new_player["player_id"] = _player_id(new_tid, name)
            src = player.get("data_source", "Sports Reference 2025-26")
            new_player["data_source"] = (
                f"{src} · 2026-27 roster status: transfer to {new_tid.replace('_', ' ').title()}"
            )
            if row.get("class_year_2026_27"):
                new_player["class_year_2026_27"] = row["class_year_2026_27"]
            if row.get("source_url"):
                new_player["roster_status_source"] = row["source_url"]
            if note:
                new_player["roster_status_notes"] = note
            out.append(new_player)
            by_key[(nname, new_tid)] = new_player
            logs.append(f"Roster status transfer: {name} {old_tid} → {new_tid}")
            continue

        if status in UNKNOWN_STATUSES and old_tid:
            key = (nname, old_tid)
            player = by_key.get(key)
            if player:
                player["roster_status_caveat"] = f"Unverified 2026-27 status — {note}"
                if row.get("class_year_2026_27"):
                    player["class_year_2026_27"] = row["class_year_2026_27"]
                logs.append(f"Roster status caveat: {name} on {old_tid}")
            continue

        if status in KEEP_STATUSES:
            if old_tid and row.get("class_year_2026_27"):
                player = by_key.get((nname, old_tid))
                if player:
                    player["class_year_2026_27"] = row["class_year_2026_27"]
            logs.append(f"Roster status keep: {name}")
            continue

        logs.append(f"SKIP roster_status (unknown status '{status}'): {name}")

    # Drop stale duplicate if transfer landed on new team
    transferred_names = {
        _norm_name(r["player_name"])
        for r in status_rows
        if r["status"] in TRANSFER_IN_STATUSES and r["old_team"] and r["new_team"]
    }
    if transferred_names:
        out = [
            p
            for p in out
            if _norm_name(p["player_name"]) not in transferred_names
            or any(
                r["new_team"] == p["team_id"]
                and _norm_name(r["player_name"]) == _norm_name(p["player_name"])
                for r in status_rows
                if r["status"] in TRANSFER_IN_STATUSES
            )
        ]

    return out, logs


if __name__ == "__main__":
    for line in load_roster_status_rows():
        print(line)
