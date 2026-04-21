#!/usr/bin/env python3
"""
AdsCreator – Erstellt professionelle Produkt-Ad-Videos mit Runway Gen-4 Turbo.
Unterstützt Image-to-Video (Produktfoto → Video) und Text-to-Video (nur Beschreibung).
Nano Banana wird integriert sobald die API-Waitlist durch ist.
"""

import os
import time
import json
import logging
import base64
import requests
from pathlib import Path

logger = logging.getLogger("ads_creator")

RUNWAY_API_BASE = "https://api.dev.runwayml.com/v1"
RUNWAY_MODEL    = "gen4_turbo"

# Wartezeit zwischen Status-Polls (Sekunden)
POLL_INTERVAL = 5
POLL_TIMEOUT  = 300  # 5 Minuten max


class AdsCreator:
    def __init__(self, settings: dict):
        self.settings = settings
        self.api_key = settings.get("api_keys", {}).get("runway", "")
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY fehlt in .env / settings")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }
        self.cfg = settings.get("ads", {})

    # ── Öffentliche API ──────────────────────────────────────────

    def create_from_image(
        self,
        image_path: str,
        product_name: str,
        product_description: str,
        output_path: str,
        duration: int = 5,
        portrait: bool = False,
    ) -> str:
        """
        Image-to-Video: Produktfoto → bewegtes Ad-Video.
        Beste Qualität, empfohlen wenn ein Produktbild vorhanden ist.
        """
        ratio = "720:1280" if portrait else "1280:720"
        prompt = self._build_ad_prompt(product_name, product_description, portrait)

        logger.info(f"🎬 Image-to-Video Ad: {product_name} ({ratio}, {duration}s)")

        image_b64 = self._encode_image(image_path)

        payload = {
            "model": RUNWAY_MODEL,
            "promptImage": f"data:image/jpeg;base64,{image_b64}",
            "promptText": prompt,
            "duration": duration,
            "ratio": ratio,
        }

        task_id = self._start_task("image_to_video", payload)
        return self._wait_and_download(task_id, output_path)

    def create_from_text(
        self,
        product_name: str,
        product_description: str,
        output_path: str,
        duration: int = 5,
        portrait: bool = False,
    ) -> str:
        """
        Text-to-Video: Nur Beschreibung → KI generiert das Video komplett.
        Kein Produktbild nötig.
        """
        ratio = "720:1280" if portrait else "1280:720"
        prompt = self._build_ad_prompt(product_name, product_description, portrait)

        logger.info(f"🎬 Text-to-Video Ad: {product_name} ({ratio}, {duration}s)")

        payload = {
            "model": RUNWAY_MODEL,
            "promptText": prompt,
            "duration": duration,
            "ratio": ratio,
        }

        task_id = self._start_task("text_to_video", payload)
        return self._wait_and_download(task_id, output_path)

    def create_batch(
        self,
        products: list[dict],
        output_dir: str,
        portrait: bool = False,
        duration: int = 5,
    ) -> list[dict]:
        """
        Erstellt mehrere Ad-Videos auf einmal.
        products: [{"name": "...", "description": "...", "image_path": "..." (optional)}, ...]
        Gibt Liste von {"product": name, "video_path": path, "status": ok/error} zurück.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        results = []

        for i, product in enumerate(products):
            name = product.get("name", f"Produkt {i+1}")
            desc = product.get("description", "")
            img  = product.get("image_path", "")
            out  = str(Path(output_dir) / f"ad_{i+1}_{self._safe_name(name)}.mp4")

            logger.info(f"\n[{i+1}/{len(products)}] {name}")
            try:
                if img and Path(img).exists():
                    video_path = self.create_from_image(img, name, desc, out, duration, portrait)
                else:
                    video_path = self.create_from_text(name, desc, out, duration, portrait)

                results.append({"product": name, "video_path": video_path, "status": "success"})
                logger.info(f"   ✅ Fertig: {video_path}")

            except Exception as e:
                logger.error(f"   ❌ Fehler: {e}")
                results.append({"product": name, "video_path": None, "status": "error", "error": str(e)})

            # Kurze Pause zwischen API-Calls
            if i < len(products) - 1:
                time.sleep(3)

        success = sum(1 for r in results if r["status"] == "success")
        logger.info(f"\n✅ Batch fertig: {success}/{len(products)} erfolgreich")
        return results

    # ── Runway API Internals ─────────────────────────────────────

    def _start_task(self, endpoint: str, payload: dict) -> str:
        """Startet einen Runway-Task und gibt die Task-ID zurück."""
        url = f"{RUNWAY_API_BASE}/{endpoint}"
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Runway API Fehler {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            raise RuntimeError(f"Keine Task-ID in Runway-Antwort: {data}")

        logger.info(f"   Task gestartet: {task_id}")
        return task_id

    def _wait_and_download(self, task_id: str, output_path: str) -> str:
        """Pollt den Task-Status und lädt das fertige Video herunter."""
        url = f"{RUNWAY_API_BASE}/tasks/{task_id}"
        elapsed = 0

        while elapsed < POLL_TIMEOUT:
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                raise RuntimeError(f"Status-Poll Fehler: {response.status_code}")

            data = response.json()
            status = data.get("status", "")
            progress = data.get("progress", 0)

            logger.info(f"   Status: {status} ({progress:.0%}) – {elapsed}s")

            if status == "SUCCEEDED":
                video_url = (data.get("output") or [None])[0]
                if not video_url:
                    raise RuntimeError("Runway: kein Output-URL trotz SUCCEEDED")
                return self._download_video(video_url, output_path)

            if status in ("FAILED", "CANCELLED"):
                error = data.get("failure") or data.get("error") or status
                raise RuntimeError(f"Runway Task fehlgeschlagen: {error}")

        raise TimeoutError(f"Runway Task nach {POLL_TIMEOUT}s noch nicht fertig: {task_id}")

    def _download_video(self, url: str, output_path: str) -> str:
        """Lädt das fertige Video von Runway herunter."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"   ⬇ Download: {url[:60]}...")

        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"   ✅ Video gespeichert: {output_path} ({size_mb:.1f} MB)")
        return output_path

    # ── Prompt-Builder ───────────────────────────────────────────

    def _build_ad_prompt(self, name: str, description: str, portrait: bool) -> str:
        """Baut einen professionellen Werbe-Prompt für Runway."""
        framing = "vertical TikTok-style close-up" if portrait else "cinematic wide product shot"
        return (
            f"Professional product advertisement for '{name}'. {description}. "
            f"{framing}, smooth camera movement, premium studio lighting, "
            f"photorealistic 4K quality, elegant brand aesthetic, "
            f"no text overlays, no people unless essential to product use."
        )

    # ── Hilfsfunktionen ──────────────────────────────────────────

    def _encode_image(self, path: str) -> str:
        """Kodiert ein Bild als Base64-String."""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _safe_name(self, name: str) -> str:
        """Dateiname-sichere Version eines Strings."""
        import re
        return re.sub(r'[^\w]', '_', name)[:30].strip("_")


# ── CLI ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Produkt-Ad Creator (Runway AI)")
    parser.add_argument("--name", required=True, help="Produktname")
    parser.add_argument("--description", required=True, help="Produktbeschreibung")
    parser.add_argument("--image", default=None, help="Pfad zum Produktbild (optional)")
    parser.add_argument("--output", default="output/ads/ad.mp4", help="Output-Pfad")
    parser.add_argument("--portrait", action="store_true", help="9:16 Format (TikTok/Reels)")
    parser.add_argument("--duration", type=int, default=5, choices=[5, 10], help="Videolänge in Sekunden")
    parser.add_argument("--config", default="config/settings.json")
    args = parser.parse_args()

    from main import load_settings
    settings = load_settings(args.config)

    creator = AdsCreator(settings)

    if args.image:
        path = creator.create_from_image(
            args.image, args.name, args.description, args.output, args.duration, args.portrait
        )
    else:
        path = creator.create_from_text(
            args.name, args.description, args.output, args.duration, args.portrait
        )

    print(f"\n✅ Ad-Video erstellt: {path}")
