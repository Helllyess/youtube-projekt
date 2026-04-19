@echo off
echo ============================================
echo   YouTube Automation v2.1
echo   Neuen Kanal hinzufuegen
echo ============================================
echo.
cd /d "%~dp0"

echo Bestehende Kanaele:
python channel_manager.py --list
echo.

set /p KANAL_ID="Kanal-ID eingeben (z.B. kanal2, kein Leerzeichen): "
set /p KANAL_NAME="Kanal-Name eingeben (z.B. Mein Trading Kanal): "
set /p SPRACHE="Sprache (de/en, Standard: de): "

if "%SPRACHE%"=="" set SPRACHE=de

echo.
echo Erstelle Kanal '%KANAL_NAME%' (ID: %KANAL_ID%)...
python channel_manager.py --create --id "%KANAL_ID%" --name "%KANAL_NAME%" --language "%SPRACHE%"

echo.
echo ============================================
echo NAECHSTE SCHRITTE:
echo ============================================
echo.
echo 1. Oeffne den Ordner: channels\%KANAL_ID%\
echo.
echo 2. Ersetze die Datei 'youtube_client_secret.json'
echo    mit deiner echten OAuth-Datei von:
echo    console.cloud.google.com
echo    (APIs ^& Dienste - Anmeldedaten - Desktop-App)
echo.
echo 3. Starte das System fuer diesen Kanal:
echo    python main.py --channel %KANAL_ID%
echo.
pause
