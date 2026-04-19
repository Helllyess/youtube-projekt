#!/usr/bin/env python3
"""
Researcher – Findet trending Topics für Storytelling YouTube Videos.
Unterstützt Geschichte, Dokumentationen, Biographien, Brainrot und Comedy.
"""

import json
import logging
import random
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger("researcher")

NICHE_PROMPTS = {
    "storytelling":   "Storytelling, Geschichte, Biographien, Dokumentationen",
    "history":        "historische Ereignisse, Schlachten, Imperien, vergessene Geschichte",
    "biography":      "faszinierende Lebensgeschichten berühmter und unbekannter Persönlichkeiten",
    "documentary":    "Dokumentations-Themen, Mysterien, ungeklärte Fälle, Verschwörungen",
    "brainrot":       "absurder Humor, virale Trends, Meme-Kultur, Brainrot-Content",
    "comedy":         "lustige Alltagsgeschichten, komische historische Fakten, kuriose Ereignisse",
    "science":        "faszinierende Wissenschaft, verrückte Experimente, Entdeckungen",
    "mystery":        "ungeklärte Mysterien, Geisterstädte, verschwundene Zivilisationen",
    "crime":          "berühmte Verbrechen, Betrugsskandale, dramatische Gerichtsverfahren",
    "custom":         "allgemeines Storytelling und Entertainment",
}


class Researcher:
    def __init__(self, settings: dict):
        self.settings = settings
        self.client = OpenAI(api_key=settings["api_keys"]["openai"])
        self.model = settings["openai"].get("research_model", "gpt-4o-mini")
        self.niche = settings["channel"].get("niche", "storytelling")
        self.language = settings["channel"].get("language", "de")
        self.base_topics = settings["research"].get("topics", [])

    def find_trending_topic(self) -> tuple[str, list[str]]:
        """Findet das aktuell beste Story-Topic für den Kanal."""
        logger.info("Suche trending Storytelling-Topic...")

        niche_desc = NICHE_PROMPTS.get(self.niche, NICHE_PROMPTS["storytelling"])
        prompt = self._build_research_prompt(niche_desc)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du bist ein erfahrener YouTube-Stratege spezialisiert auf "
                            "Storytelling, Geschichte und Entertainment-Content. "
                            "Du findest Themen die Menschen fesseln, zum Klicken verleiten "
                            "und bis zum Ende schauen lassen."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.85,
            )

            data = json.loads(response.choices[0].message.content)
            topic = data.get("topic", random.choice(self.base_topics))
            keywords = data.get("keywords", topic.split())
            score = data.get("viral_score", 0)

            logger.info(f"Topic gefunden: '{topic}' (Viral-Score: {score}/10)")
            return topic, keywords

        except Exception as e:
            logger.warning(f"API-Fehler bei Recherche: {e}. Nutze Fallback-Topic.")
            fallback = random.choice(self.base_topics) if self.base_topics else "Geheimnisse der Antike"
            return fallback, fallback.split()

    def _build_research_prompt(self, niche_desc: str) -> str:
        topics_str = "\n".join(f"- {t}" for t in self.base_topics)
        current_month = datetime.now().strftime("%B %Y")
        return f"""
Wir haben {current_month}. Analysiere welche Storytelling-Themen aus dem Bereich "{niche_desc}" gerade viral gehen.

Unsere Basis-Themen:
{topics_str}

Berücksichtige:
- Faszinierende, wenig bekannte Fakten und Geschichten
- Emotionale Storys die Menschen berühren oder überraschen
- Themen mit hohem Schock- oder Staunensfaktor
- Was auf YouTube, TikTok und Reddit gerade diskutiert wird
- Zeitlose Storys die immer gut ankommen (History, Mystery, Comedy)
- Aktuelle Trends im Entertainment-Bereich

Finde das BESTE Story-Topic für ein {self.language.upper()}-sprachiges YouTube-Langvideo (8-15 Minuten).

Antwort als JSON:
{{
  "topic": "Das konkrete Story-Topic (spezifisch und klickwürdig)",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "viral_score": 8,
  "reasoning": "Warum diese Story jetzt viral gehen wird",
  "hook_angle": "Der beste emotionale Einstieg für diese Story",
  "content_type": "history|biography|comedy|brainrot|documentary|mystery"
}}
"""

    def research_story_ideas(self, theme: str, count: int = 10) -> list[dict]:
        """Generiert mehrere Story-Ideen zu einem Thema (für den Story-Planer)."""
        prompt = f"""
Generiere {count} fesselnde YouTube-Story-Ideen zum Thema: "{theme}"

Jede Idee soll:
- Einen klickwürdigen Titel haben (max. 70 Zeichen)
- Eine kurze Beschreibung (1-2 Sätze) was die Story spannend macht
- Einen emotionalen Hook-Aspekt nennen
- Gut für ein 8-15 Minuten-Video funktionieren

JSON-Array:
[
  {{
    "title": "Titel der Story",
    "desc": "Kurzbeschreibung was die Story spannend macht",
    "hook": "Der stärkste emotionale Einstieg",
    "content_type": "history|biography|comedy|mystery|documentary",
    "estimated_duration_min": 10
  }}
]
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein kreativer YouTube-Stratege für fesselndes Storytelling.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=2000,
            )
            text = response.choices[0].message.content.strip()
            start = text.find("[")
            end = text.rfind("]")
            if start >= 0 and end > start:
                return json.loads(text[start:end + 1])
        except Exception as e:
            logger.warning(f"Story-Recherche fehlgeschlagen: {e}")
        return []

    def analyze_competitors(self, topic: str) -> dict:
        """Analysiert was erfolgreiche Storytelling-Kanäle zu einem Topic machen."""
        prompt = f"""
Analysiere YouTube-Konkurrenz zum Storytelling-Topic: "{topic}"

Was machen erfolgreiche deutsche Storytelling-YouTuber zu diesem Thema?
Welchen Unique Angle können WIR einnehmen?

JSON-Antwort:
{{
  "common_approaches": ["Ansatz 1", "Ansatz 2"],
  "our_unique_angle": "So differenzieren wir uns",
  "hook_ideas": ["Hook 1", "Hook 2", "Hook 3"],
  "thumbnail_concepts": ["Konzept 1", "Konzept 2"]
}}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Competitor-Analyse fehlgeschlagen: {e}")
            return {"our_unique_angle": f"Einzigartiger Storytelling-Ansatz für: {topic}"}
