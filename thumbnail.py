#!/usr/bin/env python3
"""
ThumbnailGenerator – Erstellt professionelle YouTube-Thumbnails.
Nutzt Pillow für Storytelling-Design mit Gradient-Hintergrund.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger("thumbnail")

STORYTELLING_THEMES = {
    "mystery": {  # Geheimnisvoll – History/Crime/Thriller
        "bg_from": (10, 5, 20),
        "bg_to": (25, 10, 50),
        "accent": (140, 80, 255),
        "text": (255, 255, 255),
        "highlight": (180, 120, 255),
    },
    "drama": {  # Dramatisch – Biographien/Geschichte/Episch
        "bg_from": (30, 8, 5),
        "bg_to": (60, 15, 5),
        "accent": (220, 80, 30),
        "text": (255, 255, 255),
        "highlight": (255, 140, 60),
    },
    "comedy": {  # Bunt – Comedy/Brainrot/Fun
        "bg_from": (5, 10, 35),
        "bg_to": (15, 20, 70),
        "accent": (255, 200, 0),
        "text": (255, 255, 255),
        "highlight": (255, 230, 60),
    },
    "neutral": {  # Standard – Doku/Standard
        "bg_from": (10, 10, 30),
        "bg_to": (5, 20, 60),
        "accent": (99, 102, 241),
        "text": (255, 255, 255),
        "highlight": (165, 180, 252),
    },
}


class ThumbnailGenerator:
    def __init__(self, settings: dict):
        self.settings = settings
        self.cfg = settings.get("thumbnail", {})
        self.theme_name = "neutral"

    def _get_size(self, portrait: bool) -> tuple:
        if portrait:
            return (720, 1280)  # 9:16 für Shorts/Reels
        return tuple(self.cfg.get("resolution", [1280, 720]))  # 16:9 Standard

    def create(self, title: str, subtitle: str, output_path: str, portrait: bool = False) -> str:
        """Erstellt ein Thumbnail – automatisch 16:9 oder 9:16 je nach Format."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fmt = "9:16 (Short)" if portrait else "16:9"
        logger.info(f"  Thumbnail-Format: {fmt}")

        try:
            from PIL import Image, ImageDraw, ImageFont
            return self._create_with_pillow(title, subtitle, output_path, portrait,
                                            Image, ImageDraw, ImageFont)
        except ImportError:
            logger.warning("Pillow nicht installiert. Erstelle einfaches Thumbnail...")
            return self._create_placeholder(title, output_path, portrait)

    def _create_with_pillow(self, title: str, subtitle: str, output_path: str,
                             portrait: bool, Image, ImageDraw, ImageFont) -> str:
        """Erstellt professionelles Thumbnail mit Pillow."""
        theme = STORYTELLING_THEMES.get(self._detect_theme(title), STORYTELLING_THEMES["neutral"])
        size = self._get_size(portrait)
        w, h = size

        # Basis-Image mit Gradient
        img = Image.new("RGB", size, theme["bg_from"])
        draw = ImageDraw.Draw(img)

        # Gradient-Hintergrund
        self._draw_gradient(draw, w, h, theme["bg_from"], theme["bg_to"])

        # Dekorative Linien
        self._draw_chart_decoration(draw, w, h, theme["accent"])

        # Akzent-Linie oben
        draw.rectangle([(0, 0), (w, 8)], fill=theme["accent"])
        draw.rectangle([(0, h - 8), (w, h)], fill=theme["accent"])

        # Titel-Text – bei Portrait etwas kleinere Schrift wegen schmalerer Breite
        title_clean = self._prepare_title(title)
        font_size_title = self.cfg.get("font_size_title", 72) if not portrait else 58
        font_size_sub = self.cfg.get("font_size_subtitle", 40) if not portrait else 32

        try:
            # Versuche System-Font zu laden
            font_title = self._get_font(font_size_title, bold=True)
            font_sub = self._get_font(font_size_sub, bold=False)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        # Text-Schatten für bessere Lesbarkeit
        shadow_offset = 3

        # Subtitle oben (kleiner, farbiger Akzent-Text)
        if subtitle:
            sub_clean = subtitle.upper()[:30]
            sub_x = 60
            sub_y = 40
            # Hintergrund-Box für Subtitle
            try:
                sub_bbox = draw.textbbox((sub_x, sub_y), sub_clean, font=font_sub)
                box_padding = 10
                draw.rectangle(
                    [sub_bbox[0] - box_padding, sub_bbox[1] - box_padding // 2,
                     sub_bbox[2] + box_padding, sub_bbox[3] + box_padding // 2],
                    fill=theme["accent"]
                )
                draw.text((sub_x, sub_y), sub_clean, fill=(0, 0, 0), font=font_sub)
            except Exception:
                draw.text((sub_x, sub_y), sub_clean, fill=theme["highlight"], font=font_sub)

        # Haupt-Titel (zentriert, mit Zeilenumbruch)
        lines = self._wrap_text(title_clean, max_chars_per_line=22)
        total_text_height = len(lines) * (font_size_title + 10)
        start_y = (h - total_text_height) // 2 + 30

        for i, line in enumerate(lines[:3]):  # Max 3 Zeilen
            y = start_y + i * (font_size_title + 10)
            x = 60

            # Schatten
            draw.text((x + shadow_offset, y + shadow_offset), line,
                      fill=(0, 0, 0), font=font_title)
            # Haupt-Text
            draw.text((x, y), line, fill=theme["text"], font=font_title)

        # Untere Info-Leiste
        footer_text = "CONTENTSTUDIO PRO"
        draw.rectangle([(0, h - 60), (w, h - 8)], fill=(0, 0, 0, 180))
        try:
            draw.text((60, h - 50), footer_text, fill=theme["highlight"],
                      font=self._get_font(30, bold=True))
        except Exception:
            pass

        # Speichern
        img.save(output_path, "JPEG", quality=95)
        size_kb = os.path.getsize(output_path) / 1024
        logger.info(f"Thumbnail erstellt: {output_path} ({size_kb:.0f} KB)")
        return output_path

    def _draw_gradient(self, draw, w, h, color_from, color_to):
        """Zeichnet einen vertikalen Gradient."""
        for y in range(h):
            ratio = y / h
            r = int(color_from[0] + (color_to[0] - color_from[0]) * ratio)
            g = int(color_from[1] + (color_to[1] - color_from[1]) * ratio)
            b = int(color_from[2] + (color_to[2] - color_from[2]) * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

    def _draw_chart_decoration(self, draw, w, h, accent_color):
        """Zeichnet dekorative Chart-ähnliche Linien."""
        import random
        random.seed(42)  # Konsistente Optik

        # Simulierter Chart im Hintergrund (sehr transparent/subtil)
        points = [(0, h * 0.7)]
        step = w // 20
        for i in range(1, 21):
            x = i * step
            y = h * 0.7 + random.randint(-80, 80)
            y = max(h * 0.3, min(h * 0.9, y))
            points.append((x, y))

        # Dünne Chart-Linie
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=(*accent_color[:3], 40), width=2)

    def _get_font(self, size: int, bold: bool = False):
        """Lädt einen System-Font."""
        from PIL import ImageFont
        import sys

        font_paths = []
        if sys.platform == "win32":
            font_dir = "C:/Windows/Fonts/"
            if bold:
                font_paths = [
                    font_dir + "arialbd.ttf",
                    font_dir + "calibrib.ttf",
                    font_dir + "verdanab.ttf",
                ]
            else:
                font_paths = [
                    font_dir + "arial.ttf",
                    font_dir + "calibri.ttf",
                    font_dir + "verdana.ttf",
                ]
        elif sys.platform == "darwin":
            font_paths = ["/System/Library/Fonts/Helvetica.ttc"]
        else:
            font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]

        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

        return ImageFont.load_default()

    def _prepare_title(self, title: str) -> str:
        """Bereinigt Titel für Thumbnail."""
        import re
        # Emojis entfernen
        title = re.sub(r'[^\w\s\-.,!?:|€$%&()]', '', title)
        # Pipe und Bindestrich als Trennzeichen behandeln
        title = title.replace("|", "\n").replace(" - ", "\n")
        return title.strip()

    def _wrap_text(self, text: str, max_chars_per_line: int = 22) -> list[str]:
        """Bricht Text in Zeilen um."""
        if "\n" in text:
            return [line.strip() for line in text.split("\n") if line.strip()]

        words = text.split()
        lines = []
        current = ""

        for word in words:
            if len(current) + len(word) + 1 <= max_chars_per_line:
                current += (word + " ") if current else word
            else:
                if current:
                    lines.append(current.strip())
                current = word

        if current:
            lines.append(current.strip())

        return lines

    def _detect_theme(self, title: str) -> str:
        """Erkennt das passende Theme aus dem Titel."""
        title_lower = title.lower()
        if any(w in title_lower for w in ["geheimnis", "mord", "verbrechen", "verschwörung",
                                           "thriller", "horror", "mystery", "dark", "crime"]):
            return "mystery"
        if any(w in title_lower for w in ["lustig", "witzig", "comedy", "absurd",
                                           "brainrot", "fail", "challenge", "fun"]):
            return "comedy"
        if any(w in title_lower for w in ["biografie", "geschichte", "krieg", "held",
                                           "kaiser", "könig", "drama", "episch", "legende"]):
            return "drama"
        return "neutral"

    def _create_placeholder(self, title: str, output_path: str, portrait: bool = False) -> str:
        """Fallback: Erstellt ein einfaches schwarzes Thumbnail via ffmpeg."""
        size_str = "720x1280" if portrait else "1280x720"
        try:
            import subprocess
            tmp = output_path.replace(".jpg", "_temp.jpg")
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x0A0A1E:size={size_str}:rate=1",
                "-frames:v", "1", tmp,
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
            import shutil
            shutil.move(tmp, output_path)
            logger.info(f"Placeholder-Thumbnail erstellt: {output_path} ({size_str})")
        except Exception as e:
            logger.warning(f"Thumbnail-Erstellung fehlgeschlagen: {e}")
            Path(output_path).touch()

        return output_path
