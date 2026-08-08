#!/bin/zsh

set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

if [[ ! -x .venv-audio/bin/python ]]; then
  echo "Setting up the audio downloader..."
  python3 -m venv .venv-audio
  .venv-audio/bin/pip install -q -r requirements.txt
fi

.venv-audio/bin/python download_rtrfm_audio.py
echo
echo "The Rounds audio archive is in: $HOME/RTRFM Audio/The Rounds"
read -r "REPLY?Press Return to close..."
