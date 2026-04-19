#!/usr/bin/env python3
"""
ScriptWriter – Erstellt vollständige YouTube-Video-Scripts mit OpenAI GPT-4o.
Optimiert für Finance/Daytrading Content auf Deutsch.
"""

import json
import logging
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger("scriptwriter")


class ScriptWriter:
    def __init__(self, settings: dict):
        self.settings = settings
        self.client = OpenAI(api_key=settings["api_keys"]["openai"])
        self.model = settings["openai"].get("script_model", "gpt-4o")
        self.temperature = settings["openai"].get("temperature", 0.7)
        self.max_tokens = settings["openai"].get("max_tokens", 4000)
        self.script_cfg = settings.get("script", {})
        self.compliance_cfg = settings.get("compliance", {})
        self.channel_cfg = settings.get("channel", {})

    def create_script(self, topic: str, keywords: list[str]) -> dict:
        """Erstellt ein vollständiges Video-Script für das gegebene Topic."""
        logger.info(f"Erstelle Script für: '{topic}'")

        # Legal-Regeln laden und in Prompt einbauen
        self._load_legal_rules()

        # Haupt-Script generieren
        script_data = self._generate_script(topic, keywords)

        # Titel & Beschreibung optimieren
        meta = self._generate_metadata(topic, script_data, keywords)

        script = {
            "topic": topic,
            "keywords": keywords,
            "title": meta["title"],
            "subtitle": meta.get("subtitle", ""),
            "description": meta["description"],
            "tags": meta["tags"],
            "hook": script_data.get("hook", ""),
            "sections": script_data.get("sections", []),
            "outro": script_data.get("outro", ""),
            "full_text": self._compile_full_text(script_data),
            "duration_estimate_min": self.script_cfg.get("target_duration_minutes", 8),
            "thumbnail_text": meta.get("thumbnail_text", topic[:30]),
        }

        logger.info(f"Script erstellt: '{script['title']}' (~{script['duration_estimate_min']} Min.)")
        return script

    def _load_legal_rules(self):
        """Lädt legal_rules.json und baut den Regel-Text für den Prompt."""
        rules_file = Path(__file__).parent / "config" / "legal_rules.json"
        self._rules_prompt = ""
        if rules_file.exists():
            try:
                from compliance import ComplianceChecker
                checker = ComplianceChecker(self.settings)
                self._rules_prompt = checker.get_rules_for_prompt()
                if self._rules_prompt:
                    logger.info("Legal-Rules in Prompt geladen ✓")
            except Exception as e:
                logger.warning(f"Legal-Rules konnten nicht geladen werden: {e}")

    def _generate_script(self, topic: str, keywords: list[str]) -> dict:
        duration = self.script_cfg.get("target_duration_minutes", 8)
        disclaimer = self.compliance_cfg.get("disclaimer_text", "")
        kw_str = ", ".join(keywords)

        # Legal-Rules Block (wird nur eingefügt wenn Regeln vorhanden)
        rules_block = ""
        if hasattr(self, '_rules_prompt') and self._rules_prompt:
            rules_block = f"""

═══════════════════════════════════════════════
RECHTLICHE REGELN – MÜSSEN EINGEHALTEN WERDEN:
═══════════════════════════════════════════════
{self._rules_prompt}
═══════════════════════════════════════════════
"""

        prompt = f"""
Erstelle ein professionelles YouTube-Video-Script auf DEUTSCH zum Thema:
**"{topic}"**

Keywords: {kw_str}
Ziel-Länge: ~{duration} Minuten (ca. {duration * 130} Wörter gesprochen)
Stil: Bildend, verständlich, engagierend – wie ein erfahrener Trading-Coach
{rules_block}
SCRIPT-STRUKTUR:

**1. HOOK (erste 30 Sekunden - WICHTIGSTE PART!):**
- Starke Eröffnung die sofort Aufmerksamkeit fängt
- Stelle eine provokante Frage oder share eine überraschende Tatsache
- Versprechen was der Zuschauer lernen wird

**2. INTRO (30-60 Sekunden):**
- Kurze Vorstellung des Themas
- Was genau werden wir heute besprechen?
- Warum ist das wichtig für den Zuschauer?

**3. HAUPT-CONTENT (5-6 Minuten) – unterteile in 3-4 Sektionen:**
- Jede Sektion mit klarem Titel
- Konkrete Informationen, Zahlen, Beispiele
- Praxisnahe Tipps die Zuschauer direkt anwenden können
- Trading/Finance spezifisches Wissen

**4. OUTRO & CTA (1 Minute):**
- Zusammenfassung der Key Points
- Starker Call-to-Action (Kanal abonnieren, Glocke aktivieren)
- Hinweis auf nächstes Video
- PFLICHT: Disclaimer: "{disclaimer}"

Antworte als JSON:
{{
  "hook": "Vollständiger Hook-Text (30 Sekunden)",
  "intro": "Intro-Text",
  "sections": [
    {{
      "title": "Sektion 1 Titel",
      "content": "Vollständiger Sektion-Text"
    }},
    {{
      "title": "Sektion 2 Titel",
      "content": "Vollständiger Sektion-Text"
    }},
    {{
      "title": "Sektion 3 Titel",
      "content": "Vollständiger Sektion-Text"
    }}
  ],
  "outro": "Outro mit CTA und Disclaimer"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du bist ein professioneller YouTuber und Trading-Experte aus Deutschland. "
                            "Du erstellst hochwertige, informative und fesselnde Video-Scripts. "
                            "Du sprichst deine Zuschauer direkt an und nutzt eine klare, verständliche Sprache. "
                            "Alle Scripts sind auf Deutsch und enthalten keine Finanzberatung."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Script-Generierung fehlgeschlagen: {e}")
            raise

    def _generate_metadata(self, topic: str, script_data: dict, keywords: list[str]) -> dict:
        hook_preview = script_data.get("hook", topic)[:200]
        prompt = f"""
