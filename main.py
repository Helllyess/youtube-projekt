#!/usr/bin/env python3
"""
YouTube Automation v2.1 – Main Pipeline Orchestrator
Erstellt automatisch Finance/Daytrading Videos und lädt sie auf YouTube hoch.
Unterstützt mehrere Kanäle via --channel Parameter.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Module imports
from researcher import Researcher
from scriptwriter import ScriptWriter
from voiceover import Voiceover
from compliance import ComplianceChecker
from video_creator import VideoCreator
from thumbnail import ThumbnailGenerator
from uploader import YouTubeUploader
from channel_manager import ChannelManager


def load_settings(path: str = "config/settings.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_logging(settings: dict) -> logging.Logger:
    log_cfg = settings.get("logging", {})
    log_dir = Path(settings["paths"]["logs_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_cfg.get("level", "INFO")),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_cfg.get("file", "logs/automation.log"), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("main")


def run_pipeline(settings: dict, topic: str = None, dry_run: bool = False):
    logger = logging.getLogger("main")
    logger.info("=" * 60)
    logger.info(f"YouTube Automation v{settings['version']} gestartet")
    logger.info("=" * 60)

    # Temp-Ordner vorbereiten
    temp_dir = Path(settings["paths"].get("temp_dir", "output/temp"))
    temp_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(settings["paths"]["output_dir"]) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "timestamp": timestamp,
        "status": "running",
        "topic": None,
        "script_path": None,
        "audio_path": None,
        "video_path": None,
        "thumbnail_path": None,
        "youtube_url": None,
    }

    try:
        # ── Schritt 1: Topic-Recherche ──────────────────────────────────
        logger.info("📊 Schritt 1: Topic-Recherche...")
        researcher = Researcher(settings)
        if topic:
            video_topic = topic
            keywords = topic.split()
        else:
            video_topic, keywords = researcher.find_trending_topic()
        logger.info(f"   Topic: {video_topic}")
        result["topic"] = video_topic

        # ── Schritt 2: Script schreiben ─────────────────────────────────
        logger.info("✍️  Schritt 2: Script-Erstellung...")
        writer = ScriptWriter(settings)
        script = writer.create_script(video_topic, keywords)
        script_path = output_dir / "script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        logger.info(f"   Script gespeichert: {script_path}")
        result["script_path"] = str(script_path)

        # ── Schritt 3: Compliance-Check ─────────────────────────────────
        logger.info("✅ Schritt 3: Compliance-Check...")
        checker = ComplianceChecker(settings)
        compliance_result = checker.check(script)
        if not compliance_result["passed"]:
            logger.warning(f"   Compliance-Probleme: {compliance_result['issues']}")
            script = checker.fix_script(script, compliance_result)
        else:
            logger.info("   Compliance OK ✓")

        # ── Schritt 4: Voiceover erstellen ──────────────────────────────
        logger.info("🎙️  Schritt 4: Voiceover-Erstellung...")
        vo = Voiceover(settings)
        audio_path = output_dir / "voiceover.mp3"
        vo.create(script["full_text"], str(audio_path))
        logger.info(f"   Audio gespeichert: {audio_path}")
        result["audio_path"] = str(audio_path)

        # ── Schritt 5: Thumbnail erstellen ──────────────────────────────
        logger.info("🖼️  Schritt 5: Thumbnail-Erstellung...")
        thumb_gen = ThumbnailGenerator(settings)
        thumbnail_path = output_dir / "thumbnail.jpg"
        thumb_gen.create(script["title"], script.get("subtitle", ""), str(thumbnail_path))
        logger.info(f"   Thumbnail gespeichert: {thumbnail_path}")
        result["thumbnail_path"] = str(thumbnail_path)

        # ── Schritt 6: Video erstellen ──────────────────────────────────
        logger.info("🎬 Schritt 6: Video-Erstellung...")
        creator = VideoCreator(settings)
        video_path = output_dir / "video.mp4"
        creator.create(
            audio_path=str(audio_path),
            script=script,
            output_path=str(video_path),
            temp_dir=str(temp_dir),
        )
        logger.info(f"   Video gespeichert: {video_path}")
        result["video_path"] = str(video_path)

        # ── Schritt 7: YouTube Upload ───────────────────────────────────
        if not dry_run:
            logger.info("🚀 Schritt 7: YouTube Upload...")
            uploader = YouTubeUploader(settings)
            youtube_url = uploader.upload(
                video_path=str(video_path),
                thumbnail_path=str(thumbnail_path),
                title=script["title"],
                description=script["description"],
                tags=script.get("tags", settings["channel"]["default_tags"]),
            )
            logger.info(f"   Video online: {youtube_url}")
            result["youtube_url"] = youtube_url
        else:
            logger.info("   [DRY RUN] Upload übersprungen")

        result["status"] = "success"
        logger.info("=" * 60)
        logger.info("✅ Pipeline erfolgreich abgeschlossen!")
        if result["youtube_url"]:
            logger.info(f"   🔗 {result['youtube_url']}")
        logger.info("=" * 60)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"❌ Pipeline-Fehler: {e}", exc_info=True)

    # Ergebnis speichern
    result_path = output_dir / "result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Video zur Historie hinzufügen (für Dashboard Videos-Tab)
    try:
        from scheduler import VideoScheduler
        sched = VideoScheduler(settings)
        sched.add_to_history(result)
        logger.info("📋 Video zur Historie hinzugefügt")
    except Exception as e:
        logger.warning(f"Historie-Update fehlgeschlagen: {e}")

    return result


def run_all_channels(base_settings: dict, topic: str = None, dry_run: bool = False):
    """Führt die Pipeline für ALLE aktiven Kanäle aus."""
    manager = ChannelManager(base_settings)
    channels = [ch for ch in manager.list_channels() if ch.get("active", True)]

    if not channels:
        logger = logging.getLogger("main")
        logger.warning("Keine aktiven Kanäle gefunden. Nutze Standard-Settings.")
        return [run_pipeline(base_settings, topic=topic, dry_run=dry_run)]

    results = []
    for ch in channels:
        logger = logging.getLogger("main")
        logger.info(f"\n{'='*60}")
        logger.info(f"KANAL: {ch.get('name', ch['_folder'])}")
        logger.info(f"{'='*60}")
        try:
            ch_settings = manager.build_settings_for_channel(ch["_folder"])
            result = run_pipeline(ch_settings, topic=topic, dry_run=dry_run)
            result["channel"] = ch.get("name", ch["_folder"])
            results.append(result)
        except Exception as e:
            logger.error(f"Kanal '{ch['_folder']}' fehlgeschlagen: {e}")
            results.append({"channel": ch["_folder"], "status": "error", "error": str(e)})
    return results


def main():
    parser = argparse.ArgumentParser(description="YouTube Automation v2.1")
    parser.add_argument("--topic", type=str, help="Manuelles Video-Topic (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Kein Upload, nur Generierung")
    parser.add_argument("--config", type=str, default="config/settings.json")
    parser.add_argument("--channel", type=str, default=None,
                        help="Kanal-ID (Ordnername in channels/). Leer = alle aktiven Kanäle")
    parser.add_argument("--list-channels", action="store_true", help="Alle Kanäle anzeigen")
    args = parser.parse_args()

    settings = load_settings(args.config)
    setup_logging(settings)

    # Kanal-Liste anzeigen
    if args.list_channels:
        ChannelManager(settings).print_status()
        sys.exit(0)

    # Einzelner Kanal
    if args.channel:
        manager = ChannelManager(settings)
        ch_settings = manager.build_settings_for_channel(args.channel)
        result = run_pipeline(ch_settings, topic=args.topic, dry_run=args.dry_run)
        sys.exit(0 if result["status"] == "success" else 1)

    # Alle Kanäle ODER Standard (wenn keine channels/ Ordner vorhanden)
    manager = ChannelManager(settings)
    if manager.list_channels():
        results = run_all_channels(settings, topic=args.topic, dry_run=args.dry_run)
        success = all(r["status"] == "success" for r in results)
        sys.exit(0 if success else 1)
    else:
        # Fallback: Standard-Pipeline ohne Multi-Channel
        result = run_pipeline(settings, topic=args.topic, dry_run=args.dry_run)
        sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
