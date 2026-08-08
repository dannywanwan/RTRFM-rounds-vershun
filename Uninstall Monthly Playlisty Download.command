#!/bin/zsh
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.dannywanwan.rtrfm-playlisty-monthly.plist"

launchctl bootout "gui/$UID" "$PLIST" 2>/dev/null || true

if [ -f "$PLIST" ]; then
  rm "$PLIST"
fi

echo
echo "Monthly Playlisty download is uninstalled."
echo "You can close this window."
