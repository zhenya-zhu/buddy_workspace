@echo off
chcp 65001 >nul
cd /d "%~dp0"
if defined DEVICE_NAV_PYTHON (
  "%DEVICE_NAV_PYTHON%" server.py
  goto :end
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py
) else (
  python server.py
)
:end
pause
