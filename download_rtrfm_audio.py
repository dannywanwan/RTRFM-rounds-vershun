#!/usr/bin/env python3
"""Download available RTRFM The Rounds episodes for personal archiving."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests


SHOW_NAME = "The Rounds"
SHOW_SLUG = "therounds"
RESTREAM_ENDPOINT = "https://restreams.rtrfm.com.au/rzz"
DEFAULT_OUTPUT_DIR = Path.home() / "RTRFM Audio" / SHOW_NAME
DEFAULT_LOOKBACK_DAYS = 35
REQUEST_TIMEOUT = (20, 60)


def episode_dates(today: dt.date, lookback_days: int) -> list[dt.date]:
    """Return Saturdays in the lookback window, oldest first."""
    first_day = today - dt.timedelta(days=lookback_days)
    dates = []
    cursor = first_day
    while cursor <= today:
        if cursor.weekday() == 5:
            dates.append(cursor)
        cursor += dt.timedelta(days=1)
    return dates


def stream_url(session: requests.Session, episode_date: dt.date) -> str | None:
    params = urlencode({"n": SHOW_SLUG, "d": episode_date.isoformat()})
    response = session.get(f"{RESTREAM_ENDPOINT}?{params}", timeout=REQUEST_TIMEOUT)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    url = payload.get("u")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError(f"Unexpected RTRFM response for {episode_date}: {payload!r}")
    return url


def download_episode(
    session: requests.Session,
    episode_date: dt.date,
    output_dir: Path,
    dry_run: bool,
) -> Path:
    filename = f"{SHOW_NAME} - {episode_date.isoformat()}.mp3"
    destination = output_dir / filename
    if destination.exists() and destination.stat().st_size > 0:
        print(f"Already downloaded: {destination}")
        return destination

    url = stream_url(session, episode_date)
    if url is None:
        print(f"Not available: {episode_date}")
        return destination

    if dry_run:
        print(f"Available: {episode_date} -> {destination}")
        return destination

    output_dir.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    print(f"Downloading {episode_date}...", flush=True)
    with session.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()
        with partial.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
    partial.replace(destination)
    print(f"Saved: {destination}")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Download {SHOW_NAME} audio from RTRFM.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"where to keep dated MP3 files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=DEFAULT_LOOKBACK_DAYS,
        help=f"how far back to check (default: {DEFAULT_LOOKBACK_DAYS})",
    )
    parser.add_argument("--dry-run", action="store_true", help="list available episodes without downloading")
    args = parser.parse_args()

    if args.lookback_days < 1:
        parser.error("--lookback-days must be positive")

    session = requests.Session()
    session.headers.update({"User-Agent": "RTRFM-The-Rounds-Archive/1.0"})
    dates = episode_dates(dt.date.today(), args.lookback_days)
    print(f"Checking {SHOW_NAME} episodes from {dates[0]} to {dates[-1]}...")

    try:
        for episode_date in dates:
            download_episode(session, episode_date, args.output_dir, args.dry_run)
    except (requests.RequestException, ValueError, RuntimeError, OSError) as exc:
        print(f"Download stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
