@echo off
title YouTube Automation - Alle Bibliotheken installieren
cd /d "%~dp0"
echo.
echo  ============================================
echo    ALLE BIBLIOTHEKEN INSTALLIEREN
echo  ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLER] Python nicht gefunden!
    echo Installiere Python von: https://python.org
    echo WICHTIG: Haken bei "Add Python to PATH" setzen!
    pause
    exit /b 1
)

echo [OK] Python gefunden:
python --version
echo.

echo [1/8] requests (fuer Fish Audio API)...
pip install requests --quiet
echo [2/8] openai (fuer GPT Scripts + Recherche)...
pip install openai --quiet
echo [3/8] google-api-python-client (fuer YouTube Upload)...
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib --quiet
echo [4/8] Pillow (fuer Thumbnails)...
pip install Pillow --quiet
echo [5/8] moviepy (fuer Video-Erstellung)...
pip install moviepy --quiet
echo [6/8] gTTS + pydub (fuer Voiceover)...
pip install gtts pydub --quiet
echo [7/8] customtkinter (fuer Dashboard)...
pip install customtkinter --quiet
echo [8/8] numpy (fuer MoviePy)...
pip install numpy --quiet
echo.

echo ============================================
echo  PRUEFE OB ALLES FUNKTIONIERT:
echo ============================================
echo.

python -c "import requests; print('[OK] requests', requests.__version__)"
python -c "import openai; print('[OK] openai', openai.__version__)"
python -c "from googleapiclient.discovery import build; print('[OK] google-api-python-client')"
python -c "from PIL import Image; print('[OK] Pillow')"
python -c "import customtkinter; print('[OK] customtkinter', customtkinter.__version__)"
python -c "import gtts; print('[OK] gTTS')"
python -c "import numpy; print('[OK] numpy', numpy.__version__)"

echo.
python -c "import moviepy; print('[OK] moviepy')" 2>nul
if %errorlevel% neq 0 (
    echo [!] moviepy hat evtl. Probleme - ffmpeg muss installiert sein
    echo     Download: https://ffmpeg.org/download.html
)

echo.
echo ============================================
echo  FFmpeg pruefen:
echo ============================================
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLT] FFmpeg ist NICHT installiert!
    echo.
    echo  So installierst du FFmpeg:
    echo  1. Gehe zu: https://ffmpeg.org/download.html
    echo  2. Lade "ffmpeg-release-essentials.zip" herunter
    echo  3. Entpacke den Ordner z.B. nach C:\ffmpeg
    echo  4. Fuege C:\ffmpeg\bin zu deinem PATH hinzu:
    echo     - Windows-Suche: "Umgebungsvariablen"
    echo     - System PATH bearbeiten
    echo     - C:\ffmpeg\bin hinzufuegen
    echo  5. PC neu starten
    echo.
) else (
    echo [OK] FFmpeg ist installiert
)

echo.
echo ============================================
echo  FERTIG! Du kannst jetzt START_DASHBOARD.bat
echo  starten.
echo ============================================
echo.
pause
