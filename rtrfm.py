import re
import sys
from datetime import date
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
]
STOP_LINES = {
    "Episode recap",
    "Presented by:",
    "Loading...",
}
TIMESTAMP_RE = re.compile(r"(?:\d{1,2}:\d{2}|--:--)")  # RTRFM timestamps


def fetch_tracks(show):
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

    return tracks


def save_playlist(show, tracks, playlist_date, output_dir):
    show_name = show["name"]
    title = f"{show_name} \u2014 {playlist_date:%Y-%m-%d}"
    content = f"{title}\n\n" + "\n".join(tracks)

    dated_path = output_dir / f"{show_name} - {playlist_date:%Y-%m-%d}.txt"
    latest_path = output_dir / f"{show_name} - Latest.txt"

    dated_path.write_text(content, encoding="utf-8")
    latest_path.write_text(content, encoding="utf-8")

    return dated_path, latest_path


def main():
    script_dir = Path(__file__).resolve().parent
    playlist_date = date.today()
    failures = []

    for show in SHOWS:
        try:
            tracks = fetch_tracks(show)
            dated_path, latest_path = save_playlist(show, tracks, playlist_date, script_dir)
        except Exception as exc:
            failures.append((show["name"], exc))
            print(f"{show['name']}: failed: {exc}")
            continue

        print(f"{show['name']}: found {len(tracks)} tracks.")
        print(f"Dated playlist: {dated_path}")
        print(f"Latest playlist: {latest_path}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
