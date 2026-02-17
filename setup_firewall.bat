@echo off
echo ==================================================
echo   RSC Firewall Setup
echo ==================================================

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Admin privileges confirmed.
) else (
    echo [ERROR] Current permissions are insufficient.
    echo.
    echo Please right-click this file and select "Run as Administrator".
    echo.
    pause
    exit /b
)

echo.
echo Adding Firewall Rule for Port 5000...
netsh advfirewall firewall add rule name="RSC Web Server" dir=in action=allow protocol=TCP localport=5000

if %errorLevel% == 0 (
    echo.
    echo [SUCCESS] Firewall rule added successfully.
    echo You should now be able to connect from other devices.
) else (
    echo.
    echo [FAILED] Could not add firewall rule.
)
echo.
pause