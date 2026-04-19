#!/usr/bin/env python3
"""
Voiceover – Dispatcher für alle TTS-Anbieter.
Wählt automatisch den konfigurierten Provider aus.
"""

import logging
from pathlib import Path

logger = logging.getLogger("voiceover")


class Voiceover:
    def __init__(self, settings: dict):
        self.settings = settings
        self.provider = settings.get("voiceover", {}).get("provider", "fish_audio")
        logger.info(f"Voiceover-Provider: {self.provider}")

    def create(self, text: str, output_path: str) -> str:
        """Erstellt ein Voiceover-Audio aus dem gegebenen Text."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if self.provider == "fish_audio":
            from voiceover_fish import FishAudioVoiceover
            tts = FishAudioVoiceover(self.settings)
        elif self.provider == "openai":
            tts = self._get_openai_tts()
        else:
            from voiceover_free import FreeVoiceover
            tts = FreeVoiceover(self.settings)

        result = tts.create(text, output_path)
        logger.info(f"Voiceover erstellt: {output_path} ({self.provider})")
        return result

    def _get_openai_tts(self):
        """OpenAI TTS als integrierter Provider."""
        from openai import OpenAI

        settings = self.settings

        class OpenAITTS:
            def __init__(self):
                self.client = OpenAI(api_key=settings["api_keys"]["openai"])

            def create(self, text: str, output_path: str) -> str:
                # OpenAI hat ein 4096-Zeichen-Limit pro Request → Text splitten
                chunks = _split_text(text, max_chars=4000)
                audio_chunks = []

                for i, chunk in enumerate(chunks):
                    response = self.client.audio.speech.create(
                        model="tts-1-hd",
                        voice="onyx",
                        input=chunk,
                        response_format="mp3",
                    )
                    chunk_path = output_path.replace(".mp3", f"_chunk{i}.mp3")
                    response.stream_to_file(chunk_path)
                    audio_chunks.append(chunk_path)

                if len(audio_chunks) == 1:
                    import shutil
                    shutil.move(audio_chunks[0], output_path)
                else:
                    _merge_audio_files(audio_chunks, output_path)

                return output_path

        return OpenAITTS()


def _split_text(text: str, max_chars: int = 4000) -> list[str]:
    """Teilt langen Text in kleinere Chunks auf (an Satzgrenzen)."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    sentences = text.replace("! ", "!|").replace("? ", "?|").replace(". ", ".|").split("|")
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) < max_chars:
            current += sentence + " "
        else:
            if current:
                chunks.append(current.strip())
            current = sentence + " "

    if current:
        chunks.append(current.strip())

    return chunks


def _merge_audio_files(files: list[str], output: str):
    """Fügt mehrere MP3-Dateien zusammen."""
    try:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for f in files:
            combined += AudioSegment.from_mp3(f)
        combined.export(output, format="mp3", bitrate="128k")
        # Temp-Files löschen
        for f in files:
            import os
            try:
                os.remove(f)
            except Exception:
                pass
    except ImportError:
        # Fallback: erste Datei nutzen wenn pydub nicht verfügbar
        import shutil
        shutil.copy(files[0], output)
        logger.warning("pydub nicht installiert – nur erstes Audio-Chunk verwendet")
