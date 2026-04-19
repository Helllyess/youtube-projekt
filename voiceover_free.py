#!/usr/bin/env python3
"""
voiceover_free.py – Kostenlose TTS-Optionen.
Nutzt gTTS (Google Text-to-Speech) ohne API-Key.
Fallback wenn Fish Audio / OpenAI nicht verfügbar.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger("voiceover_free")


class FreeVoiceover:
    def __init__(self, settings: dict):
        self.settings = settings
        cfg = settings.get("voiceover", {}).get("free", {})
        self.language = cfg.get("language", "de")
        self.slow = cfg.get("slow", False)
        self.provider = cfg.get("provider", "gtts")

    def create(self, text: str, output_path: str) -> str:
        """Erstellt Voiceover mit kostenlosem TTS."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if self.provider == "gtts":
            return self._gtts(text, output_path)
        elif self.provider == "pyttsx3":
            return self._pyttsx3(text, output_path)
        else:
            return self._gtts(text, output_path)

    def _gtts(self, text: str, output_path: str) -> str:
        """Google Text-to-Speech (gratis, benötigt Internet)."""
        try:
            from gtts import gTTS

            # Text aufteilen (gTTS-Limit ~5000 Zeichen)
            chunks = self._split_text(text, max_chars=4500)

            if len(chunks) == 1:
                tts = gTTS(text=text, lang=self.language, slow=self.slow)
                tts.save(output_path)
            else:
                chunk_files = []
                for i, chunk in enumerate(chunks):
                    chunk_path = output_path.replace(".mp3", f"_chunk{i}.mp3")
                    tts = gTTS(text=chunk, lang=self.language, slow=self.slow)
                    tts.save(chunk_path)
                    chunk_files.append(chunk_path)

                self._merge_audio(chunk_files, output_path)

            logger.info(f"gTTS Voiceover erstellt: {output_path}")
            return output_path

        except ImportError:
            logger.error("gTTS nicht installiert. Bitte: pip install gtts")
            raise ImportError("Bitte installiere gTTS: pip install gtts")
        except Exception as e:
            logger.error(f"gTTS Fehler: {e}")
            raise

    def _pyttsx3(self, text: str, output_path: str) -> str:
        """Offline TTS mit pyttsx3 (kein Internet nötig)."""
        try:
            import pyttsx3

            engine = pyttsx3.init()
            voices = engine.getProperty("voices")

            # Deutschen Voice suchen
            for voice in voices:
                if "german" in voice.name.lower() or "de_" in voice.id.lower():
                    engine.setProperty("voice", voice.id)
                    break

            engine.setProperty("rate", 175)  # Sprechgeschwindigkeit
            engine.setProperty("volume", 0.9)

            engine.save_to_file(text, output_path)
            engine.runAndWait()

            logger.info(f"pyttsx3 Voiceover erstellt: {output_path}")
            return output_path

        except ImportError:
            logger.error("pyttsx3 nicht installiert. Bitte: pip install pyttsx3")
            raise ImportError("Bitte installiere pyttsx3: pip install pyttsx3")

    def _split_text(self, text: str, max_chars: int = 4500) -> list[str]:
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 2 <= max_chars:
                current += para + "\n\n"
            else:
                if current:
                    chunks.append(current.strip())
                current = para + "\n\n"

        if current:
            chunks.append(current.strip())

        return chunks

    def _merge_audio(self, files: list[str], output: str):
        """Zusammenfügen mehrerer Audio-Chunks."""
        try:
            from pydub import AudioSegment
            combined = AudioSegment.empty()
            for f in files:
                combined += AudioSegment.from_mp3(f)
            combined.export(output, format="mp3", bitrate="128k")
            for f in files:
                try:
                    os.remove(f)
                except Exception:
                    pass
        except ImportError:
            import shutil
            shutil.copy(files[0], output)
            logger.warning("pydub nicht verfügbar – nur erster Chunk verwendet")
