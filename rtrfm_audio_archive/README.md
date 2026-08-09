# RTRFM Audio Archive

This Home Assistant app downloads The Rounds from RTRFM. It keeps the newest available episode at the stable path `/media/rtrfm/The Rounds/The Rounds - Latest.mp3` and permanently keeps older episodes with dated names in the same local folder.

The app checks every 24 hours by default and does not require a QNAP mount. It also installs the dashboard card automatically at `/config/www/rtrfm-episode-card.js` when the app starts.
