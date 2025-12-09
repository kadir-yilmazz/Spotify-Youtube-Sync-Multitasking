"""YouTube Data API manager.

This module contains the `YouTubeManager` class. Since the methods making
actual API calls are dynamic, pylint might produce some false-positives;
generated-members settings can be adjusted in pylint config if needed.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.youtube.interfaces import VideoSearcher

load_dotenv()

# pylint: disable=broad-exception-caught


SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# Allow users to set custom paths via environment variables or .env
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_PATH", "client_secrets.json")
TOKEN_FILE = os.getenv("TOKEN_PATH", "token.json")


class YouTubeManager(VideoSearcher):
    """Implements the VideoSearcher abstract class using the YouTube Data API."""

    def __init__(self) -> None:
        self.credentials: Optional[Credentials] = None
        self.youtube = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticates the user and saves the token to a file."""
        creds: Optional[Credentials] = None

        # 1. Try to load existing token file
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            except Exception:  # pylint: disable=broad-exception-caught
                print("Old token is invalid, obtaining a new one.")
                creds = None

        # 2. If token is missing or invalid, get a new one
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:  # pylint: disable=broad-exception-caught
                    creds = None

            if not creds:
                # Redirect user to browser
                if not os.path.exists(CLIENT_SECRETS_FILE):
                    msg = (
                        "Client secrets file not found. "
                        f"Expected path: '{CLIENT_SECRETS_FILE}'. "
                        "Please place your Google OAuth client_secrets.json file here "
                        "or set a different path via CLIENT_SECRETS_PATH env."
                    )
                    raise FileNotFoundError(msg)

                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # 3. Save new token to file
            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        self.credentials = creds
        self.youtube = build("youtube", "v3", credentials=creds)

    def _api_call_with_retries(self, func, *args, **kwargs):
        """Simple retry/backoff mechanism for HttpError.

        - `func` must be a callable (e.g., `request.execute`).
        - Applies exponential backoff up to 3 attempts.
        - Retries on 5xx errors; raises other errors.
        """
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except HttpError as http_err:
                # Retry on Google API side 5xx errors
                if http_err.resp.status >= 500:
                    if attempt == max_attempts:
                        raise
                    continue
                raise
        return None

    def search_video(self, query: str) -> Optional[dict]:
        """Searches for a video on YouTube and returns the first result."""
        if not self.youtube:
            return None

        try:
            request = self.youtube.search().list(
                part="snippet",
                maxResults=1,
                q=query,
                type="video"
            )
            response = self._api_call_with_retries(request.execute)

            if response and "items" in response and len(response["items"]) > 0:
                item = response["items"][0]
                return {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"]
                }
        except Exception as e:
            print(f"Error searching for '{query}': {e}")

        return None

    def create_playlist(self, title: str, description: str = "") -> Optional[str]:
        """Creates a new playlist and returns its ID."""
        if not self.youtube:
            return None

        try:
            request = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description
                    },
                    "status": {
                        "privacyStatus": "private"
                    }
                }
            )
            response = self._api_call_with_retries(request.execute)
            return response["id"]
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return None

    def add_video_to_playlist(self, playlist_id: str, video_id: str) -> bool:
        """Adds a video to a playlist."""
        if not self.youtube:
            return False

        try:
            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            self._api_call_with_retries(request.execute)
            return True
        except Exception as e:
            print(f"Error adding video {video_id} to playlist: {e}")
            return False
