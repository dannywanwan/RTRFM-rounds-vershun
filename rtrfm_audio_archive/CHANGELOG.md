# Changelog

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
