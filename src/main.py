from __future__ import annotations
import argparse
import os
from typing import List
from dotenv import load_dotenv

from .util import log
from .youtube_client import YouTubeClient
from .spotify_client import SpotifyClient
from .mapping import guess_artist_title

load_dotenv()


def run(playlist_name: str, max_results: int, dry_run: bool):
    yt = YouTubeClient(oauth_port=int(os.getenv("GOOGLE_OAUTH_PORT", 8081)))
    sp = SpotifyClient()

    liked = yt.get_liked_videos(max_results=max_results)

    # Map to (artist, title)
    mapped: List[dict] = []
    for v in liked:
        artist, title = guess_artist_title(v["title"], v.get("channel"))
        mapped.append({"artist": artist, "title": title, "yt_title": v["title"]})

    # Resolve on Spotify
    found_ids: List[str] = []
    misses: List[str] = []
    for m in mapped:
        tid = sp.search_track(m["artist"], m["title"]) or sp.search_track("", m["title"])
        if tid:
            found_ids.append(tid)
        else:
            misses.append(m["yt_title"])

    log.info(f"Resolved {len(found_ids)} / {len(mapped)} tracks on Spotify")

    if dry_run:
        log.info("DRY RUN: not creating playlist or adding tracks.")
        if misses:
            log.info("Unresolved examples: " + "; ".join(misses[:10]))
        return

    pl_id = sp.get_or_create_playlist(playlist_name)

    # De-duplicate: avoid adding tracks that already exist
    existing = set(sp.playlist_track_ids(pl_id))
    to_add = [t for t in found_ids if t not in existing]

    if not to_add:
        log.info("Nothing new to add—playlist already up to date.")
        return

    batch_size = int(os.getenv("BATCH_SIZE", 90))
    sp.add_tracks(pl_id, to_add, batch_size=batch_size)
    log.info("Done.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--playlist", default=os.getenv("DEFAULT_PLAYLIST", "YouTube Likes (Auto)"))
    p.add_argument("--max", type=int, default=int(os.getenv("MAX_RESULTS", 200)))
    p.add_argument("--dry-run", default=os.getenv("DRY_RUN", "false"))
    args = p.parse_args()

    run(args.playlist, args.max, str(args.dry_run).lower() in {"1", "true", "yes", "y"})
