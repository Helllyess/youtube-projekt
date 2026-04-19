@echo off
echo ============================================
echo   YouTube Automation v2.1
echo   Einzelnen Kanal starten
echo ============================================
echo.
cd /d "%~dp0"

echo Verfuegbare Kanaele:
python channel_manager.py --list
echo.

set /p KANAL_ID="Kanal-ID eingeben (z.B. kanal_hauptkanal): "

echo.
echo Starte Pipeline fuer Kanal: %KANAL_ID%
echo.

python main.py --channel "%KANAL_ID%" %*

echo.
pause
