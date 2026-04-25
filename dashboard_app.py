#!/usr/bin/env python3
"""
YouTube Automation v2.1 – Desktop Dashboard (Vollversion)
Modernes Desktop-Fenster mit Ideen-Manager, Style-Picker und Stimmen-Auswahl.
"""

import os, sys, json, threading, subprocess, time, re
from datetime import datetime as _dt, timedelta as _td
from pathlib import Path
from datetime import datetime

# ── Auto-Install ─────────────────────────────────────────────────
try:
    import customtkinter as ctk
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter", "--break-system-packages"],
                   capture_output=True)
    import customtkinter as ctk

# ── Konstanten ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

C = {  # Farben – Studio Light Theme
    "bg":           "#F1F5F9",   # slate-100 Hintergrund
    "bg2":          "#FFFFFF",   # Sidebar / Header (weiß)
    "card":         "#FFFFFF",   # Karten-Hintergrund
    "card_hover":   "#F8FAFC",   # Karten-Hover
    "accent":       "#6366F1",   # Indigo – Hauptfarbe
    "accent_h":     "#4F46E5",   # Indigo dunkel – Hover
    "gold":         "#D97706",   # Amber
    "green":        "#059669",   # Emerald
    "red":          "#DC2626",   # Rot
    "orange":       "#EA580C",   # Orange
    "purple":       "#7C3AED",   # Violett
    "cyan":         "#0284C7",   # Sky-Blau
    "text":         "#0F172A",   # slate-900 – Haupttext
    "muted":        "#64748B",   # slate-500 – Nebentext
    "border":       "#E2E8F0",   # slate-200 – Rahmen
    "input":        "#F8FAFC",   # Input-Hintergrund
    "step_done":    "#059669",
    "step_run":     "#6366F1",
    "step_wait":    "#CBD5E1",   # slate-300
    "active_bg":    "#EEF2FF",   # Indigo-50 – aktiver Sidebar-Eintrag
}

PIPELINE = [
    ("📖", "Recherche",   "researcher.py",    "Story-Topics finden"),
    ("✍️",  "Script",     "scriptwriter.py",  "Story-Script mit GPT-4o"),
    ("✅",  "Compliance", "compliance.py",    "Richtlinien-Check"),
    ("🎙️", "Voiceover",  "voiceover.py",     "Erzähler-Stimme generieren"),
    ("🖼️", "Thumbnail",  "thumbnail.py",     "Vorschaubild erstellen"),
    ("🎬",  "Video",      "video_creator.py", "Video zusammenstellen"),
    ("🚀",  "Upload",     "uploader.py",      "YouTube hochladen"),
]

# ── Animations-Stile ────────────────────────────────────────────
ANIMATION_STYLES = {
    "minimal": {
        "name": "Minimal / Clean",
        "desc": "Schwarzer Hintergrund, weißer Text.\nKlare Kapitel-Titel, keine Ablenkung.\nPerfekt für seriöse Dokumentationen.",
        "preview": "⬛  Text pur auf dunklem Hintergrund",
        "bg_color": [10, 10, 20],
        "font_size": 60,
        "text_color": "white",
        "accent_color": "#FFFFFF",
    },
    "story_amber": {
        "name": "Story Amber",
        "desc": "Warmes Amber auf Dunkel – wie ein altes Buch.\nPerfekt für Geschichte und Biographien.\nErzeugt nostalgische Atmosphäre.",
        "preview": "🟠  Amber-Text auf warmem Dunkel",
        "bg_color": [15, 10, 5],
        "font_size": 58,
        "text_color": "#F59E0B",
        "accent_color": "#D97706",
    },
    "premium_gold": {
        "name": "Premium Gold",
        "desc": "Dunkler Hintergrund mit goldenen Akzenten.\nWertiger, epischer Look.\nIdeal für Biographien und Drama.",
        "preview": "🟡  Gold-Text auf dunklem Blau",
        "bg_color": [10, 10, 30],
        "font_size": 62,
        "text_color": "#FFD700",
        "accent_color": "#FFD700",
    },
    "neon_blue": {
        "name": "Neon Blue",
        "desc": "Leuchtende blaue Akzente.\nModerner Sci-Fi-Look.\nFür Tech, Science und Mystery.",
        "preview": "🔵  Neon-Blau auf Dunkel",
        "bg_color": [5, 5, 20],
        "font_size": 58,
        "text_color": "#60A5FA",
        "accent_color": "#3B82F6",
    },
    "brainrot": {
        "name": "Brainrot / Chaos",
        "desc": "Knallige Farben, maximaler Chaos-Look.\nPerfekt für Brainrot und Comedy-Content.\nHält ADHS-Zuschauer bei der Stange.",
        "preview": "🌈  Bunt, laut, überwältigend!",
        "bg_color": [5, 0, 15],
        "font_size": 64,
        "text_color": "#FF6BFF",
        "accent_color": "#A855F7",
    },
}

# ── Stimmen-Bibliothek ──────────────────────────────────────────
VOICES = {
    "54a5170264694bfc8e9ad98df7bd89c3": {
        "name": "Erzähler DE (Männlich)",
        "lang": "🇩🇪 Deutsch",
        "desc": "Klare, professionelle Stimme.\nIdeal für Dokumentationen und Geschichte.",
        "gender": "♂",
        "style": "Sachlich",
    },
    "d7a641feef2e46b4aece4d7d04f009e9": {
        "name": "Dramatisch DE (Männlich)",
        "lang": "🇩🇪 Deutsch",
        "desc": "Dynamisch und dramatisch.\nIdeal für spannungsgeladene Storys.",
        "gender": "♂",
        "style": "Energisch",
    },
    "a0e99c3ad8a04e1fb3e0d84d2a27b430": {
        "name": "Sanft DE (Weiblich)",
        "lang": "🇩🇪 Deutsch",
        "desc": "Sanfte, vertrauenswürdige Stimme.\nGut für Biographien und Feelgood-Storys.",
        "gender": "♀",
        "style": "Ruhig",
    },
    "7f92f8afb8ec43bf81429cc1c9199cb1": {
        "name": "Narrator EN (Male)",
        "lang": "🇬🇧 English",
        "desc": "Professional, clear voice.\nGreat for documentary narration.",
        "gender": "♂",
        "style": "Professional",
    },
    "e58b0d7efca34b2a9cf07b3e0eaaec3c": {
        "name": "Epic EN (Male)",
        "lang": "🇬🇧 English",
        "desc": "Deep, authoritative voice.\nPerfect for history and epic stories.",
        "gender": "♂",
        "style": "Authoritative",
    },
    "CUSTOM": {
        "name": "🔧 Eigene Voice-ID",
        "lang": "Beliebig",
        "desc": "Gib deine eigene Fish Audio\nVoice-ID ein.",
        "gender": "-",
        "style": "Custom",
    },
}


