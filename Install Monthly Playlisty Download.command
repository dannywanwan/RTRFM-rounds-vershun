#!/bin/zsh
set -euo pipefail

REPO_DIR="${0:A:h}"
RUNNER="$REPO_DIR/Run Monthly Playlisty Download.command"
PLIST="$HOME/Library/LaunchAgents/com.dannywanwan.rtrfm-playlisty-monthly.plist"
LOG_DIR="$HOME/Library/Logs"

if [ ! -x "$RUNNER" ]; then
  chmod +x "$RUNNER"
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

/usr/libexec/PlistBuddy -c "Clear dict" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :Label string com.dannywanwan.rtrfm-playlisty-monthly" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :ProgramArguments array" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :ProgramArguments:0 string /bin/zsh" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :ProgramArguments:1 string $RUNNER" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :RunAtLoad bool true" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :StartInterval integer 21600" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :StandardOutPath string $LOG_DIR/rtrfm-playlisty-monthly.out.log" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :StandardErrorPath string $LOG_DIR/rtrfm-playlisty-monthly.err.log" "$PLIST"

launchctl bootout "gui/$UID" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$PLIST"
launchctl kickstart -k "gui/$UID/com.dannywanwan.rtrfm-playlisty-monthly"

echo
echo "Monthly Playlisty download is installed."
echo "It checks every 6 hours while the Mac is awake and only downloads once per month."
echo
echo "You can close this window."
