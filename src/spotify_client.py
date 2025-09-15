from __future__ import annotations
import os
from typing import List, Optional

import backoff
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from rapidfuzz import fuzz

from .util import log

SCOPE = "playlist-modify-public playlist-modify-private"


class SpotifyClient:
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
                scope=SCOPE,
                cache_path="credentials/spotify_cache",
                open_browser=True,
            )
        )
        self.user = self.sp.current_user()
        self.username = self.user.get("id")
        log.info(f"Spotify user: {self.username}")

    @backoff.on_exception(backoff.expo, SpotifyException, max_time=60)
    def search_track(self, artist: str, title: str) -> Optional[str]:
        query_parts: List[str] = []
        if title:
            query_parts.append(f"track:{title}")
        if artist:
            query_parts.append(f"artist:{artist}")
        q = " ".join(query_parts) or title or artist
        res = self.sp.search(q=q, type="track", limit=5)
        items = res.get("tracks", {}).get("items", [])
        if not items:
            return None
        best_id, best_score = None, -1.0
        for it in items:
            name = it.get("name", "")
            artists = ", ".join(a["name"] for a in it.get("artists", []))
            s1 = fuzz.partial_ratio(name.lower(), (title or "").lower())
            s2 = fuzz.partial_ratio(artists.lower(), (artist or "").lower())
            score = s1 * 0.7 + s2 * 0.3
            if score > best_score:
                best_score = score
                best_id = it.get("id")
        return best_id

    def get_or_create_playlist(self, name: str, public: bool = False) -> str:
        # Try to find existing
        limit = 50
        offset = 0
        while True:
            pls = self.sp.current_user_playlists(limit=limit, offset=offset)
            for p in pls.get("items", []):
                if p.get("name") == name:
                    return p.get("id")
            if pls.get("next"):
                offset += limit
            else:
                break
        # Create new
        pl = self.sp.user_playlist_create(self.username, name, public=public)
        return pl.get("id")

    def playlist_track_ids(self, playlist_id: str) -> List[str]:
        ids: List[str] = []
        limit = 100
        offset = 0
        while True:
            res = self.sp.playlist_items(playlist_id, limit=limit, offset=offset)
            for it in res.get("items", []):
                tr = it.get("track") or {}
                if tr.get("id"):
                    ids.append(tr["id"])
            if res.get("next"):
                offset += limit
            else:
                break
        return ids

    def add_tracks(self, playlist_id: str, track_ids: List[str], batch_size: int = 90) -> None:
        from .util import sleep_with_jitter
        if not track_ids:
            return
        for i in range(0, len(track_ids), batch_size):
            chunk = track_ids[i : i + batch_size]
            self.sp.playlist_add_items(playlist_id, chunk)
            log.info(f"Added {len(chunk)} tracks ({i + len(chunk)}/{len(track_ids)})…")
            sleep_with_jitter(0.6, 0.2)
