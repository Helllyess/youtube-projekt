#!/usr/bin/env python3
"""
Researcher – Findet trending Topics für Finance/Daytrading YouTube Videos.
Nutzt OpenAI GPT um Trends zu analysieren und das beste Topic auszuwählen.
"""

import json
import logging
import random
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger("researcher")


class Researcher:
    def __init__(self, settings: dict):
        self.settings = settings
        self.client = OpenAI(api_key=settings["api_keys"]["openai"])
        self.model = settings["openai"].get("research_model", "gpt-4o-mini")
        self.niche = settings["channel"].get("niche", "finance_daytrading")
        self.language = settings["channel"].get("language", "de")
        self.base_topics = settings["research"].get("topics", [])

    def find_trending_topic(self) -> tuple[str, list[str]]:
        """Findet das aktuell beste Video-Topic für den Kanal."""
        logger.info("Suche trending Topic...")

        current_month = datetime.now().strftime("%B %Y")
        prompt = self._build_research_prompt(current_month)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du bist ein erfahrener YouTube-Stratege spezialisiert auf "
                            "Finance und Trading-Content. Du analysierst Trends und findest "
                            "die besten Video-Topics für maximale Views und Engagement."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
            )

            data = json.loads(response.choices[0].message.content)
            topic = data.get("topic", random.choice(self.base_topics))
            keywords = data.get("keywords", topic.split())
            score = data.get("viral_score", 0)

            logger.info(f"Topic gefunden: '{topic}' (Viral-Score: {score}/10)")
            return topic, keywords

        except Exception as e:
            logger.warning(f"API-Fehler bei Recherche: {e}. Nutze Fallback-Topic.")
            fallback = random.choice(self.base_topics) if self.base_topics else "Daytrading für Anfänger"
            return fallback, fallback.split()

    def _build_research_prompt(self, current_month: str) -> str:
        topics_str = "\n".join(f"- {t}" for t in self.base_topics)
        return f"""
Wir haben {current_month}. Analysiere welche Finance/Trading-Themen gerade viral gehen.

Unsere Basis-Themen:
{topics_str}

Berücksichtige:
- Aktuelle Marktlage und Ereignisse
- Saisonale Trends (Steuern, Dividenden, Q-Berichte)
- Was Anfänger und erfahrene Trader gerade beschäftigt
- Welche Fragen auf Reddit (r/stocks, r/wallstreetbets) und YouTube diskutiert werden
- Hohe Suchvolumen + geringe Konkurrenz = perfekte Kombination

Gib mir das BESTE Topic für ein {self.language.upper()}-sprachiges YouTube-Video.
Antwort als JSON:
{{
  "topic": "Das konkrete Video-Topic (spezifisch und klickwürdig)",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "viral_score": 8,
  "reasoning": "Warum dieses Topic jetzt viral gehen wird",
  "search_volume": "hoch/mittel/niedrig",
  "competition": "hoch/mittel/niedrig"
}}
"""

    def analyze_competitors(self, topic: str) -> dict:
        """Analysiert was Konkurrenten zu einem Topic machen."""
        prompt = f"""
Analysiere YouTube-Konkurrenz zum Topic: "{topic}"

Was machen erfolgreiche deutsche Finance-YouTuber zu diesem Thema?
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
            return {"our_unique_angle": f"Einzigartiger Blickwinkel auf {topic}"}
