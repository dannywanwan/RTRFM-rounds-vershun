#!/bin/zsh
set -euo pipefail

REPO_DIR="${0:A:h}"
RUNNER="$REPO_DIR/Run Monthly Playlisty Download.command"
SUPPORT_DIR="$HOME/Library/Application Support/RTRFM Playlisty"
INSTALLED_RUNNER="$SUPPORT_DIR/run-monthly-playlisty-download.zsh"
PLIST="$HOME/Library/LaunchAgents/com.dannywanwan.rtrfm-playlisty-monthly.plist"
LOG_DIR="$HOME/Library/Logs"
REMOTE_URL="$(git -C "$REPO_DIR" remote get-url origin)"
DOWNLOAD_DIR="$HOME/RTRFM Playlisty"

if [ ! -x "$RUNNER" ]; then
  chmod +x "$RUNNER"
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR" "$SUPPORT_DIR"

{
  print -r '#!/bin/zsh'
  print -r 'set -euo pipefail'
  printf 'REMOTE_URL=%q\n' "$REMOTE_URL"
  printf 'DOWNLOAD_DIR=%q\n' "$DOWNLOAD_DIR"
  print -r 'STAMP_DIR="$HOME/Library/Application Support/RTRFM Playlisty"'
  print -r 'STAMP_FILE="$STAMP_DIR/monthly-download-stamp"'
  print -r 'LOG_FILE="$STAMP_DIR/monthly-download.log"'
  print -r 'CACHE_REPO="$STAMP_DIR/repo-cache"'
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
  print -r 'if ! command -v git >/dev/null 2>&1; then'
  print -r '  echo "$(date): Git is not available to the monthly runner." >> "$LOG_FILE"'
  print -r '  exit 1'
  print -r 'fi'
  print -r ''
  print -r 'if [ -d "$CACHE_REPO/.git" ]; then'
  print -r '  git -C "$CACHE_REPO" fetch origin main >> "$LOG_FILE" 2>&1'
  print -r 'else'
  print -r '  git clone --filter=blob:none --no-checkout "$REMOTE_URL" "$CACHE_REPO" >> "$LOG_FILE" 2>&1'
  print -r '  git -C "$CACHE_REPO" fetch origin main >> "$LOG_FILE" 2>&1'
  print -r 'fi'
  print -r ''
  print -r 'playlist_files="$(git -C "$CACHE_REPO" ls-tree -r --name-only origin/main | awk '"'"'/^((The Rounds|Jamdown Vershun) - .*\.txt|Playlisty\/.*\.txt)$/ { print }'"'"')"'
  print -r ''
  print -r 'if [ -z "$playlist_files" ]; then'
  print -r '  echo "$(date): No Playlisty text files were found on GitHub." >> "$LOG_FILE"'
  print -r '  exit 1'
  print -r 'fi'
  print -r ''
  print -r 'mkdir -p "$DOWNLOAD_DIR"'
  print -r ''
  print -r 'echo "$playlist_files" | while IFS= read -r file; do'
  print -r '  mkdir -p "$DOWNLOAD_DIR/$(dirname "$file")"'
  print -r '  git -C "$CACHE_REPO" show "origin/main:$file" > "$DOWNLOAD_DIR/$file"'
  print -r '  echo "$(date): Updated $file" >> "$LOG_FILE"'
  print -r 'done'
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
/usr/libexec/PlistBuddy -c "Add :WorkingDirectory string $SUPPORT_DIR" "$PLIST"
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
echo "Files will download to: $DOWNLOAD_DIR"
echo
echo "You can close this window."
