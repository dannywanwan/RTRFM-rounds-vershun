#!/usr/bin/env python3
"""Keep the newest The Rounds episode local and archive older episodes to QNAP."""

from __future__ import annotations

import datetime as dt
import json
import logging
import shutil
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

import requests


SHOW_NAME = "The Rounds"
SHOW_SLUG = "therounds"
RESTREAM_ENDPOINT = "https://restreams.rtrfm.com.au/rzz"
LOCAL_DIR = Path("/media/rtrfm") / SHOW_NAME
ARCHIVE_DIR = Path("/media/qnap_rtrfm") / SHOW_NAME
LATEST_FILE = LOCAL_DIR / f"{SHOW_NAME} - Latest.mp3"
LATEST_DATE_FILE = Path("/config/latest-date")
TIMEZONE = ZoneInfo("Australia/Perth")
REQUEST_TIMEOUT = (20, 60)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("rtrfm-audio-archive")


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


def archive_file(source: Path) -> bool:
    archive_root = Path("/media/qnap_rtrfm")
    if not archive_root.is_dir():
        log.error("QNAP archive is not mounted at %s; keeping %s locally.", archive_root, source)
        return False
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    destination = ARCHIVE_DIR / source.name
    existing = matching_file(ARCHIVE_DIR, dt.date.fromisoformat(source.stem.rsplit(" - ", 1)[-1]))
    if existing:
        source.unlink()
        log.info("Removed duplicate local copy: %s", source)
        return True

    partial = destination.with_suffix(destination.suffix + ".part")
    try:
        shutil.copy2(source, partial)
        if partial.stat().st_size != source.stat().st_size:
            raise IOError(f"Archive size check failed for {source}")
        partial.replace(destination)
        source.unlink()
        log.info("Archived: %s", destination)
        return True
    except (OSError, shutil.Error) as exc:
        log.error("Could not archive %s: %s", source, exc)
        if partial.exists():
            partial.unlink()
        return False


def run_once(session: requests.Session, lookback_days: int) -> None:
    today = dt.datetime.now(TIMEZONE).date()
    episodes = available_dates(session, today, lookback_days)
    if not episodes:
        log.info("No available %s episodes found.", SHOW_NAME)
        return

    latest_date = max(episodes)
    legacy_latest = matching_file(LOCAL_DIR, latest_date)
    if legacy_latest:
        if not matching_file(ARCHIVE_DIR, latest_date):
            archive_file(legacy_latest)
        elif legacy_latest.exists():
            legacy_latest.unlink()

    latest = save_latest(session, latest_date, episodes[latest_date])
    if latest is None:
        log.warning("Latest episode %s could not be downloaded; leaving existing files untouched.", latest_date)
        return

    for episode_date, url in sorted(episodes.items()):
        if episode_date == latest_date:
            continue
        archived = matching_file(ARCHIVE_DIR, episode_date)
        local = matching_file(LOCAL_DIR, episode_date)
        if archived and local:
            local.unlink()
            continue
        if archived:
            continue
        if local is None:
            local = download_dated(session, episode_date, url, LOCAL_DIR)
        if local:
            archive_file(local)

    log.info("Current local episode: %s", latest)


def main() -> None:
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
