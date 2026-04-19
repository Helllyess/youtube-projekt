#!/usr/bin/env python3
"""
StoryPlanner – 5-Schritt Story-Planungs-Workflow.

Ablauf:
  1. User gibt Thema ein  →  research_story_ideas()
  2. User wählt Ideen aus (Liste von Titeln)
  3. User legt Kanal, Zeitraum, Video-Länge fest  →  create_posting_plan()
  4. Plan wird gespeichert und angezeigt
  5. User startet Produktion  →  execute_plan()
"""

import json
import logging
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("planner")

PLAN_FILE = Path(__file__).parent / "config" / "story_plan.json"


class StoryPlanner:
    def __init__(self, settings: dict):
        self.settings = settings

    # ── Schritt 1+2: Story-Ideen recherchieren ────────────────────

    def research_story_ideas(self, theme: str, count: int = 10) -> list[dict]:
        """
        Fragt GPT nach fesselnden Story-Ideen zu einem Thema.
        Gibt eine Liste von Ideen zurück: [{title, desc, hook, content_type, estimated_duration_min}]
        """
        from researcher import Researcher
        researcher = Researcher(self.settings)
        ideas = researcher.research_story_ideas(theme, count)
        logger.info(f"Recherche '{theme}': {len(ideas)} Ideen gefunden")
        return ideas

    # ── Schritt 3: Posting-Plan erstellen ─────────────────────────

    def create_posting_plan(
        self,
        selected_ideas: list[dict],
        channel: str,
        start_date: str,
        end_date: str,
        duration_minutes: int = 10,
        posts_per_week: int = 3,
        preferred_time: str = "16:00",
        preferred_days: list[str] = None,
    ) -> list[dict]:
        """
        Erstellt einen zeitlichen Posting-Plan für die ausgewählten Ideen.

        Args:
            selected_ideas: Liste der ausgewählten Story-Ideen
            channel: Kanal-ID (Ordnername in channels/)
            start_date: Startdatum "YYYY-MM-DD"
            end_date: Enddatum "YYYY-MM-DD"
            duration_minutes: Ziel-Länge jedes Videos in Minuten
            posts_per_week: Wie viele Videos pro Woche gepostet werden
            preferred_time: Upload-Uhrzeit "HH:MM"
            preferred_days: Liste der bevorzugten Wochentage

        Returns:
            Liste von Plan-Einträgen mit scheduled_date
        """
        if preferred_days is None:
            preferred_days = ["Montag", "Mittwoch", "Freitag"]

        day_map = {
            "Montag": 0, "Dienstag": 1, "Mittwoch": 2,
            "Donnerstag": 3, "Freitag": 4, "Samstag": 5, "Sonntag": 6,
        }
        pref_weekdays = [day_map[d] for d in preferred_days if d in day_map]

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        slots = []
        current = start
        while current <= end and len(slots) < len(selected_ideas):
            if current.weekday() in pref_weekdays:
                slots.append(current.strftime(f"%Y-%m-%d {preferred_time}"))
            current += timedelta(days=1)

        if len(slots) < len(selected_ideas):
            current = end + timedelta(days=1)
            while len(slots) < len(selected_ideas):
                slots.append(current.strftime(f"%Y-%m-%d {preferred_time}"))
                current += timedelta(days=1)

        plan = []
        for idea, slot in zip(selected_ideas, slots):
            plan.append({
                "id": str(uuid.uuid4()),
                "title": idea.get("title", "Unbekannt"),
                "desc": idea.get("desc", ""),
                "hook": idea.get("hook", ""),
                "content_type": idea.get("content_type", "storytelling"),
                "channel": channel,
                "duration_minutes": duration_minutes,
                "scheduled_date": slot,
                "status": "queued",
                "result": None,
            })

        self._save_plan(plan)
        logger.info(f"Posting-Plan erstellt: {len(plan)} Videos von {start_date} bis {slots[-1][:10] if slots else end_date}")
        return plan

    # ── Schritt 5: Plan ausführen ─────────────────────────────────

    def execute_plan(
        self,
        plan: list[dict] = None,
        dry_run: bool = False,
        on_progress=None,
    ) -> list[dict]:
        """
        Produziert alle Videos im Plan nacheinander.

        Args:
            plan: Plan-Liste (wenn None: wird aus Datei geladen)
            dry_run: Kein Upload, nur Generierung
            on_progress: Callback(current_idx, total, entry) für UI-Updates
        """
        from main import run_pipeline
        from channel_manager import ChannelManager

        if plan is None:
            plan = self.load_plan()

        queued = [e for e in plan if e.get("status") == "queued"]
        total = len(queued)
        logger.info(f"Starte Plan-Ausführung: {total} Videos")

        manager = ChannelManager(self.settings)

        for i, entry in enumerate(queued):
            entry["status"] = "producing"
            self._save_plan(plan)

            if on_progress:
                on_progress(i, total, entry)

            try:
                channel_id = entry.get("channel", "")
                if channel_id and channel_id != "Standard":
                    ch_settings = manager.build_settings_for_channel(channel_id)
                else:
                    ch_settings = self.settings

                ch_settings = dict(ch_settings)
                ch_settings.setdefault("script", {})["target_duration_minutes"] = entry.get("duration_minutes", 10)

                result = run_pipeline(ch_settings, topic=entry["title"], dry_run=dry_run)
                entry["status"] = "done" if result.get("status") == "success" else "error"
                entry["result"] = {
                    "youtube_url": result.get("youtube_url"),
                    "video_path": result.get("video_path"),
                    "error": result.get("error"),
                }
            except Exception as e:
                logger.error(f"Fehler bei '{entry['title']}': {e}")
                entry["status"] = "error"
                entry["result"] = {"error": str(e)}

            self._save_plan(plan)

            if i < total - 1:
                logger.info("10s Pause zwischen Videos...")
                time.sleep(10)

        done = sum(1 for e in queued if e.get("status") == "done")
        logger.info(f"Plan abgeschlossen: {done}/{total} erfolgreich")
        return plan

    # ── Plan-Persistenz ───────────────────────────────────────────

    def _save_plan(self, plan: list[dict]):
        PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PLAN_FILE, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)

    def load_plan(self) -> list[dict]:
        if PLAN_FILE.exists():
            try:
                with open(PLAN_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def clear_plan(self):
        if PLAN_FILE.exists():
            PLAN_FILE.unlink()

    def get_plan_stats(self) -> dict:
        plan = self.load_plan()
        return {
            "total": len(plan),
            "queued": sum(1 for e in plan if e["status"] == "queued"),
            "producing": sum(1 for e in plan if e["status"] == "producing"),
            "done": sum(1 for e in plan if e["status"] == "done"),
            "error": sum(1 for e in plan if e["status"] == "error"),
        }
