#!/usr/bin/env python3
"""
ChannelManager – Verwaltet mehrere YouTube-Kanäle und Plattformen.
Jeder Kanal hat eigene OAuth-Tokens, Settings und Upload-Einstellungen.

Unterstützte Plattformen:
  - YouTube (mehrere Kanäle)
  - (Erweiterbar: TikTok, Instagram Reels, etc.)

Ordnerstruktur:
  channels/
    kanal1/
      channel_config.json      ← Kanal-spezifische Einstellungen
      youtube_client_secret.json ← OAuth Credentials (von Google Console)
      token.json               ← Auto-generiert beim ersten Login
    kanal2/
      channel_config.json
      youtube_client_secret.json
      token.json
    ...
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("channel_manager")


class ChannelManager:
    def __init__(self, settings: dict):
        self.settings = settings
        self.channels_dir = Path(settings["paths"].get("channels_dir", "channels"))
        self.channels_dir.mkdir(parents=True, exist_ok=True)

    # ── Kanal-Verwaltung ────────────────────────────────────────

    def list_channels(self) -> list[dict]:
        """Gibt alle konfigurierten Kanäle zurück."""
        channels = []
        for path in sorted(self.channels_dir.iterdir()):
            if path.is_dir():
                cfg_file = path / "channel_config.json"
                if cfg_file.exists():
                    try:
                        with open(cfg_file, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                        cfg["_folder"] = path.name
                        cfg["_path"] = str(path)
                        cfg["_has_token"] = (path / "token.json").exists()
                        cfg["_has_secret"] = (path / "youtube_client_secret.json").exists()
                        channels.append(cfg)
                    except Exception as e:
                        logger.warning(f"Kanal '{path.name}' konnte nicht geladen werden: {e}")
        return channels

    def get_channel(self, channel_id: str) -> dict | None:
        """Lädt einen Kanal anhand seiner ID (Ordnername)."""
        cfg_file = self.channels_dir / channel_id / "channel_config.json"
        if not cfg_file.exists():
            logger.error(f"Kanal '{channel_id}' nicht gefunden in {self.channels_dir}")
            return None
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["_folder"] = channel_id
        cfg["_path"] = str(self.channels_dir / channel_id)
        return cfg

    def create_channel(self, channel_id: str, name: str, niche: str = "storytelling",
                       language: str = "de", privacy: str = "private",
                       content_type: str = "story", ads_mode: str = "script") -> Path:
        """Erstellt einen neuen Kanal-Ordner mit Standard-Config."""
        channel_dir = self.channels_dir / channel_id
        channel_dir.mkdir(parents=True, exist_ok=True)

        # Standard-Werte je nach Content-Typ
        type_defaults = {
            "story":  {"style": "storytelling_engaging", "duration": 10, "category": "27",
                       "tags": ["Geschichte", "Storytelling", "Doku", "Fakten"],
                       "topics": ["Historische Ereignisse", "Faszinierende Biographien",
                                  "Ungeklärte Mysterien", "Weltgeschichte"]},
            "ads":    {"style": "storytelling_engaging", "duration": 1,  "category": "26",
                       "tags": ["Produkt", "Review", "Empfehlung"],
                       "topics": []},
            "kids":   {"style": "storytelling_engaging", "duration": 5,  "category": "20",
                       "tags": ["Kinder", "Bildung", "Lernen", "Spaß"],
                       "topics": ["Tiere", "Zahlen lernen", "Farben", "Dinosaurier"]},
            "reddit": {"style": "storytelling_engaging", "duration": 8,  "category": "24",
                       "tags": ["Reddit", "Stories", "Drama", "AITA"],
                       "topics": ["Reddit AITA", "Reddit Stories", "Lustige Reddit Posts"]},
        }
        d = type_defaults.get(content_type, type_defaults["story"])

        config = {
            "id": channel_id,
            "name": name,
            "platform": "youtube",
            "niche": niche,
            "content_type": content_type,   # story | ads | kids | reddit
            "ads_mode": ads_mode,           # script | ai_runway  (nur bei content_type=ads)
            "language": language,
            "active": True,
            "upload": {
                "default_privacy": privacy,
                "default_category": d["category"],
                "made_for_kids": content_type == "kids",
                "notify_subscribers": True,
                "schedule_delay_hours": 0
            },
            "script": {
                "target_duration_minutes": d["duration"],
                "style": d["style"],
                "language": language
            },
            "voiceover": {
                "provider": "fish_audio",
                "fish_voice_id": "54a5170264694bfc8e9ad98df7bd89c3"
            },
            "topics": d["topics"],
            "default_tags": d["tags"],
            "product": {
                "_info": "Nur bei content_type=ads + ads_mode=ai_runway relevant",
                "name": "",
                "description": "",
                "image_path": ""
            },
            "branding": {
                "outro_text": f"Abonniere {name}!",
                "watermark": False
            }
        }

        cfg_file = channel_dir / "channel_config.json"
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # Platzhalter für Client Secret
        secret_placeholder = channel_dir / "youtube_client_secret.json"
        if not secret_placeholder.exists():
            placeholder = {
                "_ANLEITUNG": [
                    "1. Gehe zu console.cloud.google.com",
                    "2. Projekt auswählen → APIs & Dienste → Anmeldedaten",
                    "3. OAuth 2.0-Client-IDs → Desktop-App erstellen",
                    "4. JSON herunterladen und als 'youtube_client_secret.json' hier speichern",
                    "5. Ersetze diese Datei mit deiner echten Client-Secret-Datei"
                ],
                "installed": {
                    "client_id": "DEINE_CLIENT_ID.apps.googleusercontent.com",
                    "client_secret": "DEIN_CLIENT_SECRET",
                    "redirect_uris": ["http://localhost", "http://localhost:8080"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }
            with open(secret_placeholder, "w", encoding="utf-8") as f:
                json.dump(placeholder, f, ensure_ascii=False, indent=2)

        logger.info(f"Kanal erstellt: {channel_id} → {channel_dir}")
        print(f"\n✅ Kanal '{name}' erstellt in: {channel_dir}")
        print(f"   → Ersetze nun 'youtube_client_secret.json' mit deiner OAuth-Datei von Google Console\n")
        return channel_dir

    def build_settings_for_channel(self, channel_id: str) -> dict:
        """
        Erstellt ein vollständiges Settings-Dict für einen Kanal,
        indem es die globalen Settings mit den Kanal-Settings überschreibt.
        """
        import copy
        settings = copy.deepcopy(self.settings)
        channel_cfg = self.get_channel(channel_id)
        if not channel_cfg:
            raise ValueError(f"Kanal '{channel_id}' nicht gefunden")

        channel_path = Path(channel_cfg["_path"])

        # Kanal-spezifische Überschreibungen
        settings["channel"]["niche"] = channel_cfg.get("niche", "storytelling")
        settings["channel"]["content_type"] = channel_cfg.get("content_type", "story")
        settings["channel"]["ads_mode"] = channel_cfg.get("ads_mode", "script")
        settings["channel"]["product"] = channel_cfg.get("product", {})
        settings["channel"]["language"] = channel_cfg.get("language", "de")
        settings["channel"]["default_privacy"] = channel_cfg["upload"].get("default_privacy", "private")
        settings["channel"]["default_category"] = channel_cfg["upload"].get("default_category", "27")
        settings["channel"]["default_tags"] = channel_cfg.get("default_tags", [])
        settings["channel"]["made_for_kids"] = channel_cfg["upload"].get("made_for_kids", False)

        settings["script"].update(channel_cfg.get("script", {}))
        settings["research"]["topics"] = channel_cfg.get("topics", settings["research"]["topics"])

        # Voiceover-Stimme pro Kanal
        if "voiceover" in channel_cfg:
            vo_cfg = channel_cfg["voiceover"]
            if "provider" in vo_cfg:
                settings["voiceover"]["provider"] = vo_cfg["provider"]
            if "fish_voice_id" in vo_cfg:
                settings["voiceover"]["fish_audio"]["voice_id"] = vo_cfg["fish_voice_id"]

        # Upload: Kanal-spezifische OAuth-Dateien
        secret_file = channel_path / "youtube_client_secret.json"
        token_file = channel_path / "token.json"
        settings["upload"]["client_secret_file"] = str(secret_file)
        settings["upload"]["token_file"] = str(token_file)

        # Output-Verzeichnis pro Kanal
        settings["paths"]["output_dir"] = str(channel_path / "output")
        settings["paths"]["logs_dir"] = str(channel_path / "logs")
        settings["paths"]["temp_dir"] = str(channel_path / "output" / "temp")

        return settings

    def print_status(self):
        """Zeigt den Status aller Kanäle in der Konsole."""
        channels = self.list_channels()
        print("\n" + "=" * 55)
        print("  YOUTUBE AUTOMATION – KANAL ÜBERSICHT")
        print("=" * 55)
        if not channels:
            print("  Keine Kanäle konfiguriert.")
            print("  Führe aus: python channel_manager.py --create")
        for ch in channels:
            status = "✅" if ch["_has_token"] else ("⚠️ " if ch["_has_secret"] else "❌")
            aktiv = "AKTIV" if ch.get("active", True) else "INAKTIV"
            print(f"\n  {status} {ch.get('name', ch['_folder'])} [{ch['_folder']}]")
            print(f"     Plattform : {ch.get('platform', 'youtube').upper()}")
            print(f"     Sprache   : {ch.get('language', 'de').upper()}")
            print(f"     Status    : {aktiv}")
            print(f"     Secret    : {'✓' if ch['_has_secret'] else '✗ Fehlt!'}")
            print(f"     Token     : {'✓ Eingeloggt' if ch['_has_token'] else '✗ Noch nicht verbunden'}")
        print("\n" + "=" * 55 + "\n")


# ── CLI-Interface ────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="YouTube Automation – Kanal-Manager")
    parser.add_argument("--list", action="store_true", help="Alle Kanäle anzeigen")
    parser.add_argument("--create", action="store_true", help="Neuen Kanal erstellen")
    parser.add_argument("--id", type=str, help="Kanal-ID (Ordnername, z.B. 'kanal1')")
    parser.add_argument("--name", type=str, help="Kanal-Anzeigename")
    parser.add_argument("--niche", type=str, default="finance", help="Themenbereich")
    parser.add_argument("--language", type=str, default="de", help="Sprache (de/en)")
    parser.add_argument("--config", type=str, default="config/settings.json")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        settings = json.load(f)

    manager = ChannelManager(settings)

    if args.list:
        manager.print_status()
    elif args.create:
        if not args.id or not args.name:
            print("❌ Bitte --id und --name angeben!")
            print("   Beispiel: python channel_manager.py --create --id kanal1 --name 'Mein Trading Kanal'")
            sys.exit(1)
        manager.create_channel(args.id, args.name, args.niche, args.language)
    else:
        manager.print_status()
        print("Befehle:")
        print("  --list                          Alle Kanäle anzeigen")
        print("  --create --id ID --name 'NAME'  Neuen Kanal erstellen")
