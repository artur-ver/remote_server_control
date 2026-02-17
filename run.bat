@echo off
cd /d "%~dp0"
echo Starting RSC Server...
".venv\Scripts\python.exe" app.py
pause