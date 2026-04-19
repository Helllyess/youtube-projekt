#!/usr/bin/env python3
"""
YouTubeUploader – Lädt Videos über die YouTube Data API v3 hoch.
Unterstützt OAuth2 mit automatischer Token-Erneuerung.
"""

import os
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("uploader")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CHUNK_SIZE = 1024 * 1024 * 10  # 10 MB Chunks


class YouTubeUploader:
    def __init__(self, settings: dict):
        self.settings = settings
        self.upload_cfg = settings.get("upload", {})
        self.channel_cfg = settings.get("channel", {})
        self.client_secret_file = settings.get("upload", {}).get(
            "client_secret_file", "config/youtube_client_secret.json"
        )
        self.token_file = self.upload_cfg.get("token_file", "config/token.json")
        self.max_retries = self.upload_cfg.get("max_retries", 3)
        self.retry_delay = self.upload_cfg.get("retry_delay_seconds", 60)
        self._youtube = None

    def upload(
        self,
        video_path: str,
        thumbnail_path: str,
        title: str,
        description: str,
        tags: list = None,
        privacy: str = None,
    ) -> str:
        """Lädt ein Video auf YouTube hoch und gibt die URL zurück."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video nicht gefunden: {video_path}")

        privacy = privacy or self.channel_cfg.get("default_privacy", "private")
        tags = tags or self.channel_cfg.get("default_tags", [])
        category = self.channel_cfg.get("default_category", "25")
        made_for_kids = self.channel_cfg.get("made_for_kids", False)

        youtube = self._get_authenticated_service()

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:30],
                "categoryId": category,
                "defaultLanguage": self.channel_cfg.get("language", "de"),
            },
            "status": {
                "privacyStatus": privacy,
                "madeForKids": made_for_kids,
                "selfDeclaredMadeForKids": made_for_kids,
            },
        }

        logger.info(f"Upload gestartet: '{title}' ({privacy})")
        video_id = self._upload_with_retry(youtube, video_path, body)

        if video_id:
            # Thumbnail hochladen
            if thumbnail_path and os.path.exists(thumbnail_path):
                self._upload_thumbnail(youtube, video_id, thumbnail_path)

            url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"✅ Upload erfolgreich: {url}")
            return url
        else:
            raise RuntimeError("Upload fehlgeschlagen – keine Video-ID erhalten")

    def _upload_with_retry(self, youtube, video_path: str, body: dict) -> str:
        """Upload mit automatischem Retry bei Fehlern."""
        from googleapiclient.http import MediaFileUpload

        for attempt in range(1, self.max_retries + 1):
            try:
                media = MediaFileUpload(
                    video_path,
                    chunksize=CHUNK_SIZE,
                    resumable=True,
                    mimetype="video/mp4",
                )

                request = youtube.videos().insert(
                    part="snippet,status",
                    body=body,
                    media_body=media,
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"  Upload: {progress}%")

                video_id = response.get("id")
                logger.info(f"  Video-ID: {video_id}")
                return video_id

            except Exception as e:
                logger.warning(f"Upload-Versuch {attempt}/{self.max_retries} fehlgeschlagen: {e}")
                if attempt < self.max_retries:
                    logger.info(f"  Warte {self.retry_delay}s vor Retry...")
                    time.sleep(self.retry_delay)
                else:
                    raise

        return None

    def _upload_thumbnail(self, youtube, video_id: str, thumbnail_path: str):
        """Setzt Thumbnail für das Video."""
        try:
            from googleapiclient.http import MediaFileUpload

            media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=media,
            ).execute()
            logger.info("  Thumbnail hochgeladen ✓")
        except Exception as e:
            logger.warning(f"Thumbnail-Upload fehlgeschlagen: {e}")

    def _get_authenticated_service(self):
        """Erstellt einen authentifizierten YouTube-Service."""
        if self._youtube:
            return self._youtube

        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None

            # Vorhandenes Token laden
            if os.path.exists(self.token_file):
                try:
                    creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                    logger.info("Vorhandenes OAuth-Token geladen")
                except Exception as e:
                    logger.warning(f"Token konnte nicht geladen werden: {e}")

            # Token erneuern wenn abgelaufen
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("OAuth-Token erneuert")
                except Exception as e:
                    logger.warning(f"Token-Erneuerung fehlgeschlagen: {e}")
                    creds = None

            # Neues Token erstellen wenn nötig
            if not creds or not creds.valid:
                if not os.path.exists(self.client_secret_file):
                    raise FileNotFoundError(
                        f"YouTube Client Secret nicht gefunden: {self.client_secret_file}\n"
                        "Bitte lade deine OAuth2-Credentials von der Google Console herunter."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, SCOPES
                )
                creds = flow.run_local_server(
                    port=8080,
                    prompt="consent",
                    open_browser=True,
                )
                logger.info("Neue OAuth-Authentifizierung durchgeführt")

                # Token speichern für zukünftige Verwendung
                Path(self.token_file).parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_file, "w") as f:
                    f.write(creds.to_json())
                logger.info(f"Token gespeichert: {self.token_file}")

            self._youtube = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
            return self._youtube

        except ImportError as e:
            logger.error(
                "Google API Libraries nicht installiert.\n"
                "Bitte ausführen: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
            raise ImportError(
                "Fehlende Abhängigkeiten für YouTube Upload.\n"
                "Führe aus: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            ) from e

    def get_channel_info(self) -> dict:
        """Holt Informationen über den eigenen YouTube-Kanal."""
        try:
            youtube = self._get_authenticated_service()
            response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
            if response.get("items"):
                channel = response["items"][0]
                return {
                    "id": channel["id"],
                    "title": channel["snippet"]["title"],
                    "subscribers": channel["statistics"].get("subscriberCount", "?"),
                    "videos": channel["statistics"].get("videoCount", "?"),
                    "views": channel["statistics"].get("viewCount", "?"),
                }
        except Exception as e:
            logger.error(f"Kanal-Info Fehler: {e}")
        return {}

    def set_video_public(self, video_id: str) -> bool:
        """Schaltet ein Video von privat auf öffentlich."""
        try:
            youtube = self._get_authenticated_service()
            youtube.videos().update(
                part="status",
                body={
                    "id": video_id,
                    "status": {"privacyStatus": "public"},
                },
            ).execute()
            logger.info(f"Video {video_id} ist jetzt öffentlich")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Veröffentlichen: {e}")
            return False
