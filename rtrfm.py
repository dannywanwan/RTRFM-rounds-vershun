import argparse
import json
import re
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup


SHOWS = [
    {
        "name": "The Rounds",
        "url": "https://rtrfm.com.au/shows/therounds/",
    },
    {
        "name": "Jamdown Vershun",
        "url": "https://rtrfm.com.au/shows/jamdown/",
    },
    {
        "name": "Trainwreck",
        "url": "https://rtrfm.com.au/shows/trainwreck/",
    },
]
STOP_LINES = {
    "Episode recap",
    "Presented by:",
    "Loading...",
}
TIMESTAMP_RE = re.compile(r"(?:\d{1,2}:\d{2}|--:--)")  # RTRFM timestamps
STATE_FILE = ".rtrfm_state.json"
TRACKLIST_ARCHIVE = "RTRFM Tracklists.txt"
SCHEDULE_WEEKDAY = 6  # Python weekday: Monday is 0, Sunday is 6.
SCHEDULE_TIME = time(hour=10)


def fetch_show(show):
    response = requests.get(
        show["url"],
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in soup.get_text("\n").splitlines()
    ]
    lines = [line for line in lines if line]

    episode_date = extract_episode_date(lines)

    try:
        start = lines.index("Tracklist") + 1
    except ValueError as exc:
        raise RuntimeError(f"Couldn't find the RTRFM tracklist for {show['name']}.") from exc

    tracks = []
    seen = set()
    i = start

    while i < len(lines):
        if lines[i] in STOP_LINES:
            break

        if TIMESTAMP_RE.fullmatch(lines[i]):
            i += 1
            continue

        title = lines[i]

        i += 1
        while i < len(lines) and TIMESTAMP_RE.fullmatch(lines[i]):
            i += 1

        if i >= len(lines):
            break

        artist = lines[i]

        if artist in STOP_LINES:
            break

        track = f"{artist} - {title}"
        if track not in seen:
            tracks.append(track)
            seen.add(track)

        i += 1

    return episode_date, tracks


def extract_episode_date(lines):
    month_names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    date_re = re.compile(r"^(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z]+)$", re.IGNORECASE)

    try:
        episode_index = lines.index("Episode")
    except ValueError:
        return date.today()

    for line in lines[episode_index + 1 : episode_index + 8]:
        match = date_re.fullmatch(line)
        if not match:
            continue
        month = month_names.get(match.group(2).lower())
        if month is None:
            continue
        return date(datetime.now().year, month, int(match.group(1)))

    return date.today()


def fetch_tracks(show):
    """Compatibility wrapper returning only the tracklist."""
    _, tracks = fetch_show(show)
    return tracks


def save_playlist(show, tracks, playlist_date, output_dir):
    show_name = show["name"]
    title = f"{show_name} \u2014 {playlist_date:%Y-%m-%d}"
    content = f"{title}\n\n" + "\n".join(tracks)

    dated_path = output_dir / f"{show_name} - {playlist_date:%Y-%m-%d}.txt"
    latest_path = output_dir / f"{show_name} - Latest.txt"
    playlisty_dir = output_dir / "Playlisty"
    playlisty_latest_path = playlisty_dir / f"{show_name} - Latest.txt"

    playlisty_dir.mkdir(exist_ok=True)
    dated_path.write_text(content, encoding="utf-8")
    latest_path.write_text(content, encoding="utf-8")
    playlisty_latest_path.write_text(content, encoding="utf-8")

    return dated_path, latest_path, playlisty_latest_path


def update_tracklist_archive(entries, output_dir):
    archive_path = output_dir / TRACKLIST_ARCHIVE
    try:
        archive = archive_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        archive = "# RTRFM Tracklists Archive\n\n"

    for show, episode_date, tracks in entries:
        marker = f"## {show['name']} — {episode_date:%Y-%m-%d}"
        block = marker + "\n\n" + "\n".join(tracks) + "\n\n"
        start = archive.find(marker)
        if start >= 0:
            next_heading = re.search(r"^## .+$", archive[start + len(marker) :], re.MULTILINE)
            end = start + len(marker) + next_heading.start() if next_heading else len(archive)
            archive = archive[:start] + block + archive[end:]
        else:
            archive += block

    archive_path.write_text(archive.rstrip() + "\n", encoding="utf-8")
    return archive_path


def scheduled_slot_date(now):
    scheduled_date = now.date() - timedelta(
        days=(now.weekday() - SCHEDULE_WEEKDAY) % 7
    )
    scheduled_at = datetime.combine(scheduled_date, SCHEDULE_TIME, tzinfo=now.tzinfo)

    if now < scheduled_at:
        scheduled_date -= timedelta(days=7)

    return scheduled_date


def should_run_scheduled(output_dir, now):
    slot_date = scheduled_slot_date(now)
    state_path = output_dir / STATE_FILE

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        state = {}
    except json.JSONDecodeError:
        state = {}

    last_slot = state.get("last_successful_scheduled_slot")
    if last_slot == slot_date.isoformat():
        return False, slot_date, state_path

    return True, slot_date, state_path


def record_scheduled_run(state_path, slot_date):
    state = {
        "last_successful_scheduled_slot": slot_date.isoformat(),
        "last_successful_run": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def run_playlists(script_dir):
    failures = []
    archive_entries = []

    for show in SHOWS:
        try:
            episode_date, tracks = fetch_show(show)
            dated_path, latest_path, playlisty_latest_path = save_playlist(
                show,
                tracks,
                episode_date,
                script_dir,
            )
            archive_entries.append((show, episode_date, tracks))
        except Exception as exc:
            failures.append((show["name"], exc))
            print(f"{show['name']}: failed: {exc}")
            continue

        print(f"{show['name']}: found {len(tracks)} tracks.")
        print(f"Episode date: {episode_date}")
        print(f"Dated playlist: {dated_path}")
        print(f"Latest playlist: {latest_path}")
        print(f"Playlisty latest: {playlisty_latest_path}")

    if failures:
        sys.exit(1)

    archive_path = update_tracklist_archive(archive_entries, script_dir)
    print(f"Combined tracklist archive: {archive_path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch RTRFM show tracklists.")
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Only fetch once per Sunday 10am weekly slot.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent

    if args.scheduled:
        should_run, slot_date, state_path = should_run_scheduled(
            script_dir,
            datetime.now().astimezone(),
        )
        if not should_run:
            print(f"Already fetched RTRFM playlists for weekly slot {slot_date}.")
            return

        run_playlists(script_dir)
        record_scheduled_run(state_path, slot_date)
        print(f"Recorded scheduled run for weekly slot {slot_date}.")
        return

    run_playlists(script_dir)


if __name__ == "__main__":
    main()
