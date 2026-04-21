#!/usr/bin/env python3
"""
CharacterCreator – Erstellt AI-Charakter-Videos für TikTok.
Fish Audio liefert die Stimme, Runway animiert den Charakter.

Workflow:
  1. Charakter-Profil laden (Name, Aussehen, Stil)
  2. Fish Audio → MP3-Voiceover (bereits in voiceover.py)
  3. Runway image-to-video → Charakter spricht/tanzt zum Audio
  4. Audio + Video zusammenführen (MoviePy)
"""

import os
import json
import time
import base64
import logging
import requests
from pathlib import Path

logger = logging.getLogger("character_creator")

CHARACTERS_FILE = Path(__file__).parent / "config" / "characters.json"
CHARACTERS_IMG_DIR = Path(__file__).parent / "config" / "character_images"
RUNWAY_API_BASE = "https://api.dev.runwayml.com/v1"
RUNWAY_MODEL    = "gen4_turbo"
POLL_INTERVAL   = 5
POLL_TIMEOUT    = 360


# ── Charakter-Bibliothek ─────────────────────────────────────────

def load_characters() -> list[dict]:
    """Lädt alle gespeicherten Charakter-Profile."""
    if CHARACTERS_FILE.exists():
        with open(CHARACTERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_characters(characters: list[dict]):
    CHARACTERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHARACTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)


def get_character(character_id: str) -> dict | None:
    return next((c for c in load_characters() if c["id"] == character_id), None)


def add_character(character: dict):
    chars = load_characters()
    chars = [c for c in chars if c["id"] != character["id"]]  # update if exists
    chars.append(character)
    save_characters(chars)
    logger.info(f"Charakter gespeichert: {character['name']}")


# ── CharacterCreator ─────────────────────────────────────────────

