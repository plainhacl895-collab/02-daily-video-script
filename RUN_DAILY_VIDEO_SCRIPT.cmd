@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   每日视频脚本生成器
echo ========================================
echo.

python "%~dp0generate_script.py" %*

echo.
echo ========================================
pause
