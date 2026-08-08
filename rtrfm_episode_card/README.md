# RTRFM Episodes dashboard card

This custom Lovelace card lists audio files from the local Home Assistant Media
Source folder used by the RTRFM Audio Archive app and plays a selected file on
Sonos.

## Install

Copy `rtrfm-episode-card.js` to `/config/www/rtrfm-episode-card.js` in Home
Assistant. Add this dashboard resource under **Settings > Dashboards > ⋮ >
Resources**:

```yaml
url: /local/rtrfm-episode-card.js
type: module
```

Then add a **Manual** card to the dashboard:

```yaml
type: custom:rtrfm-episode-card
entity: media_player.dining_room_2
```

After adding a new file, use the refresh button in the card.

## Optional configuration

The title and media roots can be changed:

```yaml
type: custom:rtrfm-episode-card
title: RTRFM The Rounds
entity: media_player.dining_room_2
roots:
  - media-source://media_source/local
```