class CharacterCreator:
    def __init__(self, settings: dict):
        self.settings = settings
        self.api_key = settings.get("api_keys", {}).get("runway", "")
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY fehlt in .env")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }
        CHARACTERS_IMG_DIR.mkdir(parents=True, exist_ok=True)

    def create_video(
        self,
        character_id: str,
        audio_path: str,
        output_path: str,
        duration: int = 10,
        topic: str = "",
    ) -> str:
        """
        Erstellt ein Charakter-Video: Charakter spricht/bewegt sich zum Audio.
        audio_path: Fish Audio MP3
        output_path: finales MP4 (Audio bereits eingebettet)
        """
        character = get_character(character_id)
        if not character:
            raise ValueError(f"Charakter '{character_id}' nicht gefunden")

        logger.info(f"🎭 Charakter-Video: {character['name']} ({duration}s)")

        # Runway-Video generieren (Charakter wird animiert)
        raw_video = output_path.replace(".mp4", "_raw.mp4")
        self._generate_runway_video(character, topic, raw_video, duration)

        # Audio einbetten (Fish Audio + Runway-Video zusammenführen)
        self._embed_audio(raw_video, audio_path, output_path)

        # Temp-Datei aufräumen
        try:
            os.remove(raw_video)
        except Exception:
            pass

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"✅ Charakter-Video fertig: {output_path} ({size_mb:.1f} MB)")
        return output_path

    def _generate_runway_video(self, character: dict, topic: str,
                                output_path: str, duration: int):
        """Sendet Charakter + Prompt an Runway und lädt das Video herunter."""
        prompt = self._build_character_prompt(character, topic)
        logger.info(f"   Prompt: {prompt[:80]}...")

        img_path = character.get("image_path", "")
        if img_path and Path(img_path).exists():
            # Image-to-Video: Charakter-Bild als Basis
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = Path(img_path).suffix.lower().replace(".", "") or "jpeg"
            payload = {
                "model": RUNWAY_MODEL,
                "promptImage": f"data:image/{ext};base64,{img_b64}",
                "promptText": prompt,
                "duration": min(duration, 10),
                "ratio": "720:1280",  # TikTok 9:16
            }
            endpoint = "image_to_video"
        else:
            # Text-to-Video: Nur Prompt, kein Basisbild
            payload = {
                "model": RUNWAY_MODEL,
                "promptText": prompt,
                "duration": min(duration, 10),
                "ratio": "720:1280",
            }
            endpoint = "text_to_video"

        task_id = self._start_task(endpoint, payload)
        self._wait_and_download(task_id, output_path)

    def _build_character_prompt(self, character: dict, topic: str) -> str:
        """Baut einen Runway-Prompt für den Charakter."""
        base = character.get("base_prompt", "")
        movement = character.get("movement_style", "talking")
        style = character.get("visual_style", "")

        movement_desc = {
            "talking": "speaking naturally, subtle lip movements, slight head nods, expressive eyes",
            "dancing": "dancing energetically, full body movement, rhythmic bouncing, playful gestures",
            "both":    "talking while slightly dancing, rhythmic body movement, expressive mouth, gestures",
        }.get(movement, "talking naturally, expressive")

        context = f", discussing {topic}" if topic else ""

        return (
            f"{base}, {movement_desc}{context}. "
            f"{style} "
            f"Vertical TikTok format, centered subject, clean background, "
            f"cinematic lighting, high detail, smooth animation, no text."
        ).strip()

    # ── Runway API ───────────────────────────────────────────────

    def _start_task(self, endpoint: str, payload: dict) -> str:
        url = f"{RUNWAY_API_BASE}/{endpoint}"
        r = requests.post(url, headers=self.headers, json=payload, timeout=30)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Runway {r.status_code}: {r.text[:300]}")
        data = r.json()
        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            raise RuntimeError(f"Keine Task-ID: {data}")
        logger.info(f"   Task: {task_id}")
        return task_id

    def _wait_and_download(self, task_id: str, output_path: str) -> str:
        url = f"{RUNWAY_API_BASE}/tasks/{task_id}"
        elapsed = 0
        while elapsed < POLL_TIMEOUT:
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            r = requests.get(url, headers=self.headers, timeout=15)
            data = r.json()
            status = data.get("status", "")
            logger.info(f"   {status} ({elapsed}s)")

            if status == "SUCCEEDED":
                video_url = (data.get("output") or [None])[0]
                if not video_url:
                    raise RuntimeError("Kein Output-URL")
                return self._download(video_url, output_path)

            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Runway fehlgeschlagen: {data.get('failure', status)}")

        raise TimeoutError(f"Timeout nach {POLL_TIMEOUT}s")

    def _download(self, url: str, output_path: str) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return output_path

    # ── Audio einbetten ──────────────────────────────────────────

    def _embed_audio(self, video_path: str, audio_path: str, output_path: str):
        """Ersetzt den Audio-Track des Runway-Videos mit dem Fish-Audio."""
        import subprocess

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg Audio-Merge Fehler: {result.stderr[:200]}")
        logger.info(f"   Audio eingebettet: {output_path}")

    # ── Charakter generieren (Basisbild via Runway) ──────────────

    def generate_character_image(self, character: dict, output_path: str) -> str:
        """
        Generiert ein Basis-Charakterbild via Runway Text-to-Image.
        Wird als Referenz für spätere Videos genutzt (konsistentes Aussehen).
        """
        prompt = (
            f"{character.get('base_prompt', '')}, "
            f"portrait, centered, plain white background, "
            f"high detail, professional character design, no text"
        )

        payload = {
            "model": "gen4_image",
            "promptText": prompt,
            "ratio": "1:1",
        }

        logger.info(f"🎨 Generiere Charakterbild: {character['name']}")
        task_id = self._start_task("text_to_image", payload)
        self._wait_and_download(task_id, output_path)

        logger.info(f"   Bild gespeichert: {output_path}")
        return output_path


# ── Starter-Charaktere ───────────────────────────────────────────

