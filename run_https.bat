@echo off
cd /d "%~dp0"
echo Starting RSC Server (HTTPS Mode)...
echo.
echo NOTE: You will see a "Not Secure" warning in your browser.
echo       This is normal for a self-signed certificate.
echo       Click "Advanced" -> "Proceed" to continue.
echo.
echo NOTE: Ensure port 5000 is open in your firewall.
echo.
".venv\Scripts\python.exe" app.py ssl
pause