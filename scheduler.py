#!/usr/bin/env python3
"""
Scheduler – Batch-Produktion und zeitgesteuertes Hochladen.
Erstellt mehrere Videos auf einmal und postet sie verteilt über die Woche.
"""

import os
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("scheduler")

SCHEDULE_FILE = Path(__file__).parent / "config" / "schedule.json"
HISTORY_FILE = Path(__file__).parent / "config" / "video_history.json"


class VideoScheduler:
    def __init__(self, settings: dict):
        self.settings = settings
        self.schedule = self._load_schedule()
        self.history = self._load_history()

    # ── History (alle Videos) ────────────────────────────────────

    def _load_history(self) -> list:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_history(self):
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def add_to_history(self, result: dict):
        """Fügt ein Pipeline-Ergebnis zur Video-Historie hinzu."""
        entry = {
            "id": len(self.history) + 1,
            "title": result.get("topic", "Unbekannt"),
            "status": result.get("status", "unknown"),
            "timestamp": result.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S")),
            "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "video_path": result.get("video_path"),
            "thumbnail_path": result.get("thumbnail_path"),
            "script_path": result.get("script_path"),
            "audio_path": result.get("audio_path"),
            "youtube_url": result.get("youtube_url"),
            "channel": result.get("channel", "Standard"),
            "upload_status": "uploaded" if result.get("youtube_url") else "local",
            "scheduled_date": None,
        }
        self.history.append(entry)
        self.save_history()
        logger.info(f"Video zur Historie hinzugefügt: {entry['title']}")
        return entry

    def get_history(self, status_filter: str = None) -> list:
        """Gibt die Video-Historie zurück, optional gefiltert."""
        if status_filter:
            return [v for v in self.history if v.get("upload_status") == status_filter
                    or v.get("status") == status_filter]
        return self.history

    def update_video_status(self, video_id: int, status: str, youtube_url: str = None):
        """Aktualisiert den Status eines Videos in der Historie."""
        for v in self.history:
            if v.get("id") == video_id:
                v["upload_status"] = status
                if youtube_url:
                    v["youtube_url"] = youtube_url
                break
        self.save_history()

    # ── Schedule (geplante Uploads) ──────────────────────────────

    def _load_schedule(self) -> dict:
        if SCHEDULE_FILE.exists():
            try:
                with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "enabled": False,
            "posts_per_week": 3,
            "preferred_days": ["Montag", "Mittwoch", "Freitag"],
            "preferred_time": "16:00",
            "queue": [],
        }

    def save_schedule(self):
        SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.schedule, f, ensure_ascii=False, indent=2)

    def add_to_queue(self, video_id: int, scheduled_date: str = None):
        """Fügt ein Video zur Upload-Warteschlange hinzu."""
        if not scheduled_date:
            scheduled_date = self._next_available_slot()

        entry = {
            "video_id": video_id,
            "scheduled_date": scheduled_date,
            "status": "queued",
        }
        self.schedule.setdefault("queue", []).append(entry)
        self.save_schedule()

        # Auch in History aktualisieren
        for v in self.history:
            if v.get("id") == video_id:
                v["scheduled_date"] = scheduled_date
                v["upload_status"] = "scheduled"
                break
        self.save_history()

        logger.info(f"Video {video_id} geplant für: {scheduled_date}")
        return scheduled_date

    def _next_available_slot(self) -> str:
        """Berechnet den nächsten freien Upload-Slot."""
        day_map = {
            "Montag": 0, "Dienstag": 1, "Mittwoch": 2,
            "Donnerstag": 3, "Freitag": 4, "Samstag": 5, "Sonntag": 6
        }
        preferred = self.schedule.get("preferred_days", ["Montag", "Mittwoch", "Freitag"])
        pref_time = self.schedule.get("preferred_time", "16:00")
        preferred_weekdays = [day_map.get(d, 0) for d in preferred]

        # Bereits belegte Tage sammeln
        booked_dates = set()
        for item in self.schedule.get("queue", []):
            if item.get("status") in ("queued", "uploading"):
                booked_dates.add(item.get("scheduled_date", "")[:10])

        # Ab morgen den nächsten freien bevorzugten Tag finden
        check = datetime.now() + timedelta(days=1)
        for _ in range(30):  # Max 30 Tage in die Zukunft
            if check.weekday() in preferred_weekdays:
                date_str = check.strftime("%Y-%m-%d")
                if date_str not in booked_dates:
                    return f"{date_str} {pref_time}"
            check += timedelta(days=1)

        # Fallback: morgen
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + f" {pref_time}"

    def get_queue(self) -> list:
        """Gibt die aktuelle Upload-Warteschlange zurück."""
        queue = self.schedule.get("queue", [])
        enriched = []
        for item in queue:
            vid_id = item.get("video_id")
            video = next((v for v in self.history if v.get("id") == vid_id), {})
            enriched.append({**item, "title": video.get("title", "?"), "channel": video.get("channel", "?")})
        return sorted(enriched, key=lambda x: x.get("scheduled_date", ""))

    def remove_from_queue(self, video_id: int):
        """Entfernt ein Video aus der Warteschlange."""
        self.schedule["queue"] = [q for q in self.schedule.get("queue", []) if q.get("video_id") != video_id]
        self.save_schedule()
        for v in self.history:
            if v.get("id") == video_id:
                v["upload_status"] = "local"
                v["scheduled_date"] = None
                break
        self.save_history()

    # ── Batch-Produktion ─────────────────────────────────────────

    def batch_produce(self, topics: list, settings: dict, channel_id: str = None,
                      auto_schedule: bool = True, dry_run: bool = False) -> list:
        """
        Erstellt mehrere Videos auf einmal und plant sie zum Hochladen.
        Gibt eine Liste der Ergebnisse zurück.
        """
        from main import run_pipeline, load_settings

        results = []
        total = len(topics)
        logger.info(f"🎬 Batch-Produktion: {total} Videos")

        for i, topic in enumerate(topics, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"📹 Video {i}/{total}: {topic}")
            logger.info(f"{'='*50}")

            try:
                result = run_pipeline(settings, topic=topic, dry_run=dry_run)
                result["channel"] = channel_id or "Standard"
                entry = self.add_to_history(result)

                if auto_schedule and result["status"] == "success" and not dry_run:
                    slot = self.add_to_queue(entry["id"])
                    logger.info(f"   📅 Geplant für: {slot}")

                results.append(result)

            except Exception as e:
                logger.error(f"   ❌ Fehler bei '{topic}': {e}")
                results.append({"topic": topic, "status": "error", "error": str(e)})

            # Kurze Pause zwischen Videos (API Rate Limits)
            if i < total:
                logger.info("   ⏳ 10s Pause...")
                time.sleep(10)

        logger.info(f"\n✅ Batch fertig: {sum(1 for r in results if r.get('status')=='success')}/{total} erfolgreich")
        return results

    # ── Geplante Uploads ausführen ───────────────────────────────

    def process_queue(self):
        """Lädt alle fälligen Videos hoch."""
        from uploader import YouTubeUploader

        now = datetime.now()
        queue = self.schedule.get("queue", [])
        due = [q for q in queue if q["status"] == "queued"
               and datetime.strptime(q["scheduled_date"][:16], "%Y-%m-%d %H:%M") <= now]

        if not due:
            logger.info("Keine fälligen Videos in der Warteschlange")
            return []

        uploader = YouTubeUploader(self.settings)
        uploaded = []

        for item in due:
            vid_id = item["video_id"]
            video = next((v for v in self.history if v.get("id") == vid_id), None)
            if not video or not video.get("video_path"):
                continue

            try:
                item["status"] = "uploading"
                self.save_schedule()
                logger.info(f"🚀 Uploade: {video.get('title')}")

                # Script laden für Metadata
                script = {}
                if video.get("script_path") and Path(video["script_path"]).exists():
                    with open(video["script_path"], "r", encoding="utf-8") as f:
                        script = json.load(f)

                url = uploader.upload(
                    video_path=video["video_path"],
                    thumbnail_path=video.get("thumbnail_path", ""),
                    title=script.get("title", video.get("title", "Video")),
                    description=script.get("description", ""),
                    tags=script.get("tags", []),
                )

                item["status"] = "uploaded"
                self.update_video_status(vid_id, "uploaded", url)
                uploaded.append({"video_id": vid_id, "url": url})
                logger.info(f"   ✅ Hochgeladen: {url}")

            except Exception as e:
                item["status"] = "failed"
                logger.error(f"   ❌ Upload fehlgeschlagen: {e}")

        self.save_schedule()
        return uploaded


# ── CLI ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Video Scheduler")
    parser.add_argument("--batch", nargs="+", help="Mehrere Topics auf einmal produzieren")
    parser.add_argument("--process-queue", action="store_true", help="Fällige Videos hochladen")
    parser.add_argument("--show-history", action="store_true", help="Alle Videos anzeigen")
    parser.add_argument("--show-queue", action="store_true", help="Upload-Warteschlange anzeigen")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--config", default="config/settings.json")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        settings = json.load(f)

    sched = VideoScheduler(settings)

    if args.show_history:
        print("\n📹 Video-Historie:")
        for v in sched.history:
            st = "✅" if v.get("youtube_url") else ("📅" if v.get("scheduled_date") else "💾")
            print(f"  {st} [{v['id']}] {v['title']} – {v.get('created','')} – {v.get('upload_status','?')}")
    elif args.show_queue:
        print("\n📅 Upload-Warteschlange:")
        for q in sched.get_queue():
            print(f"  [{q['video_id']}] {q['title']} → {q['scheduled_date']} ({q['status']})")
    elif args.batch:
        sched.batch_produce(args.batch, settings, dry_run=args.dry_run)
    elif args.process_queue:
        sched.process_queue()
