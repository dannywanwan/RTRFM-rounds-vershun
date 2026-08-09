#!/usr/bin/env python3
"""Keep The Rounds episodes and the dashboard card in local Home Assistant storage."""

from __future__ import annotations

import datetime as dt
import json
import logging
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

import requests


SHOW_NAME = "The Rounds"
SHOW_SLUG = "therounds"
RESTREAM_ENDPOINT = "https://restreams.rtrfm.com.au/rzz"
LOCAL_DIR = Path("/media/rtrfm") / SHOW_NAME
LATEST_FILE = LOCAL_DIR / f"{SHOW_NAME} - Latest.mp3"
LATEST_DATE_FILE = Path("/config/latest-date")
CARD_SOURCE = Path("/rtrfm-episode-card.js")
CARD_DESTINATION = Path("/homeassistant/www/rtrfm-episode-card.js")
TIMEZONE = ZoneInfo("Australia/Perth")
REQUEST_TIMEOUT = (20, 60)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("rtrfm-audio-archive")


def install_dashboard_card() -> None:
    if not CARD_SOURCE.exists():
        log.warning("Dashboard card source is missing from the app image.")
        return
    try:
        CARD_DESTINATION.parent.mkdir(parents=True, exist_ok=True)
        if not CARD_DESTINATION.exists() or CARD_DESTINATION.read_bytes() != CARD_SOURCE.read_bytes():
            temporary = CARD_DESTINATION.with_suffix(".js.part")
            temporary.write_bytes(CARD_SOURCE.read_bytes())
            temporary.replace(CARD_DESTINATION)
            log.info("Installed dashboard card at %s", CARD_DESTINATION)
    except OSError as exc:
        log.error("Could not install dashboard card: %s", exc)


def available_dates(session: requests.Session, today: dt.date, lookback_days: int) -> dict[dt.date, str]:
    first_day = today - dt.timedelta(days=lookback_days)
    found: dict[dt.date, str] = {}
    cursor = first_day
    while cursor <= today:
        if cursor.weekday() == 5:
            params = urlencode({"n": SHOW_SLUG, "d": cursor.isoformat()})
            response = session.get(f"{RESTREAM_ENDPOINT}?{params}", timeout=REQUEST_TIMEOUT)
            if response.status_code == 404:
                cursor += dt.timedelta(days=1)
                continue
            response.raise_for_status()
            url = response.json().get("u")
            if isinstance(url, str) and url.startswith("https://"):
                found[cursor] = url
        cursor += dt.timedelta(days=1)
    return found


def matching_file(folder: Path, episode_date: dt.date) -> Path | None:
    prefix = f"{SHOW_NAME} - {episode_date.isoformat()}"
    if not folder.exists():
        return None
    for path in sorted(folder.glob(f"{prefix}.*")):
        if path.is_file() and not path.name.endswith(".part") and path.stat().st_size > 0:
            return path
    return None


def extension_for(url: str) -> str:
    extension = Path(urlparse(url).path).suffix.lower()
    return extension if extension in {".mp3", ".mp4", ".m4a"} else ".mp3"


def download_to(session: requests.Session, episode_date: dt.date, url: str, destination: Path) -> Path | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    log.info("Downloading %s to %s", episode_date, destination)
    try:
        with session.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
            if response.status_code == 404:
                log.warning("Expired or unavailable: %s", episode_date)
                return None
            response.raise_for_status()
            with partial.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
        partial.replace(destination)
        log.info("Saved: %s", destination)
        return destination
    finally:
        if partial.exists() and not destination.exists():
            partial.unlink()


def download_dated(session: requests.Session, episode_date: dt.date, url: str, folder: Path) -> Path | None:
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / f"{SHOW_NAME} - {episode_date.isoformat()}{extension_for(url)}"
    existing = matching_file(folder, episode_date)
    if existing:
        log.info("Already present: %s", existing)
        return existing
    return download_to(session, episode_date, url, destination)


def latest_date_on_disk() -> dt.date | None:
    try:
        return dt.date.fromisoformat(LATEST_DATE_FILE.read_text().strip())
    except (OSError, ValueError):
        return None


def save_latest(session: requests.Session, episode_date: dt.date, url: str) -> Path | None:
    if LATEST_FILE.exists() and latest_date_on_disk() == episode_date:
        log.info("Latest file is current: %s", LATEST_FILE)
        return LATEST_FILE

    downloaded = download_to(session, episode_date, url, LATEST_FILE)
    if downloaded is None:
        return None
    LATEST_DATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LATEST_DATE_FILE.write_text(episode_date.isoformat() + "\n")
    for legacy in LOCAL_DIR.glob(f"{SHOW_NAME} - Latest.*"):
        if legacy != LATEST_FILE and legacy.is_file():
            legacy.unlink()
            log.info("Removed obsolete latest file: %s", legacy)
    return downloaded


def run_once(session: requests.Session, lookback_days: int) -> None:
    today = dt.datetime.now(TIMEZONE).date()
    episodes = available_dates(session, today, lookback_days)
    if not episodes:
        log.info("No available %s episodes found.", SHOW_NAME)
        return

    latest_date = max(episodes)
    latest = save_latest(session, latest_date, episodes[latest_date])
    if latest is None:
        log.warning("Latest episode %s could not be downloaded; leaving existing files untouched.", latest_date)
        return

    for episode_date, url in sorted(episodes.items()):
        if episode_date == latest_date:
            continue
        local = matching_file(LOCAL_DIR, episode_date)
        if local is None:
            download_dated(session, episode_date, url, LOCAL_DIR)

    log.info("Current local episode: %s", latest)


def main() -> None:
    install_dashboard_card()
    options_path = Path("/data/options.json")
    options = json.loads(options_path.read_text()) if options_path.exists() else {}
    interval_hours = max(1, int(options.get("interval_hours", 24)))
    lookback_days = max(7, int(options.get("lookback_days", 35)))
    session = requests.Session()
    session.headers.update({"User-Agent": "RTRFM-The-Rounds-Home-Assistant/1.0"})

    while True:
        try:
            run_once(session, lookback_days)
        except Exception:
            log.exception("The archive check failed; it will retry later.")
        log.info("Next check in %s hours.", interval_hours)
        time.sleep(interval_hours * 60 * 60)


if __name__ == "__main__":
    main()
