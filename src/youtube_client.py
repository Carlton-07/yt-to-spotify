from __future__ import annotations
import os
from typing import List, Dict

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from .util import log

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


class YouTubeClient:
    def __init__(self, oauth_port: int = 8081):
        self.oauth_port = oauth_port
        self.service = self._auth()

    def _auth(self):
        creds = None
        token_path = "credentials/google_token.json"
        client_secret_path = "credentials/google_client_secret.json"

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                log.info("Refreshing Google token…")
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret_path, SCOPES
                )
                creds = flow.run_local_server(
                    port=int(os.getenv("GOOGLE_OAUTH_PORT", self.oauth_port)),
                    prompt="consent",
                    authorization_prompt_message="",
                )
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return build("youtube", "v3", credentials=creds)

    def get_liked_videos(self, max_results: int = 200) -> List[Dict]:
        """Return list of dicts: {id, title, channel} (up to max_results)."""
        out: List[Dict] = []
        page_token = None
        fetched = 0

        while True:
            req = self.service.videos().list(
                part="snippet",
                myRating="like",
                maxResults=min(50, max_results - fetched),
                pageToken=page_token,
            )
            resp = req.execute()
            for item in resp.get("items", []):
                vid = item["id"]
                sn = item["snippet"]
                out.append(
                    {
                        "id": vid,
                        "title": sn.get("title"),
                        "channel": sn.get("channelTitle"),
                    }
                )
                fetched += 1
                if fetched >= max_results:
                    break

            page_token = resp.get("nextPageToken")
            if not page_token or fetched >= max_results:
                break

        log.info(f"Fetched {len(out)} liked videos from YouTube")
        return out
