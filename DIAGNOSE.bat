@echo off
title Diagnose
cd /d "%~dp0"
echo.
echo ============================================
echo  DIAGNOSE - YouTube Automation Dashboard
echo ============================================
echo.

echo [1] Python:
python --version 2>&1
where python 2>&1
echo.

echo [2] pip:
pip --version 2>&1
echo.

echo [3] customtkinter installieren:
pip install customtkinter
echo.

echo [4] Test-Start:
python -c "import customtkinter; print('customtkinter OK:', customtkinter.__version__)"
echo.

echo [5] Dashboard direkt starten:
python dashboard_app.py

pause
