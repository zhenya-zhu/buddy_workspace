@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0autostart.ps1" -Action install
echo.
echo 已设置开机自启动。重新登录后页面会自动在 6996 端口就绪。
echo 取消：双击 uninstall-autostart.bat
pause
