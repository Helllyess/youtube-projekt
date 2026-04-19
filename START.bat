@echo off
echo ============================================
echo   YouTube Automation v2.1 - Starter
echo ============================================
echo.

REM Wechsle ins Script-Verzeichnis
cd /d "%~dp0"

REM Prüfe ob Python installiert ist
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installiere Python von https://python.org
    pause
    exit /b 1
)

REM Prüfe ob Abhängigkeiten installiert sind
python -c "import openai" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installiere Abhaengigkeiten...
    pip install -r requirements.txt
    echo.
)

echo Starte YouTube Automation...
echo.

REM Optionen:
REM --dry-run : Kein Upload, nur Video erstellen
REM --topic "Mein Topic" : Manuelles Topic
REM (leer lassen = automatisches Trend-Topic)

python main.py %*

echo.
echo Fertig! Druecke eine Taste zum Beenden.
pause
