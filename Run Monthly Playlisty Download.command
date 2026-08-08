#!/bin/zsh
set -euo pipefail

REPO_DIR="${0:A:h}"
STAMP_DIR="$HOME/Library/Application Support/RTRFM Playlisty"
STAMP_FILE="$STAMP_DIR/monthly-download-stamp"
LOG_FILE="$STAMP_DIR/monthly-download.log"
THIS_MONTH="$(date +%Y-%m)"

mkdir -p "$STAMP_DIR"

if [ -f "$STAMP_FILE" ] && [ "$(cat "$STAMP_FILE")" = "$THIS_MONTH" ]; then
  echo "$(date): Already downloaded Playlisty files for $THIS_MONTH." >> "$LOG_FILE"
  exit 0
fi

echo "$(date): Starting monthly Playlisty download for $THIS_MONTH." >> "$LOG_FILE"

"$REPO_DIR/Download Latest Playlists.command" >> "$LOG_FILE" 2>&1

echo "$THIS_MONTH" > "$STAMP_FILE"
echo "$(date): Finished monthly Playlisty download for $THIS_MONTH." >> "$LOG_FILE"