# ═════════════════════════════════════════════════════════════════
#  HAUPTFENSTER
# ═════════════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=C["bg"])
        self.title("ContentStudio Pro – Video Automation")
        self.geometry("1400x880")
        self.minsize(1100, 720)

        self.running = False
        self.process = None
        self.ideas = self._load_ideas()
        self.settings = self._load_settings()

        self._build()
        self.after(500, self._refresh_all)

    # ── Settings / Ideas laden ───────────────────────────────────

    def _load_settings(self) -> dict:
        try:
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / ".env")
        except ImportError:
            pass
        f = BASE_DIR / "config" / "settings.json"
        if f.exists():
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    s = json.load(fp)
                import os
                s.setdefault("api_keys", {})
                s["api_keys"]["openai"]     = os.environ.get("OPENAI_API_KEY", s["api_keys"].get("openai", ""))
                s["api_keys"]["fish_audio"] = os.environ.get("FISH_AUDIO_API_KEY", s["api_keys"].get("fish_audio", ""))
                return s
            except Exception as e:
                print(f"[WARNUNG] settings.json fehlerhaft: {e}")
        return {}

    def _save_settings(self):
        f = BASE_DIR / "config" / "settings.json"
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(self.settings, fp, ensure_ascii=False, indent=2)

    def _load_ideas(self) -> list:
        f = BASE_DIR / "config" / "ideas.json"
        if f.exists():
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp)
        return []

    def _save_ideas(self):
        f = BASE_DIR / "config" / "ideas.json"
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(self.ideas, fp, ensure_ascii=False, indent=2)

    def _load_channels(self) -> list:
        d = BASE_DIR / "channels"
        chs = []
        if not d.exists():
            return []
        for p in sorted(d.iterdir()):
            cfg = p / "channel_config.json"
            if p.is_dir() and cfg.exists():
                try:
                    with open(cfg, "r", encoding="utf-8") as f:
                        c = json.load(f)
                    c["_id"] = p.name
                    c["_token"] = (p / "token.json").exists()
                    # Check if real secret (not placeholder)
                    secret_f = p / "youtube_client_secret.json"
                    c["_secret"] = False
                    if secret_f.exists():
                        raw = secret_f.read_text()
                        c["_secret"] = "DEINE_CLIENT_ID" not in raw
                    chs.append(c)
                except Exception:
                    pass
        return chs

    # ── UI Build ─────────────────────────────────────────────────

    def _build(self):
        # ── Header ───────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=C["bg2"], height=60, corner_radius=0,
                           border_width=1, border_color=C["border"])
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Brand
        brand = ctk.CTkFrame(hdr, fg_color="transparent")
        brand.pack(side="left", padx=20)
        ctk.CTkLabel(brand, text="◆",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=C["accent"]).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(brand, text="ContentStudio",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(brand, text=" Pro",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C["accent"]).pack(side="left")

        # Status rechts
        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.pack(side="right", padx=20)
        self.status_dot = ctk.CTkLabel(right, text="● Bereit",
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       text_color=C["green"])
        self.status_dot.pack(side="right", padx=(12, 0))
        ctk.CTkLabel(right, text="v2.1",
                     font=ctk.CTkFont(size=11),
                     text_color=C["muted"]).pack(side="right")

        # ── Sidebar + Content ────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Sidebar
        sidebar = ctk.CTkFrame(body, fg_color=C["bg2"], width=220, corner_radius=0,
                               border_width=1, border_color=C["border"])
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        self.pages = {}
        self.nav_btns = {}

        # Sidebar Abschnitt-Label
        def _section(parent, title: str):
            ctk.CTkLabel(parent, text=title.upper(),
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color=C["muted"]).pack(anchor="w", padx=16, pady=(14, 2))

        _section(sidebar, "Produktion")
        for icon, label in [("🏠", "Dashboard"), ("💡", "Ideen"),
                             ("✨", "Vorschläge"), ("📹", "Videos"), ("📊", "Ergebnisse")]:
            btn = ctk.CTkButton(
                sidebar, text=f"  {icon}   {label}",
                font=ctk.CTkFont(size=13), height=40,
                fg_color="transparent", text_color=C["muted"],
                hover_color=C["active_bg"], anchor="w",
                corner_radius=6,
                command=lambda l=label: self._switch_page(l)
            )
            btn.pack(fill="x", padx=8, pady=1)
            self.nav_btns[label] = btn

        _section(sidebar, "Planung")
        for icon, label in [("📅", "Planer"), ("📖", "Story-Planer")]:
            btn = ctk.CTkButton(
                sidebar, text=f"  {icon}   {label}",
                font=ctk.CTkFont(size=13), height=40,
                fg_color="transparent", text_color=C["muted"],
                hover_color=C["active_bg"], anchor="w",
                corner_radius=6,
                command=lambda l=label: self._switch_page(l)
            )
            btn.pack(fill="x", padx=8, pady=1)
            self.nav_btns[label] = btn

        _section(sidebar, "Einstellungen")
        for icon, label in [("🎨", "Design"), ("🎙️", "Stimmen"), ("🎭", "Charaktere"),
                             ("⚖️", "Regeln"), ("📺", "Kanäle"), ("📋", "Log")]:
            btn = ctk.CTkButton(
                sidebar, text=f"  {icon}   {label}",
                font=ctk.CTkFont(size=13), height=40,
                fg_color="transparent", text_color=C["muted"],
                hover_color=C["active_bg"], anchor="w",
                corner_radius=6,
                command=lambda l=label: self._switch_page(l)
            )
            btn.pack(fill="x", padx=8, pady=1)
            self.nav_btns[label] = btn

        # Version unten
        ctk.CTkFrame(sidebar, fg_color=C["border"], height=1).pack(
            fill="x", side="bottom", pady=(0, 0))
        ctk.CTkLabel(sidebar, text="ContentStudio Pro v2.1",
                     font=ctk.CTkFont(size=10),
                     text_color=C["muted"]).pack(side="bottom", pady=8)

        # Content-Bereich
        self.content = ctk.CTkFrame(body, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")

        self._build_page_dashboard()
        self._build_page_ideas()
        self._build_page_suggestions()
        self._build_page_videos()
        self._build_page_ergebnisse()
        self._build_page_planner()
        self._build_page_story_planer()
        self._build_page_design()
        self._build_page_voices()
        self._build_page_characters()
        self._build_page_rules()
        self._build_page_channels()
        self._build_page_log()

        self._switch_page("Dashboard")

    # ── Navigation ───────────────────────────────────────────────

    def _switch_page(self, name: str):
        for key, frame in self.pages.items():
            frame.pack_forget()
        for key, btn in self.nav_btns.items():
            btn.configure(fg_color="transparent", text_color=C["muted"])
        if name in self.pages:
            self.pages[name].pack(fill="both", expand=True)
        if name in self.nav_btns:
            self.nav_btns[name].configure(fg_color=C["active_bg"], text_color=C["accent"])
        if name == "Kanäle":
            self._render_channels()
        if name == "Ideen":
            self._render_ideas()
        if name == "Videos":
            self._render_videos()
        if name == "Planer":
            self._render_planner()
        if name == "Vorschläge":
            self._render_suggestions()
        if name == "Ergebnisse":
            self._render_ergebnisse()
        if name == "Charaktere":
            self._render_characters()

    # ── Hilfsfunktionen ──────────────────────────────────────────

    def _card(self, parent, title: str = "", expand=False) -> ctk.CTkFrame:
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        if expand:
            wrapper.pack(fill="both", expand=True, pady=(0, 8))
        else:
            wrapper.pack(fill="x", pady=(0, 8))
        if title:
            ctk.CTkLabel(wrapper, text=title,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C["muted"]).pack(anchor="w", pady=(0, 4))
        card = ctk.CTkFrame(wrapper, fg_color=C["card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        card.pack(fill="both", expand=True)
        return card

    def _log(self, text: str, color: str = "text"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] {text}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ═════════════════════════════════════════════════════════════
    # SEITE 1: DASHBOARD
    # ═════════════════════════════════════════════════════════════

    def _build_page_dashboard(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Dashboard"] = page

        # Scroll-Container
        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Oberer Bereich: Pipeline + Steuerung nebeneinander ───
        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))
        top.columnconfigure(0, weight=3)
        top.columnconfigure(1, weight=2)

        # Pipeline links
        pipe_card = ctk.CTkFrame(top, fg_color=C["card"], corner_radius=10,
                                 border_width=1, border_color=C["border"])
        pipe_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(pipe_card, text="  🔄  Pipeline – 7 Schritte zum fertigen Video",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=16, pady=(14, 8))

        self.step_frames = []
        for i, (icon, name, _, desc) in enumerate(PIPELINE):
            row = ctk.CTkFrame(pipe_card, fg_color=C["card_hover"], corner_radius=8, height=44)
            row.pack(fill="x", padx=12, pady=2)
            row.pack_propagate(False)

            # Nummer-Badge
            badge = ctk.CTkFrame(row, fg_color=C["step_wait"], width=28, height=28,
                                 corner_radius=14)
            badge.pack(side="left", padx=(10, 8))
            badge.pack_propagate(False)
            ctk.CTkLabel(badge, text=str(i+1), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="white").place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(row, text=f"{icon} {name}",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C["text"], width=120, anchor="w").pack(side="left", padx=(0, 4))
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=11),
                         text_color=C["muted"]).pack(side="left")

            self.step_frames.append(badge)

        ctk.CTkLabel(pipe_card, text="").pack(pady=2)  # Spacer

        # Steuerung rechts
        ctrl_card = ctk.CTkFrame(top, fg_color=C["card"], corner_radius=10,
                                 border_width=1, border_color=C["border"])
        ctrl_card.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(ctrl_card, text="  ⚡  Schnellstart",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=16, pady=(14, 8))

        # Kanal-Dropdown
        ctk.CTkLabel(ctrl_card, text="Kanal:", font=ctk.CTkFont(size=11),
                     text_color=C["muted"]).pack(anchor="w", padx=16, pady=(4, 2))
        self.ch_var = ctk.StringVar(value="Alle aktiven Kanäle")
        self.ch_menu = ctk.CTkOptionMenu(ctrl_card, variable=self.ch_var,
                                          values=["Alle aktiven Kanäle"],
                                          fg_color=C["input"], button_color=C["accent"],
                                          dropdown_fg_color=C["card"], width=240,
                                          font=ctk.CTkFont(size=11))
        self.ch_menu.pack(fill="x", padx=16, pady=2)

        # Topic
        ctk.CTkLabel(ctrl_card, text="Topic (leer = automatisch):",
                     font=ctk.CTkFont(size=11),
                     text_color=C["muted"]).pack(anchor="w", padx=16, pady=(8, 2))
        self.topic_var = ctk.CTkEntry(ctrl_card, placeholder_text="z.B. Daytrading für Anfänger",
                                       fg_color=C["input"], border_color=C["border"],
                                       font=ctk.CTkFont(size=11))
        self.topic_var.pack(fill="x", padx=16, pady=2)

        # Dry-Run Switch (Default AN = Kein Auto-Upload, manuell entscheiden)
        self.dry_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(ctrl_card, text="Nur erstellen, NICHT hochladen (empfohlen)",
                      variable=self.dry_var, font=ctk.CTkFont(size=11),
                      text_color=C["text"], button_color=C["accent"],
                      progress_color=C["accent"]).pack(anchor="w", padx=16, pady=(10, 2))
        ctk.CTkLabel(ctrl_card, text="→ Du entscheidest im Videos-Tab manuell, wann hochgeladen wird.",
                     font=ctk.CTkFont(size=10), text_color=C["muted"]).pack(anchor="w", padx=16, pady=(0, 6))

        # Start-Button
        self.run_btn = ctk.CTkButton(
            ctrl_card, text="▶   STARTEN",
            font=ctk.CTkFont(size=15, weight="bold"), height=48,
            fg_color=C["accent"], hover_color=C["accent_h"],
            corner_radius=10, command=self._run_automation
        )
        self.run_btn.pack(fill="x", padx=16, pady=(6, 4))

        self.stop_btn = ctk.CTkButton(
            ctrl_card, text="⏹  Stoppen", height=34,
            font=ctk.CTkFont(size=12),
            fg_color=C["card_hover"], hover_color=C["red"],
            text_color=C["muted"], corner_radius=8,
            command=self._stop_automation
        )
        self.stop_btn.pack(fill="x", padx=16, pady=(0, 6))

        # Quick-Buttons
        qrow = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        qrow.pack(fill="x", padx=16, pady=(4, 12))
        for txt, cmd in [("📂 Output", self._open_output),
                          ("⚙️ Settings", self._open_settings),
                          ("📺 + Kanal", self._open_add_channel)]:
            ctk.CTkButton(qrow, text=txt, font=ctk.CTkFont(size=10),
                          height=28, corner_radius=6, fg_color=C["card_hover"],
                          hover_color=C["border"], text_color=C["text"],
                          command=cmd).pack(side="left", fill="x", expand=True, padx=2)

        # ── Unterer Bereich: Status-Karten ───────────────────────
        stats = ctk.CTkFrame(scroll, fg_color="transparent")
        stats.pack(fill="x", pady=(4, 0))
        for i in range(4):
            stats.columnconfigure(i, weight=1)

        self.stat_cards = {}
        stat_data = [
            ("Kanäle", "0", C["accent"]),
            ("Videos", "0", C["green"]),
            ("OpenAI", "…", C["gold"]),
            ("Fish Audio", "…", C["cyan"]),
        ]
        for i, (label, val, color) in enumerate(stat_data):
            c = ctk.CTkFrame(stats, fg_color=C["card"], corner_radius=10,
                             border_width=1, border_color=C["border"], height=80)
            c.grid(row=0, column=i, sticky="nsew", padx=4, pady=4)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=11),
                         text_color=C["muted"]).pack(anchor="w", padx=14, pady=(12, 0))
            lbl = ctk.CTkLabel(c, text=val, font=ctk.CTkFont(size=22, weight="bold"),
                               text_color=color)
            lbl.pack(anchor="w", padx=14)
            self.stat_cards[label] = lbl

    # ═════════════════════════════════════════════════════════════
    # SEITE 2: IDEEN
    # ═════════════════════════════════════════════════════════════

    def _build_page_ideas(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Ideen"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Eingabe ──────────────────────────────────────────────
        input_card = self._card_in(scroll, "💡  Neue Video-Idee hinzufügen")

        # Titel
        ctk.CTkLabel(input_card, text="Video-Idee / Topic:",
                     font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(
            anchor="w", padx=16, pady=(8, 2))
        self.idea_title = ctk.CTkEntry(input_card,
                                        placeholder_text="z.B. Die 5 besten Daytrading-Strategien 2025",
                                        fg_color=C["input"], border_color=C["border"],
                                        height=36, font=ctk.CTkFont(size=12))
        self.idea_title.pack(fill="x", padx=16, pady=2)

        # Notizen
        ctk.CTkLabel(input_card, text="Notizen / Details (optional):",
                     font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(
            anchor="w", padx=16, pady=(8, 2))
        self.idea_notes = ctk.CTkTextbox(input_card, height=60, fg_color=C["input"],
                                          border_color=C["border"], border_width=1,
                                          font=ctk.CTkFont(size=11), corner_radius=6)
        self.idea_notes.pack(fill="x", padx=16, pady=2)

        # Priorität + Button
        btn_row = ctk.CTkFrame(input_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(6, 12))

        ctk.CTkLabel(btn_row, text="Priorität:", font=ctk.CTkFont(size=11),
                     text_color=C["muted"]).pack(side="left")
        self.idea_prio = ctk.CTkOptionMenu(btn_row, values=["🔴 Hoch", "🟡 Mittel", "🟢 Niedrig"],
                                            fg_color=C["input"], button_color=C["accent"],
                                            dropdown_fg_color=C["card"], width=140,
                                            font=ctk.CTkFont(size=11))
        self.idea_prio.set("🟡 Mittel")
        self.idea_prio.pack(side="left", padx=8)

        ctk.CTkButton(btn_row, text="＋  Idee hinzufügen",
                      font=ctk.CTkFont(size=12, weight="bold"), height=34,
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      corner_radius=8, command=self._add_idea).pack(side="right")

        # ── Ideen-Liste ──────────────────────────────────────────
        ctk.CTkLabel(scroll, text="📋  Ideen-Warteschlange",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["muted"]).pack(anchor="w", pady=(8, 4))

        self.ideas_list = ctk.CTkFrame(scroll, fg_color="transparent")
        self.ideas_list.pack(fill="both", expand=True)

    def _render_ideas(self):
        for w in self.ideas_list.winfo_children():
            w.destroy()

        if not self.ideas:
            ctk.CTkLabel(self.ideas_list, text="Noch keine Ideen – füge oben deine erste hinzu!",
                         font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(pady=30)
            return

        for i, idea in enumerate(self.ideas):
            prio_colors = {"hoch": C["red"], "mittel": C["gold"], "niedrig": C["green"]}
            prio = idea.get("priority", "mittel").lower()
            for key in prio_colors:
                if key in prio:
                    prio = key
                    break

            row = ctk.CTkFrame(self.ideas_list, fg_color=C["card"], corner_radius=8,
                               border_width=1, border_color=C["border"])
            row.pack(fill="x", pady=3)

            # Farbbalken links
            bar = ctk.CTkFrame(row, fg_color=prio_colors.get(prio, C["gold"]),
                               width=4, corner_radius=0)
            bar.pack(side="left", fill="y")

            # Content
            mid = ctk.CTkFrame(row, fg_color="transparent")
            mid.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            title_row = ctk.CTkFrame(mid, fg_color="transparent")
            title_row.pack(fill="x")

            ctk.CTkLabel(title_row, text=idea.get("title", "?"),
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=C["text"]).pack(side="left")

            status = idea.get("status", "offen")
            st_color = C["green"] if status == "fertig" else (
                C["accent"] if status == "läuft" else C["muted"])
            ctk.CTkLabel(title_row, text=f"  [{status.upper()}]",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=st_color).pack(side="left", padx=4)

            if idea.get("notes"):
                ctk.CTkLabel(mid, text=idea["notes"][:100],
                             font=ctk.CTkFont(size=11), text_color=C["muted"],
                             anchor="w").pack(anchor="w")

            if idea.get("created"):
                ctk.CTkLabel(mid, text=f"Erstellt: {idea['created']}",
                             font=ctk.CTkFont(size=9), text_color=C["border"]).pack(anchor="w")

            # Buttons rechts
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=8)

            ctk.CTkButton(btns, text="▶", width=32, height=32,
                          font=ctk.CTkFont(size=14), corner_radius=6,
                          fg_color=C["accent"], hover_color=C["accent_h"],
                          command=lambda t=idea["title"]: self._run_idea(t)).pack(pady=2)
            ctk.CTkButton(btns, text="🗑️", width=32, height=32,
                          font=ctk.CTkFont(size=12), corner_radius=6,
                          fg_color=C["card_hover"], hover_color=C["red"],
                          command=lambda idx=i: self._delete_idea(idx)).pack(pady=2)

    def _add_idea(self):
        title = self.idea_title.get().strip()
        if not title:
            return
        notes = self.idea_notes.get("1.0", "end").strip()
        self.ideas.append({
            "title": title,
            "notes": notes,
            "priority": self.idea_prio.get(),
            "status": "offen",
            "created": datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        self._save_ideas()
        self.idea_title.delete(0, "end")
        self.idea_notes.delete("1.0", "end")
        self._render_ideas()
        self._log(f"💡 Neue Idee: {title}")

    def _delete_idea(self, idx: int):
        if 0 <= idx < len(self.ideas):
            removed = self.ideas.pop(idx)
            self._save_ideas()
            self._render_ideas()
            self._log(f"🗑️ Idee gelöscht: {removed.get('title')}")

    def _run_idea(self, topic: str):
        self.topic_var.delete(0, "end")
        self.topic_var.insert(0, topic)
        # Update Status
        for idea in self.ideas:
            if idea["title"] == topic:
                idea["status"] = "läuft"
        self._save_ideas()
        self._switch_page("Dashboard")
        self.after(300, self._run_automation)

    # ═════════════════════════════════════════════════════════════
    # SEITE: VORSCHLÄGE – KI-generierte Video-Ideen
    # ═════════════════════════════════════════════════════════════

    def _build_page_suggestions(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Vorschläge"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text="✨  Aktuelle Video-Vorschläge",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(scroll, text="KI generiert passende Themen basierend auf deiner gewählten Nische.",
                     font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(anchor="w", pady=(0, 10))

        # Nischen-Auswahl
        n_card = self._card_in(scroll, "🎯  Nische / Themenbereich")
        nrow = ctk.CTkFrame(n_card, fg_color="transparent")
        nrow.pack(fill="x", padx=16, pady=10)

        self.sugg_niche_var = ctk.StringVar(value=self.settings.get("channel", {}).get("niche", "storytelling"))
        ctk.CTkLabel(nrow, text="Nische:", font=ctk.CTkFont(size=12),
                     text_color=C["muted"]).pack(side="left")
        niche_menu = ctk.CTkOptionMenu(nrow, variable=self.sugg_niche_var,
                                       values=[
                                           "storytelling", "history", "biography", "documentary",
                                           "mystery", "crime", "comedy", "brainrot", "science",
                                           "travel", "gaming", "education", "motivation",
                                           "health_fitness", "tech", "ai_tools", "custom",
                                       ],
                                       fg_color=C["input"], button_color=C["accent"],
                                       dropdown_fg_color=C["card"], width=220,
                                       font=ctk.CTkFont(size=11))
        niche_menu.pack(side="left", padx=8)

        ctk.CTkLabel(nrow, text="Eigenes Thema:",
                     font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(side="left", padx=(16, 4))
        self.sugg_custom = ctk.CTkEntry(nrow, placeholder_text="z.B. Elektroautos, Kochen, ...",
                                         fg_color=C["input"], border_color=C["border"],
                                         width=220, font=ctk.CTkFont(size=11))
        self.sugg_custom.pack(side="left", padx=4)

        # Generate-Button
        self.sugg_btn = ctk.CTkButton(
            n_card, text="✨  10 neue Vorschläge generieren",
            font=ctk.CTkFont(size=13, weight="bold"), height=38,
            fg_color=C["accent"], hover_color=C["accent_h"],
            corner_radius=8, command=self._generate_suggestions
        )
        self.sugg_btn.pack(fill="x", padx=16, pady=(0, 12))

        # Ergebnis-Bereich
        ctk.CTkLabel(scroll, text="📋  Aktuelle Vorschläge",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["muted"]).pack(anchor="w", pady=(8, 4))

        self.sugg_list = ctk.CTkFrame(scroll, fg_color="transparent")
        self.sugg_list.pack(fill="both", expand=True)

    def _load_suggestions(self) -> list:
        f = BASE_DIR / "config" / "suggestions.json"
        if f.exists():
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    return json.load(fp)
            except Exception:
                pass
        return []

    def _save_suggestions(self, items: list):
        f = BASE_DIR / "config" / "suggestions.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(items, fp, ensure_ascii=False, indent=2)

    def _render_suggestions(self):
        for w in self.sugg_list.winfo_children():
            w.destroy()
        items = self._load_suggestions()
        if not items:
            ctk.CTkLabel(self.sugg_list,
                         text='Noch keine Vorschläge. Klicke oben auf "10 neue Vorschläge generieren".',
                         font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(pady=30)
            return
        for i, it in enumerate(items):
            row = ctk.CTkFrame(self.sugg_list, fg_color=C["card"], corner_radius=8,
                               border_width=1, border_color=C["border"])
            row.pack(fill="x", pady=3)
            ctk.CTkFrame(row, fg_color=C["purple"], width=4, corner_radius=0).pack(side="left", fill="y")
            mid = ctk.CTkFrame(row, fg_color="transparent")
            mid.pack(side="left", fill="both", expand=True, padx=12, pady=8)
            ctk.CTkLabel(mid, text=it.get("title", "?"),
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=C["text"], anchor="w", justify="left").pack(anchor="w")
            if it.get("desc"):
                ctk.CTkLabel(mid, text=it["desc"], font=ctk.CTkFont(size=10),
                             text_color=C["muted"], anchor="w", justify="left",
                             wraplength=700).pack(anchor="w")
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=8)
            ctk.CTkButton(btns, text="➕ Zu Ideen", width=90, height=26,
                          font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4,
                          fg_color=C["card_hover"], hover_color=C["accent"],
                          text_color=C["text"],
                          command=lambda t=it.get("title", ""), d=it.get("desc", ""):
                          self._suggestion_to_idea(t, d)).pack(pady=1)
            ctk.CTkButton(btns, text="▶ Erstellen", width=90, height=26,
                          font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4,
                          fg_color=C["green"], hover_color="#059669",
                          text_color="white",
                          command=lambda t=it.get("title", ""): self._run_idea(t)).pack(pady=1)
            ctk.CTkButton(btns, text="🗑️", width=28, height=26,
                          font=ctk.CTkFont(size=11), corner_radius=4,
                          fg_color=C["card_hover"], hover_color=C["red"],
                          text_color=C["text"],
                          command=lambda idx=i: self._delete_suggestion(idx)).pack(pady=1)

    def _delete_suggestion(self, idx: int):
        items = self._load_suggestions()
        if 0 <= idx < len(items):
            items.pop(idx)
            self._save_suggestions(items)
            self._render_suggestions()

    def _suggestion_to_idea(self, title: str, desc: str = ""):
        if not title:
            return
        self.ideas.append({
            "title": title, "notes": desc,
            "priority": "🟡 Mittel", "status": "offen",
            "created": datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        self._save_ideas()
        self._log(f"➕ Vorschlag übernommen: {title}")

    def _generate_suggestions(self):
        if self.running:
            self._log("⚠️ Bitte warten...")
            return
        niche = self.sugg_niche_var.get()
        custom = self.sugg_custom.get().strip()
        topic_area = custom if (niche == "custom" or custom) else niche
        self.sugg_btn.configure(state="disabled", text="⏳ Generiere Vorschläge...")
        self._set_running(True)

        def do_gen():
            suggestions = []
            try:
                api_key = self.settings.get("api_keys", {}).get("openai", "")
                if not api_key:
                    raise RuntimeError("Kein OpenAI-API-Key in Settings")
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    prompt = (
                        f"Generiere 10 aktuelle, klickstarke YouTube-Video-Ideen zum Thema '{topic_area}' "
                        f"auf Deutsch. Gib für jede Idee einen knackigen Titel (max. 70 Zeichen) "
                        f"und eine 1-Satz-Beschreibung. "
                        f"Antwort STRIKT als JSON-Array: "
                        f"[{{\"title\":\"...\",\"desc\":\"...\"}}, ...] – kein weiterer Text."
                    )
                    resp = client.chat.completions.create(
                        model=self.settings.get("openai", {}).get("research_model", "gpt-4o-mini"),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.9, max_tokens=1200,
                    )
                    text = resp.choices[0].message.content.strip()
                    # JSON extrahieren
                    start = text.find("[")
                    end = text.rfind("]")
                    if start >= 0 and end > start:
                        suggestions = json.loads(text[start:end+1])
                except Exception as e:
                    self.after(0, lambda: self._log(f"⚠️ KI-Fehler: {e}"))
                    # Fallback: lokale Vorschläge
                    suggestions = [{"title": f"Idee {i+1} zu {topic_area}", "desc": ""} for i in range(10)]

                self._save_suggestions(suggestions)
                self.after(0, lambda: self._log(f"✨ {len(suggestions)} Vorschläge generiert"))
                self.after(0, self._render_suggestions)
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ {e}"))
            finally:
                self.after(0, lambda: self._set_running(False))
                self.after(0, lambda: self.sugg_btn.configure(
                    state="normal", text="✨  10 neue Vorschläge generieren"))

        threading.Thread(target=do_gen, daemon=True).start()

    # ═════════════════════════════════════════════════════════════
    # SEITE: ERGEBNISSE (alle Videos, neu + alt, vollständig)
    # ═════════════════════════════════════════════════════════════

    def _build_page_ergebnisse(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Ergebnisse"] = page

        # Header-Leiste (fixiert, kein Scroll)
        hdr = ctk.CTkFrame(page, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(hdr, text="📊  Ergebnisse",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        ctk.CTkButton(hdr, text="🔄 Aktualisieren", width=130, height=30,
                      font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6,
                      fg_color=C["card_hover"], hover_color=C["accent"],
                      text_color=C["text"],
                      command=self._render_ergebnisse).pack(side="right")

        # Filter-Buttons
        filt_row = ctk.CTkFrame(hdr, fg_color="transparent")
        filt_row.pack(side="right", padx=12)
        self.erg_filter = ctk.StringVar(value="alle")
        for label, val, color in [
            ("Alle", "alle", C["text"]),
            ("✅ Erfolg", "success", C["green"]),
            ("❌ Fehler", "error", C["red"]),
            ("🔗 Online", "uploaded", C["accent"]),
        ]:
            ctk.CTkButton(filt_row, text=label, width=80, height=28,
                          font=ctk.CTkFont(size=10), corner_radius=6,
                          fg_color=C["card"], hover_color=C["card_hover"],
                          text_color=color,
                          command=lambda v=val: self._erg_set_filter(v)).pack(side="left", padx=2)

        # Stats-Zeile
        self.erg_stats_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.erg_stats_frame.pack(fill="x", padx=16, pady=(0, 8))

        # Scrollbare Liste
        self.erg_scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.erg_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    def _load_all_results(self) -> list:
        """
        Scannt alle output/**/result.json und channels/**/output/**/result.json.
        Ergänzt mit video_history.json. Dedupliziert nach timestamp.
        Gibt Liste sortiert nach timestamp (neueste zuerst) zurück.
        """
        seen = {}

        # Alle result.json-Dateien aus output/ und channels/
        for pattern in ["output/**/result.json", "channels/**/result.json"]:
            for rfile in sorted(BASE_DIR.glob(pattern)):
                try:
                    with open(rfile, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    ts = data.get("timestamp", str(rfile))
                    if ts not in seen:
                        data["_source"] = str(rfile.parent)
                        seen[ts] = data
                except Exception:
                    pass

        # video_history.json als Ergänzung (fügt upload_status hinzu)
        hist_map = {}
        for h in self._load_video_history():
            hist_map[h.get("timestamp", "")] = h

        for ts, entry in seen.items():
            if ts in hist_map:
                h = hist_map[ts]
                entry.setdefault("upload_status", h.get("upload_status", "local"))
                entry.setdefault("youtube_url", h.get("youtube_url"))
                entry.setdefault("channel", h.get("channel", "Standard"))
                entry.setdefault("scheduled_date", h.get("scheduled_date"))

        results = sorted(seen.values(), key=lambda x: x.get("timestamp", ""), reverse=True)
        return results

    def _erg_set_filter(self, val: str):
        self.erg_filter.set(val)
        self._render_ergebnisse()

    def _render_ergebnisse(self):
        # Stats-Frame leeren
        for w in self.erg_stats_frame.winfo_children():
            w.destroy()
        # Liste leeren
        for w in self.erg_scroll.winfo_children():
            w.destroy()

        all_results = self._load_all_results()
        filt = self.erg_filter.get()

        # Stats berechnen
        total   = len(all_results)
        success = sum(1 for r in all_results if r.get("status") == "success")
        errors  = sum(1 for r in all_results if r.get("status") == "error")
        online  = sum(1 for r in all_results if r.get("youtube_url"))

        for i in range(4):
            self.erg_stats_frame.columnconfigure(i, weight=1)
        for i, (val, label, color) in enumerate([
            (f"📊 {total}",   "Gesamt",      C["text"]),
            (f"✅ {success}", "Erfolgreich", C["green"]),
            (f"❌ {errors}",  "Fehler",      C["red"]),
            (f"🔗 {online}",  "Online",      C["accent"]),
        ]):
            c = ctk.CTkFrame(self.erg_stats_frame, fg_color=C["card"], corner_radius=8, height=54)
            c.grid(row=0, column=i, sticky="nsew", padx=3, pady=(0, 8))
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=val, font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=color).pack(side="left", padx=14, expand=True)
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=10),
                         text_color=C["muted"]).pack(side="left", expand=True)

        # Filtern
        filtered = all_results
        if filt == "success":
            filtered = [r for r in all_results if r.get("status") == "success"]
        elif filt == "error":
            filtered = [r for r in all_results if r.get("status") == "error"]
        elif filt == "uploaded":
            filtered = [r for r in all_results if r.get("youtube_url")]

        if not filtered:
            ctk.CTkLabel(self.erg_scroll,
                         text="Keine Ergebnisse gefunden.\nVideos werden nach der Produktion hier angezeigt.",
                         font=ctk.CTkFont(size=13), text_color=C["muted"],
                         justify="center").pack(pady=50)
            return

        for r in filtered:
            self._render_erg_card(r)

    def _render_erg_card(self, r: dict):
        status      = r.get("status", "unknown")
        upload_st   = r.get("upload_status", "local")
        topic       = r.get("topic") or r.get("title") or "Unbekannt"
        timestamp   = r.get("timestamp", "")
        channel     = r.get("channel", "Standard")
        youtube_url = r.get("youtube_url", "")
        error_msg   = r.get("error", "")
        source_dir  = r.get("_source", "")

        # Farbe nach Status
        if status == "success":
            bar_color = C["green"] if not youtube_url else C["accent"]
        elif status == "error":
            bar_color = C["red"]
        else:
            bar_color = C["muted"]

        card = ctk.CTkFrame(self.erg_scroll, fg_color=C["card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        card.pack(fill="x", pady=4)

        # Linker Farbbalken
        ctk.CTkFrame(card, fg_color=bar_color, width=5, corner_radius=0).pack(
            side="left", fill="y")

        # Haupt-Inhalt
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        # ── Zeile 1: Titel + Status-Badge ────────────────────────
        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x")

        st_label = {
            "success": "✅ Erfolgreich",
            "error":   "❌ Fehler",
            "running": "⏳ Läuft...",
        }.get(status, f"❓ {status}")
        st_color = {
            "success": C["green"],
            "error":   C["red"],
            "running": C["gold"],
        }.get(status, C["muted"])

        ctk.CTkLabel(row1, text=topic,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["text"], anchor="w",
                     wraplength=560).pack(side="left")
        ctk.CTkLabel(row1, text=st_label,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=st_color).pack(side="right")

        # ── Zeile 2: Meta ─────────────────────────────────────────
        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(2, 4))

        # Datum aus timestamp "20260413_210744" → "13.04.2026 21:07"
        ts_display = timestamp
        if len(timestamp) == 15 and "_" in timestamp:
            try:
                dt = _dt.strptime(timestamp, "%Y%m%d_%H%M%S")
                ts_display = dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass

        meta = f"🕐 {ts_display}  •  📺 {channel}"
        ctk.CTkLabel(row2, text=meta, font=ctk.CTkFont(size=10),
                     text_color=C["muted"]).pack(side="left")

        if youtube_url:
            ctk.CTkLabel(row2, text=f"  🔗 {youtube_url}",
                         font=ctk.CTkFont(size=10), text_color=C["accent"]).pack(side="left")

        # ── Zeile 3: Pipeline-Schritt-Badges ──────────────────────
        row3 = ctk.CTkFrame(body, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 4))

        steps = [
            ("Script",     r.get("script_path")),
            ("Audio",      r.get("audio_path")),
            ("Video",      r.get("video_path")),
            ("Thumbnail",  r.get("thumbnail_path")),
            ("YouTube",    r.get("youtube_url")),
        ]
        for step_name, step_val in steps:
            exists = bool(step_val) and (
                step_name == "YouTube" or Path(step_val).exists()
            )
            badge_text = f"✓ {step_name}" if exists else f"✗ {step_name}"
            badge_color = C["green"] if exists else C["card_hover"]
            text_color  = C["text"] if exists else C["muted"]
            ctk.CTkLabel(row3, text=badge_text,
                         font=ctk.CTkFont(size=9, weight="bold"),
                         fg_color=badge_color, text_color=text_color,
                         corner_radius=4, padx=6, pady=2).pack(side="left", padx=2)

        # ── Zeile 4: Fehlermeldung (nur bei error) ────────────────
        if error_msg:
            err_box = ctk.CTkFrame(body, fg_color="#FEF2F2", corner_radius=6,
                                   border_width=1, border_color=C["red"])
            err_box.pack(fill="x", pady=(2, 2))
            ctk.CTkLabel(err_box, text=f"⚠️  {error_msg[:200]}",
                         font=ctk.CTkFont(size=10), text_color=C["red"],
                         anchor="w", justify="left", wraplength=580).pack(
                anchor="w", padx=10, pady=5)

        # ── Rechts: Action-Buttons ────────────────────────────────
        btn_col = ctk.CTkFrame(card, fg_color="transparent")
        btn_col.pack(side="right", padx=10, pady=10)

        def mk_btn(parent, text, color, hover, cmd):
            ctk.CTkButton(parent, text=text, width=100, height=28,
                          font=ctk.CTkFont(size=10, weight="bold"), corner_radius=5,
                          fg_color=color, hover_color=hover, text_color="white",
                          command=cmd).pack(pady=2)

        vid_path = r.get("video_path", "")
        if vid_path and Path(vid_path).exists():
            mk_btn(btn_col, "▶ Video", C["accent"], C["accent_h"],
                   lambda p=vid_path: self._open_file(p))

        script_path = r.get("script_path", "")
        if script_path and Path(script_path).exists():
            mk_btn(btn_col, "📄 Script", C["card_hover"], C["border"],
                   lambda p=script_path: self._open_file(p))

        thumb_path = r.get("thumbnail_path", "")
        if thumb_path and Path(thumb_path).exists():
            mk_btn(btn_col, "🖼️ Thumbnail", C["card_hover"], C["border"],
                   lambda p=thumb_path: self._open_file(p))

        if source_dir and Path(source_dir).exists():
            mk_btn(btn_col, "📂 Ordner", C["card_hover"], C["border"],
                   lambda p=source_dir: self._open_file(p))

        if youtube_url:
            mk_btn(btn_col, "🔗 YouTube", C["green"], "#059669",
                   lambda u=youtube_url: self._open_url(u))

    def _open_url(self, url: str):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            self._log(f"⚠️ URL konnte nicht geöffnet werden: {e}")

    # ═════════════════════════════════════════════════════════════
    # SEITE 3: VIDEOS (Historie + Fortschritt)
    # ═════════════════════════════════════════════════════════════

    def _build_page_videos(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Videos"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        # Header
        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(top, text="📹  Meine Videos",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        # Filter-Buttons
        filt = ctk.CTkFrame(top, fg_color="transparent")
        filt.pack(side="right")
        self.vid_filter = ctk.StringVar(value="alle")
        for label, val in [("Alle", "alle"), ("Lokal", "local"),
                           ("Geplant", "scheduled"), ("Online", "uploaded")]:
            ctk.CTkButton(filt, text=label, width=70, height=28,
                          font=ctk.CTkFont(size=11), corner_radius=6,
                          fg_color=C["card_hover"], hover_color=C["accent"],
                          text_color=C["text"],
                          command=lambda v=val: self._filter_videos(v)).pack(side="left", padx=2)

        # Stats-Zeile
        self.vid_stats = ctk.CTkFrame(scroll, fg_color="transparent")
        self.vid_stats.pack(fill="x", pady=(0, 8))

        # Video-Liste
        self.vid_list = ctk.CTkFrame(scroll, fg_color="transparent")
        self.vid_list.pack(fill="both", expand=True)

    def _render_videos(self):
        for w in self.vid_stats.winfo_children():
            w.destroy()
        for w in self.vid_list.winfo_children():
            w.destroy()

        history = self._load_video_history()
        filt = self.vid_filter.get()

        if filt != "alle":
            history = [v for v in history if v.get("upload_status") == filt]

        # Stats
        all_h = self._load_video_history()
        total = len(all_h)
        local = sum(1 for v in all_h if v.get("upload_status") == "local")
        scheduled = sum(1 for v in all_h if v.get("upload_status") == "scheduled")
        uploaded = sum(1 for v in all_h if v.get("upload_status") == "uploaded")
        failed = sum(1 for v in all_h if v.get("status") == "error")

        for i in range(4):
            self.vid_stats.columnconfigure(i, weight=1)
        stats = [
            (f"📹 {total}", "Gesamt", C["text"]),
            (f"💾 {local}", "Lokal", C["gold"]),
            (f"📅 {scheduled}", "Geplant", C["cyan"]),
            (f"✅ {uploaded}", "Online", C["green"]),
        ]
        for i, (val, label, color) in enumerate(stats):
            c = ctk.CTkFrame(self.vid_stats, fg_color=C["card"], corner_radius=8, height=54)
            c.grid(row=0, column=i, sticky="nsew", padx=3)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=val, font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=color).pack(expand=True, side="left", padx=14)
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=10),
                         text_color=C["muted"]).pack(expand=True, side="left")

        if not history:
            ctk.CTkLabel(self.vid_list,
                         text="Noch keine Videos erstellt.\nStarte die Automation über Dashboard oder Planer!",
                         font=ctk.CTkFont(size=13), text_color=C["muted"],
                         justify="center").pack(pady=40)
            return

        # Videos anzeigen (neueste zuerst)
        for v in reversed(history):
            status = v.get("upload_status", "local")
            st_map = {
                "local": ("💾 Lokal", C["gold"]),
                "scheduled": ("📅 Geplant", C["cyan"]),
                "uploaded": ("✅ Online", C["green"]),
                "uploading": ("⏳ Uploading...", C["accent"]),
                "failed": ("❌ Fehler", C["red"]),
            }
            st_text, st_color = st_map.get(status, ("?", C["muted"]))

            card = ctk.CTkFrame(self.vid_list, fg_color=C["card"], corner_radius=10,
                                border_width=1, border_color=C["border"])
            card.pack(fill="x", pady=3)

            # Farbbalken
            ctk.CTkFrame(card, fg_color=st_color, width=4, corner_radius=0).pack(side="left", fill="y")

            # Mitte
            mid = ctk.CTkFrame(card, fg_color="transparent")
            mid.pack(side="left", fill="both", expand=True, padx=12, pady=10)

            # Titel-Zeile
            tr = ctk.CTkFrame(mid, fg_color="transparent")
            tr.pack(fill="x")

            ctk.CTkLabel(tr, text=f"#{v.get('id', '?')}",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=C["muted"]).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(tr, text=v.get("title", "Unbekannt"),
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=C["text"]).pack(side="left")

            # Details
            det = ctk.CTkFrame(mid, fg_color="transparent")
            det.pack(fill="x")

            details = f"{v.get('created', '?')}  •  {v.get('channel', 'Standard')}"
            if v.get("scheduled_date"):
                details += f"  •  Upload: {v['scheduled_date']}"
            ctk.CTkLabel(det, text=details, font=ctk.CTkFont(size=10),
                         text_color=C["muted"]).pack(side="left")

            if v.get("youtube_url"):
                ctk.CTkLabel(det, text=f"  🔗 {v['youtube_url']}",
                             font=ctk.CTkFont(size=10), text_color=C["accent"]).pack(side="left", padx=4)

            # Rechts: Status + Buttons
            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=10)

            ctk.CTkLabel(right, text=st_text,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=st_color).pack(pady=(6, 2))

            btn_row = ctk.CTkFrame(right, fg_color="transparent")
            btn_row.pack()

            vid_id = v.get("id", 0)
            vid_path = v.get("video_path", "")

            if vid_path and Path(vid_path).exists():
                # ▶ Abspielen (Video-Preview)
                ctk.CTkButton(btn_row, text="▶ Abspielen", width=90, height=26,
                              font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4,
                              fg_color=C["accent"], hover_color=C["accent_h"],
                              text_color="white",
                              command=lambda p=vid_path: self._open_file(p)).pack(side="left", padx=1)

            if status == "local":
                # 🚀 YouTube hochladen
                ctk.CTkButton(btn_row, text="▶ YouTube", width=80, height=26,
                              font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4,
                              fg_color=C["green"], hover_color="#059669",
                              text_color="white",
                              command=lambda vid=vid_id: self._upload_video_now(vid)).pack(side="left", padx=1)
                # 📱 TikTok hochladen
                ctk.CTkButton(btn_row, text="📱 TikTok", width=78, height=26,
                              font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4,
                              fg_color="#010101", hover_color="#333333",
                              text_color="white",
                              command=lambda vid=vid_id: self._upload_tiktok_now(vid)).pack(side="left", padx=1)
                # 📅 Planen
                ctk.CTkButton(btn_row, text="📅", width=28, height=26,
                              font=ctk.CTkFont(size=11), corner_radius=4,
                              fg_color=C["card_hover"], hover_color=C["cyan"],
                              text_color=C["text"],
                              command=lambda vid=vid_id: self._schedule_video(vid)).pack(side="left", padx=1)

            out_dir = str(Path(vid_path).parent) if vid_path else ""
            if out_dir and Path(out_dir).exists():
                ctk.CTkButton(btn_row, text="📂", width=28, height=26,
                              font=ctk.CTkFont(size=11), corner_radius=4,
                              fg_color=C["card_hover"], hover_color=C["border"],
                              text_color=C["text"],
                              command=lambda p=out_dir: self._open_file(p)).pack(side="left", padx=1)

            # 🗑️ Verwerfen (nicht posten)
            ctk.CTkButton(btn_row, text="🗑️", width=28, height=26,
                          font=ctk.CTkFont(size=11), corner_radius=4,
                          fg_color=C["card_hover"], hover_color=C["red"],
                          text_color=C["text"],
                          command=lambda vid=vid_id, t=v.get("title","?"): self._delete_video(vid, t)).pack(side="left", padx=1)

    def _filter_videos(self, filt: str):
        self.vid_filter.set(filt)
        self._render_videos()

    def _schedule_video(self, vid_id: int):
        from scheduler import VideoScheduler
        sched = VideoScheduler(self.settings)
        sched.history = self._load_video_history()
        slot = sched.add_to_queue(vid_id)
        self._log(f"📅 Video #{vid_id} geplant: {slot}")
        self._render_videos()

    def _load_video_history(self) -> list:
        f = BASE_DIR / "config" / "video_history.json"
        if f.exists():
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    return json.load(fp)
            except Exception:
                pass
        return []

    def _open_file(self, path: str):
        p = Path(path)
        if not p.exists():
            self._log(f"⚠️ Datei nicht gefunden: {path}")
            return
        try:
            if sys.platform == "win32":
                os.startfile(str(p))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
        except Exception as e:
            self._log(f"⚠️ Öffnen fehlgeschlagen: {e}")

    def _upload_video_now(self, vid_id: int):
        """Lädt ein einzelnes Video manuell auf YouTube hoch."""
        if self.running:
            self._log("⚠️ Eine Aktion läuft bereits")
            return
        history = self._load_video_history()
        video = next((v for v in history if v.get("id") == vid_id), None)
        if not video:
            self._log(f"⚠️ Video #{vid_id} nicht gefunden")
            return
        self._log(f"🚀 Upload startet: {video.get('title', '?')}")
        self._set_running(True)

        def do_up():
            try:
                from uploader import YouTubeUploader
                up = YouTubeUploader(self.settings)
                url = up.upload(
                    video_path=video.get("video_path", ""),
                    thumbnail_path=video.get("thumbnail_path", ""),
                    title=video.get("title", "Video"),
                    description=video.get("description", ""),
                    tags=video.get("tags", self.settings.get("channel", {}).get("default_tags", [])),
                )
                # History updaten
                for v in history:
                    if v.get("id") == vid_id:
                        v["upload_status"] = "uploaded"
                        v["youtube_url"] = url
                f = BASE_DIR / "config" / "video_history.json"
                with open(f, "w", encoding="utf-8") as fp:
                    json.dump(history, fp, ensure_ascii=False, indent=2)
                self.after(0, lambda: self._log(f"✅ Online: {url}"))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Upload fehlgeschlagen: {e}"))
            finally:
                self.after(0, lambda: self._set_running(False))
                self.after(0, self._render_videos)

        threading.Thread(target=do_up, daemon=True).start()

    def _upload_tiktok_now(self, vid_id: int):
        """Lädt ein Video auf TikTok hoch (Draft / SELF_ONLY in Sandbox)."""
        if self.running:
            self._log("⚠️ Eine Aktion läuft bereits")
            return
        history = self._load_video_history()
        video = next((v for v in history if v.get("id") == vid_id), None)
        if not video:
            self._log(f"⚠️ Video #{vid_id} nicht gefunden")
            return
        vid_path = video.get("video_path", "")
        if not vid_path or not Path(vid_path).exists():
            self._log("⚠️ Video-Datei nicht gefunden")
            return
        self._log(f"📱 TikTok Upload startet: {video.get('title', '?')}")
        self._log("🌐 Browser öffnet sich – bitte bei TikTok einloggen...")
        self._set_running(True)

        def do_tiktok():
            try:
                from tiktok_uploader import TikTokUploader
                up = TikTokUploader(self.settings)
                publish_id = up.upload(
                    video_path=vid_path,
                    title=video.get("title", "ContentStudio Video"),
                    privacy_level="SELF_ONLY",
                )
                for v in history:
                    if v.get("id") == vid_id:
                        v["tiktok_publish_id"] = publish_id
                f = BASE_DIR / "config" / "video_history.json"
                with open(f, "w", encoding="utf-8") as fp:
                    json.dump(history, fp, ensure_ascii=False, indent=2)
                self.after(0, lambda: self._log(f"✅ TikTok Draft erstellt – publish_id: {publish_id}"))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ TikTok Upload fehlgeschlagen: {e}"))
            finally:
                self.after(0, lambda: self._set_running(False))
                self.after(0, self._render_videos)

        threading.Thread(target=do_tiktok, daemon=True).start()

    def _delete_video(self, vid_id: int, title: str = ""):
        """Verwirft ein Video (entfernt aus Historie, Dateien bleiben erhalten)."""
        history = self._load_video_history()
        new_hist = [v for v in history if v.get("id") != vid_id]
        f = BASE_DIR / "config" / "video_history.json"
        try:
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(new_hist, fp, ensure_ascii=False, indent=2)
            self._log(f"🗑️ Verworfen: {title} (wird NICHT gepostet)")
            # Auch aus Queue entfernen
            try:
                from scheduler import VideoScheduler
                sched = VideoScheduler(self.settings)
                sched.remove_from_queue(vid_id)
            except Exception:
                pass
            self._render_videos()
        except Exception as e:
            self._log(f"⚠️ Löschen fehlgeschlagen: {e}")

    # ═════════════════════════════════════════════════════════════
    # SEITE 4: PLANER (Batch + Auto-Post)
    # ═════════════════════════════════════════════════════════════

    def _build_page_planner(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Planer"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text="📅  Batch-Produktion & Auto-Posting",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(scroll, text="Erstelle mehrere Videos auf einmal und verteile sie automatisch über die Woche.",
                     font=ctk.CTkFont(size=12), text_color=C["muted"],
                     wraplength=800).pack(anchor="w", pady=(0, 12))

        # ── Batch-Produktion ─────────────────────────────────────
        batch_card = self._card_in(scroll, "🎬  Batch-Produktion – Mehrere Videos auf einmal")

        ctk.CTkLabel(batch_card, text="Trage unten Topics ein (eins pro Zeile). Alle werden nacheinander produziert.",
                     font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(
            anchor="w", padx=16, pady=(10, 4))

        self.batch_text = ctk.CTkTextbox(batch_card, height=120, fg_color=C["input"],
                                          border_color=C["border"], border_width=1,
                                          font=ctk.CTkFont(size=12), corner_radius=6)
        self.batch_text.pack(fill="x", padx=16, pady=4)
        self.batch_text.insert("1.0", "Der Aufstieg und Fall von Napoleon Bonaparte\n"
                                       "Die verrücktesten Weltrekorde der Geschichte\n"
                                       "Das Geheimnis der verschwundenen Maya-Zivilisation")

        # Optionen
        opt_row = ctk.CTkFrame(batch_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=16, pady=(4, 4))

        self.batch_schedule_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(opt_row, text="Automatisch über die Woche verteilen",
                      variable=self.batch_schedule_var,
                      font=ctk.CTkFont(size=12), text_color=C["text"],
                      button_color=C["accent"], progress_color=C["accent"]).pack(side="left")

        self.batch_dry_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(opt_row, text="Nur erstellen (kein Upload)",
                      variable=self.batch_dry_var,
                      font=ctk.CTkFont(size=11), text_color=C["muted"],
                      button_color=C["gold"], progress_color=C["gold"]).pack(side="left", padx=20)

        # Kanal-Auswahl
        ch_row = ctk.CTkFrame(batch_card, fg_color="transparent")
        ch_row.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(ch_row, text="Kanal:", font=ctk.CTkFont(size=11),
                     text_color=C["muted"]).pack(side="left")
        self.batch_ch_var = ctk.StringVar(value="Standard")
        self.batch_ch_menu = ctk.CTkOptionMenu(ch_row, variable=self.batch_ch_var,
                                                values=self._get_channel_options(),
                                                fg_color=C["input"], button_color=C["accent"],
                                                dropdown_fg_color=C["card"], width=200,
                                                font=ctk.CTkFont(size=11))
        self.batch_ch_menu.pack(side="left", padx=8)

        # Start-Button
        self.batch_btn = ctk.CTkButton(
            batch_card, text="🚀  BATCH STARTEN – Alle Videos produzieren",
            font=ctk.CTkFont(size=14, weight="bold"), height=46,
            fg_color=C["accent"], hover_color=C["accent_h"],
            corner_radius=10, command=self._run_batch
        )
        self.batch_btn.pack(fill="x", padx=16, pady=(6, 12))

        # ── Posting-Plan ─────────────────────────────────────────
        plan_card = self._card_in(scroll, "📆  Posting-Plan – Wann soll gepostet werden?")
        plan_inner = ctk.CTkFrame(plan_card, fg_color="transparent")
        plan_inner.pack(fill="x", padx=16, pady=12)

        schedule = self._load_schedule()

        ctk.CTkLabel(plan_inner, text="Bevorzugte Posting-Tage:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 6))

        self.day_vars = {}
        days_row = ctk.CTkFrame(plan_inner, fg_color="transparent")
        days_row.pack(fill="x", pady=(0, 8))

        pref_days = schedule.get("preferred_days", ["Montag", "Mittwoch", "Freitag"])
        for day in ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]:
            var = ctk.BooleanVar(value=day in pref_days)
            self.day_vars[day] = var
            ctk.CTkCheckBox(days_row, text=day[:2], variable=var,
                            font=ctk.CTkFont(size=11), text_color=C["text"],
                            fg_color=C["accent"], width=50,
                            command=self._save_schedule_settings).pack(side="left", padx=4)

        # Uhrzeit
        time_row = ctk.CTkFrame(plan_inner, fg_color="transparent")
        time_row.pack(fill="x", pady=4)

        ctk.CTkLabel(time_row, text="Upload-Uhrzeit:",
                     font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(side="left")

        self.time_var = ctk.StringVar(value=schedule.get("preferred_time", "16:00"))
        time_menu = ctk.CTkOptionMenu(time_row, variable=self.time_var,
                                       values=["08:00", "10:00", "12:00", "14:00",
                                               "16:00", "17:00", "18:00", "19:00", "20:00"],
                                       fg_color=C["input"], button_color=C["accent"],
                                       dropdown_fg_color=C["card"], width=100,
                                       font=ctk.CTkFont(size=11),
                                       command=lambda _: self._save_schedule_settings())
        time_menu.pack(side="left", padx=8)

        # Posts pro Woche
        pw_row = ctk.CTkFrame(plan_inner, fg_color="transparent")
        pw_row.pack(fill="x", pady=4)

        ctk.CTkLabel(pw_row, text="Posts pro Woche:",
                     font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(side="left")

        self.pw_var = ctk.StringVar(value=str(schedule.get("posts_per_week", 3)))
        ctk.CTkOptionMenu(pw_row, variable=self.pw_var,
                          values=["1", "2", "3", "4", "5", "6", "7"],
                          fg_color=C["input"], button_color=C["accent"],
                          dropdown_fg_color=C["card"], width=80,
                          font=ctk.CTkFont(size=11),
                          command=lambda _: self._save_schedule_settings()).pack(side="left", padx=8)

        # ── Upload-Warteschlange ─────────────────────────────────
        ctk.CTkLabel(scroll, text="📋  Upload-Warteschlange",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["muted"]).pack(anchor="w", pady=(12, 4))

        self.queue_list = ctk.CTkFrame(scroll, fg_color="transparent")
        self.queue_list.pack(fill="both", expand=True)

        # Upload jetzt Button
        self.upload_now_btn = ctk.CTkButton(
            scroll, text="🚀  Fällige Videos JETZT hochladen",
            font=ctk.CTkFont(size=13, weight="bold"), height=40,
            fg_color=C["green"], hover_color="#059669",
            corner_radius=8, command=self._process_queue
        )
        self.upload_now_btn.pack(fill="x", pady=(8, 4))

    def _render_planner(self):
        for w in self.queue_list.winfo_children():
            w.destroy()

        queue = self._load_queue()

        if not queue:
            ctk.CTkLabel(self.queue_list,
                         text="Keine Videos in der Warteschlange.\nProduziere Videos über Batch oder plane sie über die Videos-Seite.",
                         font=ctk.CTkFont(size=12), text_color=C["muted"],
                         justify="center").pack(pady=20)
            return

        history = self._load_video_history()

        for item in queue:
            vid_id = item.get("video_id")
            video = next((v for v in history if v.get("id") == vid_id), {})
            q_status = item.get("status", "queued")

            st_map = {
                "queued": ("⏳ Wartend", C["gold"]),
                "uploading": ("🚀 Uploading...", C["accent"]),
                "uploaded": ("✅ Erledigt", C["green"]),
                "failed": ("❌ Fehlgeschlagen", C["red"]),
            }
            st_text, st_color = st_map.get(q_status, ("?", C["muted"]))

            row = ctk.CTkFrame(self.queue_list, fg_color=C["card"], corner_radius=8,
                               border_width=1, border_color=C["border"])
            row.pack(fill="x", pady=2)

            ctk.CTkFrame(row, fg_color=st_color, width=4, corner_radius=0).pack(side="left", fill="y")

            mid = ctk.CTkFrame(row, fg_color="transparent")
            mid.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            ctk.CTkLabel(mid, text=video.get("title", f"Video #{vid_id}"),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C["text"]).pack(anchor="w")

            date_str = item.get("scheduled_date", "?")
            ctk.CTkLabel(mid, text=f"📅 {date_str}  •  {video.get('channel', 'Standard')}",
                         font=ctk.CTkFont(size=10), text_color=C["muted"]).pack(anchor="w")

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=10)

            ctk.CTkLabel(right, text=st_text,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=st_color).pack(pady=(6, 2))

            if q_status == "queued":
                ctk.CTkButton(right, text="🗑️", width=28, height=24,
                              font=ctk.CTkFont(size=10), corner_radius=4,
                              fg_color=C["card_hover"], hover_color=C["red"],
                              text_color=C["text"],
                              command=lambda vid=vid_id: self._remove_from_queue(vid)).pack(pady=(0, 4))

    def _get_channel_options(self) -> list:
        """Gibt Kanal-Optionen für Dropdown-Menüs zurück."""
        opts = ["Standard"]
        try:
            for ch in self._load_channels():
                name = ch.get("name", ch.get("_id", "Kanal"))
                cid = ch.get("_id", "unknown")
                opts.append(f"{name} [{cid}]")
        except Exception:
            pass
        return opts

    def _run_batch(self):
        if self.running:
            self._log("⚠️ Automation läuft bereits!")
            return

        text = self.batch_text.get("1.0", "end").strip()
        topics = [t.strip() for t in text.split("\n") if t.strip()]
        if not topics:
            self._log("⚠️ Keine Topics eingegeben!")
            return

        auto_sched = self.batch_schedule_var.get()
        dry = self.batch_dry_var.get()

        # Channel auswählen
        ch_sel = self.batch_ch_var.get()
        ch_id = None
        if ch_sel != "Standard" and ch_sel != "Alle aktiven Kanäle":
            m = re.search(r'\[(.+)\]', ch_sel)
            if m:
                ch_id = m.group(1)

        self._log(f"🎬 Batch: {len(topics)} Videos starten...")
        self._set_running(True)
        self.batch_btn.configure(state="disabled", text="⏳  Batch läuft...")

        def do_batch():
            try:
                from scheduler import VideoScheduler
                sched = VideoScheduler(self.settings)

                for i, topic in enumerate(topics, 1):
                    if not self.running:
                        break
                    self.after(0, lambda t=topic, n=i, tot=len(topics):
                               self._log(f"📹 [{n}/{tot}] Produziere: {t}"))

                    cmd = [sys.executable, "main.py", "--topic", topic, "--dry-run"] if dry else \
                          [sys.executable, "main.py", "--topic", topic]
                    if ch_id:
                        cmd += ["--channel", ch_id]

                    proc = subprocess.Popen(cmd, cwd=str(BASE_DIR),
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            text=True, encoding="utf-8", errors="replace", bufsize=1)
                    for line in proc.stdout:
                        line = line.rstrip()
                        if line:
                            self.after(0, lambda l=line: self._log(l))
                    ret = proc.wait()

                    if ret == 0:
                        self.after(0, lambda t=topic: self._log(f"✅ Fertig: {t}"))
                        # Ergebnis zur History hinzufügen
                        out_dir = BASE_DIR / "output"
                        if out_dir.exists():
                            dirs = sorted(out_dir.iterdir(), key=lambda d: d.name, reverse=True)
                            for d in dirs:
                                result_f = d / "result.json"
                                if result_f.exists():
                                    try:
                                        with open(result_f, "r", encoding="utf-8") as f:
                                            result = json.load(f)
                                        if result.get("topic") == topic or result.get("status") == "success":
                                            entry = sched.add_to_history(result)
                                            if auto_sched and not dry:
                                                slot = sched.add_to_queue(entry["id"])
                                                self.after(0, lambda s=slot: self._log(f"📅 Geplant: {s}"))
                                            break
                                    except Exception:
                                        pass
                    else:
                        self.after(0, lambda t=topic: self._log(f"❌ Fehler bei: {t}"))

                    if i < len(topics):
                        time.sleep(5)

                self.after(0, lambda: self._log(f"✅ Batch fertig: {len(topics)} Videos verarbeitet"))

            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Batch-Fehler: {e}"))
            finally:
                self.after(0, lambda: self._set_running(False))
                self.after(0, lambda: self.batch_btn.configure(
                    state="normal", text="🚀  BATCH STARTEN – Alle Videos produzieren"))
                self.after(0, self._refresh_all)

        threading.Thread(target=do_batch, daemon=True).start()

    def _process_queue(self):
        if self.running:
            self._log("⚠️ Bitte warten bis die aktuelle Aktion fertig ist")
            return

        self._log("🚀 Starte Upload fälliger Videos...")
        self._set_running(True)

        def do_upload():
            try:
                from scheduler import VideoScheduler
                sched = VideoScheduler(self.settings)
                results = sched.process_queue()
                for r in results:
                    self.after(0, lambda u=r.get("url", ""): self._log(f"✅ Hochgeladen: {u}"))
                if not results:
                    self.after(0, lambda: self._log("📋 Keine fälligen Videos"))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Upload-Fehler: {e}"))
            finally:
                self.after(0, lambda: self._set_running(False))
                self.after(0, self._refresh_all)

        threading.Thread(target=do_upload, daemon=True).start()

    def _remove_from_queue(self, vid_id: int):
        from scheduler import VideoScheduler
        sched = VideoScheduler(self.settings)
        sched.history = self._load_video_history()
        sched.remove_from_queue(vid_id)
        self._log(f"🗑️ Video #{vid_id} aus Warteschlange entfernt")
        self._render_planner()

    def _save_schedule_settings(self):
        schedule = self._load_schedule()
        schedule["preferred_days"] = [d for d, v in self.day_vars.items() if v.get()]
        schedule["preferred_time"] = self.time_var.get()
        schedule["posts_per_week"] = int(self.pw_var.get())
        f = BASE_DIR / "config" / "schedule.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(schedule, fp, ensure_ascii=False, indent=2)
        self._log(f"📅 Posting-Plan gespeichert")

    def _load_schedule(self) -> dict:
        f = BASE_DIR / "config" / "schedule.json"
        if f.exists():
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    return json.load(fp)
            except Exception:
                pass
        return {"preferred_days": ["Montag", "Mittwoch", "Freitag"],
                "preferred_time": "16:00", "posts_per_week": 3, "queue": []}

    def _load_queue(self) -> list:
        schedule = self._load_schedule()
        return sorted(schedule.get("queue", []), key=lambda x: x.get("scheduled_date", ""))

    # ═════════════════════════════════════════════════════════════
    # SEITE 5b: STORY-PLANER (5-Schritt-Workflow)
    # ═════════════════════════════════════════════════════════════

    def _build_page_story_planer(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Story-Planer"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text="📖  Story-Planer",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(scroll,
                     text="Thema eingeben → Ideen recherchieren → Auswählen → Plan erstellen → Produzieren",
                     font=ctk.CTkFont(size=12), text_color=C["muted"],
                     wraplength=800).pack(anchor="w", pady=(0, 14))

        # ── Schritt 1: Thema ──────────────────────────────────────
        s1 = self._card_in(scroll, "① Thema & Story-Recherche")

        theme_row = ctk.CTkFrame(s1, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=(10, 6))

        ctk.CTkLabel(theme_row, text="Thema:",
                     font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(side="left")
        self.sp_theme_entry = ctk.CTkEntry(
            theme_row, placeholder_text="z.B. Geschichte, Biographien, Brainrot, Comedy...",
            fg_color=C["input"], border_color=C["border"],
            width=340, font=ctk.CTkFont(size=12))
        self.sp_theme_entry.pack(side="left", padx=10)

        count_row = ctk.CTkFrame(s1, fg_color="transparent")
        count_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(count_row, text="Anzahl Ideen:",
                     font=ctk.CTkFont(size=12), text_color=C["muted"]).pack(side="left")
        self.sp_count_var = ctk.StringVar(value="10")
        ctk.CTkOptionMenu(count_row, variable=self.sp_count_var,
                          values=["5", "8", "10", "14", "20"],
                          fg_color=C["input"], button_color=C["accent"],
                          dropdown_fg_color=C["card"], width=80,
                          font=ctk.CTkFont(size=11)).pack(side="left", padx=8)

        self.sp_research_btn = ctk.CTkButton(
            s1, text="🔍  Story-Ideen recherchieren",
            font=ctk.CTkFont(size=13, weight="bold"), height=40,
            fg_color=C["purple"], hover_color="#7C3AED",
            corner_radius=8, command=self._sp_research)
        self.sp_research_btn.pack(fill="x", padx=16, pady=(4, 12))

        # ── Schritt 2: Ideen-Liste & Auswahl ──────────────────────
        s2 = self._card_in(scroll, "② Ideen auswählen")
        ctk.CTkLabel(s2, text="Haken setzen bei den Storys die produziert werden sollen:",
                     font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(
            anchor="w", padx=16, pady=(8, 4))

        self.sp_ideas_frame = ctk.CTkScrollableFrame(s2, fg_color="transparent", height=260)
        self.sp_ideas_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.sp_idea_vars = []

        ctk.CTkLabel(s2, text="Noch keine Ideen recherchiert – Schritt ① zuerst.",
                     font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(
            anchor="w", padx=16, pady=(0, 10))

        # ── Schritt 3: Einstellungen ───────────────────────────────
        s3 = self._card_in(scroll, "③ Kanal, Zeitraum & Video-Länge")
        cfg = ctk.CTkFrame(s3, fg_color="transparent")
        cfg.pack(fill="x", padx=16, pady=10)

        # Kanal
        ctk.CTkLabel(cfg, text="Kanal:", font=ctk.CTkFont(size=12),
                     text_color=C["muted"]).grid(row=0, column=0, sticky="w", pady=4)
        self.sp_channel_var = ctk.StringVar(value="Standard")
        self.sp_ch_menu = ctk.CTkOptionMenu(cfg, variable=self.sp_channel_var,
                                             values=self._get_channel_options(),
                                             fg_color=C["input"], button_color=C["accent"],
                                             dropdown_fg_color=C["card"], width=180,
                                             font=ctk.CTkFont(size=11))
        self.sp_ch_menu.grid(row=0, column=1, sticky="w", padx=10, pady=4)

        # Startdatum
        ctk.CTkLabel(cfg, text="Start:", font=ctk.CTkFont(size=12),
                     text_color=C["muted"]).grid(row=1, column=0, sticky="w", pady=4)
        self.sp_start_entry = ctk.CTkEntry(cfg, placeholder_text="YYYY-MM-DD",
                                            fg_color=C["input"], border_color=C["border"],
                                            width=140, font=ctk.CTkFont(size=11))
        self.sp_start_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.sp_start_entry.grid(row=1, column=1, sticky="w", padx=10, pady=4)

        # Enddatum
        ctk.CTkLabel(cfg, text="Ende:", font=ctk.CTkFont(size=12),
                     text_color=C["muted"]).grid(row=2, column=0, sticky="w", pady=4)
        self.sp_end_entry = ctk.CTkEntry(cfg, placeholder_text="YYYY-MM-DD",
                                          fg_color=C["input"], border_color=C["border"],
                                          width=140, font=ctk.CTkFont(size=11))
        end_default = (_dt.now() + _td(days=30)).strftime("%Y-%m-%d")
        self.sp_end_entry.insert(0, end_default)
        self.sp_end_entry.grid(row=2, column=1, sticky="w", padx=10, pady=4)

        # Video-Länge
        ctk.CTkLabel(cfg, text="Video-Länge (Min.):", font=ctk.CTkFont(size=12),
                     text_color=C["muted"]).grid(row=3, column=0, sticky="w", pady=4)
        self.sp_duration_var = ctk.StringVar(value="10")
        ctk.CTkOptionMenu(cfg, variable=self.sp_duration_var,
                          values=["5", "8", "10", "12", "15", "20"],
                          fg_color=C["input"], button_color=C["accent"],
                          dropdown_fg_color=C["card"], width=100,
                          font=ctk.CTkFont(size=11)).grid(row=3, column=1, sticky="w", padx=10, pady=4)

        # Posts pro Woche
        ctk.CTkLabel(cfg, text="Videos pro Woche:", font=ctk.CTkFont(size=12),
                     text_color=C["muted"]).grid(row=4, column=0, sticky="w", pady=4)
        self.sp_ppw_var = ctk.StringVar(value="3")
        ctk.CTkOptionMenu(cfg, variable=self.sp_ppw_var,
                          values=["1", "2", "3", "4", "5", "7"],
                          fg_color=C["input"], button_color=C["accent"],
                          dropdown_fg_color=C["card"], width=80,
                          font=ctk.CTkFont(size=11)).grid(row=4, column=1, sticky="w", padx=10, pady=4)

        # Nur erstellen
        self.sp_dryrun_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(s3, text="Nur erstellen (kein Upload)",
                      variable=self.sp_dryrun_var,
                      font=ctk.CTkFont(size=11), text_color=C["muted"],
                      button_color=C["gold"], progress_color=C["gold"]).pack(
            anchor="w", padx=16, pady=(0, 10))

        # ── Schritt 4: Plan erstellen ──────────────────────────────
        s4 = self._card_in(scroll, "④ Posting-Plan erstellen")
        self.sp_plan_btn = ctk.CTkButton(
            s4, text="📅  Posting-Plan erstellen",
            font=ctk.CTkFont(size=13, weight="bold"), height=40,
            fg_color=C["accent"], hover_color=C["accent_h"],
            corner_radius=8, command=self._sp_create_plan)
        self.sp_plan_btn.pack(fill="x", padx=16, pady=(10, 6))

        self.sp_plan_display = ctk.CTkFrame(s4, fg_color="transparent")
        self.sp_plan_display.pack(fill="x", padx=16, pady=(0, 10))

        # ── Schritt 5: Produktion starten ─────────────────────────
        s5 = self._card_in(scroll, "⑤ Videos produzieren")
        self.sp_produce_btn = ctk.CTkButton(
            s5, text="🚀  ALLE VIDEOS PRODUZIEREN",
            font=ctk.CTkFont(size=14, weight="bold"), height=48,
            fg_color=C["green"], hover_color="#059669",
            corner_radius=10, command=self._sp_execute_plan)
        self.sp_produce_btn.pack(fill="x", padx=16, pady=(10, 6))

        self.sp_progress_label = ctk.CTkLabel(
            s5, text="Noch kein Plan erstellt.",
            font=ctk.CTkFont(size=11), text_color=C["muted"])
        self.sp_progress_label.pack(anchor="w", padx=16, pady=(0, 10))

        self._sp_plan_data = []

    # ── Story-Planer Logik ────────────────────────────────────────

    def _sp_research(self):
        theme = self.sp_theme_entry.get().strip()
        if not theme:
            self._log("⚠️ Bitte zuerst ein Thema eingeben.")
            return
        count = int(self.sp_count_var.get())
        self.sp_research_btn.configure(state="disabled", text="⏳ Recherchiere...")

        def do_research():
            try:
                from planner import StoryPlanner
                planner = StoryPlanner(self.settings)
                ideas = planner.research_story_ideas(theme, count)
                self.after(0, lambda: self._sp_render_ideas(ideas))
                self.after(0, lambda: self._log(f"✅ {len(ideas)} Story-Ideen zu '{theme}' gefunden"))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Recherche-Fehler: {e}"))
            finally:
                self.after(0, lambda: self.sp_research_btn.configure(
                    state="normal", text="🔍  Story-Ideen recherchieren"))

        threading.Thread(target=do_research, daemon=True).start()

    def _sp_render_ideas(self, ideas: list):
        for w in self.sp_ideas_frame.winfo_children():
            w.destroy()
        self.sp_idea_vars = []

        for idea in ideas:
            var = ctk.BooleanVar(value=True)
            row = ctk.CTkFrame(self.sp_ideas_frame, fg_color=C["card"],
                               corner_radius=6, border_width=1, border_color=C["border"])
            row.pack(fill="x", pady=2)

            ctk.CTkCheckBox(row, text="", variable=var,
                            fg_color=C["accent"], width=24).pack(side="left", padx=8, pady=6)
            mid = ctk.CTkFrame(row, fg_color="transparent")
            mid.pack(side="left", fill="both", expand=True, pady=4)
            ctk.CTkLabel(mid, text=idea.get("title", "?"),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C["text"], anchor="w").pack(anchor="w")
            if idea.get("desc"):
                ctk.CTkLabel(mid, text=idea["desc"],
                             font=ctk.CTkFont(size=10), text_color=C["muted"],
                             anchor="w", wraplength=600).pack(anchor="w")

            type_badge = idea.get("content_type", "story")
            ctk.CTkLabel(row, text=f"[{type_badge}]",
                         font=ctk.CTkFont(size=10), text_color=C["purple"]).pack(
                side="right", padx=8)

            self.sp_idea_vars.append((var, idea))

    def _sp_create_plan(self):
        selected = [idea for var, idea in self.sp_idea_vars if var.get()]
        if not selected:
            self._log("⚠️ Keine Ideen ausgewählt.")
            return

        try:
            from planner import StoryPlanner
            planner = StoryPlanner(self.settings)
            plan = planner.create_posting_plan(
                selected_ideas=selected,
                channel=self.sp_channel_var.get(),
                start_date=self.sp_start_entry.get().strip(),
                end_date=self.sp_end_entry.get().strip(),
                duration_minutes=int(self.sp_duration_var.get()),
                posts_per_week=int(self.sp_ppw_var.get()),
            )
            self._sp_plan_data = plan
            self._sp_render_plan(plan)
            self._log(f"📅 Plan erstellt: {len(plan)} Videos eingeplant")
        except Exception as e:
            self._log(f"❌ Plan-Fehler: {e}")

    def _sp_render_plan(self, plan: list):
        for w in self.sp_plan_display.winfo_children():
            w.destroy()
        for entry in plan:
            row = ctk.CTkFrame(self.sp_plan_display, fg_color=C["card"],
                               corner_radius=6, border_width=1, border_color=C["border"])
            row.pack(fill="x", pady=2)
            date_lbl = ctk.CTkLabel(row, text=entry.get("scheduled_date", "?")[:16],
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     text_color=C["cyan"], width=130, anchor="w")
            date_lbl.pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=entry.get("title", "?"),
                         font=ctk.CTkFont(size=11), text_color=C["text"],
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(row, text=f"{entry.get('duration_minutes', 10)} Min.",
                         font=ctk.CTkFont(size=10), text_color=C["muted"]).pack(
                side="right", padx=10)

    def _sp_execute_plan(self):
        if not self._sp_plan_data:
            self._log("⚠️ Erst Schritt ④ ausführen – Plan erstellen.")
            return
        if self.running:
            self._log("⚠️ Pipeline läuft bereits.")
            return

        dry_run = self.sp_dryrun_var.get()
        plan = self._sp_plan_data
        total = len(plan)
        self._set_running(True)
        self.sp_produce_btn.configure(state="disabled")
        self.sp_progress_label.configure(text=f"Starte Produktion: 0/{total} Videos...")

        def do_execute():
            try:
                from planner import StoryPlanner
                planner = StoryPlanner(self.settings)

                def on_progress(i, t, entry):
                    self.after(0, lambda: self.sp_progress_label.configure(
                        text=f"Produziere {i+1}/{t}: {entry['title'][:50]}..."))
                    self.after(0, lambda: self._log(f"🎬 [{i+1}/{t}] {entry['title']}"))

                result_plan = planner.execute_plan(plan, dry_run=dry_run, on_progress=on_progress)
                done = sum(1 for e in result_plan if e.get("status") == "done")
                self.after(0, lambda: self.sp_progress_label.configure(
                    text=f"✅ Fertig: {done}/{total} Videos produziert"))
                self.after(0, lambda: self._log(f"✅ Story-Plan abgeschlossen: {done}/{total} erfolgreich"))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Produktions-Fehler: {e}"))
            finally:
                self.after(0, lambda: self._set_running(False))
                self.after(0, lambda: self.sp_produce_btn.configure(state="normal"))

        threading.Thread(target=do_execute, daemon=True).start()

    # ═════════════════════════════════════════════════════════════
    # SEITE 5: DESIGN / ANIMATION STYLE
    # ═════════════════════════════════════════════════════════════

    def _build_page_design(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Design"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text="🎨  Animations-Stil für Videos wählen",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text="Wähle wie deine Videos aussehen sollen. Der Stil bestimmt Hintergrund, Textfarben und Thumbnail-Theme.",
                     font=ctk.CTkFont(size=12), text_color=C["muted"],
                     wraplength=800).pack(anchor="w", pady=(0, 12))

        # Aktueller Stil herausfinden
        current_bg = self.settings.get("video", {}).get("background_color", [10, 10, 20])
        current_style = "minimal"  # Default
        for key, style in ANIMATION_STYLES.items():
            if style["bg_color"] == current_bg:
                current_style = key
                break

        self.style_var = ctk.StringVar(value=current_style)

        # Grid mit Style-Cards
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")

        col = 0
        row_frame = ctk.CTkFrame(grid, fg_color="transparent")
        row_frame.pack(fill="x", pady=4)

        for key, style in ANIMATION_STYLES.items():
            is_active = key == current_style
            card = ctk.CTkFrame(row_frame, fg_color=C["card"] if not is_active else C["card_hover"],
                                corner_radius=12,
                                border_width=2,
                                border_color=C["accent"] if is_active else C["border"],
                                width=220)
            card.pack(side="left", padx=6, pady=4, fill="both", expand=True)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=14, pady=12)

            # Preview-Farbe
            preview_frame = ctk.CTkFrame(inner,
                                         fg_color=self._rgb_hex(style["bg_color"]),
                                         corner_radius=8, height=60)
            preview_frame.pack(fill="x", pady=(0, 8))
            preview_frame.pack_propagate(False)
            ctk.CTkLabel(preview_frame, text=style["preview"],
                         font=ctk.CTkFont(size=11),
                         text_color=style["accent_color"]).pack(expand=True)

            ctk.CTkLabel(inner, text=style["name"],
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=C["text"]).pack(anchor="w")
            ctk.CTkLabel(inner, text=style["desc"],
                         font=ctk.CTkFont(size=10), text_color=C["muted"],
                         justify="left").pack(anchor="w", pady=(4, 8))

            select_btn = ctk.CTkButton(
                inner,
                text="✓  Aktiv" if is_active else "Auswählen",
                font=ctk.CTkFont(size=11, weight="bold"),
                height=30, corner_radius=6,
                fg_color=C["green"] if is_active else C["card_hover"],
                hover_color=C["accent"],
                text_color="white",
                command=lambda k=key: self._set_style(k)
            )
            select_btn.pack(fill="x")

            col += 1
            if col >= 3:
                col = 0
                row_frame = ctk.CTkFrame(grid, fg_color="transparent")
                row_frame.pack(fill="x", pady=4)

        # ── Thumbnail-Style ──────────────────────────────────────
        ctk.CTkLabel(scroll, text="🖼️  Thumbnail-Einstellungen",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(20, 8))

        th_card = self._card_in(scroll, "")
        th_inner = ctk.CTkFrame(th_card, fg_color="transparent")
        th_inner.pack(fill="x", padx=16, pady=12)

        for label, key, default, values in [
            ("Titel-Schriftgröße", "font_size_title", "72", ["48", "60", "72", "84", "96"]),
            ("Untertitel-Schriftgröße", "font_size_subtitle", "40", ["28", "34", "40", "48", "56"]),
        ]:
            r = ctk.CTkFrame(th_inner, fg_color="transparent")
            r.pack(fill="x", pady=4)
            ctk.CTkLabel(r, text=label + ":", font=ctk.CTkFont(size=11),
                         text_color=C["muted"], width=200, anchor="w").pack(side="left")
            current_val = str(self.settings.get("thumbnail", {}).get(key, default))
            menu = ctk.CTkOptionMenu(r, values=values, fg_color=C["input"],
                                      button_color=C["accent"], dropdown_fg_color=C["card"],
                                      width=100, font=ctk.CTkFont(size=11))
            if current_val in values:
                menu.set(current_val)
            else:
                menu.set(default)
            menu.pack(side="left")

    def _set_style(self, key: str):
        style = ANIMATION_STYLES[key]
        self.settings.setdefault("video", {})["background_color"] = style["bg_color"]
        self.settings["video"]["font_size"] = style["font_size"]
        self._save_settings()
        self._log(f"🎨 Stil gewechselt: {style['name']}")
        # Seite neu aufbauen
        self.pages["Design"].destroy()
        self._build_page_design()
        self._switch_page("Design")

    def _rgb_hex(self, rgb: list) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    # ═════════════════════════════════════════════════════════════
    # SEITE 4: STIMMEN
    # ═════════════════════════════════════════════════════════════

    def _build_page_voices(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Stimmen"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text="🎙️  Stimme für Voiceover auswählen",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text="Wähle die Stimme für deine Videos. Du kannst auch eine eigene Fish Audio Voice-ID eingeben.",
                     font=ctk.CTkFont(size=12), text_color=C["muted"],
                     wraplength=800).pack(anchor="w", pady=(0, 12))

        # Aktuelle Voice-ID
        current_vid = self.settings.get("voiceover", {}).get("fish_audio", {}).get(
            "voice_id", "54a5170264694bfc8e9ad98df7bd89c3")

        # Stimmen-Grid
        for vid, voice in VOICES.items():
            is_active = (vid == current_vid)
            is_custom = (vid == "CUSTOM")

            card = ctk.CTkFrame(scroll, fg_color=C["card"],
                                corner_radius=10, border_width=2,
                                border_color=C["accent"] if is_active else C["border"])
            card.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            # Links: Info
            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            name_row = ctk.CTkFrame(left, fg_color="transparent")
            name_row.pack(fill="x")

            ctk.CTkLabel(name_row, text=voice["name"],
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C["text"]).pack(side="left")
            ctk.CTkLabel(name_row, text=f"  {voice['gender']}",
                         font=ctk.CTkFont(size=12),
                         text_color=C["muted"]).pack(side="left")
            ctk.CTkLabel(name_row, text=f"  {voice['lang']}",
                         font=ctk.CTkFont(size=11),
                         text_color=C["cyan"]).pack(side="left", padx=4)

            ctk.CTkLabel(left, text=voice["desc"],
                         font=ctk.CTkFont(size=11), text_color=C["muted"],
                         justify="left").pack(anchor="w", pady=(2, 0))

            if not is_custom:
                ctk.CTkLabel(left, text=f"ID: {vid}",
                             font=ctk.CTkFont(family="Courier New", size=9),
                             text_color=C["border"]).pack(anchor="w", pady=(2, 0))

            # Rechts: Button / Input
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")

            if is_custom:
                self.custom_voice_entry = ctk.CTkEntry(
                    right, placeholder_text="Voice-ID hier einfügen...",
                    fg_color=C["input"], border_color=C["border"],
                    width=260, font=ctk.CTkFont(size=11))
                self.custom_voice_entry.pack(pady=2)
                ctk.CTkButton(right, text="Speichern",
                              font=ctk.CTkFont(size=11), height=30,
                              fg_color=C["accent"], hover_color=C["accent_h"],
                              corner_radius=6,
                              command=self._set_custom_voice).pack(pady=2)
            else:
                ctk.CTkButton(right,
                              text="✓  Aktiv" if is_active else "Auswählen",
                              font=ctk.CTkFont(size=12, weight="bold"),
                              height=36, width=120, corner_radius=8,
                              fg_color=C["green"] if is_active else C["card_hover"],
                              hover_color=C["accent"],
                              command=lambda v=vid, n=voice["name"]: self._set_voice(v, n)
                              ).pack()

        # ── Provider-Auswahl ─────────────────────────────────────
        ctk.CTkLabel(scroll, text="⚙️  TTS-Provider",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(20, 8))

        prov_card = self._card_in(scroll, "")
        prov_inner = ctk.CTkFrame(prov_card, fg_color="transparent")
        prov_inner.pack(fill="x", padx=16, pady=12)

        current_prov = self.settings.get("voiceover", {}).get("provider", "fish_audio")
        self.prov_var = ctk.StringVar(value=current_prov)

        for prov, label, desc in [
            ("fish_audio", "🐟 Fish Audio (Empfohlen)", "Hochwertige, natürliche Stimmen via API"),
            ("openai", "🤖 OpenAI TTS", "OpenAI Text-to-Speech (benötigt Guthaben)"),
            ("free", "🆓 gTTS (Kostenlos)", "Google TTS – kostenlos aber roboterhaft"),
        ]:
            r = ctk.CTkFrame(prov_inner, fg_color=C["card_hover"] if current_prov == prov else "transparent",
                             corner_radius=8)
            r.pack(fill="x", pady=2)

            ctk.CTkRadioButton(r, text=label,
                               variable=self.prov_var, value=prov,
                               font=ctk.CTkFont(size=12),
                               text_color=C["text"],
                               fg_color=C["accent"],
                               command=self._save_provider).pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(r, text=desc, font=ctk.CTkFont(size=10),
                         text_color=C["muted"]).pack(side="left", padx=8)

    def _set_voice(self, vid: str, name: str):
        self.settings.setdefault("voiceover", {}).setdefault("fish_audio", {})["voice_id"] = vid
        self._save_settings()
        self._log(f"🎙️ Stimme gewechselt: {name}")
        self.pages["Stimmen"].destroy()
        self._build_page_voices()
        self._switch_page("Stimmen")

    def _set_custom_voice(self):
        vid = self.custom_voice_entry.get().strip()
        if vid and len(vid) > 10:
            self._set_voice(vid, "Custom Voice")
        else:
            self._log("⚠️ Ungültige Voice-ID", "gold")

    def _save_provider(self):
        prov = self.prov_var.get()
        self.settings.setdefault("voiceover", {})["provider"] = prov
        self._save_settings()
        self._log(f"⚙️ TTS-Provider: {prov}")

    # ═════════════════════════════════════════════════════════════
    # SEITE 5: REGELN / LEGAL
    # ═════════════════════════════════════════════════════════════

    def _build_page_rules(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Regeln"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text="⚖️  Regeln & Compliance",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(scroll, text="Alle Regeln hier werden automatisch bei jedem Video beachtet. Du kannst sie jederzeit ändern.",
                     font=ctk.CTkFont(size=12), text_color=C["muted"],
                     wraplength=800).pack(anchor="w", pady=(0, 12))

        rules = self._load_rules()

        # ── Disclaimers ──────────────────────────────────────────
        disc_card = self._card_in(scroll, "📜  Disclaimers (werden in jedes Video eingefügt)")
        disc_inner = ctk.CTkFrame(disc_card, fg_color="transparent")
        disc_inner.pack(fill="x", padx=16, pady=12)

        disclaimers = rules.get("disclaimers", {})
        active = disclaimers.get("active_disclaimers", [])
        self.disc_widgets = {}

        for key in ["finance_disclaimer", "affiliate_disclaimer", "ai_generated_disclaimer"]:
            text = disclaimers.get(key, "")
            if not text or text.startswith("_"):
                continue

            is_active = key in active
            name = key.replace("_", " ").title()

            row = ctk.CTkFrame(disc_inner, fg_color=C["card_hover"] if is_active else "transparent",
                              corner_radius=8)
            row.pack(fill="x", pady=3)

            var = ctk.BooleanVar(value=is_active)
            chk = ctk.CTkCheckBox(row, text=name, variable=var,
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   text_color=C["text"], fg_color=C["accent"],
                                   command=lambda k=key, v=var: self._toggle_disclaimer(k, v))
            chk.pack(anchor="w", padx=12, pady=(8, 2))

            lbl = ctk.CTkLabel(row, text=text[:150] + ("..." if len(text) > 150 else ""),
                              font=ctk.CTkFont(size=10), text_color=C["muted"],
                              wraplength=700)
            lbl.pack(anchor="w", padx=32, pady=(0, 8))

        # ── Pflicht-Regeln ───────────────────────────────────────
        rules_card = self._card_in(scroll, "⚠️  Pflicht-Regeln (GPT befolgt diese beim Script-Schreiben)")
        rules_inner = ctk.CTkFrame(rules_card, fg_color="transparent")
        rules_inner.pack(fill="x", padx=16, pady=12)

        mandatory = rules.get("script_rules", {}).get("mandatory_rules", [])
        for i, rule in enumerate(mandatory):
            r = ctk.CTkFrame(rules_inner, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=f"  {i+1}.",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=C["accent"], width=30).pack(side="left")
            ctk.CTkLabel(r, text=rule,
                        font=ctk.CTkFont(size=11), text_color=C["text"],
                        wraplength=700, anchor="w").pack(side="left", fill="x", expand=True)

        # ── Eigene Regel hinzufügen ──────────────────────────────
        add_frame = ctk.CTkFrame(rules_inner, fg_color=C["card_hover"], corner_radius=8)
        add_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(add_frame, text="＋ Eigene Regel hinzufügen:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["gold"]).pack(anchor="w", padx=12, pady=(8, 2))

        add_row = ctk.CTkFrame(add_frame, fg_color="transparent")
        add_row.pack(fill="x", padx=12, pady=(2, 10))

        self.new_rule_entry = ctk.CTkEntry(add_row,
                                            placeholder_text="z.B. Immer 3 konkrete Beispiele pro Sektion nennen",
                                            fg_color=C["input"], border_color=C["border"],
                                            font=ctk.CTkFont(size=11))
        self.new_rule_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(add_row, text="Hinzufügen", height=30, width=100,
                      font=ctk.CTkFont(size=11), corner_radius=6,
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      command=self._add_custom_rule).pack(side="right")

        # ── Verbotene Wörter ─────────────────────────────────────
        block_card = self._card_in(scroll, "🚫  Verbotene Begriffe (werden automatisch blockiert/ersetzt)")
        block_inner = ctk.CTkFrame(block_card, fg_color="transparent")
        block_inner.pack(fill="x", padx=16, pady=12)

        hard_blocks = rules.get("forbidden_words", {}).get("hard_block", [])
        if hard_blocks:
            block_text = "  •  ".join(hard_blocks)
            ctk.CTkLabel(block_inner, text="Blockiert (werden entfernt):",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=C["red"]).pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(block_inner, text=block_text,
                        font=ctk.CTkFont(size=10), text_color=C["muted"],
                        wraplength=700).pack(anchor="w", pady=(0, 8))

        replacements = rules.get("forbidden_words", {}).get("replacements", {})
        if replacements:
            ctk.CTkLabel(block_inner, text="Automatische Ersetzungen:",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=C["orange"]).pack(anchor="w", pady=(4, 4))
            for old, new in replacements.items():
                r = ctk.CTkFrame(block_inner, fg_color="transparent")
                r.pack(fill="x", pady=1)
                ctk.CTkLabel(r, text=f'  "{old}"', font=ctk.CTkFont(size=10),
                            text_color=C["red"]).pack(side="left")
                ctk.CTkLabel(r, text="  →  ", font=ctk.CTkFont(size=10),
                            text_color=C["muted"]).pack(side="left")
                ctk.CTkLabel(r, text=f'"{new}"', font=ctk.CTkFont(size=10),
                            text_color=C["green"]).pack(side="left")

        # ── Neues verbotenes Wort hinzufügen ─────────────────────
        add_block_row = ctk.CTkFrame(block_inner, fg_color=C["card_hover"], corner_radius=8)
        add_block_row.pack(fill="x", pady=(10, 0))
        inner_r = ctk.CTkFrame(add_block_row, fg_color="transparent")
        inner_r.pack(fill="x", padx=12, pady=8)

        self.new_block_entry = ctk.CTkEntry(inner_r,
                                             placeholder_text="Neues verbotenes Wort/Phrase",
                                             fg_color=C["input"], border_color=C["border"],
                                             font=ctk.CTkFont(size=11))
        self.new_block_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(inner_r, text="Blockieren", height=28, width=90,
                      font=ctk.CTkFont(size=11), corner_radius=6,
                      fg_color=C["red"], hover_color="#B91C1C",
                      command=self._add_blocked_word).pack(side="right")

        # ── Impressum ────────────────────────────────────────────
        imp_card = self._card_in(scroll, "🇩🇪  Deutschland / Impressum")
        imp_inner = ctk.CTkFrame(imp_card, fg_color="transparent")
        imp_inner.pack(fill="x", padx=16, pady=12)

        germany = rules.get("country_specific", {}).get("germany", {})
        impressum = germany.get("impressum_text", "")

        ctk.CTkLabel(imp_inner, text="Impressum (Pflicht für geschäftliche YouTube-Kanäle in DE):",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 4))

        self.impressum_box = ctk.CTkTextbox(imp_inner, height=70, fg_color=C["input"],
                                             border_color=C["border"], border_width=1,
                                             font=ctk.CTkFont(size=11), corner_radius=6)
        self.impressum_box.pack(fill="x", pady=(0, 6))
        self.impressum_box.insert("1.0", impressum)

        ctk.CTkButton(imp_inner, text="💾  Impressum speichern", height=30,
                      font=ctk.CTkFont(size=11), corner_radius=6,
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      command=self._save_impressum).pack(anchor="w")

        # ── Direkt-Editor Button ─────────────────────────────────
        ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=4)).pack()
        ctk.CTkButton(scroll, text="📝  legal_rules.json direkt bearbeiten (Notepad)",
                      font=ctk.CTkFont(size=12), height=36, corner_radius=8,
                      fg_color=C["card"], hover_color=C["card_hover"],
                      text_color=C["text"],
                      command=self._open_rules_file).pack(fill="x")

    def _load_rules(self) -> dict:
        f = BASE_DIR / "config" / "legal_rules.json"
        if f.exists():
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp)
        return {}

    def _save_rules(self, rules: dict):
        f = BASE_DIR / "config" / "legal_rules.json"
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(rules, fp, ensure_ascii=False, indent=2)

    def _toggle_disclaimer(self, key: str, var):
        rules = self._load_rules()
        active = rules.get("disclaimers", {}).get("active_disclaimers", [])
        if var.get() and key not in active:
            active.append(key)
        elif not var.get() and key in active:
            active.remove(key)
        rules["disclaimers"]["active_disclaimers"] = active
        self._save_rules(rules)
        self._log(f"⚖️ Disclaimer '{key}': {'aktiviert' if var.get() else 'deaktiviert'}")

    def _add_custom_rule(self):
        rule = self.new_rule_entry.get().strip()
        if not rule:
            return
        rules = self._load_rules()
        rules.setdefault("script_rules", {}).setdefault("mandatory_rules", []).append(rule)
        self._save_rules(rules)
        self.new_rule_entry.delete(0, "end")
        self._log(f"⚖️ Neue Regel: {rule}")
        self.pages["Regeln"].destroy()
        self._build_page_rules()
        self._switch_page("Regeln")

    def _add_blocked_word(self):
        word = self.new_block_entry.get().strip()
        if not word:
            return
        rules = self._load_rules()
        rules.setdefault("forbidden_words", {}).setdefault("hard_block", []).append(word)
        self._save_rules(rules)
        self.new_block_entry.delete(0, "end")
        self._log(f"🚫 Blockiert: '{word}'")
        self.pages["Regeln"].destroy()
        self._build_page_rules()
        self._switch_page("Regeln")

    def _save_impressum(self):
        text = self.impressum_box.get("1.0", "end").strip()
        rules = self._load_rules()
        rules.setdefault("country_specific", {}).setdefault("germany", {})["impressum_text"] = text
        self._save_rules(rules)
        self._log("🇩🇪 Impressum gespeichert")

    def _open_rules_file(self):
        f = BASE_DIR / "config" / "legal_rules.json"
        if sys.platform == "win32" and f.exists():
            os.startfile(str(f))

    # ═════════════════════════════════════════════════════════════
    # SEITE 6: KANÄLE
    # ═════════════════════════════════════════════════════════════

    # ═════════════════════════════════════════════════════════════
    # SEITE: CHARAKTERE
    # ═════════════════════════════════════════════════════════════

    def _build_page_characters(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Charaktere"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(top, text="🎭  AI-Charaktere",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        ctk.CTkButton(top, text="＋  Neuer Charakter",
                      font=ctk.CTkFont(size=12, weight="bold"), height=34,
                      fg_color=C["purple"], hover_color=C["accent"],
                      corner_radius=8,
                      command=self._open_new_character_dialog).pack(side="right")

        ctk.CTkLabel(scroll,
                     text="Wähle einen Charakter für deine TikTok-Videos. "
                          "Jeder Kanal kann einen eigenen Charakter bekommen.",
                     font=ctk.CTkFont(size=11), text_color=C["muted"],
                     justify="left").pack(anchor="w", pady=(0, 10))

        self.char_list = ctk.CTkFrame(scroll, fg_color="transparent")
        self.char_list.pack(fill="both", expand=True)

    def _render_characters(self):
        for w in self.char_list.winfo_children():
            w.destroy()

        from character_creator import load_characters, init_starter_characters
        init_starter_characters()
        characters = load_characters()

        _MOVE_LABEL = {
            "talking": "💬 Spricht",
            "dancing": "💃 Tanzt",
            "both":    "💬💃 Spricht & Tanzt",
        }
        _STYLE_COLOR = {
            "talking": C["accent"],
            "dancing": C["purple"],
            "both":    C["orange"],
        }

        cols = 2
        grid = ctk.CTkFrame(self.char_list, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, ch in enumerate(characters):
            row, col = divmod(i, cols)
            mv = ch.get("movement_style", "talking")
            mv_label = _MOVE_LABEL.get(mv, mv)
            mv_color = _STYLE_COLOR.get(mv, C["accent"])

            card = ctk.CTkFrame(grid, fg_color=C["card"], corner_radius=12,
                                border_width=1, border_color=C["border"])
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            # Header
            hdr = ctk.CTkFrame(card, fg_color=C["active_bg"], corner_radius=0,
                                height=48)
            hdr.pack(fill="x")
            hdr.pack_propagate(False)

            ctk.CTkLabel(hdr, text=f"{ch.get('emoji','🎭')}  {ch['name']}",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C["accent"]).pack(side="left", padx=14, pady=12)

            ctk.CTkLabel(hdr, text=mv_label,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=mv_color).pack(side="right", padx=12)

            # Body
            body = ctk.CTkFrame(card, fg_color="transparent")
            body.pack(fill="x", padx=14, pady=10)

            ctk.CTkLabel(body, text=ch.get("description", ""),
                         font=ctk.CTkFont(size=11), text_color=C["muted"],
                         wraplength=260, justify="left").pack(anchor="w")

            # Tags
            tags = ch.get("tags", [])
            if tags:
                tag_row = ctk.CTkFrame(body, fg_color="transparent")
                tag_row.pack(anchor="w", pady=(6, 0))
                for tag in tags[:4]:
                    ctk.CTkLabel(tag_row, text=f"#{tag}",
                                 font=ctk.CTkFont(size=9),
                                 text_color=C["muted"]).pack(side="left", padx=2)

            # Image status
            has_img = bool(ch.get("image_path") and Path(ch["image_path"]).exists())
            img_txt = "✅ Bild vorhanden" if has_img else "⚠️ Kein Bild – Text-to-Video"
            img_col = C["green"] if has_img else C["orange"]
            ctk.CTkLabel(body, text=img_txt,
                         font=ctk.CTkFont(size=10),
                         text_color=img_col).pack(anchor="w", pady=(4, 0))

            # Buttons
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=14, pady=(0, 12))

            cid = ch["id"]
            ctk.CTkButton(btn_row, text="✏️ Bearbeiten", height=28, width=110,
                          font=ctk.CTkFont(size=11), corner_radius=6,
                          fg_color=C["active_bg"], hover_color=C["border"],
                          text_color=C["accent"],
                          command=lambda c=ch: self._open_edit_character_dialog(c)
                          ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(btn_row, text="🎬 Test-Video", height=28, width=110,
                          font=ctk.CTkFont(size=11), corner_radius=6,
                          fg_color=C["purple"], hover_color=C["accent_h"],
                          text_color="white",
                          command=lambda c=cid: self._test_character(c)
                          ).pack(side="left")

    def _open_new_character_dialog(self):
        self._open_edit_character_dialog(None)

    def _open_edit_character_dialog(self, character: dict | None):
        """Dialog zum Erstellen oder Bearbeiten eines Charakters."""
        is_new = character is None
        ch = character or {
            "id": "", "name": "", "emoji": "🎭", "description": "",
            "base_prompt": "", "visual_style": "", "movement_style": "both",
            "image_path": "", "voice_id": "", "tags": [],
        }

        win = ctk.CTkToplevel(self)
        win.title("✨ Neuer Charakter" if is_new else f"✏️ {ch['name']}")
        win.geometry("520x620")
        win.resizable(False, False)
        win.grab_set()
        win.configure(fg_color=C["bg"])

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        def _row(label, var, height=32):
            r = ctk.CTkFrame(scroll, fg_color="transparent")
            r.pack(fill="x", pady=3)
            ctk.CTkLabel(r, text=label, width=130, font=ctk.CTkFont(size=11),
                         text_color=C["muted"], anchor="w").pack(side="left")
            if height == 32:
                e = ctk.CTkEntry(r, textvariable=var, height=height,
                                 fg_color=C["input"], border_color=C["border"],
                                 text_color=C["text"])
            else:
                e = ctk.CTkTextbox(r, height=height, fg_color=C["input"],
                                   border_color=C["border"], text_color=C["text"],
                                   border_width=1)
                e.insert("1.0", var if isinstance(var, str) else var.get())
            e.pack(side="left", fill="x", expand=True)
            return e

        ctk.CTkLabel(scroll, text="Charakter-Profil",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 8))

        id_var    = ctk.StringVar(value=ch["id"])
        name_var  = ctk.StringVar(value=ch["name"])
        emoji_var = ctk.StringVar(value=ch.get("emoji", "🎭"))
        img_var   = ctk.StringVar(value=ch.get("image_path", ""))
        voice_var = ctk.StringVar(value=ch.get("voice_id", ""))
        tags_var  = ctk.StringVar(value=", ".join(ch.get("tags", [])))

        _row("ID (kein Leerzeichen):", id_var)
        _row("Name:", name_var)
        _row("Emoji:", emoji_var)

        ctk.CTkLabel(scroll, text="Bewegungs-Stil:",
                     font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(anchor="w", pady=(6, 2))
        mv_var = ctk.StringVar(value=ch.get("movement_style", "both"))
        mv_row = ctk.CTkFrame(scroll, fg_color="transparent")
        mv_row.pack(fill="x")
        for val, lbl in [("talking","💬 Spricht"), ("dancing","💃 Tanzt"), ("both","💬💃 Beides")]:
            ctk.CTkRadioButton(mv_row, text=lbl, variable=mv_var, value=val,
                               fg_color=C["purple"], text_color=C["text"],
                               font=ctk.CTkFont(size=11)).pack(side="left", padx=8)

        ctk.CTkLabel(scroll, text="Aussehen-Prompt (für Runway):",
                     font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(anchor="w", pady=(8, 2))
        prompt_box = ctk.CTkTextbox(scroll, height=80, fg_color=C["input"],
                                    border_color=C["border"], text_color=C["text"],
                                    border_width=1, font=ctk.CTkFont(size=11))
        prompt_box.insert("1.0", ch.get("base_prompt", ""))
        prompt_box.pack(fill="x")

        ctk.CTkLabel(scroll, text="Visueller Stil (Lighting, Farben, etc.):",
                     font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(anchor="w", pady=(6, 2))
        style_box = ctk.CTkTextbox(scroll, height=50, fg_color=C["input"],
                                   border_color=C["border"], text_color=C["text"],
                                   border_width=1, font=ctk.CTkFont(size=11))
        style_box.insert("1.0", ch.get("visual_style", ""))
        style_box.pack(fill="x")

        _row("Bild-Pfad (optional):", img_var)
        _row("Tags (kommagetrennt):", tags_var)

        ctk.CTkLabel(scroll, text="Beschreibung:",
                     font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(anchor="w", pady=(6, 2))
        desc_box = ctk.CTkTextbox(scroll, height=50, fg_color=C["input"],
                                  border_color=C["border"], text_color=C["text"],
                                  border_width=1, font=ctk.CTkFont(size=11))
        desc_box.insert("1.0", ch.get("description", ""))
        desc_box.pack(fill="x")

        def _save():
            from character_creator import add_character
            new_ch = {
                "id":             id_var.get().strip().replace(" ", "_").lower(),
                "name":           name_var.get().strip(),
                "emoji":          emoji_var.get().strip() or "🎭",
                "description":    desc_box.get("1.0", "end").strip(),
                "base_prompt":    prompt_box.get("1.0", "end").strip(),
                "visual_style":   style_box.get("1.0", "end").strip(),
                "movement_style": mv_var.get(),
                "image_path":     img_var.get().strip(),
                "voice_id":       voice_var.get().strip(),
                "tags":           [t.strip() for t in tags_var.get().split(",") if t.strip()],
                "created":        _dt.now().strftime("%Y-%m-%d"),
            }
            if not new_ch["id"] or not new_ch["name"]:
                self._log("❌ ID und Name sind Pflichtfelder")
                return
            add_character(new_ch)
            self._log(f"✅ Charakter '{new_ch['name']}' gespeichert")
            self.after(0, self._render_characters)
            win.destroy()

        ctk.CTkButton(win, text="💾  Speichern", height=36,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=C["purple"], hover_color=C["accent"],
                      corner_radius=8, command=_save).pack(pady=12, padx=20, fill="x")

    def _test_character(self, character_id: str):
        """Erstellt ein kurzes Test-Video mit dem Charakter (dry-run)."""
        self._log(f"🎭 Test-Video für Charakter '{character_id}' gestartet...")
        self._log("   (Benötigt Runway API-Credits – ~$0.25)")

        def _run():
            try:
                from character_creator import get_character
                ch = get_character(character_id)
                if not ch:
                    self.after(0, lambda: self._log(f"❌ Charakter '{character_id}' nicht gefunden"))
                    return
                self.after(0, lambda: self._log(
                    f"   Charakter: {ch['emoji']} {ch['name']}\n"
                    f"   Prompt: {ch['base_prompt'][:80]}...\n"
                    f"   Zum testen: python character_creator.py --character {character_id} "
                    f"--audio output/voiceover.mp3 --output output/test_char.mp4"
                ))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Fehler: {e}"))

        threading.Thread(target=_run, daemon=True).start()

    def _build_page_channels(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Kanäle"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(top, text="📺  Deine YouTube-Kanäle",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        ctk.CTkButton(top, text="＋  Neuen Kanal hinzufügen",
                      font=ctk.CTkFont(size=12, weight="bold"), height=34,
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      corner_radius=8, command=self._open_add_channel).pack(side="right")

        self.ch_list = ctk.CTkFrame(scroll, fg_color="transparent")
        self.ch_list.pack(fill="both", expand=True)

    def _render_channels(self):
        for w in self.ch_list.winfo_children():
            w.destroy()

        channels = self._load_channels()
        if not channels:
            ctk.CTkLabel(self.ch_list,
                         text="Noch keine Kanäle\n\nKlicke oben auf '+ Neuen Kanal hinzufügen'\noder starte KANAL_HINZUFUEGEN.bat",
                         font=ctk.CTkFont(size=13), text_color=C["muted"],
                         justify="center").pack(pady=40)
            return

        _CT_BADGE = {
            "story":  ("📖 Story",  C["accent"]),
            "ads":    ("🛍️ Ads",   C["purple"]),
            "kids":   ("👶 Kids",  C["green"]),
            "reddit": ("🎭 Reddit", C["orange"]),
        }
        _AM_BADGE = {
            "script":     "Script-Pipeline",
            "ai_runway":  "⚡ KI-Runway",
        }

        for ch in channels:
            ok_token = ch.get("_token", False)
            ok_secret = ch.get("_secret", False)
            active = ch.get("active", True)

            color = C["green"] if ok_token else (C["orange"] if ok_secret else C["red"])
            status = "✓ Verbunden" if ok_token else ("○ Bereit" if ok_secret else "✗ Secret fehlt")
            ct = ch.get("content_type", "story")
            ct_label, ct_color = _CT_BADGE.get(ct, ("📖 Story", C["accent"]))

            card = ctk.CTkFrame(self.ch_list, fg_color=C["card"], corner_radius=10,
                                border_width=1, border_color=C["border"])
            card.pack(fill="x", pady=4)

            bar = ctk.CTkFrame(card, fg_color=ct_color, width=4, corner_radius=0)
            bar.pack(side="left", fill="y")

            mid = ctk.CTkFrame(card, fg_color="transparent")
            mid.pack(side="left", fill="both", expand=True, padx=14, pady=10)

            nr = ctk.CTkFrame(mid, fg_color="transparent")
            nr.pack(fill="x")
            ctk.CTkLabel(nr, text=ch.get("name", ch["_id"]),
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C["text"]).pack(side="left")

            # Content-Typ Badge
            ctk.CTkLabel(nr, text=f"  {ct_label}",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=ct_color).pack(side="left", padx=6)

            # Ads-Modus Badge
            if ct == "ads":
                am = _AM_BADGE.get(ch.get("ads_mode", "script"), "Script")
                ctk.CTkLabel(nr, text=f"· {am}",
                             font=ctk.CTkFont(size=10),
                             text_color=C["muted"]).pack(side="left")

            if not active:
                ctk.CTkLabel(nr, text="  INAKTIV",
                             font=ctk.CTkFont(size=10, weight="bold"),
                             text_color=C["orange"]).pack(side="left", padx=4)

            details = f"ID: {ch['_id']}  •  {ch.get('language', 'de').upper()}  •  {ch.get('niche', '-')}"
            topics = ch.get("topics", [])
            if topics:
                details += f"  •  {len(topics)} Topics"
            ctk.CTkLabel(mid, text=details, font=ctk.CTkFont(size=11),
                         text_color=C["muted"]).pack(anchor="w")

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=12)

            ctk.CTkLabel(right, text=status,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=color).pack(pady=(8, 2))

            cid = ch["_id"]
            ctk.CTkButton(right, text="▶ Starten", height=28, width=100,
                          font=ctk.CTkFont(size=11), corner_radius=6,
                          fg_color=C["accent"], hover_color=C["accent_h"],
                          command=lambda c=cid: self._run_channel(c)).pack(pady=(0, 4))

            ctk.CTkButton(right, text="⚙️ Typ ändern", height=24, width=100,
                          font=ctk.CTkFont(size=10), corner_radius=6,
                          fg_color=C["active_bg"], hover_color=C["border"],
                          text_color=C["accent"],
                          command=lambda c=cid: self._open_channel_settings(c)).pack(pady=(0, 4))

            ctk.CTkButton(right, text="📂 Öffnen", height=24, width=100,
                          font=ctk.CTkFont(size=10), corner_radius=6,
                          fg_color=C["card_hover"], hover_color=C["border"],
                          text_color=C["text"],
                          command=lambda c=cid: self._open_channel_dir(c)).pack(pady=(0, 6))

    def _open_channel_settings(self, cid: str):
        """Dialog zum Ändern des Content-Typs und Ads-Modus eines Kanals."""
        cfg_path = BASE_DIR / "channels" / cid / "channel_config.json"
        if not cfg_path.exists():
            self._log(f"❌ channel_config.json für '{cid}' nicht gefunden")
            return

        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        win = ctk.CTkToplevel(self)
        win.title(f"⚙️  {cfg.get('name', cid)} – Content-Typ")
        win.geometry("480x520")
        win.resizable(False, False)
        win.grab_set()
        win.configure(fg_color=C["bg"])

        ctk.CTkLabel(win, text=f"Content-Typ für: {cfg.get('name', cid)}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["text"]).pack(pady=(20, 4), padx=24, anchor="w")
        ctk.CTkLabel(win, text="Welche Art von Videos produziert dieser Kanal?",
                     font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(padx=24, anchor="w")

        # Content-Typ Auswahl
        ct_var = ctk.StringVar(value=cfg.get("content_type", "story"))
        am_var = ctk.StringVar(value=cfg.get("ads_mode", "script"))

        type_frame = ctk.CTkFrame(win, fg_color=C["card"], corner_radius=10,
                                   border_width=1, border_color=C["border"])
        type_frame.pack(fill="x", padx=24, pady=12)

        types = [
            ("📖", "story",  "Story / Doku",   "Storytelling, Geschichte, Biographien"),
            ("🛍️", "ads",   "Produkt-Ads",    "Werbeclips für Produkte"),
            ("👶", "kids",   "Kinder-Content", "COPPA-konform, bunte Animationen"),
            ("🎭", "reddit", "Reddit Stories", "Reddit-Posts als dramatische Videos"),
        ]

        for emoji, val, label, desc in types:
            row = ctk.CTkFrame(type_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkRadioButton(row, text=f"{emoji}  {label}", variable=ct_var, value=val,
                               font=ctk.CTkFont(size=12, weight="bold"),
                               text_color=C["text"],
                               fg_color=C["accent"],
                               command=lambda: _toggle_ads_frame()).pack(side="left")
            ctk.CTkLabel(row, text=f"  — {desc}", font=ctk.CTkFont(size=10),
                         text_color=C["muted"]).pack(side="left")

        # Ads-Modus (nur sichtbar wenn Ads gewählt)
        ads_frame = ctk.CTkFrame(win, fg_color=C["card"], corner_radius=10,
                                  border_width=1, border_color=C["border"])

        ctk.CTkLabel(ads_frame, text="Ads-Modus:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=12, pady=(10, 4))

        for val, label, desc in [
            ("script",    "Script-Pipeline",
             "GPT schreibt Ad-Text → Voiceover → Video. Günstig, hohe Stückzahl."),
            ("ai_runway", "⚡ KI-Runway (Premium)",
             "Produktfoto/Beschreibung → Runway Gen-4 generiert KI-Video. ~$0.25/Video."),
        ]:
            r = ctk.CTkFrame(ads_frame, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=3)
            ctk.CTkRadioButton(r, text=label, variable=am_var, value=val,
                               font=ctk.CTkFont(size=12),
                               text_color=C["text"],
                               fg_color=C["purple"]).pack(side="left")
            ctk.CTkLabel(r, text=f"  {desc}", font=ctk.CTkFont(size=10),
                         text_color=C["muted"], wraplength=280,
                         justify="left").pack(side="left", padx=6)

        # Produkt-Info Felder (nur bei KI-Runway)
        prod_cfg = cfg.get("product", {})
        prod_frame = ctk.CTkFrame(win, fg_color=C["card"], corner_radius=10,
                                   border_width=1, border_color=C["border"])

        ctk.CTkLabel(prod_frame, text="Produkt-Info für KI-Runway:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=12, pady=(10, 4))

        pf1 = ctk.CTkFrame(prod_frame, fg_color="transparent")
        pf1.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(pf1, text="Produktname:", width=120, font=ctk.CTkFont(size=11),
                     text_color=C["muted"]).pack(side="left")
        prod_name_var = ctk.StringVar(value=prod_cfg.get("name", ""))
        ctk.CTkEntry(pf1, textvariable=prod_name_var, height=28,
                     fg_color=C["input"], border_color=C["border"],
                     text_color=C["text"]).pack(side="left", fill="x", expand=True)

        pf2 = ctk.CTkFrame(prod_frame, fg_color="transparent")
        pf2.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(pf2, text="Beschreibung:", width=120, font=ctk.CTkFont(size=11),
                     text_color=C["muted"]).pack(side="left")
        prod_desc_var = ctk.StringVar(value=prod_cfg.get("description", ""))
        ctk.CTkEntry(pf2, textvariable=prod_desc_var, height=28,
                     fg_color=C["input"], border_color=C["border"],
                     text_color=C["text"]).pack(side="left", fill="x", expand=True)

        pf3 = ctk.CTkFrame(prod_frame, fg_color="transparent")
        pf3.pack(fill="x", padx=12, pady=(3, 10))
        ctk.CTkLabel(pf3, text="Bild-Pfad:", width=120, font=ctk.CTkFont(size=11),
                     text_color=C["muted"]).pack(side="left")
        prod_img_var = ctk.StringVar(value=prod_cfg.get("image_path", ""))
        ctk.CTkEntry(pf3, textvariable=prod_img_var, height=28,
                     fg_color=C["input"], border_color=C["border"],
                     text_color=C["text"]).pack(side="left", fill="x", expand=True)

        def _toggle_ads_frame():
            is_ads = ct_var.get() == "ads"
            if is_ads:
                ads_frame.pack(fill="x", padx=24, pady=(0, 8))
                _toggle_prod_frame()
            else:
                ads_frame.pack_forget()
                prod_frame.pack_forget()

        def _toggle_prod_frame(*_):
            if ct_var.get() == "ads" and am_var.get() == "ai_runway":
                prod_frame.pack(fill="x", padx=24, pady=(0, 8))
            else:
                prod_frame.pack_forget()

        am_var.trace_add("write", _toggle_prod_frame)

        # Initial sichtbarkeit
        _toggle_ads_frame()

        # Speichern
        # Charakter-Zuweisung
        char_frame = ctk.CTkFrame(win, fg_color=C["card"], corner_radius=10,
                                   border_width=1, border_color=C["border"])
        char_frame.pack(fill="x", padx=24, pady=(0, 8))
        ctk.CTkLabel(char_frame, text="🎭  TikTok-Charakter:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=12, pady=(10, 4))

        from character_creator import load_characters, init_starter_characters
        init_starter_characters()
        char_options = ["(Kein Charakter)"] + [
            f"{c.get('emoji','')} {c['name']} [{c['id']}]"
            for c in load_characters()
        ]
        current_char = cfg.get("character_id", "")
        current_display = next((o for o in char_options if f"[{current_char}]" in o),
                               "(Kein Charakter)")
        char_var = ctk.StringVar(value=current_display)
        ctk.CTkOptionMenu(char_frame, variable=char_var, values=char_options,
                          fg_color=C["input"], button_color=C["accent"],
                          text_color=C["text"],
                          font=ctk.CTkFont(size=11)).pack(fill="x", padx=12, pady=(0, 10))

        def _save():
            cfg["content_type"] = ct_var.get()
            cfg["ads_mode"] = am_var.get()
            cfg.setdefault("product", {})
            cfg["product"]["name"] = prod_name_var.get()
            cfg["product"]["description"] = prod_desc_var.get()
            cfg["product"]["image_path"] = prod_img_var.get()

            sel = char_var.get()
            if "[" in sel and "]" in sel:
                cfg["character_id"] = sel.split("[")[-1].rstrip("]")
            else:
                cfg.pop("character_id", None)

            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)

            self._log(f"✅ Kanal '{cid}': Typ={cfg['content_type']} · "
                      f"Charakter={cfg.get('character_id','keiner')}")
            self.after(0, self._render_channels)
            win.destroy()

        ctk.CTkButton(win, text="💾  Speichern", height=36,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      corner_radius=8, command=_save).pack(pady=12, padx=24, fill="x")

    # ═════════════════════════════════════════════════════════════
    # SEITE 6: LOG
    # ═════════════════════════════════════════════════════════════

    def _build_page_log(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["Log"] = page

        ctk.CTkLabel(page, text="  📋  Live-Log",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=16, pady=(12, 4))

        self.log_box = ctk.CTkTextbox(page, fg_color=C["bg2"],
                                      text_color=C["text"],
                                      font=ctk.CTkFont(family="Courier New", size=11),
                                      corner_radius=8, wrap="word",
                                      border_width=1, border_color=C["border"])
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.log_box.configure(state="disabled")
        self._log("🟢 Dashboard gestartet")
        self._log(f"📂 Verzeichnis: {BASE_DIR}")

        # Buttons unten
        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(btn_row, text="📋 Log-Datei öffnen",
                      font=ctk.CTkFont(size=11), height=30, corner_radius=6,
                      fg_color=C["card"], hover_color=C["card_hover"],
                      text_color=C["text"], command=self._open_log_file).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="🗑️ Log leeren",
                      font=ctk.CTkFont(size=11), height=30, corner_radius=6,
                      fg_color=C["card"], hover_color=C["red"],
                      text_color=C["text"], command=self._clear_log).pack(side="left", padx=4)

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._log("🗑️ Log geleert")

    # ── Card-Helfer (ohne extra Wrapper) ─────────────────────────

    def _card_in(self, parent, title: str) -> ctk.CTkFrame:
        if title:
            ctk.CTkLabel(parent, text=title,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C["muted"]).pack(anchor="w", pady=(0, 4))
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        card.pack(fill="x", pady=(0, 8))
        return card

    # ═════════════════════════════════════════════════════════════
    # AUTOMATION STARTEN / STOPPEN
    # ═════════════════════════════════════════════════════════════

    def _run_automation(self):
        if self.running:
            self._log("⚠️ Automation läuft bereits!")
            return

        cmd = [sys.executable, "main.py"]
        sel = self.ch_var.get()
        if sel != "Alle aktiven Kanäle":
            m = re.search(r'\[(.+)\]', sel)
            if m:
                cmd += ["--channel", m.group(1)]
        topic = self.topic_var.get().strip()
        if topic:
            cmd += ["--topic", topic]
        if self.dry_var.get():
            cmd.append("--dry-run")

        self._log(f"🚀 Starte: {' '.join(cmd)}")
        self._set_running(True)
        self._reset_steps()
        threading.Thread(target=self._process, args=(cmd,), daemon=True).start()

    def _run_channel(self, cid: str):
        if self.running:
            self._log("⚠️ Automation läuft bereits!")
            return
        cmd = [sys.executable, "main.py", "--channel", cid]
        if self.dry_var.get():
            cmd.append("--dry-run")
        self._log(f"▶ Kanal '{cid}': {' '.join(cmd)}")
        self._set_running(True)
        self._reset_steps()
        threading.Thread(target=self._process, args=(cmd,), daemon=True).start()

    def _stop_automation(self):
        if self.process:
            self.process.terminate()
            self._log("⏹ Gestoppt")
            self._set_running(False)

    def _process(self, cmd):
        try:
            self.process = subprocess.Popen(cmd, cwd=str(BASE_DIR),
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            text=True, encoding="utf-8", errors="replace", bufsize=1)
            kw_map = {"recherche": 0, "topic": 0, "script": 1, "compliance": 2,
                      "voiceover": 3, "audio": 3, "thumbnail": 4, "video": 5,
                      "upload": 6, "youtube": 6}
            cur = -1
            for line in self.process.stdout:
                line = line.rstrip()
                if not line:
                    continue
                self.after(0, lambda l=line: self._log(l))
                for kw, idx in kw_map.items():
                    if kw in line.lower() and idx > cur:
                        cur = idx
                        self.after(0, lambda s=idx: self._step_run(s))
                        if idx > 0:
                            self.after(0, lambda p=idx-1: self._step_done(p))

            ret = self.process.wait()
            if ret == 0:
                for i in range(len(PIPELINE)):
                    self.after(0, lambda i=i: self._step_done(i))
                self.after(0, lambda: self._log("✅ Erfolgreich abgeschlossen!"))
                self.after(0, lambda: self.status_dot.configure(
                    text="● Fertig ✓", text_color=C["green"]))
                # Idee als fertig markieren
                topic = self.topic_var.get().strip()
                if topic:
                    for idea in self.ideas:
                        if idea["title"] == topic and idea["status"] == "läuft":
                            idea["status"] = "fertig"
                    self._save_ideas()
            else:
                self.after(0, lambda: self._log(f"❌ Fehler (Code {ret})"))
                self.after(0, lambda: self.status_dot.configure(
                    text="● Fehler", text_color=C["red"]))
        except Exception as e:
            self.after(0, lambda: self._log(f"❌ {e}"))
        finally:
            self.process = None
            self.after(0, lambda: self._set_running(False))
            self.after(0, self._refresh_all)

    # ── Step-Animation ───────────────────────────────────────────

    def _reset_steps(self):
        for f in self.step_frames:
            f.configure(fg_color=C["step_wait"])

    def _step_run(self, i):
        if 0 <= i < len(self.step_frames):
            self.step_frames[i].configure(fg_color=C["step_run"])

    def _step_done(self, i):
        if 0 <= i < len(self.step_frames):
            self.step_frames[i].configure(fg_color=C["step_done"])

    def _set_running(self, on: bool):
        self.running = on
        if on:
            self.run_btn.configure(state="disabled", text="⏳  Läuft...")
            self.status_dot.configure(text="● Läuft...", text_color=C["accent"])
        else:
            self.run_btn.configure(state="normal", text="▶   STARTEN")

    # ── Refresh ──────────────────────────────────────────────────

    def _refresh_all(self):
        self.settings = self._load_settings()
        chs = self._load_channels()
        active = sum(1 for c in chs if c.get("active", True))
        self.stat_cards["Kanäle"].configure(text=str(active))

        out = BASE_DIR / "output"
        vids = sum(1 for _ in out.rglob("*.mp4")) if out.exists() else 0
        self.stat_cards["Videos"].configure(text=str(vids))

        ok_key = bool(self.settings.get("api_keys", {}).get("openai", ""))
        self.stat_cards["OpenAI"].configure(
            text="✓ OK" if ok_key else "✗",
            text_color=C["green"] if ok_key else C["red"])

        ok_fish = bool(self.settings.get("api_keys", {}).get("fish_audio", ""))
        self.stat_cards["Fish Audio"].configure(
            text="✓ OK" if ok_fish else "✗",
            text_color=C["green"] if ok_fish else C["red"])

        opts = ["Alle aktiven Kanäle"]
        for ch in chs:
            opts.append(f"{ch.get('name', ch['_id'])} [{ch['_id']}]")
        self.ch_menu.configure(values=opts)

        self.after(8000, self._refresh_all)

    # ── Ordner öffnen ────────────────────────────────────────────

    def _open_output(self):
        p = BASE_DIR / "output"
        p.mkdir(exist_ok=True)
        if sys.platform == "win32": os.startfile(str(p))

    def _open_settings(self):
        if sys.platform == "win32": os.startfile(str(BASE_DIR / "config" / "settings.json"))

    def _open_add_channel(self):
        bat = BASE_DIR / "KANAL_HINZUFUEGEN.bat"
        if sys.platform == "win32" and bat.exists():
            os.startfile(str(bat))
        self._log("📺 Kanal hinzufügen gestartet")

    def _open_channel_dir(self, cid):
        p = BASE_DIR / "channels" / cid
        if sys.platform == "win32" and p.exists():
            os.startfile(str(p))

    def _open_log_file(self):
        f = BASE_DIR / "logs" / "automation.log"
        if f.exists() and sys.platform == "win32":
            os.startfile(str(f))


# ═════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        # Fehler in Datei speichern
        crash_file = Path(__file__).parent / "CRASH_LOG.txt"
        with open(crash_file, "w", encoding="utf-8") as f:
            f.write(f"Dashboard Crash: {datetime.now()}\n")
            f.write("=" * 60 + "\n")
            f.write(error_msg)
        # Fehler auch in Konsole anzeigen
        print("\n" + "=" * 60)
        print("DASHBOARD FEHLER:")
        print("=" * 60)
        print(error_msg)
        print("=" * 60)
        print(f"Fehler-Log gespeichert in: {crash_file}")
        print("Bitte diesen Text an Claude schicken!")
        print("=" * 60)
        input("Drücke Enter zum Schließen...")
