# RTRFM Audio Archive

This Home Assistant app downloads The Rounds from RTRFM. It keeps the newest available episode at the stable path `/media/rtrfm/The Rounds/The Rounds - Latest.mp3` and permanently keeps older episodes with dated names in the same local folder.

The app checks once every Sunday at 3:00am Australia/Perth time by default and does not require a QNAP mount. It downloads both The Rounds and Jamdown Vershun, keeping each show in its own folder under `/media/rtrfm/`. The `sunday_hour` option can change the hour. It also installs the dashboard card automatically at `/config/www/rtrfm-episode-card.js` when the app starts.

Release details are recorded in [`CHANGELOG.md`](CHANGELOG.md) and will be updated with each new app version.
