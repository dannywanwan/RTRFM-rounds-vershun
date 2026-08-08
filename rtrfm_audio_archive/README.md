# RTRFM Audio Archive

This Home Assistant app downloads The Rounds from RTRFM. It keeps the newest available episode at the stable path `/media/rtrfm/The Rounds/The Rounds - Latest.mp4` and permanently archives older episodes with dated names in `/share/qnap_rtrfm/The Rounds/`.

The app checks every 24 hours by default. It never deletes a local episode until the QNAP copy has completed and passed a size check.
