"""
Merge Sports Reference players_advanced (BPM, OBPM, DBPM, PER, Win Shares) into sr_cache JSON.

Fetches each team page (same URL as full ingest) and patches cached rotation players by name.
Run before build_full_dataset.py / seed_database.py.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ingest_sports_reference import (
    REQUEST_DELAY,
    _load_cache,
    _save_cache,
    configure_ingest,
    fetch_html,
    merge_advanced_stats,
    parse_players_advanced,
)
from team_slugs import TEAM_SLUGS
from teams_universe import TEAMS_SPEC


def enrich_team_cache(team_id: str, slug: str) -> tuple[int, int, int]:
    """Returns (rotation_players, matched_with_bpm, advanced_table_rows)."""
    cached = _load_cache(team_id)
    if not cached or not cached.get("players"):
        return 0, 0, 0

    html = fetch_html(slug)
    advanced = parse_players_advanced(html)
    players, matched = merge_advanced_stats(cached["players"], advanced)
    cached["players"] = players
    _save_cache(team_id, cached)
    return len(players), matched, len(advanced)


def enrich_all_caches(*, delay: float | None = None, team_ids: list[str] | None = None) -> None:
    wait = delay if delay is not None else REQUEST_DELAY
    total_players = 0
    total_matched = 0
    failed: list[str] = []

    targets = [
        (tid, tname, conf)
        for tid, tname, conf in TEAMS_SPEC
        if team_ids is None or tid in team_ids
    ]

    for i, (tid, tname, _conf) in enumerate(targets, 1):
        slug = TEAM_SLUGS.get(tid)
        if not slug:
            failed.append(tid)
            continue
        if not _load_cache(tid):
            print(f"  [{i}/{len(targets)}] skip {tname}: no cache")
            continue
        try:
            n_players, n_matched, n_adv = enrich_team_cache(tid, slug)
            total_players += n_players
            total_matched += n_matched
            print(
                f"  [{i}/{len(targets)}] ✓ {tname}: {n_matched}/{n_players} players "
                f"({n_adv} rows on SR advanced table)"
            )
        except Exception as e:
            print(f"  [{i}/{len(targets)}] ✗ {tname}: {e}")
            failed.append(tid)
        time.sleep(wait)

    print(
        f"\nAdvanced merge complete: {total_matched} player rows updated across caches."
    )
    if failed:
        print(f"Failed teams ({len(failed)}): {failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich sr_cache with SR players_advanced stats")
    parser.add_argument("--delay", type=float, default=10.0, help="Seconds between team fetches")
    parser.add_argument("--team", action="append", dest="teams", help="Only these team_id values")
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="",
        help="Cache folder under backend/data (default: sr_cache)",
    )
    parser.add_argument("--sr-year", type=int, default=2026)
    args = parser.parse_args()

    from ingest_sports_reference import DATA_DIR

    cache = DATA_DIR / (args.cache_dir or "sr_cache")
    configure_ingest(sr_year=args.sr_year, cache_dir=cache)
    enrich_all_caches(delay=args.delay, team_ids=args.teams)


if __name__ == "__main__":
    main()
