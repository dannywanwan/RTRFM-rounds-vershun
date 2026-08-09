# Changelog

## 1.15.0

- Added a configurable show name to the Lovelace card.
- Added a separate Jamdown Vershun card configuration.
- The Rounds and Jamdown episode lists remain independent.

## 1.14.0

- Runs one check when the app starts, then continues with the weekly Sunday schedule.
- Restarting the app now provides an on-demand refresh without changing its schedule.

## 1.13.0

- Added Saturday replay downloads for Jamdown Vershun using RTRFM slug `jamdown`.
- Keeps Jamdown files locally in `/media/rtrfm/Jamdown Vershun/`.
- Adds a stable `Jamdown Vershun - Latest.mp3` and dated episode files.
- Keeps The Rounds download and state handling unchanged.

## 1.12.0

- Added an automatic cache-busting loader for the Lovelace card.
- Future card updates no longer require changing the dashboard resource URL.
- The loader fetches the current implementation whenever the dashboard loads.

## 1.11.0

- Locks the dashboard card to the confirmed Media Source folder `rtrfm/The Rounds`.
- Removes the broad media-tree scan.

## 1.10.0

- Replaced the daily polling loop with one scheduled check every Sunday at 3:00am Australia/Perth time.
- Added a configurable `sunday_hour` option.
- Kept `interval_hours` for compatibility with existing app settings; it is no longer used.

## 1.9.0

- Sends Sonos the supported generic `music` media type instead of the detected `audio/mp4` type.
- Keeps the dashboard resource URL stable so future app updates do not require changing the resource entry.

## 1.8.0

- Limits the dashboard list to audio files inside the `The Rounds` folder.
- Excludes audio files from other media folders and QNAP branches.

## 1.7.0

- Searches both Media Source root forms for audio files.
- Removed filename and folder-name assumptions that could hide valid episodes.
- Ignores unavailable Media Source branches while continuing the search.

## 1.6.0

- Improved the Lovelace card search so it finds `The Rounds - ...` audio files across the local Media Source tree.
- Ignores inaccessible media branches instead of failing the complete episode list.
- Keeps automatic dashboard-card installation enabled.

## 1.5.0

- Installs and updates the Lovelace card automatically at `/config/www/rtrfm-episode-card.js`.
- Added the required Home Assistant configuration mapping for card installation.

## 1.4.0

- Keeps dated episodes in local Home Assistant media storage.
- Removed the QNAP archive-copy requirement.

## 1.3.0

- Exposed the QNAP archive through Home Assistant media storage.

## 1.2.1

- Bumped the app version to force Home Assistant to refresh app metadata.

## 1.2.0

- Standardized the stable latest file as `The Rounds - Latest.mp3`.

## 1.1.0

- Added stable latest-file naming and cleanup of obsolete latest extensions.

## 1.0.0

- Initial Home Assistant audio archive app.
