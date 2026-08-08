# RTRFM Playlisty exports

This project fetches RTRFM tracklists for:

- The Rounds
- Jamdown Vershun

It writes Playlisty-friendly text files and keeps the full dated archive in this repository.

## The Rounds audio proof of concept

`download_rtrfm_audio.py` checks recent Saturday episodes of The Rounds and downloads any available MP3 recordings. It keeps dated files permanently in:

```text
~/RTRFM Audio/The Rounds/
```

To run it by double-clicking, open:

```text
Download The Rounds Audio.command
```

The proof of concept checks the last 35 days, skips files already downloaded, and writes incomplete downloads as temporary files until they finish.

## Home Assistant audio archive app

The `rtrfm_audio_archive/` folder is a Home Assistant app repository entry. Add this GitHub repository to the Home Assistant app store, install **RTRFM Audio Archive**, and start it. It keeps the newest The Rounds episode at the stable path `/media/rtrfm/The Rounds/The Rounds - Latest.mp3` and moves older episodes to dated files in `/media/qnap_rtrfm/The Rounds/`.

## Where the files go

The repository root keeps every generated dated export forever:

- `The Rounds - YYYY-MM-DD.txt`
- `Jamdown Vershun - YYYY-MM-DD.txt`

The repository root also keeps convenience latest files:

- `The Rounds - Latest.txt`
- `Jamdown Vershun - Latest.txt`

The `Playlisty/` folder contains only the latest files, so it is the cleanest place to look when importing into Playlisty:

- `Playlisty/The Rounds - Latest.txt`
- `Playlisty/Jamdown Vershun - Latest.txt`

## Automatic GitHub run

GitHub Actions runs `rtrfm.py` every Sunday at about 10:00am Australia/Perth time. The workflow can also be run manually from the Actions tab in GitHub.

Each successful run:

- installs the Python dependencies from `requirements.txt`
- fetches the RTRFM tracklists
- commits changed `.txt` playlist files back to `main`
- uploads a `playlisty-text` artifact to the workflow run
- preserves `.rtrfm_state.json` in the Actions cache without committing it

No extra secrets are needed for the current script. GitHub uses its built-in `GITHUB_TOKEN` to commit the generated text files.

## Download the latest files to this Mac

Double-click:

```text
Download Latest Playlists.command
```

That command downloads the latest Playlisty text files from GitHub into this local folder. It updates only:

- `The Rounds - *.txt`
- `Jamdown Vershun - *.txt`
- `Playlisty/*.txt`

It does not update code or workflow files.

## Download automatically once per month

Double-click this once:

```text
Install Monthly Playlisty Download.command
```

That installs a Mac LaunchAgent for the current user. It checks every 6 hours while the Mac is awake, including after login, and downloads the latest Playlisty files only once per calendar month.

Monthly automatic downloads are saved here:

```text
~/RTRFM Playlisty/
```

The monthly runner keeps its stamp and log here:

```text
~/Library/Application Support/RTRFM Playlisty/
```

The LaunchAgent itself is installed here:

```text
~/Library/LaunchAgents/com.dannywanwan.rtrfm-playlisty-monthly.plist
```

To remove the monthly automation, double-click:

```text
Uninstall Monthly Playlisty Download.command
```

## Run locally

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Fetch playlists:

```bash
python3 rtrfm.py
```

For the weekly scheduled guard:

```bash
python3 rtrfm.py --scheduled
```

## Runtime files

These are intentionally ignored and should not be committed:

- `.rtrfm_state.json`
- `rtrfm.log`
- `rtrfm_error.log`
