@echo off
title YouTube Automation v2.1 - Dashboard
cd /d "%~dp0"
echo.
echo  ============================================
echo    YouTube Automation v2.1 - Dashboard
echo  ============================================
echo.

REM ── Python pruefen ───────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLER] Python nicht gefunden!
    echo.
    echo Bitte installiere Python von: https://python.org
    echo WICHTIG: Haken bei "Add Python to PATH" setzen!
    pause
    exit /b 1
)
echo [OK] Python:
python --version

REM ── Bibliotheken installieren ────────────────────────────────
echo.
echo [..] Installiere/pruefe Bibliotheken...
pip install customtkinter --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [!] Versuche alternative Installation...
    python -m pip install customtkinter
)
echo [OK] Bibliotheken fertig

REM ── Dashboard starten ────────────────────────────────────────
echo.
echo [>>] Starte Dashboard...
echo      (Dieses Fenster kann minimiert werden)
echo.

python dashboard_app.py

REM ── Fehler abfangen ─────────────────────────────────────────
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo  FEHLER beim Starten! Bitte lesen:
    echo ============================================
    echo.
    echo Moegliche Loesungen:
    echo  1) pip install customtkinter
    echo  2) Python neu installieren (python.org)
    echo     - Haken "Add to PATH" setzen!
    echo  3) Diesen Fehler an Claude schicken
    echo.
)
pause
