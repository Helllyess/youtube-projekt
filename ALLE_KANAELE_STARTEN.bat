@echo off
echo ============================================
echo   YouTube Automation v2.1
echo   ALLE Kanaele starten
echo ============================================
echo.
cd /d "%~dp0"

echo Aktuelle Kanaele:
python channel_manager.py --list
echo.

echo Starte Pipeline fuer ALLE aktiven Kanaele...
echo (Jeder Kanal bekommt ein eigenes Video)
echo.

python main.py %*

echo.
echo Fertig! Alle Kanaele verarbeitet.
pause
