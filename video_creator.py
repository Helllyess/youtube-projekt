#!/usr/bin/env python3
"""
VideoCreator – Erstellt YouTube-Videos aus Audio + Visuals.
Nutzt MoviePy für die Video-Komposition.
Format wird automatisch anhand der Audio-Dauer gewählt:
  < shorts_threshold Sekunden → 9:16 Portrait (Shorts/Reels)
  ≥ shorts_threshold Sekunden → 16:9 Landscape (normale Videos)
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger("video_creator")

# Unter diesem Wert → Shorts/Reels (9:16), darüber → normale Videos (16:9)
DEFAULT_SHORTS_THRESHOLD = 180  # 3 Minuten

RESOLUTION_LANDSCAPE = (1920, 1080)
RESOLUTION_PORTRAIT  = (1080, 1920)


class VideoCreator:
    def __init__(self, settings: dict):
        self.settings = settings
        self.cfg = settings.get("video", {})
        self.fps = self.cfg.get("fps", 30)
        self.bg_color = tuple(self.cfg.get("background_color", [10, 10, 20]))
        self.font_size = self.cfg.get("font_size", 60)
        self.output_format = self.cfg.get("output_format", "mp4")
        self.shorts_threshold = self.cfg.get("shorts_threshold_seconds", DEFAULT_SHORTS_THRESHOLD)

    def _pick_resolution(self, duration_seconds: float) -> tuple:
        """Wählt automatisch das Format anhand der Videolänge."""
        if duration_seconds < self.shorts_threshold:
            logger.info(f"  Format: 9:16 Portrait (Shorts/Reels) – {duration_seconds:.0f}s < {self.shorts_threshold}s")
            return RESOLUTION_PORTRAIT
        logger.info(f"  Format: 16:9 Landscape – {duration_seconds:.0f}s ≥ {self.shorts_threshold}s")
        return RESOLUTION_LANDSCAPE

    def create(self, audio_path: str, script: dict, output_path: str, temp_dir: str = "output/temp") -> str:
        """Erstellt ein vollständiges Video mit MoviePy."""
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Video-Erstellung gestartet: {output_path}")

        try:
            from moviepy.editor import (
                AudioFileClip, ColorClip, TextClip, CompositeVideoClip,
                concatenate_videoclips
            )
            return self._create_with_moviepy(
                audio_path, script, output_path, temp_dir,
                AudioFileClip, ColorClip, TextClip, CompositeVideoClip,
                concatenate_videoclips
            )
        except ImportError:
            logger.warning("MoviePy nicht verfügbar. Erstelle einfaches Video...")
            return self._create_simple_video(audio_path, script, output_path)

    def _create_with_moviepy(self, audio_path, script, output_path, temp_dir,
                              AudioFileClip, ColorClip, TextClip, CompositeVideoClip,
                              concatenate_videoclips):
        """Erstellt professionelles Video mit MoviePy."""
        from moviepy.editor import AudioFileClip

        audio = AudioFileClip(audio_path)
        total_duration = audio.duration
        logger.info(f"  Audio-Dauer: {total_duration:.1f}s")

        resolution = self._pick_resolution(total_duration)
        is_portrait = resolution[0] < resolution[1]

        bg = ColorClip(size=resolution, color=self.bg_color, duration=total_duration)
        clips = [bg]

        # Titel-Text (erste 5 Sekunden) – bei Portrait etwas kleinere Schrift
        title = script.get("title", "ContentStudio Video")
        title_clean = self._clean_text(title)
        font_size = self.font_size if not is_portrait else max(self.font_size - 10, 40)

        try:
            title_clip = (
                TextClip(
                    title_clean,
                    fontsize=font_size,
                    color="white",
                    font="Arial-Bold",
                    size=(resolution[0] - 100, None),
                    method="caption",
                )
                .set_position("center")
                .set_start(0)
                .set_duration(min(5, total_duration))
                .crossfadein(0.5)
            )
            clips.append(title_clip)
        except Exception as e:
            logger.warning(f"Titel-Clip Fehler: {e}")

        # Script-Sektionen
        sections = script.get("sections", [])
        if sections and total_duration > 10:
            section_duration = (total_duration - 10) / max(len(sections), 1)
            for i, section in enumerate(sections):
                start_time = 5 + (i * section_duration)
                section_title = section.get("title", f"Teil {i+1}")

                try:
                    sec_clip = (
                        TextClip(
                            self._clean_text(section_title),
                            fontsize=font_size - 10,
                            color="#A78BFA",
                            font="Arial-Bold",
                            size=(resolution[0] - 100, None),
                            method="caption",
                        )
                        .set_position(("center", resolution[1] // 3))
                        .set_start(start_time)
                        .set_duration(min(section_duration * 0.3, 4))
                        .crossfadein(0.3)
                        .crossfadeout(0.3)
                    )
                    clips.append(sec_clip)
                except Exception as e:
                    logger.debug(f"Sections-Clip {i} Fehler: {e}")

        # Disclaimer am Ende (nur bei langen Videos)
        if not is_portrait and total_duration > 8:
            disclaimer = self.settings.get("compliance", {}).get(
                "disclaimer_text", "Nur zu Unterhaltungs- und Bildungszwecken."
            )
            try:
                disc_clip = (
                    TextClip(
                        disclaimer[:100],
                        fontsize=24,
                        color="#AAAAAA",
                        font="Arial",
                        size=(resolution[0] - 100, None),
                        method="caption",
                    )
                    .set_position(("center", resolution[1] - 80))
                    .set_start(total_duration - 6)
                    .set_duration(5)
                    .crossfadein(0.5)
                )
                clips.append(disc_clip)
            except Exception as e:
                logger.debug(f"Disclaimer-Clip Fehler: {e}")

        final = CompositeVideoClip(clips).set_audio(audio)

        codec = self.cfg.get("codec", "libx264")
        bitrate = self.cfg.get("bitrate", "8000k")

        logger.info(f"  Exportiere Video ({codec}, {bitrate}, {resolution[0]}x{resolution[1]})...")
        final.write_videofile(
            output_path,
            fps=self.fps,
            codec=codec,
            audio_codec="aac",
            bitrate=bitrate,
            temp_audiofile=os.path.join(temp_dir, "temp_audio.aac"),
            remove_temp=True,
            verbose=False,
            logger=None,
        )

        final.close()
        audio.close()

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        fmt = "9:16 (Short)" if is_portrait else "16:9"
        logger.info(f"  Video fertig: {output_path} ({size_mb:.1f} MB, {fmt})")
        return output_path

    def _create_simple_video(self, audio_path: str, script: dict, output_path: str) -> str:
        """Fallback: Einfaches Video mit ffmpeg direkt."""
        import subprocess

        # Dauer via ffprobe ermitteln für korrekte Formatwahl
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True, text=True, timeout=30
            )
            duration = float(probe.stdout.strip()) if probe.returncode == 0 else 999
        except Exception:
            duration = 999

        resolution = self._pick_resolution(duration)
        size_str = f"{resolution[0]}x{resolution[1]}"

        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x0A0A14:size={size_str}:rate=30",
                "-i", audio_path,
                "-shortest",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg Fehler: {result.stderr}")

            logger.info(f"Einfaches Video erstellt: {output_path} ({size_str})")
            return output_path

        except Exception as e:
            logger.error(f"Video-Erstellung fehlgeschlagen: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """Entfernt Sonderzeichen die TextClip nicht verarbeiten kann."""
        import re
        text = re.sub(r'[^\w\s\-.,!?:|()/€$%&]', '', text)
        return text.strip()[:100]
