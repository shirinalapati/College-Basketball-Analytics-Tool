"""
Apply 2026-27 roster corrections: transfers and draft/portal departures.

Sports Reference team pages reflect where players played in 2025-26, not always
their next roster. This module moves players to committed schools and removes
departed players before building the app dataset.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRANSFERS_PATH = DATA_DIR / "roster_transfers_2027.json"
WITHDRAWALS_PATH = DATA_DIR / "nba_draft_withdrawals_2026.json"


def _player_id(team_id: str, name: str) -> str:
    return f"{team_id}_{re.sub(r'[^a-z0-9]+', '_', name.lower())}"


def _norm_name(name: str) -> str:
    s = re.sub(r"\s+", " ", name.strip().lower())
    return s.replace(".", "")


def load_draft_withdrawals() -> set[tuple[str, str]]:
    """Players returning after withdrawing from NBA draft — do not remove as departures."""
    if not WITHDRAWALS_PATH.exists():
        return set()
    payload = json.loads(WITHDRAWALS_PATH.read_text())
    return {
        (_norm_name(p["player_name"]), p["team_id"])
        for p in payload.get("players", [])
        if p.get("player_name") and p.get("team_id")
    }


def load_roster_corrections() -> dict:
    if not TRANSFERS_PATH.exists():
        return {"transfers": [], "departures": []}
    return json.loads(TRANSFERS_PATH.read_text())


def apply_roster_corrections(players: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Returns (updated_players, log_messages).
    """
    cfg = load_roster_corrections()
    transfers = cfg.get("transfers", [])
    departures = cfg.get("departures", [])

    logs: list[str] = []
    out = list(players)

    withdrawals = load_draft_withdrawals()

    # Remove draft / portal departures (left college, not on a new app team)
    dep_keys = {
        (_norm_name(d["player_name"]), d["team_id"])
        for d in departures
        if d.get("player_name") and d.get("team_id")
        and (_norm_name(d["player_name"]), d["team_id"]) not in withdrawals
    }
    skipped = [
        d for d in departures
        if (_norm_name(d.get("player_name", "")), d.get("team_id", "")) in withdrawals
    ]
    for d in skipped:
        logs.append(f"Keep (draft withdrawal / returning): {d['player_name']} on {d['team_id']}")
    if dep_keys:
        before = len(out)
        out = [
            p
            for p in out
            if (_norm_name(p["player_name"]), p["team_id"]) not in dep_keys
        ]
        logs.append(f"Removed {before - len(out)} departed players")

    # Build lookup by (name, team)
    by_key: dict[tuple[str, str], dict] = {}
    for p in out:
        by_key[(_norm_name(p["player_name"]), p["team_id"])] = p

    moved_names: set[str] = set()

    for t in transfers:
        name = t.get("player_name", "").strip()
        from_tid = t.get("from_team_id", "").strip()
        to_tid = t.get("to_team_id", "").strip()
        if not name or not from_tid or not to_tid:
            continue

        key = (_norm_name(name), from_tid)
        player = by_key.pop(key, None)
        if not player:
            logs.append(f"SKIP transfer (not on roster): {name} from {from_tid}")
            continue

        out = [p for p in out if p is not player]

        new_player = dict(player)
        new_player["team_id"] = to_tid
        new_player["player_id"] = _player_id(to_tid, name)
        new_player["data_source"] = (
            f"{player.get('data_source', 'Sports Reference')} · "
            f"2026-27 transfer from {from_tid.replace('_', ' ').title()}"
        )
        out.append(new_player)
        by_key[(_norm_name(name), to_tid)] = new_player
        moved_names.add(_norm_name(name))
        logs.append(f"Transfer: {name} {from_tid} → {to_tid}")

    # Drop duplicate name on old team if transfer succeeded elsewhere
    if moved_names:
        out = [
            p
            for p in out
            if _norm_name(p["player_name"]) not in moved_names
            or any(
                t.get("to_team_id") == p["team_id"]
                and _norm_name(t.get("player_name", "")) == _norm_name(p["player_name"])
                for t in transfers
            )
        ]

    from roster_status import apply_roster_status_overrides

    out, status_logs = apply_roster_status_overrides(out)
    logs.extend(status_logs)

    return out, logs


if __name__ == "__main__":
    import pandas as pd
    from build_full_dataset import build

    # Quick test from CSV
    path = DATA_DIR / "players_demo.csv"
    if path.exists():
        rows = pd.read_csv(path).to_dict(orient="records")
        fixed, logs = apply_roster_corrections(rows)
        for line in logs:
            print(line)
        print(f"Players: {len(rows)} → {len(fixed)}")
