#!/bin/zsh
set -euo pipefail

cd "${0:A:h}"

echo "Updating RTRFM Playlisty text files..."
echo

if ! command -v git >/dev/null 2>&1; then
  echo "Git is not installed or is not available in this Terminal session."
  exit 1
fi

git fetch origin main

playlist_files="$(git ls-tree -r --name-only origin/main | awk '/^((The Rounds|Jamdown Vershun) - .*\.txt|Playlisty\/.*\.txt)$/ { print }')"

if [ -z "$playlist_files" ]; then
  echo "No Playlisty text files were found on GitHub."
  exit 1
fi

echo "$playlist_files" | while IFS= read -r file; do
  mkdir -p "$(dirname "$file")"
  git show "origin/main:$file" > "$file"
  echo "Updated $file"
done

echo
echo "Done. You can close this window."
