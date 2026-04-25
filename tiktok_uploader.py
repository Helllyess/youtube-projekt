#!/usr/bin/env python3
"""
TikTokUploader – Lädt Videos über die TikTok Content Posting API hoch.
Nutzt OAuth 2.0 mit lokalem Callback-Server (Port 8080).

Sandbox:    TIKTOK_CLIENT_KEY=sbaw62nxydz07l7twr
Production: TIKTOK_CLIENT_KEY=awkxj83dntx3tri1  (nach App-Review)
"""

import os
import json
import time
import logging
import secrets
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests

logger = logging.getLogger("tiktok_uploader")

AUTH_URL       = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL      = "https://open.tiktokapis.com/v2/oauth/token/"
INIT_URL       = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL     = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
REDIRECT_URI   = "http://localhost:8080/callback"
SCOPES         = "user.info.basic,video.upload"
TOKEN_FILE     = Path(__file__).parent / "config" / "tiktok_token.json"
CHUNK_SIZE     = 10 * 1024 * 1024  # 10 MB
POLL_INTERVAL  = 5
POLL_TIMEOUT   = 300


# ── OAuth Callback Server ─────────────────────────────────────────

class _CallbackHandler(BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        _CallbackHandler.code = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<h2>ContentStudio Pro</h2>"
            b"<p>TikTok verbunden! Du kannst dieses Fenster schlie&szlig;en.</p>"
        )

    def log_message(self, format, *args):
        pass  # suppress server log spam


def _run_callback_server() -> str:
    """Startet lokalen HTTP-Server und wartet auf OAuth-Code."""
    server = HTTPServer(("localhost", 8080), _CallbackHandler)
    server.timeout = 120
    _CallbackHandler.code = None
    while _CallbackHandler.code is None:
        server.handle_request()
    server.server_close()
    return _CallbackHandler.code


# ── TikTokUploader ────────────────────────────────────────────────

