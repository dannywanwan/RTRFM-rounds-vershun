#!/bin/zsh
set -euo pipefail

REPO_DIR="${0:A:h}"
RUNNER="$REPO_DIR/Run Monthly Playlisty Download.command"
SUPPORT_DIR="$HOME/Library/Application Support/RTRFM Playlisty"
INSTALLED_RUNNER="$SUPPORT_DIR/run-monthly-playlisty-download.zsh"
PLIST="$HOME/Library/LaunchAgents/com.dannywanwan.rtrfm-playlisty-monthly.plist"
LOG_DIR="$HOME/Library/Logs"

if [ ! -x "$RUNNER" ]; then
  chmod +x "$RUNNER"
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR" "$SUPPORT_DIR"

{
  print -r '#!/bin/zsh'
  print -r 'set -euo pipefail'
  printf 'REPO_DIR=%q\n' "$REPO_DIR"
  print -r 'STAMP_DIR="$HOME/Library/Application Support/RTRFM Playlisty"'
  print -r 'STAMP_FILE="$STAMP_DIR/monthly-download-stamp"'
  print -r 'LOG_FILE="$STAMP_DIR/monthly-download.log"'
  print -r 'THIS_MONTH="$(date +%Y-%m)"'
  print -r ''
  print -r 'mkdir -p "$STAMP_DIR"'
  print -r ''
  print -r 'if [ -f "$STAMP_FILE" ] && [ "$(cat "$STAMP_FILE")" = "$THIS_MONTH" ]; then'
  print -r '  echo "$(date): Already downloaded Playlisty files for $THIS_MONTH." >> "$LOG_FILE"'
  print -r '  exit 0'
  print -r 'fi'
  print -r ''
  print -r 'echo "$(date): Starting monthly Playlisty download for $THIS_MONTH." >> "$LOG_FILE"'
  print -r ''
  print -r '/bin/zsh "$REPO_DIR/Download Latest Playlists.command" >> "$LOG_FILE" 2>&1'
  print -r ''
  print -r 'echo "$THIS_MONTH" > "$STAMP_FILE"'
  print -r 'echo "$(date): Finished monthly Playlisty download for $THIS_MONTH." >> "$LOG_FILE"'
} > "$INSTALLED_RUNNER"

chmod +x "$INSTALLED_RUNNER"

/usr/libexec/PlistBuddy -c "Clear dict" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :Label string com.dannywanwan.rtrfm-playlisty-monthly" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :ProgramArguments array" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :ProgramArguments:0 string /bin/zsh" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :ProgramArguments:1 string $INSTALLED_RUNNER" "$PLIST"
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