STARTER_CHARACTERS = [
    {
        "id": "tanzkatze",
        "name": "Tanzkatze",
        "emoji": "🐱",
        "description": "Eine verspielte, animierte Katze die zur Musik tanzt und Fakten erklärt.",
        "base_prompt": (
            "cute animated cat character with big expressive eyes, colorful orange and white fur, "
            "wearing a tiny bow tie, standing upright like a human, cartoon-realistic style"
        ),
        "visual_style": "Vibrant colors, soft lighting, cartoon-realistic 3D render.",
        "movement_style": "both",
        "image_path": "",
        "voice_id": "54a5170264694bfc8e9ad98df7bd89c3",
        "created": "2026-04-21",
        "tags": ["cat", "dancing", "cute", "fun"],
    },
    {
        "id": "skybot",
        "name": "SkyBot",
        "emoji": "🤖",
        "description": "Ein futuristischer KI-Roboter der Wissen vermittelt – seriös aber sympathisch.",
        "base_prompt": (
            "sleek futuristic humanoid robot with glowing blue eyes and silver metallic body, "
            "holographic face display showing expressive emotions, high-tech design"
        ),
        "visual_style": "Sci-fi aesthetic, blue neon accents, dark tech background.",
        "movement_style": "talking",
        "image_path": "",
        "voice_id": "54a5170264694bfc8e9ad98df7bd89c3",
        "created": "2026-04-21",
        "tags": ["robot", "tech", "serious", "educational"],
    },
    {
        "id": "luna_mystic",
        "name": "Luna",
        "emoji": "🌙",
        "description": "Mystische weibliche Charakter-Avatar für Geschichte und Mystery-Content.",
        "base_prompt": (
            "beautiful mystical female character with flowing silver hair and glowing violet eyes, "
            "ethereal magical appearance, fantasy style, slight smile, elegant"
        ),
        "visual_style": "Ethereal purple and gold tones, magical particle effects, cinematic.",
        "movement_style": "talking",
        "image_path": "",
        "voice_id": "54a5170264694bfc8e9ad98df7bd89c3",
        "created": "2026-04-21",
        "tags": ["mystery", "history", "female", "magical"],
    },
    {
        "id": "brainrot_bunny",
        "name": "BrainrotBunny",
        "emoji": "🐰",
        "description": "Chaotischer, überdrehter Hase für Brainrot- und Comedy-Content.",
        "base_prompt": (
            "chaotic cartoon bunny with wild multicolored fur, enormous googly eyes, "
            "manic grin, holding random objects, hyper-energetic pose, meme-worthy design"
        ),
        "visual_style": "Over-saturated colors, chaotic background, energetic comic style.",
        "movement_style": "dancing",
        "image_path": "",
        "voice_id": "54a5170264694bfc8e9ad98df7bd89c3",
        "created": "2026-04-21",
        "tags": ["comedy", "brainrot", "chaotic", "meme"],
    },
    {
        "id": "pro_human",
        "name": "Alex (Human Avatar)",
        "emoji": "🧑",
        "description": "Realistischer menschlicher Avatar für seriösen oder Produkt-Content.",
        "base_prompt": (
            "photorealistic young adult with friendly smile, modern casual clothing, "
            "natural skin tone, clean professional appearance, neutral background"
        ),
        "visual_style": "Photorealistic, studio lighting, natural colors.",
        "movement_style": "talking",
        "image_path": "",
        "voice_id": "54a5170264694bfc8e9ad98df7bd89c3",
        "created": "2026-04-21",
        "tags": ["human", "realistic", "professional", "ads"],
    },
]


def init_starter_characters():
    """Erstellt die Starter-Charaktere wenn noch keine existieren."""
    if not CHARACTERS_FILE.exists():
        save_characters(STARTER_CHARACTERS)
        logger.info(f"✅ {len(STARTER_CHARACTERS)} Starter-Charaktere erstellt")


# ── CLI ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Charakter Creator")
    parser.add_argument("--list", action="store_true", help="Alle Charaktere anzeigen")
    parser.add_argument("--init", action="store_true", help="Starter-Charaktere erstellen")
    parser.add_argument("--character", type=str, help="Charakter-ID")
    parser.add_argument("--audio", type=str, help="Pfad zum Audio (MP3)")
    parser.add_argument("--output", type=str, default="output/character_video.mp4")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--topic", type=str, default="")
    parser.add_argument("--config", default="config/settings.json")
    args = parser.parse_args()

    if args.init:
        init_starter_characters()
        print("✅ Starter-Charaktere erstellt")
    elif args.list:
        for c in load_characters():
            print(f"  {c['emoji']} [{c['id']}] {c['name']} — {c['description'][:60]}")
    elif args.character and args.audio:
        from main import load_settings
        settings = load_settings(args.config)
        creator = CharacterCreator(settings)
        path = creator.create_video(args.character, args.audio, args.output,
                                    args.duration, args.topic)
        print(f"\n✅ Video: {path}")
    else:
        parser.print_help()
