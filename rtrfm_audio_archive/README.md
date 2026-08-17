# RTRFM Audio Archive

This Home Assistant app downloads The Rounds from RTRFM. It keeps the newest available episode at the stable path `/media/rtrfm/The Rounds/The Rounds - Latest.mp3` and permanently keeps older episodes with dated names in the same local folder.

The app runs one check when it starts, then checks again every Sunday at 3:00am Australia/Perth time by default. Restarting the app provides an on-demand refresh. It does not require a QNAP mount and downloads The Rounds, Jamdown Vershun, and Trainwreck, keeping each show in its own folder under `/media/rtrfm/`. It also copies the combined tracklist archive into `/media/rtrfm/RTRFM Tracklists.txt`, reports the combined local storage used by those files, and installs the dashboard card automatically at `/config/www/rtrfm-episode-card.js` when the app starts. The `sunday_hour` option can change the hour.

Release details are recorded in [`CHANGELOG.md`](CHANGELOG.md) and will be updated with each new app version.
