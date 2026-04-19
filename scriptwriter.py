#!/usr/bin/env python3
"""
ScriptWriter – Erstellt vollständige YouTube-Scripts für Storytelling-Content.
Optimiert für Geschichte, Dokumentationen, Biographien, Brainrot und Comedy.
"""

import json
import logging
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger("scriptwriter")

STYLE_PROMPTS = {
    "storytelling_engaging": (
        "Du bist ein meisterhafter Geschichtenerzähler im Stil von deutschen Doku-YouTubern. "
        "Du erzählst Storys so fesselnd wie einen Thriller – mit Spannung, Wendepunkten "
        "und einem unwiderstehlichen Sog der Zuschauer bis zum Ende dran hält."
    ),
    "brainrot": (
        "Du bist ein kreativer Brainrot-Content-Creator. Dein Stil ist chaotisch-lustig, "
        "überdreht, voller Meme-Referenzen und irrsinnigen Übergängen. "
        "Du redest schnell, springst zwischen Themen und machst alles absurd-unterhaltsam."
    ),
    "documentary": (
        "Du bist ein seriöser Dokumentar-Erzähler im BBC/Arte-Stil. "
        "Sachlich, tiefgehend, gut recherchiert – aber trotzdem spannend und zugänglich."
    ),
    "comedy": (
        "Du bist ein Comedy-Youtuber der Fakten und Geschichten mit viel Humor erzählt. "
        "Du findest das Absurde im Alltäglichen und machst selbst trockene Geschichte lustig."
    ),
}


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
        self.style = self.script_cfg.get("style", "storytelling_engaging")

    def create_script(self, topic: str, keywords: list[str]) -> dict:
        """Erstellt ein vollständiges Video-Script für das gegebene Story-Topic."""
        logger.info(f"Erstelle Storytelling-Script für: '{topic}'")

        self._load_legal_rules()
        script_data = self._generate_script(topic, keywords)
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
            "duration_estimate_min": self.script_cfg.get("target_duration_minutes", 10),
            "thumbnail_text": meta.get("thumbnail_text", topic[:30]),
        }

        logger.info(f"Script erstellt: '{script['title']}' (~{script['duration_estimate_min']} Min.)")
        return script

    def _load_legal_rules(self):
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
        duration = self.script_cfg.get("target_duration_minutes", 10)
        disclaimer = self.compliance_cfg.get("disclaimer_text",
            "Dieses Video dient ausschließlich Unterhaltungs- und Bildungszwecken.")
        kw_str = ", ".join(keywords)

        rules_block = ""
        if hasattr(self, "_rules_prompt") and self._rules_prompt:
            rules_block = f"""

═══════════════════════════════════════════════
RECHTLICHE REGELN – MÜSSEN EINGEHALTEN WERDEN:
═══════════════════════════════════════════════
{self._rules_prompt}
═══════════════════════════════════════════════
"""

        system_prompt = STYLE_PROMPTS.get(self.style, STYLE_PROMPTS["storytelling_engaging"])

        prompt = f"""
Erstelle ein professionelles YouTube-Video-Script auf DEUTSCH für folgende Story:
**"{topic}"**

Keywords: {kw_str}
Ziel-Länge: ~{duration} Minuten (ca. {duration * 140} Wörter gesprochen)
{rules_block}
SCRIPT-STRUKTUR FÜR STORYTELLING:

**1. HOOK (erste 30-45 Sekunden – ENTSCHEIDEND!):**
- Starte MITTEN IN DER ACTION oder mit einer schockierenden Aussage
- Stelle eine Frage die sofort neugierig macht
- Verspreche dem Zuschauer was er am Ende wissen wird
- KEIN langsames Aufwärmen – direkt rein!

**2. AUFBAU (1-2 Minuten):**
- Kontext und Hintergrund der Story
- Wer sind die Hauptpersonen? Was ist die Ausgangssituation?
- Erzeuge emotionale Verbindung zum Zuschauer

**3. HAUPT-STORY (6-10 Minuten) – 3-4 Akte/Kapitel:**
- Jedes Kapitel mit eigenem Titel und Spannungsbogen
- Konkrete Details, Zahlen, Zitate, Anekdoten
- Wendepunkte und Überraschungen einbauen
- Cliffhanger zwischen Kapiteln ("Aber dann passierte etwas Unerwartetes...")
- Emotionale Hochs und Tiefs

**4. AUFLÖSUNG & OUTRO (1-2 Minuten):**
- Befriedigende Auflösung der Story
- "Was bedeutet das für uns heute?" – Moral oder Relevanz
- Starker Call-to-Action (Abonnieren, Kommentieren)
- PFLICHT: Disclaimer: "{disclaimer}"

Antworte als JSON:
{{
  "hook": "Vollständiger Hook-Text (30-45 Sekunden, mitreißend)",
  "intro": "Aufbau-Text mit Kontext und Charakteren",
  "sections": [
    {{
      "title": "Kapitel 1: [Name]",
      "content": "Vollständiger Kapitel-Text mit Details und Spannung"
    }},
    {{
      "title": "Kapitel 2: [Name]",
      "content": "Vollständiger Kapitel-Text mit Wendepunkt"
    }},
    {{
      "title": "Kapitel 3: [Name]",
      "content": "Vollständiger Kapitel-Text mit Klimax"
    }}
  ],
  "outro": "Auflösung, Moral, CTA und Disclaimer"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
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
Erstelle optimierte YouTube-Metadaten für dieses Storytelling-Video:
Topic: {topic}
Keywords: {", ".join(keywords)}
Script-Anfang: {hook_preview}

Erstelle:
1. Einen klickwürdigen Titel (max 70 Zeichen, mit Emoji, auf Deutsch – neugierig machend)
2. Einen Untertitel für Thumbnail (max 30 Zeichen, Impact-Statement)
3. Eine SEO-optimierte Beschreibung (300-400 Wörter) mit Story-Teaser
4. 15 relevante Tags

JSON-Format:
{{
  "title": "😱 Story-Titel der sofort neugierig macht",
  "subtitle": "KURZER SCHOCKTEXT",
  "description": "Vollständige Beschreibung mit Story-Teaser und Keywords...",
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
                "title": f"😱 {topic} – Die ganze Geschichte!",
                "subtitle": topic[:25].upper(),
                "description": f"In diesem Video erzählen wir die faszinierende Geschichte von {topic}.\n\n{', '.join(keywords)}",
                "tags": default_tags + keywords,
                "thumbnail_text": topic[:20].upper(),
            }

    def _compile_full_text(self, script_data: dict) -> str:
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