Erstelle optimierte YouTube-Metadaten für dieses Video:
Topic: {topic}
Keywords: {", ".join(keywords)}
Script-Anfang: {hook_preview}

Erstelle:
1. Einen klickwürdigen Titel (max 60 Zeichen, mit Emoji, auf Deutsch)
2. Einen Untertitel für Thumbnail (max 30 Zeichen, großes Impact-Statement)
3. Eine SEO-optimierte Beschreibung (300-500 Wörter)
4. 15 relevante Tags

JSON-Format:
{{
  "title": "🔥 Clickbait-Titel | Unterpunkt",
  "subtitle": "KURZTEXT FÜR THUMBNAIL",
  "description": "Vollständige Beschreibung mit Timestamps, Links-Platzhalter und Keywords...",
  "tags": ["tag1", "tag2", "..."],
  "thumbnail_text": "TEXT FÜR THUMBNAIL"
}}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.8,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Metadata-Generierung fehlgeschlagen: {e}")
            default_tags = self.channel_cfg.get("default_tags", [])
            return {
                "title": f"🔥 {topic} – Alles was du wissen musst!",
                "subtitle": topic[:25].upper(),
                "description": f"In diesem Video sprechen wir über {topic}.\n\n{', '.join(keywords)}",
                "tags": default_tags + keywords,
                "thumbnail_text": topic[:20].upper(),
            }

    def _compile_full_text(self, script_data: dict) -> str:
        """Fügt alle Script-Teile zu einem lesbaren Text zusammen."""
        parts = []

        if script_data.get("hook"):
            parts.append(script_data["hook"])

        if script_data.get("intro"):
            parts.append(script_data["intro"])

        for section in script_data.get("sections", []):
            if section.get("content"):
                parts.append(section["content"])

        if script_data.get("outro"):
            parts.append(script_data["outro"])

        return "\n\n".join(parts)
