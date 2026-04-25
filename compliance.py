#!/usr/bin/env python3
"""
ComplianceChecker v2 – Liest legal_rules.json und erzwingt alle Regeln automatisch.
Prüft Scripts, Titel, Beschreibungen und blockiert bei Verstößen den Upload.
"""

import re
import json
import logging
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger("compliance")

RULES_FILE = Path(__file__).parent / "config" / "legal_rules.json"


class ComplianceChecker:
    def __init__(self, settings: dict):
        self.settings = settings
        self.client = OpenAI(api_key=settings["api_keys"]["openai"])
        self.rules = self._load_rules()
        self.violations = []

    def _load_rules(self) -> dict:
        """Lädt die editierbare Regel-Datei."""
        if RULES_FILE.exists():
            try:
                with open(RULES_FILE, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                logger.info(f"Legal-Rules geladen: {RULES_FILE}")
                return rules
            except Exception as e:
                logger.error(f"Fehler beim Laden von legal_rules.json: {e}")
        return {}

    # ── Haupt-Check ──────────────────────────────────────────────

    def check(self, script: dict) -> dict:
        """Führt ALLE Compliance-Checks durch basierend auf legal_rules.json."""
        self.violations = []
        issues = []
        warnings = []

        full_text = script.get("full_text", "")
        title = script.get("title", "")
        description = script.get("description", "")

        # 1. Disclaimers prüfen
        disc_issues = self._check_disclaimers(full_text, description)
        issues.extend(disc_issues)

        # 2. Verbotene Wörter prüfen
        word_issues = self._check_forbidden_words(full_text)
        issues.extend(word_issues)

        # 3. Titel-Regeln prüfen
        title_issues = self._check_title_rules(title)
        warnings.extend(title_issues)

        # 4. Beschreibungs-Regeln prüfen
        desc_issues = self._check_description_rules(description)
        warnings.extend(desc_issues)

        # 5. Content-Flags (AI-Check)
        ai_issues = self._ai_deep_check(full_text, title)
        warnings.extend(ai_issues)

        # 6. Länderspezifische Regeln
        country_issues = self._check_country_rules(description)
        warnings.extend(country_issues)

        passed = len(issues) == 0
        block_upload = not passed and self.rules.get("metadata", {}).get("block_upload_on_violation", True)

        result = {
            "passed": passed,
            "issues": issues,
            "warnings": warnings,
            "block_upload": block_upload,
            "disclaimer_present": self._has_all_disclaimers(full_text),
            "total_checks": len(issues) + len(warnings),
        }

        if self.rules.get("metadata", {}).get("log_violations", True):
            for issue in issues:
                logger.warning(f"COMPLIANCE ISSUE: {issue}")
            for warn in warnings:
                logger.info(f"COMPLIANCE WARN: {warn}")

        if passed:
            logger.info(f"✅ Compliance-Check bestanden ({len(warnings)} Warnungen)")
        else:
            logger.warning(f"❌ Compliance-Check FEHLGESCHLAGEN: {len(issues)} Issues, {len(warnings)} Warnungen")

        return result

    # ── Fix Script ───────────────────────────────────────────────

    def fix_script(self, script: dict, compliance_result: dict) -> dict:
        """Repariert automatisch alle gefundenen Probleme."""
        logger.info("🔧 Repariere Compliance-Probleme...")

        # 1. Disclaimers einfügen wenn fehlend
        disclaimer_text = self._build_full_disclaimer()

        # Script / Outro
        if not self._text_has_disclaimer(script.get("full_text", "")):
            script["outro"] = f"{script.get('outro', '')}\n\n⚠️ DISCLAIMER:\n{disclaimer_text}"
            script["full_text"] = f"{script.get('full_text', '')}\n\n{disclaimer_text}"
            logger.info("   ✓ Disclaimer zum Script hinzugefügt")

        # Beschreibung – immer separat prüfen
        desc = script.get("description", "")
        if not self._text_has_disclaimer(desc):
            desc = f"{desc}\n\n⚠️ {disclaimer_text}"
            logger.info("   ✓ Disclaimer zur Beschreibung hinzugefügt")

        # KI-Disclaimer in Beschreibung
        ai_disc = self.rules.get("disclaimers", {}).get("ai_generated_disclaimer", "")
        if ai_disc and "ki" not in desc.lower() and "ai" not in desc.lower():
            desc = f"{desc}\n🤖 {ai_disc}"
            logger.info("   ✓ KI-Disclaimer zur Beschreibung hinzugefügt")

        script["description"] = desc

        # 2. Verbotene Wörter ersetzen
        replacements = self.rules.get("forbidden_words", {}).get("replacements", {})
        for old, new in replacements.items():
            if old.lower() in script["full_text"].lower():
                script["full_text"] = re.sub(re.escape(old), new, script["full_text"], flags=re.IGNORECASE)
                logger.info(f"   ✓ Ersetzt: '{old}' → '{new}'")

        # 3. Hard-Block Wörter entfernen
        hard_blocks = self.rules.get("forbidden_words", {}).get("hard_block", [])
        for phrase in hard_blocks:
            if phrase.lower() in script["full_text"].lower():
                script["full_text"] = re.sub(re.escape(phrase), "[entfernt]", script["full_text"], flags=re.IGNORECASE)
                logger.info(f"   ✓ Entfernt: '{phrase}'")

        # 4. Impressum in Beschreibung wenn nötig
        germany = self.rules.get("country_specific", {}).get("germany", {})
        if germany.get("impressum_required", False):
            impressum = germany.get("impressum_text", "")
            if impressum and "impressum" not in script.get("description", "").lower():
                script["description"] = f"{script['description']}\n\n📋 Impressum:\n{impressum}"
                logger.info("   ✓ Impressum hinzugefügt")

        # 5. Titel kürzen wenn zu lang
        max_len = self.rules.get("youtube_compliance", {}).get("title_rules", {}).get("max_length", 100)
        if len(script.get("title", "")) > max_len:
            script["title"] = script["title"][:max_len-3] + "..."
            logger.info(f"   ✓ Titel gekürzt auf {max_len} Zeichen")

        return script

    # ── Regel-Builder für Scriptwriter ───────────────────────────

    def get_rules_for_prompt(self) -> str:
        """
        Gibt alle Regeln als Text zurück, der direkt in den GPT-Prompt
        für den Scriptwriter eingefügt wird.
        """
        parts = []

        # Pflicht-Regeln
        mandatory = self.rules.get("script_rules", {}).get("mandatory_rules", [])
        if mandatory:
            parts.append("⚠️ PFLICHT-REGELN (MÜSSEN befolgt werden):")
            for i, rule in enumerate(mandatory, 1):
                parts.append(f"  {i}. {rule}")

        # Stil-Regeln
        style = self.rules.get("script_rules", {}).get("style_rules", [])
        if style:
            parts.append("\n📝 STIL-REGELN:")
            for rule in style:
                parts.append(f"  - {rule}")

        # Custom-Regeln
        custom = self.rules.get("script_rules", {}).get("custom_rules", [])
        real_custom = [r for r in custom if "eigene Regeln" not in r.lower()]
        if real_custom:
            parts.append("\n🔧 ZUSÄTZLICHE REGELN:")
            for rule in real_custom:
                parts.append(f"  - {rule}")

        # Verbotene Wörter
        blocked = self.rules.get("forbidden_words", {}).get("hard_block", [])
        if blocked:
            parts.append(f"\n🚫 VERBOTENE BEGRIFFE (NIEMALS verwenden):")
            parts.append(f"  {', '.join(blocked[:15])}")

        # Disclaimer
        disclaimer = self._build_full_disclaimer()
        if disclaimer:
            parts.append(f"\n⚠️ DISCLAIMER (PFLICHT am Ende des Scripts):")
            parts.append(f"  \"{disclaimer}\"")

        return "\n".join(parts) if parts else ""

    # ── Disclaimer-Check ─────────────────────────────────────────

    def _check_disclaimers(self, full_text: str, description: str) -> list:
        issues = []
        active = self.rules.get("disclaimers", {}).get("active_disclaimers", [])

        # Prüft alle aktiven Disclaimer (finance_disclaimer UND entertainment_disclaimer)
        disclaimer_keys = {"finance_disclaimer", "entertainment_disclaimer"}
        if disclaimer_keys & set(active):
            if not self._text_has_disclaimer(full_text):
                issues.append("PFLICHT: Disclaimer fehlt im Script")
            if not self._text_has_disclaimer(description):
                issues.append("PFLICHT: Disclaimer fehlt in der Beschreibung")

        if "ai_generated_disclaimer" in active:
            ai_disc = self.rules.get("disclaimers", {}).get("ai_generated_disclaimer", "")
            if ai_disc and "ki" not in description.lower() and "ai" not in description.lower():
                issues.append("KI-Disclaimer fehlt in der Beschreibung")

        return issues

    def _has_all_disclaimers(self, text: str) -> bool:
        return self._text_has_disclaimer(text)

    def _text_has_disclaimer(self, text: str) -> bool:
        t = text.lower()
        keywords = [
            # Finance
            "keine finanzberatung", "keine anlageberatung", "bildungszweck",
            "nicht als finanzberatung", "informationszweck",
            # Entertainment / Storytelling
            "unterhaltungs- und bildungszweck", "unterhaltungszweck",
            "bildungs- und unterhaltungszweck", "nur zu unterhaltung",
            # Universal
            "disclaimer", "haftungsausschluss",
        ]
        return any(kw in t for kw in keywords)

    def _build_full_disclaimer(self) -> str:
        disclaimers = self.rules.get("disclaimers", {})
        active = disclaimers.get("active_disclaimers", [])
        parts = []
        for key in active:
            text = disclaimers.get(key, "")
            if text and not text.startswith("_"):
                parts.append(text)
        return " ".join(parts) if parts else "Dies ist keine Finanzberatung."

    # ── Verbotene Wörter ─────────────────────────────────────────

    def _check_forbidden_words(self, text: str) -> list:
        issues = []
        text_lower = text.lower()

        hard_blocks = self.rules.get("forbidden_words", {}).get("hard_block", [])
        for phrase in hard_blocks:
            if phrase.lower() in text_lower:
                issues.append(f"Verbotener Begriff gefunden: '{phrase}'")

        return issues

    # ── Titel-Regeln ─────────────────────────────────────────────

    def _check_title_rules(self, title: str) -> list:
        warnings = []
        rules = self.rules.get("youtube_compliance", {}).get("title_rules", {})

        max_len = rules.get("max_length", 100)
        if len(title) > max_len:
            warnings.append(f"Titel zu lang: {len(title)}/{max_len} Zeichen")

        max_caps = rules.get("max_caps_percent", 50)
        if title:
            caps_pct = sum(1 for c in title if c.isupper()) / max(len(title), 1) * 100
            if caps_pct > max_caps:
                warnings.append(f"Zu viele Großbuchstaben im Titel: {caps_pct:.0f}% (max {max_caps}%)")

        forbidden = rules.get("forbidden_in_title", [])
        for word in forbidden:
            if word.lower() in title.lower():
                warnings.append(f"Verbotenes Wort im Titel: '{word}'")

        return warnings

    # ── Beschreibungs-Regeln ─────────────────────────────────────

    def _check_description_rules(self, description: str) -> list:
        warnings = []
        rules = self.rules.get("youtube_compliance", {}).get("description_rules", {})

        max_hashtags = rules.get("max_hashtags", 15)
        hashtag_count = description.count("#")
        if hashtag_count > max_hashtags:
            warnings.append(f"Zu viele Hashtags: {hashtag_count}/{max_hashtags}")

        max_links = rules.get("max_links", 10)
        link_count = len(re.findall(r'https?://', description))
        if link_count > max_links:
            warnings.append(f"Zu viele Links: {link_count}/{max_links}")

        return warnings

    # ── Länderspezifisch ─────────────────────────────────────────

    def _check_country_rules(self, description: str) -> list:
        warnings = []
        germany = self.rules.get("country_specific", {}).get("germany", {})

        if germany.get("impressum_required", False):
            impressum = germany.get("impressum_text", "")
            if impressum and "HIER EINFÜGEN" in impressum:
                warnings.append("Impressum noch nicht ausgefüllt (config/legal_rules.json → country_specific → germany → impressum_text)")

        return warnings

    # ── KI-basierter Deep Check ──────────────────────────────────

    def _ai_deep_check(self, text: str, title: str) -> list:
        """GPT prüft auf subtile Compliance-Probleme."""
        rules_text = self.get_rules_for_prompt()
        content_flags = self.rules.get("youtube_compliance", {}).get("content_flags", [])
        flags_str = "\n".join(f"- {f}" for f in content_flags) if content_flags else ""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Du bist ein YouTube-Content-Policy und Finanzrecht-Experte."},
                    {"role": "user", "content": f"""
Prüfe diesen YouTube-Finance-Content streng auf Verstöße.

TITEL: {title[:100]}

SCRIPT (Auszug):
{text[:2500]}

REGELN DIE GELTEN:
{rules_text[:1500]}

ZUSÄTZLICHE CONTENT-FLAGS:
{flags_str}

Prüfe auf:
1. Irreführende Finanzversprechen
2. YouTube-Monetarisierungs-Risiken
3. Rechtliche Probleme (DE/EU)
4. Clickbait das nicht zum Inhalt passt
5. Verstöße gegen die oben genannten Regeln

NUR echte Probleme melden. JSON-Antwort:
{{"issues": ["Problem 1", "Problem 2"]}}
Keine Probleme? {{"issues": []}}
"""}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("issues", [])
        except Exception as e:
            logger.debug(f"KI-Compliance-Check fehlgeschlagen: {e}")
            return []
