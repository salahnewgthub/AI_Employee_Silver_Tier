@echo off
echo ============================================
echo   AI Employee - Task Scheduler Setup
echo ============================================
echo.
echo This will create scheduled tasks for:
echo   1. Daily Briefing (every day at 8:00 AM)
echo   2. Orchestrator Heartbeat (every 15 minutes)
echo   3. LinkedIn Draft Check (every 2 days at 9:00 AM)
echo.
echo IMPORTANT: This script must be run as Administrator!
echo.
pause
echo.

python "%~dp0scripts\setup_scheduler.py"

echo.
pause