class TikTokUploader:
    def __init__(self, settings: dict):
        self.client_key    = settings.get("api_keys", {}).get("tiktok_client_key", "")
        self.client_secret = settings.get("api_keys", {}).get("tiktok_client_secret", "")
        if not self.client_key or not self.client_secret:
            raise ValueError(
                "TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET fehlen in .env"
            )
        self._token_data: dict = {}

    # ── Öffentliche API ──────────────────────────────────────────

    def upload(
        self,
        video_path: str,
        title: str,
        privacy_level: str = "SELF_ONLY",
    ) -> str:
        """
        Lädt ein Video auf TikTok hoch.
        privacy_level: SELF_ONLY | MUTUAL_FOLLOW_FRIENDS | FOLLOWER_OF_CREATOR | PUBLIC_TO_EVERYONE
        Gibt die publish_id zurück.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video nicht gefunden: {video_path}")

        access_token = self._get_access_token()
        video_size   = os.path.getsize(video_path)
        chunk_count  = max(1, (video_size + CHUNK_SIZE - 1) // CHUNK_SIZE)

        logger.info(f"📱 TikTok Upload: '{title}' ({video_size / 1024 / 1024:.1f} MB, {chunk_count} Chunk(s))")

        publish_id, upload_url = self._init_upload(
            access_token, title, privacy_level, video_size, chunk_count
        )
        self._upload_chunks(upload_url, video_path, video_size, chunk_count)
        self._wait_for_publish(access_token, publish_id)

        logger.info(f"✅ TikTok Upload fertig – publish_id: {publish_id}")
        return publish_id

    # ── OAuth ────────────────────────────────────────────────────

    def _get_access_token(self) -> str:
        """Gibt gültiges Access Token zurück – lädt aus Datei oder startet OAuth-Flow."""
        self._token_data = self._load_token()

        if self._token_data.get("access_token"):
            expires_at = self._token_data.get("expires_at", 0)
            if time.time() < expires_at - 60:
                logger.info("TikTok Token aus Datei geladen")
                return self._token_data["access_token"]

            # Refresh versuchen
            refreshed = self._refresh_token(self._token_data.get("refresh_token", ""))
            if refreshed:
                return refreshed

        # Neuer OAuth-Flow
        return self._oauth_flow()

    def _oauth_flow(self) -> str:
        """Öffnet Browser für TikTok Login und tauscht Code gegen Token."""
        state = secrets.token_urlsafe(16)
        params = {
            "client_key":     self.client_key,
            "scope":          SCOPES,
            "response_type":  "code",
            "redirect_uri":   REDIRECT_URI,
            "state":          state,
        }
        auth_url = AUTH_URL + "?" + urlencode(params)
        logger.info(f"Öffne TikTok Login: {auth_url}")
        webbrowser.open(auth_url)

        logger.info("Warte auf OAuth-Callback (Port 8080)...")
        code = _run_callback_server()
        if not code:
            raise RuntimeError("Kein OAuth-Code empfangen – Login abgebrochen?")

        return self._exchange_code(code)

    def _exchange_code(self, code: str) -> str:
        """Tauscht Authorization Code gegen Access Token."""
        r = requests.post(TOKEN_URL, data={
            "client_key":    self.client_key,
            "client_secret": self.client_secret,
            "code":          code,
            "grant_type":    "authorization_code",
            "redirect_uri":  REDIRECT_URI,
        }, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RuntimeError(f"Token-Exchange Fehler: {data}")

        self._save_token(data)
        logger.info("TikTok Token gespeichert")
        return data["access_token"]

    def _refresh_token(self, refresh_token: str) -> str | None:
        """Erneuert Access Token mit Refresh Token."""
        if not refresh_token:
            return None
        try:
            r = requests.post(TOKEN_URL, data={
                "client_key":    self.client_key,
                "client_secret": self.client_secret,
                "grant_type":    "refresh_token",
                "refresh_token": refresh_token,
            }, timeout=15)
            r.raise_for_status()
            data = r.json()
            if data.get("access_token"):
                self._save_token(data)
                logger.info("TikTok Token erneuert")
                return data["access_token"]
        except Exception as e:
            logger.warning(f"Token-Refresh fehlgeschlagen: {e}")
        return None

    def _save_token(self, data: dict):
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        data["expires_at"] = time.time() + data.get("expires_in", 86400)
        with open(TOKEN_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _load_token(self) -> dict:
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    # ── Content Posting API ──────────────────────────────────────

    def _init_upload(
        self,
        access_token: str,
        title: str,
        privacy_level: str,
        video_size: int,
        chunk_count: int,
    ) -> tuple[str, str]:
        """Initialisiert den Upload – gibt (publish_id, upload_url) zurück."""
        payload = {
            "post_info": {
                "title":         title[:150],
                "privacy_level": privacy_level,
                "disable_duet":  False,
                "disable_stitch": False,
                "disable_comment": False,
            },
            "source_info": {
                "source":            "FILE_UPLOAD",
                "video_size":        video_size,
                "chunk_size":        min(CHUNK_SIZE, video_size),
                "total_chunk_count": chunk_count,
            },
        }
        r = requests.post(
            INIT_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json; charset=UTF-8",
            },
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("error", {}).get("code", "ok") != "ok":
            raise RuntimeError(f"TikTok Init Fehler: {data['error']}")

        publish_id = data["data"]["publish_id"]
        upload_url = data["data"]["upload_url"]
        logger.info(f"   publish_id: {publish_id}")
        return publish_id, upload_url

    def _upload_chunks(
        self, upload_url: str, video_path: str, video_size: int, chunk_count: int
    ):
        """Lädt Video in Chunks hoch."""
        with open(video_path, "rb") as f:
            for i in range(chunk_count):
                start = i * CHUNK_SIZE
                chunk = f.read(CHUNK_SIZE)
                end   = start + len(chunk) - 1

                r = requests.put(
                    upload_url,
                    headers={
                        "Content-Type":  "video/mp4",
                        "Content-Range": f"bytes {start}-{end}/{video_size}",
                        "Content-Length": str(len(chunk)),
                    },
                    data=chunk,
                    timeout=120,
                )
                r.raise_for_status()
                logger.info(f"   Chunk {i + 1}/{chunk_count} hochgeladen")

    def _wait_for_publish(self, access_token: str, publish_id: str):
        """Wartet bis TikTok das Video verarbeitet hat."""
        elapsed = 0
        while elapsed < POLL_TIMEOUT:
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            r = requests.post(
                STATUS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type":  "application/json; charset=UTF-8",
                },
                json={"publish_id": publish_id},
                timeout=15,
            )
            r.raise_for_status()
            data   = r.json()
            status = data.get("data", {}).get("status", "")
            logger.info(f"   Status: {status} ({elapsed}s)")

            if status == "PUBLISH_COMPLETE":
                return
            if status in ("FAILED", "SPAM_RISK_TOO_MANY_POSTS", "PUBLISH_FAILED"):
                err = data.get("data", {}).get("fail_reason", status)
                raise RuntimeError(f"TikTok Publish fehlgeschlagen: {err}")

        raise TimeoutError(f"TikTok Publish Timeout nach {POLL_TIMEOUT}s")


# ── CLI ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    from main import load_settings

    parser = argparse.ArgumentParser(description="TikTok Video Upload")
    parser.add_argument("--video",   required=True, help="Pfad zur MP4-Datei")
    parser.add_argument("--title",   required=True, help="Video-Titel")
    parser.add_argument("--privacy", default="SELF_ONLY",
                        choices=["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS",
                                 "FOLLOWER_OF_CREATOR", "PUBLIC_TO_EVERYONE"])
    parser.add_argument("--config",  default="config/settings.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = load_settings(args.config)
    uploader = TikTokUploader(settings)
    pid = uploader.upload(args.video, args.title, args.privacy)
    print(f"\n✅ Veröffentlicht – publish_id: {pid}")
