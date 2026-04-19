#!/usr/bin/env python3
"""
voiceover_fish.py – Fish Audio TTS Integration.
Nutzt die Fish Audio API für hochwertige, natürliche Stimmen.
Docs: https://docs.fish.audio/
"""

import os
import io
import logging
import requests
from pathlib import Path

logger = logging.getLogger("voiceover_fish")

FISH_API_URL = "https://api.fish.audio/v1/tts"
MAX_CHARS_PER_REQUEST = 2000


class FishAudioVoiceover:
    def __init__(self, settings: dict):
        self.settings = settings
        cfg = settings.get("voiceover", {}).get("fish_audio", {})
        self.api_key = settings["api_keys"]["fish_audio"]
        self.voice_id = cfg.get("voice_id", "54a5170264694bfc8e9ad98df7bd89c3")
        self.format = cfg.get("format", "mp3")
        self.bitrate = cfg.get("bitrate", 128)
        self.speed = cfg.get("speed", 1.0)
        self.volume = cfg.get("volume", 1.0)

    def create(self, text: str, output_path: str) -> str:
        """Erstellt Voiceover via Fish Audio API."""
        logger.info(f"Fish Audio TTS: {len(text)} Zeichen → {output_path}")

        chunks = self._split_text(text)
        audio_parts = []

        for i, chunk in enumerate(chunks):
            logger.debug(f"  Chunk {i+1}/{len(chunks)}: {len(chunk)} Zeichen")
            audio_data = self._request_tts(chunk)
            audio_parts.append(audio_data)

        # Audio zusammenfügen
        combined = b"".join(audio_parts)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(combined)

        size_kb = os.path.getsize(output_path) / 1024
        logger.info(f"Fish Audio fertig: {output_path} ({size_kb:.1f} KB)")
        return output_path

    def _request_tts(self, text: str) -> bytes:
        """Sendet einen TTS-Request an die Fish Audio API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "reference_id": self.voice_id,
            "format": self.format,
            "mp3_bitrate": self.bitrate,
            "normalize": True,
            "latency": "normal",
        }

        response = requests.post(
            FISH_API_URL,
            json=payload,
            headers=headers,
            timeout=60,
        )

        if response.status_code != 200:
            logger.error(f"Fish Audio API Fehler {response.status_code}: {response.text}")
            response.raise_for_status()

        return response.content

    def _split_text(self, text: str, max_chars: int = MAX_CHARS_PER_REQUEST) -> list[str]:
        """Teilt Text an Satz-/Absatzgrenzen auf."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        # Erst an Absätzen trennen
        paragraphs = text.split("\n\n")
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 2 <= max_chars:
                current += para + "\n\n"
            else:
                if current:
                    chunks.append(current.strip())
                # Wenn Paragraph selbst zu lang → an Sätzen trennen
                if len(para) > max_chars:
                    sentences = para.replace("! ", "!|||").replace("? ", "?|||").replace(". ", ".|||").split("|||")
                    sub_current = ""
                    for s in sentences:
                        if len(sub_current) + len(s) < max_chars:
                            sub_current += s + " "
                        else:
                            if sub_current:
                                chunks.append(sub_current.strip())
                            sub_current = s + " "
                    if sub_current:
                        chunks.append(sub_current.strip())
                    current = ""
                else:
                    current = para + "\n\n"

        if current:
            chunks.append(current.strip())

        return [c for c in chunks if c.strip()]

    def list_voices(self) -> list:
        """Listet verfügbare Fish Audio Stimmen auf."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(
                "https://api.fish.audio/model",
                headers=headers,
                params={"page_size": 20, "sort_by": "score", "language": "de"},
                timeout=30,
            )
            if response.status_code == 200:
                return response.json().get("items", [])
        except Exception as e:
            logger.warning(f"Stimmen-Liste nicht abrufbar: {e}")
        return []
