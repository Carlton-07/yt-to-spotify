# yt-to-spotify

# YouTube Likes → Spotify Playlist

Turn your **YouTube Liked videos** into a **Spotify playlist** with one command.

![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB)
![YouTube Data API v3](https://img.shields.io/badge/API-YouTube%20Data%20API%20v3-FF0000)
![Spotify Web API](https://img.shields.io/badge/API-Spotify%20Web%20API-1DB954)
![License: MIT](https://img.shields.io/badge/License-MIT-informational)

> OAuth 2.0 for both platforms · Token caching/refresh · Rate-limit safe batching · Idempotent (no duplicates) · Clean logs

---

## ✨ Features

- **One-click sync**: Pulls your YouTube **Liked** videos and builds/updates a Spotify playlist.
- **Fuzzy mapping**: Heuristics + fuzzy matching to map video titles to `{artist, track}`.
- **No duplicates**: Checks existing playlist tracks before adding.
- **Resilient**: Handles API rate limits and transient errors with backoff.

---

## 🖼️ How it works

```mermaid
flowchart LR
  YT[YouTube Liked Videos] -->|Data API v3| Map[Title→Artist/Track Mapping]
  Map --> Search[Spotify Search]
  Search -->|Best Match IDs| Diff[De-dupe vs Playlist]
  Diff --> Add[Batch Add Tracks]
  Add --> SP[Spotify Playlist]

