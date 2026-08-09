#!/usr/bin/env python3
"""Keep The Rounds episodes and the dashboard card in local Home Assistant storage."""

from __future__ import annotations

import datetime as dt
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

import requests


RESTREAM_ENDPOINT = "https://restreams.rtrfm.com.au/rzz"
LOCAL_ROOT = Path("/media/rtrfm")
CARD_SOURCE = Path("/rtrfm-episode-card.js")
CARD_DESTINATION = Path("/homeassistant/www/rtrfm-episode-card.js")
CARD_IMPL_SOURCE = Path("/rtrfm-episode-card-impl.js")
CARD_IMPL_DESTINATION = Path("/homeassistant/www/rtrfm-episode-card-impl.js")
TIMEZONE = ZoneInfo("Australia/Perth")
REQUEST_TIMEOUT = (20, 60)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("rtrfm-audio-archive")


@dataclass(frozen=True)
class Show:
    name: str
    slug: str
    latest_state_file: Path

    @property
    def local_dir(self) -> Path:
        return LOCAL_ROOT / self.name

    @property
    def latest_file(self) -> Path:
        return self.local_dir / f"{self.name} - Latest.mp3"


SHOWS = (
    Show("The Rounds", "therounds", Path("/config/latest-date")),
    Show("Jamdown Vershun", "jamdown", Path("/config/jamdown-vershun-latest-date")),
)


def install_dashboard_card() -> None:
    if not CARD_SOURCE.exists():
        log.warning("Dashboard card source is missing from the app image.")
        return
    try:
        CARD_DESTINATION.parent.mkdir(parents=True, exist_ok=True)
        for source, destination in (
            (CARD_SOURCE, CARD_DESTINATION),
            (CARD_IMPL_SOURCE, CARD_IMPL_DESTINATION),
        ):
            if not source.exists():
                log.warning("Dashboard card source is missing: %s", source)
                continue
            if not destination.exists() or destination.read_bytes() != source.read_bytes():
                temporary = destination.with_suffix(".js.part")
                temporary.write_bytes(source.read_bytes())
                temporary.replace(destination)
                log.info("Installed dashboard card file at %s", destination)
    except OSError as exc:
        log.error("Could not install dashboard card: %s", exc)


def available_dates(
    session: requests.Session,
    show: Show,
    today: dt.date,
    lookback_days: int,
) -> dict[dt.date, str]:
    first_day = today - dt.timedelta(days=lookback_days)
    found: dict[dt.date, str] = {}
    cursor = first_day
    while cursor <= today:
        if cursor.weekday() == 5:
            params = urlencode({"n": show.slug, "d": cursor.isoformat()})
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


def matching_file(folder: Path, show: Show, episode_date: dt.date) -> Path | None:
    prefix = f"{show.name} - {episode_date.isoformat()}"
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


def download_dated(session: requests.Session, show: Show, episode_date: dt.date, url: str) -> Path | None:
    folder = show.local_dir
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / f"{show.name} - {episode_date.isoformat()}{extension_for(url)}"
    existing = matching_file(folder, show, episode_date)
    if existing:
        log.info("Already present: %s", existing)
        return existing
    return download_to(session, episode_date, url, destination)


def latest_date_on_disk(show: Show) -> dt.date | None:
    try:
        return dt.date.fromisoformat(show.latest_state_file.read_text().strip())
    except (OSError, ValueError):
        return None


def save_latest(session: requests.Session, show: Show, episode_date: dt.date, url: str) -> Path | None:
    if show.latest_file.exists() and latest_date_on_disk(show) == episode_date:
        log.info("Latest file is current for %s: %s", show.name, show.latest_file)
        return show.latest_file

    downloaded = download_to(session, episode_date, url, show.latest_file)
    if downloaded is None:
        return None
    show.latest_state_file.parent.mkdir(parents=True, exist_ok=True)
    show.latest_state_file.write_text(episode_date.isoformat() + "\n")
    for legacy in show.local_dir.glob(f"{show.name} - Latest.*"):
        if legacy != show.latest_file and legacy.is_file():
            legacy.unlink()
            log.info("Removed obsolete latest file: %s", legacy)
    return downloaded


def run_show(session: requests.Session, show: Show, lookback_days: int) -> None:
    today = dt.datetime.now(TIMEZONE).date()
    episodes = available_dates(session, show, today, lookback_days)
    if not episodes:
        log.info("No available %s episodes found.", show.name)
        return

    latest_date = max(episodes)
    latest = save_latest(session, show, latest_date, episodes[latest_date])
    if latest is None:
        log.warning("Latest %s episode %s could not be downloaded; leaving existing files untouched.", show.name, latest_date)
        return

    for episode_date, url in sorted(episodes.items()):
        if episode_date == latest_date:
            continue
        local = matching_file(show.local_dir, show, episode_date)
        if local is None:
            download_dated(session, show, episode_date, url)

    log.info("Current local %s episode: %s", show.name, latest)


def run_once(session: requests.Session, lookback_days: int) -> None:
    for show in SHOWS:
        try:
            run_show(session, show, lookback_days)
        except Exception:
            log.exception("The %s check failed; continuing with the other shows.", show.name)


def seconds_until_sunday(hour: int) -> float:
    now = dt.datetime.now(TIMEZONE)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    days_until_sunday = (6 - now.weekday()) % 7
    target += dt.timedelta(days=days_until_sunday)
    if target <= now:
        target += dt.timedelta(days=7)
    return (target - now).total_seconds()


def main() -> None:
    install_dashboard_card()
    options_path = Path("/data/options.json")
    options = json.loads(options_path.read_text()) if options_path.exists() else {}
    lookback_days = max(7, int(options.get("lookback_days", 35)))
    sunday_hour = min(23, max(0, int(options.get("sunday_hour", 3))))
    session = requests.Session()
    session.headers.update({"User-Agent": "RTRFM-The-Rounds-Home-Assistant/1.0"})

    while True:
        wait_seconds = seconds_until_sunday(sunday_hour)
        next_run = dt.datetime.now(TIMEZONE) + dt.timedelta(seconds=wait_seconds)
        log.info("Next weekly check at %s.", next_run.strftime("%Y-%m-%d %H:%M %Z"))
        time.sleep(wait_seconds)
        try:
            run_once(session, lookback_days)
        except Exception:
            log.exception("The archive check failed; it will retry later.")


if __name__ == "__main__":
    main()
